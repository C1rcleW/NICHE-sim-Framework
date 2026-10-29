from __future__ import annotations

import asyncio
import functools
import json
import logging
import math
import os
import threading
import uuid
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, ConfigDict, Field, StrictInt, field_validator, model_validator

from ..core.environment import Environment
from ..core.scheduler import Scheduler
from ..core.simulation import Simulation
from ..family.family_member import FamilyMember
from ..family.household import Household
from ..fitting.fitter import make_fitter
from ..fitting.lanchester import MODEL_REGISTRY, MODEL_STATE_NAMES
from ..ml.recorder import StateRecorder
from ..niche.micro_niche import MicroNiche
from ..parameters import (
    MAX_FAMILIES,
    MAX_MEMBERS_PER_FAMILY,
    MAX_STEPS,
    MAX_TOTAL_MEMBERS,
    PARAM_GROUPS,
    PARAM_SPECS,
    SIM_LIMITS,
)
from .run_store import RunSnapshot, RunStore, UnknownRunError

HERE = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(HERE / 'templates'))


def _package_version() -> str:
    """版本号取自包源代码声明，避免与 pyproject.toml 漂移。

    round-2 审查 D8：此处曾硬编码 `version='0.2.0'`，而包版本已是 0.1.0，
    于是 /openapi.json 报告的版本与实际安装的包不一致（对外文档错误）。
    单一真源是 pyproject.toml 的 [project].version（见 family_abm/__init__.py，
    两者由 tests/test_packaging.py 强制一致）。

    这里优先用源码里的 `__version__` 而不是 `importlib.metadata.version()`：
    后者读的是**安装元数据**，在 editable 安装下可能滞后于源码（改了版本号但
    没重装时会报出旧版本，实测踩到过）。源码版本才是与 pyproject 同步的那个。
    """
    from .. import __version__

    return __version__


app = FastAPI(title='Family ABM Dashboard', version=_package_version())
app.mount('/static', StaticFiles(directory=str(HERE / 'static')), name='static')


@app.exception_handler(RequestValidationError)
async def _validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """把校验错误也变成**必然可序列化**的结构化 JSON。

    背景：Pydantic 的 422 详情里会回显出错位置的输入值与上下文。当输入含
    `nan`/`inf` 时（JSON 允许这两个字面量），`float('nan')` 无法被序列化成合法
    JSON；`model_validator` 里抛出的异常对象还会被放进 `ctx`。两者都会让
    FastAPI 在**生成 422 响应时自己抛错**——错误处理反而变成故障。

    这里对每个字段做一次试探性序列化，不可序列化的降级为字符串表示，
    保证响应一定发得出去。

    契约与其它端点一致：`{'error': ..., 'status': 'validation_error'}` + 原始详情。
    """

    def _safe(value: Any) -> Any:
        """能序列化就原样保留，否则降级为 repr（保留可读性又不破坏 JSON）。"""
        try:
            json.dumps(value, allow_nan=False)
        except (TypeError, ValueError):
            return repr(value)
        return value

    errors = []
    for err in exc.errors():
        item = {key: _safe(val) for key, val in err.items()}
        errors.append(item)

    first = errors[0].get('msg', '请求体校验失败') if errors else '请求体校验失败'
    return JSONResponse(
        {
            'error': f'请求体校验失败：{first}',
            'status': 'validation_error',
            'detail': errors,
        },
        422,
    )

logger = logging.getLogger('family_abm.web')

# /api/fit 的 CPU 密集工作放在 worker 线程里执行（见 api_fit），超过该秒数即返回
# 结构化 504。可用环境变量 FAMILY_ABM_FIT_TIMEOUT_SECONDS 覆盖；非法值回退默认值。
DEFAULT_FIT_TIMEOUT_SECONDS = 120.0


def _load_fit_timeout_seconds() -> float:
    raw = os.environ.get('FAMILY_ABM_FIT_TIMEOUT_SECONDS', '').strip()
    if not raw:
        return DEFAULT_FIT_TIMEOUT_SECONDS
    try:
        seconds = float(raw)
    except ValueError:
        logger.warning('FAMILY_ABM_FIT_TIMEOUT_SECONDS=%r 不是数字，回退到 %.0fs',
                       raw, DEFAULT_FIT_TIMEOUT_SECONDS)
        return DEFAULT_FIT_TIMEOUT_SECONDS
    if not math.isfinite(seconds) or seconds <= 0:
        logger.warning('FAMILY_ABM_FIT_TIMEOUT_SECONDS=%r 不是有限正数，回退到 %.0fs',
                       raw, DEFAULT_FIT_TIMEOUT_SECONDS)
        return DEFAULT_FIT_TIMEOUT_SECONDS
    return seconds


FIT_TIMEOUT_SECONDS = _load_fit_timeout_seconds()

# ── Run state and heavy-work slots ─────────────────────────────────────────
_run_store = RunStore()
_run_slot = threading.BoundedSemaphore(1)
_fit_slot = threading.BoundedSemaphore(1)


def _resolve_run(run_id: str | None) -> tuple[RunSnapshot | None, JSONResponse | None]:
    try:
        snapshot = _run_store.get(run_id or None)
    except UnknownRunError as exc:
        return None, JSONResponse({
            'error': (
                f'未知运行 {exc.run_id!r}。该结果可能已被新运行替换；'
                '请重新运行仿真或使用当前 run_id。'
            ),
            'status': 'unknown_run',
        }, 404)
    if snapshot is None:
        return None, JSONResponse({
            'error': 'No simulation data. POST /api/run first.',
            'status': 'no_simulation',
        }, 400)
    return snapshot, None

# ── Pydantic models ────────────────────────────────────────────────────────

class MemberConfig(BaseModel):
    """家庭成员输入。

    只允许公开字段：任意额外键既不会参与动力学，又可能沿用 ``**kwargs``
    进入智能体构造器，造成 500 或注入非预期状态列。未知字段在校验层直接拒绝。
    """
    model_config = ConfigDict(allow_inf_nan=False, extra='forbid')

    name: str
    age: float = 25.0
    gender: str = 'other'
    role_name: str = 'adult'
    personality: dict[str, float] | None = None

    @field_validator('age', mode='before')
    @classmethod
    def _age_not_bool(cls, value: Any) -> Any:
        if isinstance(value, bool):
            raise ValueError(f'age 必须是数值，收到 {value!r}')
        return value

    @field_validator('age')
    @classmethod
    def _age_reasonable(cls, value: float) -> float:
        """年龄必须在合理区间：负年龄或超大年龄会让生命阶段推导失去意义。"""
        if value < 0 or value > 120:
            raise ValueError(f'age 必须在 0–120 之间，收到 {value}')
        return value


class FamilyConfig(BaseModel):
    model_config = ConfigDict(extra='forbid')

    name: str
    members: list[MemberConfig] = Field(default_factory=list)


class SimConfig(BaseModel):
    # allow_inf_nan=False：JSON 允许 NaN/Infinity 字面量，输入层直接拒绝。
    model_config = ConfigDict(allow_inf_nan=False)

    steps: StrictInt = Field(default=120, ge=1, le=MAX_STEPS)
    # 随机种子：给出后同一配置可复现（含智能体初始化）。
    seed: StrictInt | None = 42
    # 动力学参数：必须是数值，且键和范围由 PARAM_SPECS 统一约束。
    params: dict[str, float] = Field(default_factory=dict)
    # 默认值必须用模型构造：Pydantic v2 不校验裸默认值。
    families: list[FamilyConfig] = Field(default_factory=lambda: [
        FamilyConfig(name='Smith', members=[
            MemberConfig(name='Father', age=40, gender='male', role_name='parent'),
            MemberConfig(name='Mother', age=38, gender='female', role_name='parent'),
            MemberConfig(name='Child', age=10, gender='male', role_name='child'),
        ]),
        FamilyConfig(name='Jones', members=[
            MemberConfig(name='Mom', age=35, gender='female', role_name='parent'),
            MemberConfig(name='Daughter', age=8, gender='female', role_name='child'),
        ]),
    ])

    @model_validator(mode='after')
    def _check_ranges(self) -> SimConfig:
        """Reject unknown, out-of-range, or oversized inputs before simulation."""
        unknown = sorted(set(self.params) - set(PARAM_SPECS))
        if unknown:
            raise ValueError(f'未知参数：{unknown}。可用参数：{sorted(PARAM_SPECS)}')

        for key, value in self.params.items():
            spec = PARAM_SPECS[key]
            if not math.isfinite(value):
                raise ValueError(f'参数 {key} 必须是有限数值，收到 {value!r}')
            if not spec.minimum <= value <= spec.maximum:
                raise ValueError(
                    f'参数 {key} 必须在 {spec.minimum:g}–{spec.maximum:g} 之间，收到 {value:g}'
                )
            if spec.kind == 'switch' and value not in (0.0, 1.0):
                raise ValueError(f'参数 {key} 只能是 0 或 1，收到 {value:g}')

        if len(self.families) > MAX_FAMILIES:
            raise ValueError(f'家庭数不能超过 {MAX_FAMILIES}，收到 {len(self.families)}')
        total_members = 0
        for family in self.families:
            if len(family.members) > MAX_MEMBERS_PER_FAMILY:
                raise ValueError(
                    f'家庭 {family.name!r} 的成员数不能超过 {MAX_MEMBERS_PER_FAMILY}，'
                    f'收到 {len(family.members)}'
                )
            total_members += len(family.members)
        if total_members > MAX_TOTAL_MEMBERS:
            raise ValueError(f'总成员数不能超过 {MAX_TOTAL_MEMBERS}，收到 {total_members}')
        return self

class FitRequest(BaseModel):
    model_name: str = 'wellbeing'
    agent_id: str | None = None
    robust: bool = True
    run_id: str | None = None
    # 抽象模型（square_law 的 R1/R2、influence 的 O1/O2 等）与 ABM 状态列之间没有
    # 默认语义对应关系，必须由调用方显式给出；默认 None 表示使用
    # 「状态名 -> state_<状态名>」约定。
    state_mapping: dict[str, str] | None = None


# ── 端点兜底：任何未预期异常都必须保持结构化 JSON ──────────────────────────
#
# 背景（round-2 审查 C3）：此前只有 /api/fit 有函数级 try/except，其余端点一旦抛
# 异常就走 Starlette 默认 500，返回 text/plain "Internal Server Error"——前端
# res.json() 解析失败、HTTP 状态码也丢了，用户只看到一句 JSON 语法错误。
# 下面这个装饰器把端点包成与 /api/fit 一致的契约：
#   ValueError（可预期的输入问题）→ 400 {'error': <人话>, 'status': 'invalid_input'}
#   其它 Exception（服务端 bug）  → 500 {'error': <人话>, 'status': 'internal_error'}
# 并把完整 traceback 写进 logging（不是吞掉）。

_INPUT_ERROR_HINTS = (
    ('could not convert string to float', '参数或成员字段需要数值，但收到了无法解析的字符串'),
    ('invalid literal for int', '参数或成员字段需要整数，但收到了无法解析的字符串'),
    ('JSON compliant', '数据中存在 NaN/Inf 等非有限数值（例如 /api/run 传入了 age=NaN）'),
    ('division by zero', '某个参数取值为 0 导致除零（例如 income_age_spread=0）'),
    ('unexpected keyword argument', '家庭成员字段含未知键（可用键：name/age/gender/role_name/personality）'),
    ('unsupported operand', '成员字段类型不合法（age 等数值字段收到了字符串）'),
)


def _describe_exception(exc: BaseException) -> str:
    """把异常翻译成一句对用户有用的话，而不是直接甩出 Python 原文。"""
    text = str(exc).lower()
    for needle, hint in _INPUT_ERROR_HINTS:
        if needle.lower() in text:
            return hint
    if isinstance(exc, KeyError):
        missing = exc.args[0] if exc.args else '?'
        return f'请求体缺少必需字段 {missing!r}（families[*] 需要 name，members[*] 需要 name）'
    if isinstance(exc, TypeError):
        return '请求体字段类型不合法（例如 age 传入了字符串，或成员字段含未知键）'
    if isinstance(exc, ValueError):
        return '请求体含非法数值'
    return f'服务端内部错误（{type(exc).__name__}）'


def _guard_endpoint(endpoint: str):
    """给端点加函数级兜底；成功路径原样返回，不改变任何响应字段。"""

    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except HTTPException:
                # 显式声明的 HTTP 语义（404/422 等）原样透出，不要被包成 500
                raise
            except ValueError as exc:
                # 可预期的输入问题：保持与 /api/fit 相同的 400 invalid_input 契约
                logger.warning('%s 输入问题 (%s): %s', endpoint, type(exc).__name__, exc)
                return JSONResponse({
                    'error': f'{endpoint} 无法完成请求：{_describe_exception(exc)}',
                    'status': 'invalid_input',
                }, 400)
            except Exception as exc:
                # 未预期异常：记录完整 traceback，返回结构化 500（绝不只吞掉）
                logger.error('%s 未预期异常: %s', endpoint, exc, exc_info=True)
                return JSONResponse({
                    'error': (
                        f'{endpoint} 处理请求时发生服务端错误（{type(exc).__name__}）。'
                        f'详情已记录到服务端日志。可能的原因：{_describe_exception(exc)}'
                    ),
                    'status': 'internal_error',
                }, 500)

        return wrapper

    return decorator


# ── Routes ─────────────────────────────────────────────────────────────────

@app.get('/', response_class=HTMLResponse)
async def dashboard(request: Request):
    template = templates.get_template('index.html')
    return HTMLResponse(
        template.render(request=request, models=list(MODEL_REGISTRY.keys()))
    )


@app.get('/api/params')
async def api_params():
    from ..family.family_member import DEFAULT_PARAMS
    groups = {
        name: [key for key in keys if key in DEFAULT_PARAMS]
        for name, keys in PARAM_GROUPS.items()
    }
    unknown = [
        key for key in DEFAULT_PARAMS
        if not any(key in keys for keys in groups.values())
    ]
    if unknown:
        groups["Other"] = unknown
    specs = {
        key: PARAM_SPECS[key].to_dict()
        for key in DEFAULT_PARAMS
        if key in PARAM_SPECS
    }
    return JSONResponse({
        'defaults': DEFAULT_PARAMS,
        'groups': groups,
        'specs': specs,
        'limits': SIM_LIMITS,
    })


def _api_run_impl(cfg: SimConfig) -> JSONResponse:
    env = Environment()
    env.params = cfg.params
    # 先建立随机数上下文：这样智能体初始化与后续演化都来自同一条可复现的随机流
    sim = Simulation(env, scheduler=Scheduler('sequential'), seed=cfg.seed)

    for fam in cfg.families:
        hh = Household(name=f"{fam.name} Household", environment=env)
        env.add_agent(hh)
        for m in fam.members:
            # exclude_none：personality=None 表示"未指定"，交给 FamilyMember 自己
            # 生成；若原样传入会把 None 当成显式人格值。
            member = FamilyMember(environment=env, **m.model_dump(exclude_none=True))
            hh.add_member(member)

    recorder = StateRecorder(record_agents=True)
    sim.add_recorder(recorder)
    sim.run(cfg.steps)

    snapshot = RunSnapshot(
        run_id=uuid.uuid4().hex,
        env=env,
        df=recorder.to_dataframe(),
        recorder=recorder,
    )
    _run_store.publish(snapshot)

    return JSONResponse({
        'status': 'ok',
        'run_id': snapshot.run_id,
        'steps': cfg.steps,
        'seed': cfg.seed,
        'agents': len(env.agents),
        'observations': len(snapshot.df),
    })


def _api_run_thread(cfg: SimConfig) -> JSONResponse:
    with _run_slot:
        return _api_run_impl(cfg)


@app.post('/api/run')
@_guard_endpoint('POST /api/run')
async def api_run(cfg: SimConfig):
    return await asyncio.to_thread(_api_run_thread, cfg)


@app.get('/api/data')
@_guard_endpoint('GET /api/data')
async def api_data(run_id: str | None = None):
    snapshot, error = _resolve_run(run_id)
    if error is not None:
        return error

    env, source_df, recorder = snapshot.env, snapshot.df, snapshot.recorder

    agents = []
    for a in env.get_agents():
        if isinstance(a, FamilyMember):
            agents.append({
                'id': a.id,
                'name': a.get_attribute('name'),
                'role': a.get_attribute('role'),
                'age': round(a.get_attribute('age'), 1),
            })

    df = source_df.copy()
    for c in df.columns:
        if pd.api.types.is_float_dtype(df[c]):
            df[c] = df[c].round(4)

    # 缺失值一律传 null，不再 fillna(0)：
    # Household 行没有 state_happiness 等成员状态列，填 0 会让前端聚合值
    # 比真实值低约 28.6%，并与 fitter 自己用的 NaN 跳过均值不是同一序列。
    # pandas 的 NaN 在 json.dumps 中会变成非法的 NaN 字面量，因此显式转成 None。
    records = df.astype(object).where(pd.notna(df), None).to_dict(orient='records')
    statistics = recorder.to_statistics_dataframe() if recorder is not None else pd.DataFrame()

    return JSONResponse({
        'run_id': snapshot.run_id,
        'agents': agents,
        'columns': list(df.columns),
        'data': records,
        'statistics': statistics.to_dict(orient='records'),
        'steps': int(df['time'].max()) if 'time' in df.columns else 0,
    })


VARIANCE_EPS = 1e-9


def _column_variance_report(df: pd.DataFrame) -> tuple[list[str], list[str], list[str]]:
    """把 ``state_`` 列分成 (可用于拟合, 常量, 无法验证)。

    判据刻意采用**拟合目标序列**本身（即按 time 聚合后的均值），而不是全表
    pooled 的 min/max：全表跨度会把"每个 agent 各自恒定、但不同 agent 取值不同"
    的列误判为有变化（跨 agent 方差不是时间序列方差），而拟合用的正是按 time
    聚合后的序列。

    - 可用于拟合：按 time 聚合后的均值序列跨度 > VARIANCE_EPS
    - 常量：能算出序列但跨度 ~ 0
    - 无法验证：完全没有有效观测（例如该列全为 NaN），按"不可信"处理
    """
    usable: list[str] = []
    constant: list[str] = []
    unverifiable: list[str] = []
    if df is None or df.empty or 'time' not in df.columns:
        return usable, constant, unverifiable

    for column in sorted(str(c) for c in df.columns if str(c).startswith('state_')):
        series = df[column] if column in df.columns else None
        if series is None:
            unverifiable.append(column)
            continue
        # 某些 time 分组可能全为 NaN（例如该时段该状态没有有效观测），
        # dropna 后若一个有效分组都不剩，则无法验证该列的方差，按不可信处理。
        means = series.groupby(df['time']).mean().dropna()
        if len(means) < 2:
            unverifiable.append(column)
            continue
        span = float(means.max() - means.min())
        (usable if span > VARIANCE_EPS else constant).append(column)
    return usable, constant, unverifiable


@app.get('/api/models')
@_guard_endpoint('GET /api/models')
async def api_models(agent_id: str | None = None, run_id: str | None = None):
    """列出可用模型及其状态名、以及相对当前数据的可映射性。

    前端据此决定下拉里哪些模型可以直接拟合；对不可直接映射的模型给出**候选**
    state_mapping（由调用方核对语义后使用），避免"选了模型却永远 400"。

    候选列的选取必须排除**零方差列**：按字母序取前 N 个 ``state_`` 列会选中
    Household 专属的常量列（例如 state_cultural_level），把模型拟到常数列上会得到
    R²=0.0 却 converged=True，是比"静默猜列"更糟的误导（实测 logistic 命中）。
    因此这里只提供"有变化"的列，并且当候选不足以覆盖状态数时明确标记
    ``needs_manual_mapping``，不给出看似可用的建议。

    对"默认映射恰好命中常量列"的模型（例如某些数据下 happiness/stress 为常量），
    ``directly_fittable`` 也必须判为 False —— 否则用户点一下就会得到
    R²≈0 却 converged=True 的误导结果。

    Parameters
    ----------
    agent_id : str, optional
        按单个 agent 评估可拟合性。拟合到单个 agent 时用的是该 agent 自己的序列，
        因此"整体有变化、但该 agent 恒定"的列必须按该 agent 的子集重新判定。
    run_id : str, optional
        固定读取的运行快照；空值表示最新运行。
    """
    snapshot, error = _resolve_run(run_id)
    if error is not None:
        return error
    frame = snapshot.df
    if agent_id is not None:
        if 'agent_id' not in frame.columns:
            return JSONResponse({
                'error': '没有仿真数据或数据缺少 agent_id 列。',
                'status': 'invalid_dataframe',
            }, 400)
        frame = frame[frame['agent_id'] == agent_id]
        if frame.empty:
            return JSONResponse({
                'error': f'没有 agent_id={agent_id!r} 的记录。',
                'status': 'unknown_agent',
            }, 400)

    usable, constant, unverifiable = _column_variance_report(frame)
    flat_columns = set(constant) | set(unverifiable)

    models = []
    for name, state_names in MODEL_STATE_NAMES.items():
        expected = {s: f'state_{s}' for s in state_names}
        # 默认映射命中，且该列确实有变化，才算"可直接拟合"
        default_ok = all(col in usable for col in expected.values())
        # 不可验证/为常量的默认映射列，作为"存在但不可用"单独列出
        unusable_defaults = {s: col for s, col in expected.items() if col in flat_columns}
        missing = [] if default_ok else [s for s in state_names if expected[s] not in usable]

        if default_ok:
            suggested = expected
        else:
            alternative = [c for c in usable if c not in expected.values()]
            suggested = ({s: alternative[i] for i, s in enumerate(state_names)}
                         if len(alternative) >= len(state_names) else None)
        needs_manual = bool(missing) and suggested is None

        # mapping_kind 把三种情形显式区分开——此前前端只能看到 suggested_mapping
        # 非空，无法分辨"模型原生状态恰好就是这两列"与"这是从可用列里按字母序
        # 任取的替代品"。后者会被自动提交给 /api/fit，把 square_law 拟到
        # economic_pressure/education 上，返回 status=ok + converged=true，
        # 实测 R² 低至 -2368436——用户却看不到究竟拟合了哪两列。
        if default_ok:
            mapping_kind = 'default'
        elif suggested is not None:
            mapping_kind = 'auto'
        else:
            mapping_kind = 'none'

        models.append({
            'name': name,
            'state_names': state_names,
            'expected_columns': expected,
            'unusable_default_columns': unusable_defaults,
            'missing_states': missing,
            'directly_fittable': default_ok,
            'needs_manual_mapping': needs_manual,
            'mapping_kind': mapping_kind,
            'suggested_mapping': suggested,
        })
    return JSONResponse({
        'run_id': snapshot.run_id,
        'models': models,
        'available_state_columns': usable + constant + unverifiable,
        'usable_state_columns': usable,
        'constant_state_columns': constant,
        'unverifiable_state_columns': unverifiable,
    })


@app.post('/api/fit')
async def api_fit(req: FitRequest):
    """在线程池里跑 CPU 密集的拟合，并对事件循环加超时保护。

    拟合绑定请求开始时解析出的运行快照。新的 run 可以同时发布，但不会改变本次
    拟合读取的数据；超时后线程仍可能继续运行，迟到结果不会发布到任何全局状态。
    """
    snapshot, error = _resolve_run(req.run_id)
    if error is not None:
        return error

    timeout = FIT_TIMEOUT_SECONDS
    try:
        return await asyncio.wait_for(
            asyncio.to_thread(_api_fit_thread, req, snapshot), timeout=timeout,
        )
    except asyncio.TimeoutError:
        logger.error('POST /api/fit 超过 %gs 上限，放弃等待（worker 线程可能仍在运行）', timeout)
        return JSONResponse({
            'error': (
                f'POST /api/fit 拟合超过 {timeout:g}s 上限，已放弃等待。'
                '可减少步数或起点数、改用直接拟合，或用环境变量 '
                'FAMILY_ABM_FIT_TIMEOUT_SECONDS 调大上限。'
            ),
            'status': 'fit_timeout',
        }, 504)
    except ValueError as exc:
        return JSONResponse({'error': str(exc), 'status': 'invalid_input'}, 400)
    except RuntimeError as exc:
        return JSONResponse({'error': f'{exc}', 'status': 'runtime_error'}, 400)
    except Exception as exc:
        # 函数级兜底：任何未预期异常都必须保持结构化 JSON。
        # 若让它逃出端点，FastAPI 会返回 text/plain "Internal Server Error"，
        # 前端 api() 只能拿到 JSON 解析错误，排障信息全部丢失。
        logger.error('POST /api/fit 未预期异常: %s', exc, exc_info=True)
        return JSONResponse({
            'error': f'{type(exc).__name__}: {exc}',
            'status': 'fitting_error',
        }, 500)


def _api_fit_thread(req: FitRequest, snapshot: RunSnapshot) -> JSONResponse:
    with _fit_slot:
        return _api_fit_impl(req, snapshot)


def _api_fit_impl(req: FitRequest, snapshot: RunSnapshot):
    """api_fit 的实现体（同步，由 api_fit 放进 worker 线程执行）。

    异常处理统一由 api_fit 的函数级兜底负责。
    """
    df = snapshot.df
    required = {'time'}
    if req.agent_id is not None:
        required.add('agent_id')
    missing = sorted(c for c in required if c not in df.columns)
    if missing:
        return JSONResponse({
            'error': f'仿真数据缺少必需列 {missing}（当前列：{list(df.columns)}）。',
            'status': 'invalid_dataframe',
        }, 400)

    # 只有"未知模型名"这一种情况应归因于调用方输入；把它限制在 make_fitter 调用上，
    # 而不是用 `except KeyError` 包住整个流程 —— 否则"数据缺列"之类的 KeyError 会被
    # 误报成"未知模型名"（复核实测：缺 time/agent_id 列时曾返回 400 unknown_model）。
    try:
        fitter = make_fitter(req.model_name, state_mapping=req.state_mapping)
    except KeyError:
        return JSONResponse({
            'error': f'未知模型名 {req.model_name!r}。可用模型：{list(MODEL_REGISTRY)}',
            'status': 'unknown_model',
        }, 400)

    # 显式映射指向非数值列：这是调用方输入错误（不是服务端故障），提前给出 400 与
    # 可用列清单，而不是等 pandas 抛出 TypeError 再报 500
    # （复核实测：state_mapping 把状态映射到 agent_id 等字符串列时得到 500 fitting_error）。
    numeric_columns = set(df.select_dtypes(include='number').columns)
    expected_columns = {state: fitter._resolve_col(state) for state in fitter.state_names}
    invalid = {state: col for state, col in expected_columns.items()
               if col in df.columns and col not in numeric_columns}
    if invalid:
        return JSONResponse({
            'error': (
                f'以下状态映射指向非数值列：{invalid}。可用数值列：'
                f'{sorted(c for c in numeric_columns if str(c).startswith("state_"))}。'
            ),
            'status': 'invalid_mapping',
        }, 400)

    try:
        if req.robust:
            result = fitter.fit_robust(df, agent_id=req.agent_id)
        else:
            result = fitter.fit_from_dataframe(df, agent_id=req.agent_id)
    except ValueError as exc:
        # 状态列无法解析 / 参数边界不合法 / 数据不足等可预期的输入问题
        return JSONResponse({'error': str(exc), 'status': 'invalid_input'}, 400)
    except RuntimeError as exc:
        return JSONResponse({
            'error': f'{exc}（多起点拟合全部失败；请检查状态列选择与参数边界，或减少起点数重试）',
            'status': 'all_starts_failed',
        }, 400)

    # 优化器自身失败（超过迭代上限等）属于"模型/边界不适用"，返回 400 并带诊断。
    if result is None or not bool(getattr(result, 'success', False)):
        return JSONResponse({
            'error': (
                f'模型 {req.model_name} 的优化未能收敛（optimizer success=False）。'
                '常见原因：该模型结构与当前数据量纲不匹配，或参数边界不合适。'
                '可尝试放宽 bounds、改选状态列，或改用差分进化全局搜索。'
            ),
            'status': 'optimizer_failed',
            'summary': fitter.summary_json(),
        }, 400)

    summary = fitter.summary_json()

    # 哨兵判定必须在 predict 之前：命中哨兵说明解本身未成功积分，再去算预测轨迹
    # 既浪费又会把结论颠倒（真实场景：resource_competition + robust=false 时
    # predict 必然失败，曾因此把"模型不适用"错报成 500 prediction_failed）。
    # 返回 200 + warning，让前端的告警条真正可达（前端对非 200 一律提前 return）。
    if summary['hit_sentinel']:
        return JSONResponse({
            'status': 'model_not_applicable',
            'run_id': snapshot.run_id,
            'model': req.model_name,
            'state_columns': fitter._resolved_columns,
            'state_names': fitter.state_names,
            'summary': summary,
            'predict_trace': [],
            'prediction_skipped': True,
            'warning': (
                f'模型 {req.model_name} 在给定数据与参数边界下未能积分出可用解（优化停留在失败哨兵）；'
                'R² 与参数估计无意义，预测轨迹已跳过。可尝试放宽 bounds、改选状态列，'
                '或改用差分进化全局搜索。'
            ),
        })

    # Build prediction trace
    predict_trace: list[dict] = []
    if fitter._t is not None and fitter._y0 is not None:
        try:
            t_pred = np.linspace(fitter._t[0], fitter._t[-1], 200)
            _, y_pred = fitter.predict(t_pred, fitter._y0)
            predict_trace = [
                {'t': list(t_pred.astype(float)), 'y': [float(v) for v in y_pred[i]]}
                for i in range(fitter.n_states)
            ]
        except Exception as exc:
            # 预测失败不是输入问题：返回 500 以便暴露真实 bug。
            # 必须在实现体内 return（而不是让异常冒泡），否则会被 api_fit 的
            # RuntimeError 兜底改写成 400 runtime_error，诊断被掩盖。
            return JSONResponse({
                'error': f'拟合成功但预测轨迹生成失败：{type(exc).__name__}: {exc}',
                'status': 'prediction_failed',
            }, 500)

    return JSONResponse({
        'status': 'ok',
        'run_id': snapshot.run_id,
        'model': req.model_name,
        'state_columns': fitter._resolved_columns,
        'state_names': fitter.state_names,
        'summary': summary,
        'predict_trace': predict_trace,
        'warning': None,
    })


_NICHE_STATE_FIELDS = {
    'economic': 'state_income',
    'cultural': 'state_education',
    'social': 'state_social_capital',
    'emotional': 'state_happiness',
}


def _finite_number(value: Any) -> float | None:
    """Return a finite float, or None for missing/non-finite state values."""
    if value is None:
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) else None


@app.get('/api/niche')
@_guard_endpoint('GET /api/niche')
async def api_niche(run_id: str | None = None):
    snapshot, error = _resolve_run(run_id)
    if error is not None:
        return error
    env, source_df = snapshot.env, snapshot.df

    niches = []
    for agent in env.get_agents():
        if isinstance(agent, FamilyMember):
            n = MicroNiche(niche_id=agent.id)
            sub = source_df[source_df['agent_id'] == agent.id]
            raw_values: dict[str, float | None] = {}
            observed: dict[str, float] = {}
            if not sub.empty:
                last = sub.iloc[-1]
                for dimension, column in _NICHE_STATE_FIELDS.items():
                    raw = _finite_number(last.get(column))
                    raw_values[dimension] = raw
                    if raw is not None:
                        observed[dimension] = raw
                        # 直接按维度写入；update_from_agent_state 的默认键是
                        # income/education/...，传入维度名会静默保留 0.5 默认坐标。
                        n.set_position(dimension, raw)
            else:
                raw_values = {dimension: None for dimension in _NICHE_STATE_FIELDS}

            position = {
                dimension: n.position[dimension] if dimension in observed else None
                for dimension in n.dimensions
            }
            missing = [d for d in n.dimensions if d not in observed]
            clipped = [
                d for d, value in observed.items()
                if value < 0.0 or value > 1.0
            ]
            niches.append({
                'id': agent.id,
                'name': agent.get_attribute('name'),
                'role': agent.get_attribute('role'),
                'position': position,
                'raw_values': raw_values,
                'observed_dimensions': list(observed),
                'missing_dimensions': missing,
                'clipped_dimensions': clipped,
            })
    return JSONResponse({'run_id': snapshot.run_id, 'niches': niches})


@app.get('/api/network')
@_guard_endpoint('GET /api/network')
async def api_network(run_id: str | None = None):
    snapshot, error = _resolve_run(run_id)
    if error is not None:
        return error

    networks = []
    for agent in snapshot.env.get_agents():
        if isinstance(agent, Household):
            nodes = []
            for mid, m in agent.members.items():
                nodes.append({
                    'id': mid,
                    'name': m.get_attribute('name') or mid[:8],
                    'role': m.get_attribute('role'),
                })
            edges = []
            for (a, b), rel in agent.relationships.items():
                if a < b:
                    edges.append({
                        'source': a, 'target': b,
                        'weight': round(rel.affection, 3),
                        'conflict': round(rel.conflict, 3),
                        'trust': round(rel.trust, 3),
                    })
            networks.append({
                'name': agent.get_attribute('name'),
                'nodes': nodes,
                'edges': edges,
            })
    return JSONResponse({'run_id': snapshot.run_id, 'networks': networks})
