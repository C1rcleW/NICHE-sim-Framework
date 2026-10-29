/**
 * dashboard.js 的真实行为测试（Node，无需浏览器）。
 *
 * 背景：此前"全禁用时禁止拟合"只有源码 grep 断言——把 fitSelectionBlocked() 的
 * 函数体换成 `return false;`（保留所有被断言的字符串）后 pytest 依旧全绿，
 * 即测试没有判别力。这里用最小 DOM 桩真正执行 dashboard.js 的拦截逻辑。
 *
 * 用法：node tools/check_dashboard_behavior.js
 * 退出码：0 = 全部通过，1 = 有失败
 */
'use strict';

const fs = require('fs');
const path = require('path');
const vm = require('vm');

// 允许通过环境变量指向另一份 dashboard.js —— 便于做突变测试
// （把被测逻辑改坏，确认本脚本会失败，从而证明它有判别力）。
const DASHBOARD = process.env.DASHBOARD_JS
  ? path.resolve(process.env.DASHBOARD_JS)
  : path.join(__dirname, '..', 'family_abm', 'web', 'static', 'js', 'dashboard.js');
const source = fs.readFileSync(DASHBOARD, 'utf8');

const failures = [];
function check(condition, label, detail) {
  const mark = condition ? 'PASS' : 'FAIL';
  console.log(`[${mark}] ${label}${detail ? '  -> ' + detail : ''}`);
  if (!condition) failures.push(label);
}

function makeElement(id, tag = 'div') {
  const classes = new Set();
  const element = {
    id,
    tagName: String(tag).toUpperCase(),
    _innerHTML: '',
    textContent: '',
    _value: '',
    disabled: false,
    selectedIndex: -1,
    options: [],
    children: [],
    style: {},
    dataset: {},
    classList: {
      add: (c) => classes.add(c),
      remove: (c) => classes.delete(c),
      toggle: () => {},
      contains: (c) => classes.has(c),
    },
    addEventListener: () => {},
    click: () => {},
    querySelector: () => makeElement('nested'),
    querySelectorAll: () => [],
    appendChild: (child) => {
      element.children.push(child);
      return child;
    },
    remove: () => {},
  };

  // 模拟浏览器对 <select> 的解析：设置 innerHTML 时提取 <option>，
  // 并让 value/selectedIndex 保持一致（否则 fitSelectionBlocked 的行为无法验证）
  function parseOptions(html) {
    const found = [];
    // 同时抓取标签属性与**显示文本**：文本是断言"选项后缀"的唯一依据，
    // 只解析 value 会让"选项文案是否区分自动映射/原生映射"无法验证。
    const re = /<option\s+value="([^"]*)"([^>]*)>([\s\S]*?)<\/option>/g;
    let match;
    while ((match = re.exec(html)) !== null) {
      found.push({
        value: match[1],
        disabled: /\bdisabled\b/.test(match[2]),
        textContent: match[3].replace(/<[^>]*>/g, '').trim(),
      });
    }
    return found;
  }

  Object.defineProperty(element, 'innerHTML', {
    get() { return element._innerHTML; },
    set(html) {
      element._innerHTML = String(html);
      if (element.id === 'fitModel' || element.id === 'fitAgent') {
        element.options = parseOptions(element._innerHTML);
        // 按规范：重建 options 后浏览器选中第一个**未被禁用**的选项
        // （此前恒取 index 0，遇到首个 option 被 disabled 时与真实行为不一致）
        const firstEnabled = element.options.findIndex((o) => !o.disabled);
        element.selectedIndex = firstEnabled;
        element._value = firstEnabled >= 0 ? element.options[firstEnabled].value : '';
      }
    },
  });

  Object.defineProperty(element, 'value', {
    get() { return element._value; },
    set(v) {
      const wanted = String(v);
      const idx = element.options.findIndex((o) => o.value === wanted);
      element._value = wanted;
      element.selectedIndex = idx; // 找不到时与浏览器一致：-1
    },
  });

  return element;
}

function makeDocument() {
  const elements = new Map();
  const get = (id) => {
    if (!elements.has(id)) elements.set(id, makeElement(id));
    return elements.get(id);
  };
  const doc = {
    getElementById: get,
    querySelector: () => makeElement('q'),
    querySelectorAll: () => [],
    addEventListener: () => {},
    createElement: (tag) => makeElement('created', tag),
    body: makeElement('body'),
    documentElement: { lang: 'en' },
    cookie: '',
  };
  return { doc, get };
}

/** 用给定请求日志与响应建立上下文并加载 dashboard.js。
 *  apiResponses 可以是函数，也可以是 {resolve(url)} 形式以便控制响应时机（测乱序）。
 */
function loadDashboard(apiResponses, options) {
  const { doc, get } = makeDocument();
  const requests = [];
  const plots = [];
  const deferred = (options && options.deferred) || false;

  const fetchStub = async (url, opts) => {
    const target = String(url);
    requests.push({ url: target, method: (opts && opts.method) || 'GET', body: opts && opts.body });
    // 关键：在**请求发出时**就固定该请求对应的响应，而不是在 resolve 时再取值。
    // 否则乱序 resolve 会让两个请求拿到同一份响应，场景也就失去了判别力。
    const isModelRequest = target.includes('/api/models');
    const isFitRequest = target.includes('/api/fit');
    let payload = apiResponses(target, requests.length);
    if (payload === undefined) {
      payload = isFitRequest ? FIT_OK : { defaults: {}, groups: {} };
    }
    // 只延迟模型列表请求（用于测乱序）；其它请求（如 /api/params）立即返回，
    // 否则页面初始化时的调用会一直挂住。
    if (deferred && isModelRequest) {
      return new Promise((resolve) => {
        pendingResolvers.push(() => resolve({ ok: true, status: 200, json: async () => payload }));
      });
    }
    return {
      ok: true,
      status: 200,
      json: async () => payload,
    };
  };
  const pendingResolvers = [];

  const sandbox = {
    document: doc,
    window: {},
    console: { log: () => {}, warn: () => {}, error: () => {} },
    fetch: fetchStub,
    Plotly: {
      newPlot: (id, traces, layout, config) => {
        plots.push({ id, traces, layout, config });
      },
      purge: () => {},
    },
    localStorage: {
      _store: {},
      getItem(k) { return Object.prototype.hasOwnProperty.call(this._store, k) ? this._store[k] : null; },
      setItem(k, v) { this._store[k] = String(v); },
      removeItem(k) { delete this._store[k]; },
    },
    setTimeout,
    clearTimeout,
    encodeURIComponent,
    Math,
    Object,
    Array,
    Number,
    String,
    JSON,
    Boolean,
    Date,
    isNaN,
    parseInt,
    parseFloat,
  };
  sandbox.window = sandbox;

  const context = vm.createContext(sandbox);
  vm.runInContext(source, context, { filename: DASHBOARD });
  // 大多数行为场景模拟“已完成一次运行”的拟合页；生产代码禁止无 run_id 拟合。
  vm.runInContext("simRunId = 'test-run';", context);
  return { sandbox, get, requests, pendingResolvers, plots, context };
}

const FIT_OK = {
  status: 'ok',
  model: 'logistic',
  state_columns: { population: 'state_only' },
  summary: {
    model: 'logistic_growth',
    params: { r: 0.2, K: 1.0 },
    r_squared: 0.9,
    converged: true,
    params_at_bounds: [],
    hit_sentinel: false,
  },
  predict_trace: [],
  warning: null,
};

const ALL_DISABLED = {
  models: [
    { name: 'wellbeing', directly_fittable: false, needs_manual_mapping: true, suggested_mapping: null },
    { name: 'square_law', directly_fittable: false, needs_manual_mapping: true, suggested_mapping: null },
    { name: 'logistic', directly_fittable: false, needs_manual_mapping: true, suggested_mapping: null },
  ],
  usable_state_columns: [],
  constant_state_columns: ['state_x'],
};

// 所有模型都可选但都不可直接映射（走 suggested_mapping 路径）：
// 用它验证"被拦截时不发 /api/fit"，避免像 ALL_DISABLED 那样被
// currentStateMapping 的 undefined 分支提前拦住，使断言空转。
const ALL_SELECTABLE_NEEDS_MAPPING = {
  models: [
    {
      name: 'logistic',
      directly_fittable: false,
      needs_manual_mapping: false,
      suggested_mapping: { population: 'state_only' },
    },
  ],
  usable_state_columns: ['state_only'],
  constant_state_columns: [],
};

const ONE_AVAILABLE = {
  models: [
    { name: 'wellbeing', directly_fittable: false, needs_manual_mapping: true, suggested_mapping: null },
    { name: 'logistic', directly_fittable: false, needs_manual_mapping: false, suggested_mapping: { population: 'state_only' } },
  ],
  usable_state_columns: ['state_only'],
  constant_state_columns: [],
};

async function scenarioAllDisabled() {
  console.log('== 场景 1：所有模型都不可选 ==');
  const { sandbox, get, requests } = loadDashboard(() => ALL_DISABLED);
  // 模拟一次 run 之后的状态
  const sel = get('fitModel');
  get('fitAgent').value = '';
  const state = await sandbox.loadModelInfo();

  check(state === 'none', 'loadModelInfo 返回 none（区分于 error/stale）', String(state));
  check(get('fitRunBtn').disabled === true, '拟合按钮被禁用');
  check(sel.dataset.allDisabled === '1', '标记 allDisabled');
  check(sandbox.fitSelectionBlocked() === true, 'fitSelectionBlocked() 返回 true');

  sandbox.buildFittingView();
  check(String(get('statusText').textContent).length > 0, '切到拟合页时给出原因', String(get('statusText').textContent));

  const before = requests.length;
  await sandbox.runFitting();
  const fitCalls = requests.slice(before).filter((r) => r.url.includes('/api/fit'));
  check(fitCalls.length === 0, '被拦截时不发起 /api/fit 请求', `实际 ${fitCalls.length} 次`);
}

async function scenarioBlockedBeforeFit() {
  console.log('\n== 场景 1b：模型可选但映射缺失时仍应拦住（非空转断言）==');
  const { sandbox, get, requests } = loadDashboard((url) => (
    String(url).includes('/api/models') ? ALL_SELECTABLE_NEEDS_MAPPING : undefined
  ));
  get('fitAgent').value = '';
  const state = await sandbox.loadModelInfo();

  check(state === 'ready', 'loadModelInfo 返回 ready');
  check(get('fitRunBtn').disabled === false, '存在可尝试的模型，按钮可用');
  // 关键：currentStateMapping 会返回 suggested_mapping（不是 undefined），
  // 因此流程真的会走到 /api/fit 分支，这里的零请求断言才有意义。
  check(sandbox.currentStateMapping('logistic') !== undefined, 'currentStateMapping 返回映射而非 undefined');

  const before = requests.length;
  await sandbox.runFitting();
  const fitCalls = requests.slice(before).filter((r) => r.url.includes('/api/fit'));
  check(fitCalls.length === 1, '未被拦截时确实发出 1 次 /api/fit', `实际 ${fitCalls.length} 次`);
  if (fitCalls.length) {
    const body = JSON.parse(fitCalls[0].body || '{}');
    check(body.state_mapping && body.state_mapping.population === 'state_only', '请求携带 suggested_mapping', JSON.stringify(body.state_mapping));
  }
}

async function scenarioStaleMappingIsRefreshed() {
  console.log('\n== 场景 1c：切换 agent 后立刻拟合，映射必须与该 agent 一致 ==');
  const { sandbox, get, requests } = loadDashboard((url) => {
    const u = String(url);
    if (!u.includes('/api/models')) return undefined;
    return u.includes('agent_id=A')
      ? { models: [{ name: 'logistic', directly_fittable: false, needs_manual_mapping: false, suggested_mapping: { population: 'state_from_A' } }], usable_state_columns: ['state_from_A'], constant_state_columns: [] }
      : { models: [{ name: 'logistic', directly_fittable: false, needs_manual_mapping: false, suggested_mapping: { population: 'state_from_B' } }], usable_state_columns: ['state_from_B'], constant_state_columns: [] };
  });
  get('fitAgent').value = 'A';
  await sandbox.loadModelInfo();
  // 切换到 B 但不等待防抖：runFitting 必须自行重载，不能沿用 A 的映射
  get('fitAgent').value = 'B';
  const before = requests.length;
  await sandbox.runFitting();
  const fitCalls = requests.slice(before).filter((r) => r.url.includes('/api/fit'));
  check(fitCalls.length === 1, '发出 1 次 /api/fit', `实际 ${fitCalls.length} 次`);
  if (fitCalls.length) {
    const body = JSON.parse(fitCalls[0].body || '{}');
    check(body.agent_id === 'B', 'agent_id 为最新选择 B', String(body.agent_id));
    check(
      body.state_mapping && body.state_mapping.population === 'state_from_B',
      '映射已刷新为 B 的列（不是陈旧的 A）',
      JSON.stringify(body.state_mapping),
    );
  }
}

async function scenarioRunSimulationStatus() {
  console.log('\n== 场景 4：runSimulation 全链路的状态栏与按钮 ==');
  const { sandbox, get } = loadDashboard((url) => {
    const u = String(url);
    if (u.includes('/api/run')) return { status: 'ok', steps: 20, agents: 2, observations: 40 };
    if (u.includes('/api/data')) return { agents: [], columns: [], data: [], statistics: [], steps: 20 };
    if (u.includes('/api/models')) return ALL_DISABLED;
    return {};
  });
  // 真实页面带默认值；桩必须显式提供，才能验证“不再静默兜底”的输入契约。
  get('simSteps').value = '20';
  get('simSeed').value = '42';
  await sandbox.runSimulation();

  check(get('fitRunBtn').disabled === true, '全禁用时按钮被禁用');
  check(get('runSimBtn').disabled === false, '运行结束后运行按钮恢复可用');
  check(
    String(get('statusText').textContent) === sandbox.t('fitting.none_available'),
    '状态栏说明"没有可拟合模型"（而不是被"仿真完成"覆盖）',
    String(get('statusText').textContent),
  );
}

async function scenarioOneAvailable() {
  console.log('\n== 场景 2：仅 logistic 可选 ==');
  const { sandbox, get } = loadDashboard(() => ONE_AVAILABLE);
  get('fitAgent').value = '';
  const state = await sandbox.loadModelInfo();

  check(state === 'ready', 'loadModelInfo 返回 ready（存在可拟合模型）', String(state));
  check(get('fitRunBtn').disabled === false, '拟合按钮可用');
  check(get('fitModel').value === 'logistic', '默认选中唯一可用的 logistic', get('fitModel').value);
  check(get('fitModel').dataset.allDisabled !== '1', '未标记 allDisabled');
  check(sandbox.fitSelectionBlocked() === false, 'fitSelectionBlocked() 返回 false');
}

async function scenarioStaleResponseDiscarded() {
  console.log('\n== 场景 3：乱序返回时丢弃陈旧响应 ==');
  // 按 URL 里的 agent_id 决定响应：A -> 全部不可用；B（或无）-> 有可用
  const { sandbox, get, pendingResolvers } = loadDashboard(
    (url) => (String(url).includes('agent_id=A') ? ALL_DISABLED : ONE_AVAILABLE),
    { deferred: true },
  );
  get('fitAgent').value = 'A';
  const first = sandbox.loadModelInfo();
  get('fitAgent').value = 'B';
  const second = sandbox.loadModelInfo();

  check(pendingResolvers.length >= 2, '两个请求都已发出', `实际 ${pendingResolvers.length}`);
  // 关键：让**第一个**（陈旧的 A）在第二个（B）之后才 resolve。
  // 取最后两个受控项，避免页面初始化时遗留的等待项干扰。
  const last = pendingResolvers.length - 1;
  await Promise.resolve();            // 让之前已发出的请求先处理完
  pendingResolvers[last]();           // 先解析 B（较新）
  await Promise.resolve();
  await Promise.resolve();
  pendingResolvers[last - 1]();       // 再解析 A（陈旧）
  const [firstState, secondState] = await Promise.all([first, second]);

  // 直接断言返回态：陈旧调用必须自报 'stale'。
  // 只断言终态是不够的——若守卫改为返回 'ready'，陈旧响应会覆盖 UI，
  // 但后续没有新的加载来纠正时终态本身可能恰好仍正确（突变实验证明会漏网）。
  check(firstState === 'stale', '陈旧调用自报 stale（而不是伪装成 ready）', String(firstState));
  check(secondState === 'ready', '最新调用返回 ready', String(secondState));

  // 后发请求（B）应胜出
  check(get('fitRunBtn').disabled === false, '最终采用最新请求的结果（按钮可用）');
  check(sandbox.fitSelectionBlocked() === false, '陈旧响应未覆盖新响应');
}

/**
 * 桩必须与真实 DOM 结构一致：如果模板里关键 id 不存在（或改了名），
 * 本 harness 用的"凭空造元素"桩仍会全绿，但真实页面会在 setStatus 时
 * 因 null.textContent 抛错。这里做一次结构校验。
 */
function verifyTemplateIds() {
  console.log('== 场景 0：模板关键 id 与桩一致 ==');
  const templatePath = path.join(__dirname, '..', 'family_abm', 'web', 'templates', 'index.html');
  const html = fs.readFileSync(templatePath, 'utf8');
  const required = ['fitModel', 'fitAgent', 'fitRunBtn', 'fitKPIs', 'fitParams', 'statusText', 'statusDot', 'simSteps', 'simSeed', 'runSimBtn', 'familyConfigs', 'paramGroups'];
  const missingIds = required.filter((id) => !html.includes(`id="${id}"`));
  check(missingIds.length === 0, '模板包含 harness 依赖的全部 id', missingIds.length ? `缺少 ${JSON.stringify(missingIds)}` : 'ok');
}

// ── C1：映射透明化（round-2 审查）────────────────────────────────────────
//
// 回归：/api/models 的 suggested_mapping 对抽象模型是**从可用列里按字母序任取**
// 的替代品，前端自动提交给 /api/fit，返回 status=ok + converged=true，
// 而界面从不显示究竟拟合了哪两列（state_columns 由后端返回，前端 0 处引用）。

const AUTO_MAPPED = {
  models: [
    {
      name: 'square_law',
      directly_fittable: false,
      needs_manual_mapping: false,
      mapping_kind: 'auto',
      suggested_mapping: { R1: 'state_economic_pressure', R2: 'state_education' },
    },
    {
      name: 'wellbeing',
      directly_fittable: true,
      needs_manual_mapping: false,
      mapping_kind: 'default',
      suggested_mapping: { happiness: 'state_happiness', stress: 'state_stress' },
    },
  ],
  usable_state_columns: ['state_economic_pressure', 'state_education', 'state_happiness', 'state_stress'],
  constant_state_columns: [],
};

const FIT_BAD_R2 = {
  status: 'ok',
  model: 'square_law',
  state_columns: { R1: 'state_economic_pressure', R2: 'state_education' },
  summary: {
    model: 'square_law',
    params: { a: 1.0, b: 2.0 },
    r_squared: -2368436.78,
    converged: true,
    params_at_bounds: [],
    hit_sentinel: false,
  },
  predict_trace: [],
  warning: null,
};

async function scenarioAutoMappingIsVisible() {
  console.log('\n== 场景 C1a：自动映射必须可见（后缀 + 实际列名）==');
  const { sandbox, get, requests } = loadDashboard((url) => {
    const target = String(url);
    if (target.includes('/api/models')) return AUTO_MAPPED;
    if (target.includes('/api/fit')) return FIT_BAD_R2;
    return undefined;
  });
  get('fitAgent').value = '';
  await sandbox.loadModelInfo();

  const sel = get('fitModel');
  const squareOption = Array.from(sel.options).find((o) => o.value === 'square_law');
  const wellbeingOption = Array.from(sel.options).find((o) => o.value === 'wellbeing');
  check(!!squareOption && !!wellbeingOption, '两个模型都出现在下拉中');
  // 自动映射与原生映射必须能被区分：此前两者共用「需映射」或干脆无后缀
  check(
    /auto-mapped|自动映射/.test(String(squareOption.textContent)),
    'square_law 的选项标注"自动映射"',
    String(squareOption.textContent),
  );
  check(
    !/auto-mapped|自动映射|needs mapping|需映射/.test(String(wellbeingOption.textContent)),
    'wellbeing（原生映射）不得带任何映射后缀',
    String(wellbeingOption.textContent),
  );

  // 真实拟合：结果卡片必须显示实际使用的状态列
  sel.value = 'square_law';
  sel.dataset.allDisabled = '';
  await sandbox.runFitting();
  const kpis = String(get('fitKPIs').innerHTML);
  check(
    kpis.includes('state_economic_pressure') && kpis.includes('state_education'),
    '结果卡片显示实际使用的状态列',
    kpis.slice(0, 200),
  );
  check(
    /自动从可用列中选取|picked automatically/.test(kpis),
    '自动映射给出显式告警（结果只反映替代列，不代表模型原意）',
    kpis.slice(0, 260),
  );
  const fitBody = requests.filter((r) => r.url.includes('/api/fit')).pop();
  check(
    !!fitBody && String(fitBody.body).includes('state_economic_pressure'),
    '发出的 /api/fit 请求确实携带该映射',
    fitBody ? String(fitBody.body) : 'no fit request',
  );
  check(
    get('fitRunBtn').disabled === false,
    '拟合结束后拟合按钮恢复可用',
  );
}

async function scenarioNonPositiveR2DoesNotLookLikePass() {
  console.log('\n== 场景 C1b：R² 非正时 Converged 不构成"通过" ==');
  const { sandbox, get } = loadDashboard((url) => {
    const target = String(url);
    if (target.includes('/api/models')) return AUTO_MAPPED;
    if (target.includes('/api/fit')) return FIT_BAD_R2;
    return undefined;
  });
  get('fitAgent').value = '';
  await sandbox.loadModelInfo();
  const sel = get('fitModel');
  sel.value = 'square_law';
  sel.dataset.allDisabled = '';
  await sandbox.runFitting();
  const kpis = String(get('fitKPIs').innerHTML);

  // 修复前：<div class="value">是</div> 与 R²=-2368436 并排显示成两个成功指标
  check(
    /R\^2 is non-positive|R² 非正，Converged 不构成/.test(kpis),
    'R² 非正时明确说明 Converged 不构成"通过"',
    kpis.slice(0, 240),
  );
  check(
    kpis.includes('result-kpi muted'),
    '对应的 KPI 卡片被降级显示（不再与荒谬的 R² 并排当成功指标）',
  );

  // 对照：R² 为正时不得出现该降级
  const good = loadDashboard((url) => {
    const target = String(url);
    if (target.includes('/api/models')) return AUTO_MAPPED;
    if (target.includes('/api/fit')) return FIT_OK;
    return undefined;
  });
  good.get('fitAgent').value = '';
  await good.sandbox.loadModelInfo();
  const gsel = good.get('fitModel');
  gsel.value = 'wellbeing';
  gsel.dataset.allDisabled = '';
  await good.sandbox.runFitting();
  const goodKpis = String(good.get('fitKPIs').innerHTML);
  check(!goodKpis.includes('result-kpi muted'), 'R² 为正时不出现降级样式');
}

async function scenarioFitContextIsInvalidated() {
  console.log('\n== 场景 S5b：切换成员/模型或运行中不得复用旧拟合 ==');
  const { sandbox, context, get, requests } = loadDashboard((url) => (
    String(url).includes('/api/models') ? ONE_AVAILABLE : undefined
  ));
  const data = {
    agents: [
      { id: 'A', name: 'Member A', role: 'parent', age: 35 },
      { id: 'B', name: 'Member B', role: 'child', age: 8 },
    ],
    columns: [],
    data: [],
    steps: 0,
  };
  vm.runInContext(`simData = ${JSON.stringify(data)};`, context);
  sandbox.buildAgentList();
  get('fitAgent').value = '';
  await sandbox.loadModelInfo();
  get('fitModel').value = 'logistic';
  get('fitModel').dataset.allDisabled = '';
  await sandbox.runFitting();
  check(get('fitResultCard').style.display === 'block', '拟合结果已显示');

  get('fitAgent').value = 'B';
  get('fitAgent').onchange();
  check(get('fitResultCard').style.display === 'none', '切换成员后旧拟合结果被隐藏');
  check(
    vm.runInContext('lastFitResult === null && lastFitContext === null', context),
    '切换成员后拟合上下文被清除',
  );

  vm.runInContext('runInFlight = true;', context);
  const before = requests.length;
  await sandbox.runFitting();
  const fitCalls = requests.slice(before).filter((r) => r.url.includes('/api/fit'));
  check(fitCalls.length === 0, '运行中禁止发起拟合请求');
  vm.runInContext('runInFlight = false;', context);
}

async function scenarioAgentNamesAreRenderedAsText() {
  console.log('\n== 场景 S5：智能体名称不得被当作 HTML ==');
  const { sandbox, context, get } = loadDashboard(() => ({}));
  const payload = {
    agents: [{ id: 'a1', name: '<img src=x onerror=alert(1)>', role: 'child' }],
    columns: [],
    data: [],
    steps: 0,
  };
  vm.runInContext(`simData = ${JSON.stringify(payload)};`, context);
  sandbox.buildAgentList();
  const chip = get('agentsList').children[0];
  check(!!chip && chip.tagName === 'SPAN', '成员标签已通过 DOM 创建');
  check(
    !!chip && chip.textContent === '<img src=x onerror=alert(1)> (child)',
    '名称保留为纯文本',
    chip ? String(chip.textContent) : 'missing',
  );
  check(
    !!chip && !String(chip.innerHTML).includes('<img'),
    '名称未进入 innerHTML',
    chip ? String(chip.innerHTML) : 'missing',
  );
}

async function scenarioFitChartUsesOnlyMappedStates() {
  console.log('\n== 场景 C2：拟合图只画实际映射状态 ==');
  const { sandbox, context, plots } = loadDashboard(() => ({}));
  const data = {
    agents: [{ id: 'm1', name: 'M1', role: 'parent', age: 40 }],
    columns: ['agent_id', 'time', 'state_a', 'state_b', 'state_other'],
    data: [
      { agent_id: 'm1', time: 0, state_a: 0.1, state_b: 0.2, state_other: 0.9 },
      { agent_id: 'm1', time: 1, state_a: 0.3, state_b: 0.4, state_other: 0.9 },
    ],
    steps: 1,
  };
  vm.runInContext(`simData = ${JSON.stringify(data)};`, context);
  const fit = {
    state_columns: { R1: 'state_a', R2: 'state_b' },
    state_names: ['R1', 'R2'],
    predict_trace: [
      { t: [0, 1], y: [0.11, 0.31] },
      { t: [0, 1], y: [0.21, 0.41] },
    ],
  };
  sandbox.buildFitChart(fit);
  const plot = plots.filter((p) => p.id === 'chartFit').pop();
  check(!!plot, '拟合图已绘制');
  if (!plot) return;
  check(plot.traces.length === 4, '只绘制 2 个映射状态的观测与预测', `实际 ${plot.traces.length} 条`);
  const names = plot.traces.map((tr) => tr.name);
  check(
    names.includes('R1 data') && names.includes('R2 data')
      && names.includes('R1 ODE fit') && names.includes('R2 ODE fit'),
    '观测与预测按状态一一命名',
    JSON.stringify(names),
  );
  check(
    !plot.traces.some((tr) => JSON.stringify(tr.y).includes('0.9')),
    '未映射的 state_other 不进入拟合图',
  );
  check(!(plot.layout.yaxis && plot.layout.yaxis.range), 'Y 轴不再固定为 [0,1]');
}

(async () => {
  verifyTemplateIds();
  await scenarioAllDisabled();
  await scenarioBlockedBeforeFit();
  await scenarioStaleMappingIsRefreshed();
  await scenarioOneAvailable();
  await scenarioStaleResponseDiscarded();
  await scenarioRunSimulationStatus();
  await scenarioAutoMappingIsVisible();
  await scenarioNonPositiveR2DoesNotLookLikePass();
  await scenarioAgentNamesAreRenderedAsText();
  await scenarioFitContextIsInvalidated();
  await scenarioFitChartUsesOnlyMappedStates();
  console.log('');
  if (failures.length) {
    console.log(`结果：失败 ${failures.length} 项 -> ${JSON.stringify(failures)}`);
    process.exit(1);
  }
  console.log('结果：全部通过');
})();
