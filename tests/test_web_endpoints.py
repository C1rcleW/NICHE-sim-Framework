"""Web 端点回归测试：结构化错误契约（round-2 审查 C3）与拟合不阻塞事件循环（C4）。

覆盖：
- 6 个实测反例必须返回结构化 JSON（application/json + {'error','status'}），不再是
  Starlette 默认的 text/plain "Internal Server Error"；
- 成功路径的响应字段逐字段不变（前端依赖）；
- /api/fit 的 CPU 工作必须在线程池里执行（用桩验证并发请求不被阻塞）并有超时保护；
- functools.wraps 包装后 FastAPI 仍能识别请求体模型（OpenAPI 不受影响）。
"""
from __future__ import annotations

import asyncio
import importlib
import inspect
import json
import logging
import time

import httpx
import pytest
from fastapi.responses import JSONResponse
from fastapi.testclient import TestClient

from family_abm.web.app import app as web_app
from family_abm.web.run_store import RunStore

# 注意：`import family_abm.web.app as m` 会因包的属性遮蔽拿到 FastAPI 实例而不是模块，
# 需要 monkeypatch 模块级对象时必须用 importlib（与 test_simulation_and_fitting.py 同源）。
APP_MODULE = importlib.import_module("family_abm.web.app")


@pytest.fixture()
def reset_state(monkeypatch):
    """每个用例都从「没有仿真数据」的干净状态开始。"""
    monkeypatch.setattr(APP_MODULE, "_run_store", RunStore())


@pytest.fixture()
def client(reset_state):
    return TestClient(web_app, raise_server_exceptions=False)


def _assert_structured_error(response, expected_status: int) -> dict:
    assert response.status_code == expected_status, response.text
    assert response.headers["content-type"].startswith("application/json"), response.headers
    body = response.json()
    assert set(body) == {"error", "status"}, body
    assert isinstance(body["error"], str) and body["error"].strip(), body
    assert body["status"] in {"invalid_input", "internal_error"}, body
    # 不要把人话错误信息写成 Python 原文堆栈
    assert "Traceback" not in body["error"], body
    return body


def _assert_validation_error(response) -> dict:
    """422 校验错误的契约：{'error','status','detail'}，且必须可被严格 JSON 解析。

    与运行期错误（400/500）分开断言，因为二者来源不同：
    - 422：请求体没通过 Pydantic 校验（输入问题，最靠近现场）
    - 400/500：请求体合法，但运行时出错
    """
    assert response.status_code == 422, response.text
    assert response.headers["content-type"].startswith("application/json"), response.headers
    body = response.json()
    assert set(body) == {"error", "status", "detail"}, body
    assert body["status"] == "validation_error", body
    assert isinstance(body["detail"], list) and body["detail"], body
    return body


# ── C3：6 个反例 ────────────────────────────────────────────────────────────
#
# 注意契约演进：这些反例原先会一路跑到仿真内部才报错（500 internal_error 或
# 400 invalid_input）。加入**输入模型化**（MemberConfig/FamilyConfig/params 类型化
# + allow_inf_nan=False）后，它们在校验层就被拦下，返回 422 validation_error——
# 错误位置从"仿真深处"前移到"请求入口"，这是改进而不是契约破坏。
# 运行期错误的 400/500 契约仍由 /api/not-existing-provider 之外的路径覆盖，
# 见 test_runtime_error_guard_still_logs_traceback。

@pytest.mark.parametrize(
    "payload",
    [
        pytest.param({"steps": 3, "params": {"income_age_spread": 0}}, id="income_age_spread_zero"),
        pytest.param({"steps": 3, "params": {"randomness": "abc"}}, id="params_non_numeric"),
        pytest.param({"steps": 3, "families": [{"name": "A", "members": [{"name": "x", "age": "old"}]}]},
                     id="member_age_string"),
        pytest.param({"steps": 3, "families": [{"members": []}]}, id="family_missing_name"),
        pytest.param({"steps": 3, "families": [{"name": "A", "members": [{"name": "x", "age": -5}]}]},
                     id="member_age_negative"),
        pytest.param({"steps": -5}, id="steps_negative"),
    ],
)
def test_run_counterexamples_return_structured_json(client, payload):
    """反例必须返回结构化 JSON（不再是 text/plain 'Internal Server Error'）。"""
    body = _assert_validation_error(client.post("/api/run", json=payload))
    assert "请求体校验失败" in body["error"], body


def test_nan_age_is_rejected_at_validation_layer(client):
    """age=NaN 必须在校验层被拒（422），而不是被接受后等到 /api/data 才暴露。

    此处曾是 P2 级缺口：`families: list[dict]` 不做类型校验，NaN 一路进仿真，
    10 步之后才表现为 /api/data 的 400/500。类型化 + allow_inf_nan=False 后
    错误前移到入口。
    """
    raw = ('{"steps": 12, "families": [{"name": "A", "members": '
           '[{"name": "x", "age": NaN, "gender": "male", "role_name": "parent"}]}]}')
    run = client.post("/api/run", content=raw, headers={"Content-Type": "application/json"})
    body = _assert_validation_error(run)
    assert "finite" in body["error"].lower() or "有限" in body["error"], body


def test_non_finite_params_and_age_are_rejected(client):
    """NaN/Infinity 在各层都被拒：成员年龄、参数、步骤。"""
    cases = [
        '{"steps": 5, "families": [{"name": "A", "members": [{"name": "x", "age": Infinity}]}]}',
        '{"steps": 5, "params": {"randomness": NaN}}',
        '{"steps": 5, "params": {"income_age_spread": Infinity}}',
    ]
    for raw in cases:
        response = client.post("/api/run", content=raw, headers={"Content-Type": "application/json"})
        _assert_validation_error(response)


def test_runtime_error_guard_still_logs_traceback(caplog):
    """端点兜底对**运行期**异常仍然生效，且把 traceback 写进 logging。

    输入模型化之后，审查列出的反例都在校验层被拦下，因此这里直接用
    `_guard_endpoint` 包一个会抛异常的函数来验证兜底路径本身——
    而不是依赖某个恰好能穿过校验的输入（那会让测试变脆）。
    """
    from fastapi.responses import JSONResponse

    guarded = APP_MODULE._guard_endpoint("POST /api/test")(
        lambda: (_ for _ in ()).throw(RuntimeError("boom"))
    )
    with caplog.at_level(logging.ERROR, logger="family_abm.web"):
        result = asyncio.run(guarded())
    assert isinstance(result, JSONResponse)
    assert result.status_code == 500
    payload = json.loads(bytes(result.body).decode("utf-8"))
    assert payload["status"] == "internal_error"
    assert payload["error"].startswith("POST /api/test")
    logged = [r for r in caplog.records if r.name == "family_abm.web" and r.exc_info]
    assert logged, f"500 分支没有把 traceback 写进 logging：{caplog.text}"


def test_guard_maps_value_error_to_400():
    """ValueError 是输入问题 → 400 invalid_input；HTTPException 原样透出。"""
    from fastapi import HTTPException

    guarded = APP_MODULE._guard_endpoint("POST /api/test")(
        lambda: (_ for _ in ()).throw(ValueError("bad input"))
    )
    result = asyncio.run(guarded())
    assert result.status_code == 400
    payload = json.loads(bytes(result.body).decode("utf-8"))
    assert payload["status"] == "invalid_input"

    passthrough = APP_MODULE._guard_endpoint("POST /api/test")(
        lambda: (_ for _ in ()).throw(HTTPException(status_code=418, detail="teapot"))
    )
    with pytest.raises(HTTPException):
        asyncio.run(passthrough())


# ── 成功路径：字段与 null 语义保持不变 ──────────────────────────────────────

def test_success_payload_fields_unchanged(client):
    run = client.post("/api/run", json={"steps": 20})
    assert run.status_code == 200, run.text
    assert set(run.json()) == {"status", "run_id", "steps", "seed", "agents", "observations"}

    data = client.get("/api/data")
    assert set(data.json()) == {"run_id", "agents", "columns", "data", "statistics", "steps"}
    assert client.get("/api/niche").json().keys() == {"run_id", "niches"}
    assert client.get("/api/network").json().keys() == {"run_id", "networks"}

    records = data.json()["data"]
    households = [r for r in records if r.get("agent_type") == "Household"]
    members = [r for r in records if r.get("agent_type") == "FamilyMember"]
    assert households and members
    # null 契约：Household 行没有成员状态，成员行没有 household 状态（不是 0）
    assert all(r["state_happiness"] is None for r in households)
    assert all(r["state_total_income"] is None for r in members)


def test_missing_simulation_still_returns_400(client):
    for path in ("/api/data", "/api/niche", "/api/network"):
        response = client.get(path)
        assert response.status_code == 400, path
        assert response.json()["error"]
    assert client.post("/api/fit", json={}).status_code == 400


def test_run_id_rejects_reads_from_replaced_runs(client):
    first = client.post("/api/run", json={"steps": 1})
    assert first.status_code == 200, first.text
    first_id = first.json()["run_id"]

    second = client.post("/api/run", json={"steps": 2})
    assert second.status_code == 200, second.text
    second_id = second.json()["run_id"]
    assert first_id != second_id

    for path in ("/api/data", "/api/models", "/api/niche", "/api/network"):
        response = client.get(f"{path}?run_id={first_id}")
        assert response.status_code == 404, (path, response.text)
        assert response.json()["status"] == "unknown_run"

    stale_fit = client.post("/api/fit", json={"model_name": "wellbeing", "run_id": first_id})
    assert stale_fit.status_code == 404, stale_fit.text
    assert stale_fit.json()["status"] == "unknown_run"

    current = client.get(f"/api/data?run_id={second_id}")
    assert current.status_code == 200, current.text
    assert current.json()["run_id"] == second_id


# ── C4：执行方式与超时 ─────────────────────────────────────────────────────

def test_fit_implementation_is_sync_and_endpoint_is_async():
    """实现体必须同步（否则无法交给线程池），端点保持 async（现有调用方 await 它）。"""
    assert inspect.iscoroutinefunction(APP_MODULE.api_fit)
    assert not inspect.iscoroutinefunction(APP_MODULE._api_fit_impl)


def test_api_run_runs_cpu_work_off_the_event_loop(monkeypatch):
    def slow_run(_cfg):
        time.sleep(0.6)
        return JSONResponse({"status": "ok", "run_id": "stub", "steps": 1})

    monkeypatch.setattr(APP_MODULE, "_api_run_impl", slow_run)

    async def scenario():
        transport = httpx.ASGITransport(app=web_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http:
            run_task = asyncio.create_task(http.post("/api/run", json={"steps": 1}))
            await asyncio.sleep(0.1)  # 让运行进入 worker 线程
            started = time.perf_counter()
            params = await http.get("/api/params")
            latency = time.perf_counter() - started
            return params, latency, await run_task

    params, latency, run_response = asyncio.run(scenario())
    assert params.status_code == 200
    assert params.json()["defaults"]
    assert run_response.status_code == 200 and run_response.json()["run_id"] == "stub"
    assert latency < 0.3, f"运行期间 /api/params 延迟 {latency:.3f}s：事件循环仍被阻塞"


def test_api_fit_runs_cpu_work_off_the_event_loop(client, monkeypatch):
    assert client.post("/api/run", json={"steps": 1}).status_code == 200
    calls = []

    def slow_impl(req, _snapshot):
        calls.append(req.model_name)
        time.sleep(0.6)
        return JSONResponse({"status": "ok", "stub": True})

    monkeypatch.setattr(APP_MODULE, "_api_fit_impl", slow_impl)

    async def scenario():
        transport = httpx.ASGITransport(app=web_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http:
            fit_task = asyncio.create_task(http.post("/api/fit", json={"model_name": "wellbeing"}))
            await asyncio.sleep(0.1)  # 让拟合进入 worker 线程
            started = time.perf_counter()
            params = await http.get("/api/params")
            latency = time.perf_counter() - started
            return params, latency, await fit_task

    params, latency, fit_response = asyncio.run(scenario())
    assert params.status_code == 200
    assert params.json()["defaults"]
    assert fit_response.status_code == 200 and fit_response.json()["stub"] is True
    assert calls == ["wellbeing"]
    # 拟合 0.6s 期间 /api/params 必须几乎立即返回（修复前是全程阻塞）
    assert latency < 0.3, f"拟合期间 /api/params 延迟 {latency:.3f}s：事件循环仍被阻塞"


def test_api_fit_timeout_returns_structured_504(client, monkeypatch):
    assert client.post("/api/run", json={"steps": 1}).status_code == 200

    def slow_impl(req, _snapshot):
        time.sleep(0.5)
        return JSONResponse({"status": "ok"})

    monkeypatch.setattr(APP_MODULE, "_api_fit_impl", slow_impl)
    monkeypatch.setattr(APP_MODULE, "FIT_TIMEOUT_SECONDS", 0.05)

    async def scenario():
        transport = httpx.ASGITransport(app=web_app)
        async with httpx.AsyncClient(transport=transport, base_url="http://testserver") as http:
            started = time.perf_counter()
            response = await http.post("/api/fit", json={})
            return response, time.perf_counter() - started

    response, elapsed = asyncio.run(scenario())
    assert response.status_code == 504, response.text
    body = response.json()
    assert set(body) == {"error", "status"}
    assert body["status"] == "fit_timeout"
    assert "FAMILY_ABM_FIT_TIMEOUT_SECONDS" in body["error"]
    assert elapsed < 0.4, f"超时未及时返回：{elapsed:.3f}s"


@pytest.mark.parametrize(
    ("raw", "expected"),
    [("5", 5.0), ("2.5", 2.5), ("abc", None), ("-1", None), ("0", None), ("", None)],
)
def test_fit_timeout_env_override(monkeypatch, raw, expected):
    monkeypatch.setenv("FAMILY_ABM_FIT_TIMEOUT_SECONDS", raw)
    value = APP_MODULE._load_fit_timeout_seconds()
    if expected is None:
        assert value == APP_MODULE.DEFAULT_FIT_TIMEOUT_SECONDS
    else:
        assert value == expected
    assert APP_MODULE.FIT_TIMEOUT_SECONDS > 0


# ── 包装后 FastAPI 仍能识别请求体（functools.wraps 的签名保持） ─────────────

def test_openapi_request_models_survive_wrapping(client):
    schema = client.get("/openapi.json").json()
    paths = schema["paths"]
    run_ref = paths["/api/run"]["post"]["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    fit_ref = paths["/api/fit"]["post"]["requestBody"]["content"]["application/json"]["schema"]["$ref"]
    assert run_ref.endswith("/SimConfig"), run_ref
    assert fit_ref.endswith("/FitRequest"), fit_ref
    for path in ("/api/data", "/api/niche", "/api/network"):
        assert path in paths, path
    assert "parameters" in paths["/api/models"]["get"]
