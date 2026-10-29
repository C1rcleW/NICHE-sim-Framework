// ── I18N ────────────────────────────────────────────────────────────────────
const I18N = {
  zh: {
    'app.title': '家庭ABM仪表板',
    'app.logo': 'Family ABM',
    'tab.setup': '仿真设置',
    'tab.charts': '数据图表',
    'tab.fitting': '曲线拟合',
    'tab.network': '关系网络',
    'status.ready': '就绪',
    'status.running': '运行中...',
    'status.simDone': '仿真完成',
    'status.fitting': '拟合中...',
    'status.fitDone': '拟合完成 (R^2={0})',
    'status.error': '错误',
    'setup.title': '仿真设置',
    'setup.steps': '步数',
    'setup.seed': '随机种子',
    'setup.run': '运行仿真',
    'setup.results': '结果',
    'setup.agents': '成员',
    'setup.family': '家庭',
    'setup.name': '名称',
    'setup.age': '年龄',
    'setup.required_field': '{0} 不能为空',
    'setup.number_invalid': '{0} 必须是有效数字',
    'setup.integer_invalid': '{0} 必须是整数',
    'setup.range_invalid': '{0} 必须在 {1} 到 {2} 之间',
    'setup.params_failed': '无法加载参数配置。',
    'setup.kpi_steps': '步数',
    'setup.kpi_agents': '智能体',
    'setup.kpi_records': '记录条数',
    'charts.warn': '请先运行仿真以查看图表。',
    'charts.timeseries': '时间序列',
    'charts.no_data': '当前选择下没有可绘制的数据（该 agent 没有对应状态量）。',
    'fitting.need_mapping': '该模型的状态名与 ABM 列名没有默认对应关系，无法直接拟合。',
    'fitting.mapping_suffix': ' （需映射）',
    'fitting.mapping_auto_suffix': ' （自动映射，非原生状态）',
    'fitting.manual_suffix': ' （需人工指定映射）',
    'fitting.uses_columns': '拟合使用的状态列：{0}',
    'fitting.mapping_auto_warn': '该模型的原生状态列不可用，已自动从可用列中选取替代列；结果只反映这些列之间的关系，不代表模型原意。',
    'fitting.converged_not_meaningful': 'R² 非正，Converged 不构成"通过"',
    'fitting.warn_sentinel': '优化停在失败哨兵：该解未成功积分，R² 无意义。',
    'fitting.warn_bounds': '参数被边界钉住：{0}（该方向可能不可辨识或边界不合适）。',
    'fitting.warn_r2_nonpositive': 'R² 非正：该模型结构不适合这些状态列，Converged 只表示优化器跑完了。',
    'fitting.none_available': '当前数据下没有可直接拟合的模型（可用状态列过少或全为常量）。',
    'fitting.models_failed': '无法获取模型列表（/api/models 请求失败）。',
    'charts.niche': '生境空间',
    'charts.niche_no_points': '没有可绘制的生境点：经济或社会维度缺失。',
    'charts.niche_missing_dims': '缺失维度：{0}；缺少坐标的成员不会被绘制。',
    'charts.niche_clipped_dims': '以下原始值被截断到 [0,1]：{0}；原始值见 /api/niche。',
    'charts.plotly_failed': 'Plotly 未能加载，图表不可用；请检查网络或改用离线版资源。',
    'network.failed': '家庭关系网络加载失败。',
    'fitting.run_in_progress': '仿真仍在运行，请完成后再拟合。',
    'fitting.warn': '请先运行仿真，然后选择模型进行拟合。',
    'fitting.title': 'ODE模型拟合（兰彻斯特型）',
    'fitting.model': '模型',
    'fitting.agent': '智能体（空=聚合）',
    'fitting.aggregate': '— 聚合 —',
    'fitting.run': '拟合模型',
    'fitting.result': '拟合结果',
    'fitting.state_metrics': '分状态诊断',
    'fitting.rmse': 'RMSE',
    'fitting.chart': 'ABM数据 vs ODE拟合',
    'fitting.converged_yes': '是',
    'fitting.converged_no': '否',
    'fitting.data_suffix': ' 数据',
    'fitting.ode_fit': 'ODE拟合',
    'network.warn': '请先运行仿真以查看家庭关系网络。',
    'network.trust': '信任',
    'network.conflict': '冲突',
    'setup.params': '参数设置',
    'setup.reset_params': '恢复默认',
    'param.Education': '教育', 'param.Income': '收入', 'param.Health': '健康',
    'param.Stress': '压力', 'param.Happiness': '幸福', 'param.Noise': '随机扰动',
    'param.Family Support': '家庭支持', 'param.Influence Shape': '影响曲线',
    'param.education_rate': '学习速率', 'param.income_base': '基础收入',
    'param.income_edu_boost': '教育加成', 'param.income_age_peak': '收入峰值年龄',
    'param.income_age_spread': '年龄跨度', 'param.health_floor': '健康下限',
    'param.health_decay_rate': '健康衰减率', 'param.health_edu_protection': '教育保护',
    'param.stress_base': '基础压力', 'param.stress_work_add': '工作压力',
    'param.stress_decay': '衰减速率', 'param.stress_neuro_sensitivity': '神经质敏感',
    'param.stress_pressure_gain': '经济压力传导', 'param.income_baseline': '收入基准',
    'param.happiness_baseline': '基础值', 'param.happiness_health_weight': '健康权重',
    'param.happiness_income_weight': '收入权重', 'param.happiness_edu_weight': '教育权重',
    'param.happiness_stress_penalty': '压力惩罚', 'param.happiness_recovery': '恢复速率',
    'param.randomness': '扰动强度',
    'param.influence_strength': '影响强度', 'param.income_support': '收入支持',
    'param.use_life_stage_susceptibility': '阶段易感性',
    'param.role_switch': '成年角色切换',
    'param.susceptibility_scale': '易感性缩放', 'param.stage_shift_years': '阶段平移（年）',
    'chart.agent_series': '智能体状态时间序列',
    'chart.time': '时间',
    'chart.value': '数值',
    'chart.niche_title': '社会生境空间',
    'chart.economic': '经济',
    'chart.social': '社会',
    'chart.fit_title': 'ABM数据 vs ODE拟合',
  },
  en: {
    'app.title': 'Family ABM Dashboard',
    'app.logo': 'Family ABM',
    'tab.setup': 'Setup',
    'tab.charts': 'Charts',
    'tab.fitting': 'Fitting',
    'tab.network': 'Network',
    'status.ready': 'Ready',
    'status.running': 'Running...',
    'status.simDone': 'Simulation complete',
    'status.fitting': 'Fitting...',
    'status.fitDone': 'Fit done (R^2={0})',
    'status.error': 'Error',
    'setup.title': 'Simulation Setup',
    'setup.steps': 'Steps',
    'setup.seed': 'Random Seed',
    'setup.run': 'Run Simulation',
    'setup.results': 'Results',
    'setup.agents': 'Agents',
    'setup.family': 'Family',
    'setup.name': 'Name',
    'setup.age': 'Age',
    'setup.required_field': '{0} is required',
    'setup.number_invalid': '{0} must be a valid number',
    'setup.integer_invalid': '{0} must be an integer',
    'setup.range_invalid': '{0} must be between {1} and {2}',
    'setup.params_failed': 'Could not load parameter configuration.',
    'setup.kpi_steps': 'Steps',
    'setup.kpi_agents': 'Agents',
    'setup.kpi_records': 'Records',
    'charts.warn': 'Run a simulation first to see charts.',
    'charts.timeseries': 'Time Series',
    'charts.no_data': 'No plottable data for the current selection (this agent has no such state).',
    'fitting.need_mapping': 'This model has no default column mapping and cannot be fitted directly.',
    'fitting.mapping_suffix': ' (needs mapping)',
    'fitting.mapping_auto_suffix': ' (auto-mapped, not native states)',
    'fitting.manual_suffix': ' (manual mapping required)',
    'fitting.uses_columns': 'State columns used for the fit: {0}',
    'fitting.mapping_auto_warn': 'This model\'s native state columns are unavailable, so substitute columns were picked automatically; the result describes those columns only, not the model\'s intent.',
    'fitting.converged_not_meaningful': 'R^2 is non-positive; Converged is not a pass',
    'fitting.warn_sentinel': 'Optimizer stopped on the failure sentinel: the solution never integrated, R^2 is meaningless.',
    'fitting.warn_bounds': 'Parameters pinned at bounds: {0} (that direction may be unidentifiable or the bounds unsuitable).',
    'fitting.warn_r2_nonpositive': 'Non-positive R^2: this model structure does not suit these state columns; Converged only means the optimizer finished.',
    'fitting.none_available': 'No directly fittable model for the current data (too few usable state columns, or all are constant).',
    'fitting.models_failed': 'Could not load the model list (/api/models failed).',
    'charts.niche': 'Niche Space',
    'charts.niche_no_points': 'No niche points to plot: the economic or social dimension is missing.',
    'charts.niche_missing_dims': 'Missing dimensions: {0}; members without a coordinate are not plotted.',
    'charts.niche_clipped_dims': 'Raw values clipped to [0,1]: {0}; see /api/niche for raw values.',
    'charts.plotly_failed': 'Plotly failed to load; charts are unavailable. Check the network or use local assets.',
    'network.failed': 'Could not load family networks.',
    'fitting.run_in_progress': 'The simulation is still running; wait before fitting.',
    'fitting.warn': 'Run a simulation first, then select a model to fit.',
    'fitting.title': 'ODE Model Fitting (Lanchester-type)',
    'fitting.model': 'Model',
    'fitting.agent': 'Agent (empty = aggregate)',
    'fitting.aggregate': '— Aggregate —',
    'fitting.run': 'Fit Model',
    'fitting.result': 'Fit Result',
    'fitting.state_metrics': 'Per-state diagnostics',
    'fitting.rmse': 'RMSE',
    'fitting.chart': 'ABM Data vs ODE Fit',
    'fitting.converged_yes': 'Yes',
    'fitting.converged_no': 'No',
    'fitting.data_suffix': ' data',
    'fitting.ode_fit': 'ODE fit',
    'network.warn': 'Run a simulation first to see family networks.',
    'network.trust': 'Trust',
    'network.conflict': 'Conflict',
    'setup.params': 'Parameters',
    'setup.reset_params': 'Reset Defaults',
    'param.Education': 'Education', 'param.Income': 'Income', 'param.Health': 'Health',
    'param.Stress': 'Stress', 'param.Happiness': 'Happiness', 'param.Noise': 'Noise',
    'param.Family Support': 'Family Support', 'param.Influence Shape': 'Influence Shape',
    'param.education_rate': 'Learn Rate', 'param.income_base': 'Base Income',
    'param.income_edu_boost': 'Edu Boost', 'param.income_age_peak': 'Peak Age',
    'param.income_age_spread': 'Age Spread', 'param.health_floor': 'Health Floor',
    'param.health_decay_rate': 'Health Decay', 'param.health_edu_protection': 'Edu Protection',
    'param.stress_base': 'Base Load', 'param.stress_work_add': 'Work Add',
    'param.stress_decay': 'Decay Rate', 'param.stress_neuro_sensitivity': 'Neuro Sens',
    'param.stress_pressure_gain': 'Pressure Gain', 'param.income_baseline': 'Income Baseline',
    'param.happiness_baseline': 'Baseline', 'param.happiness_health_weight': 'Health Wt',
    'param.happiness_income_weight': 'Income Wt', 'param.happiness_edu_weight': 'Edu Wt',
    'param.happiness_stress_penalty': 'Stress Pen', 'param.happiness_recovery': 'Recovery',
    'param.randomness': 'Noise Level',
    'param.influence_strength': 'Influence Strength', 'param.income_support': 'Income Support',
    'param.use_life_stage_susceptibility': 'Life-stage Susceptibility',
    'param.role_switch': 'Adult Role Switch',
    'param.susceptibility_scale': 'Susceptibility Scale',
    'param.stage_shift_years': 'Stage Shift (years)',
    'chart.agent_series': 'Agent State Time Series',
    'chart.time': 'Time',
    'chart.value': 'Value',
    'chart.niche_title': 'Social Niche Space',
    'chart.economic': 'Economic',
    'chart.social': 'Social',
    'chart.fit_title': 'ABM Data vs ODE Fit',
  },
};

const LANG_KEY = 'family_abm_lang';
let currentLang = localStorage.getItem(LANG_KEY) || 'en';

function t(key, ...args) {
  const map = I18N[currentLang] || I18N['en'];
  let s = map[key] || I18N['en'][key] || key;
  args.forEach((a, i) => { s = s.replace('{' + i + '}', a); });
  return s;
}

function refreshI18n() {
  document.documentElement.lang = currentLang;
  document.querySelectorAll('[data-i18n]').forEach(el => {
    const key = el.getAttribute('data-i18n');
    el.textContent = t(key);
  });
  document.querySelectorAll('.family-card').forEach(card => {
    const name = card.dataset.familyName;
    const heading = card.querySelector('h3');
    if (name && heading) heading.textContent = `${name} ${t('setup.family')}`;
  });
  refreshStatusI18n();
  document.querySelectorAll('[data-i18n-title]').forEach(el => {
    el.title = t(el.getAttribute('data-i18n-title'));
  });
  document.querySelectorAll('[data-i18n-placeholder]').forEach(el => {
    el.placeholder = t(el.getAttribute('data-i18n-placeholder'));
  });
  document.title = t('app.title');
  document.querySelectorAll('#langDrop .lang-item').forEach(item => {
    item.classList.toggle('active', item.dataset.lang === currentLang);
    item.textContent = item.dataset.lang === 'zh' ? '简体中文' : 'English';
  });
  if (simData) {
    document.getElementById('agentSelectCard').querySelector('h2').textContent = t('setup.agents');
    document.querySelectorAll('#resultKPIs .label').forEach((el, i) => {
      el.textContent = t(['setup.kpi_steps', 'setup.kpi_agents', 'setup.kpi_records'][i]);
    });
  }
}

function setLang(lang) {
  currentLang = lang;
  localStorage.setItem(LANG_KEY, lang);
  refreshI18n();
  if (!simData) return;

  buildAgentList();
  buildCharts();
  const activeTab = document.querySelector('.tab-content.active');
  if (activeTab && activeTab.id === 'tab-fitting') {
    buildFittingView();
    loadModelInfo().then(() => {
      if (lastFitResult && fitContextMatches()) {
        document.getElementById('fitResultCard').style.display = 'block';
        document.getElementById('fitChartCard').style.display = 'block';
        renderFitResult(lastFitResult, lastFitModel, lastFitContext);
      } else {
        hideFitResult();
      }
    });
  } else if (activeTab && activeTab.id === 'tab-network') {
    buildNetwork();
  }
}

// ── State ──────────────────────────────────────────────────────────────────
let simData = null;
let simRunId = null;
let _runSeq = 0;
let lastFitResult = null;
let lastFitModel = null;
let lastFitContext = null;
let runInFlight = false;
let statusInfo = { state: 'ready', message: null, kind: null, r2: null };
const CHART_THEME = {
  paper_bgcolor: '#fff', plot_bgcolor: '#f8fafc',
  font: { family: '-apple-system,BlinkMacSystemFont,sans-serif', size: 11 },
  margin: { l: 50, r: 30, t: 30, b: 50 },
  legend: { orientation: 'h', y: 1.12, font: { size: 10 } },
};

// ── Tabs ───────────────────────────────────────────────────────────────────
document.querySelectorAll('#tabNav button').forEach(btn => {
  btn.addEventListener('click', () => {
    document.querySelectorAll('#tabNav button').forEach(b => b.classList.remove('active'));
    btn.classList.add('active');
    document.querySelectorAll('.tab-content').forEach(t => t.classList.remove('active'));
    document.getElementById('tab-' + btn.dataset.tab).classList.add('active');
    onTabSwitch(btn.dataset.tab);
  });
});

function onTabSwitch(tab) {
  if (tab === 'charts' && simData) buildCharts();
  if (tab === 'fitting' && simData) {
    buildFittingView();
    if (lastFitResult && fitContextMatches()) {
      document.getElementById('fitResultCard').style.display = 'block';
      document.getElementById('fitChartCard').style.display = 'block';
      renderFitResult(lastFitResult, lastFitModel, lastFitContext);
    } else {
      hideFitResult();
    }
  }
  if (tab === 'network' && simData) buildNetwork();
}

// ── Language switcher ──────────────────────────────────────────────────────
document.getElementById('langBtn').addEventListener('click', e => {
  e.stopPropagation();
  document.getElementById('langDrop').classList.toggle('show');
});
document.querySelectorAll('#langDrop .lang-item').forEach(item => {
  item.addEventListener('click', () => {
    setLang(item.dataset.lang);
    document.getElementById('langDrop').classList.remove('show');
  });
});
document.addEventListener('click', () => {
  document.getElementById('langDrop').classList.remove('show');
});

// ── API ────────────────────────────────────────────────────────────────────
async function api(url, opts = {}) {
  try {
    const res = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opts });
    let payload;
    try {
      payload = await res.json();
    } catch (_err) {
      return { error: `HTTP ${res.status}: invalid JSON response` };
    }
    if (!res.ok && (!payload || typeof payload !== 'object')) {
      return { error: `HTTP ${res.status}` };
    }
    if (!res.ok && !payload.error) {
      payload.error = `HTTP ${res.status}`;
    }
    return payload;
  } catch (e) {
    return { error: e.message || 'Network error' };
  }
}

function hasPlotly() {
  return typeof Plotly !== 'undefined';
}

function showPlotlyFailure(containerId) {
  const el = document.getElementById(containerId);
  if (el) el.textContent = t('charts.plotly_failed');
}

function withRunId(url, runId = simRunId) {
  if (!runId) return url;
  const sep = url.includes('?') ? '&' : '?';
  return `${url}${sep}run_id=${encodeURIComponent(runId)}`;
}

function hideFitResult() {
  ['fitResultCard', 'fitChartCard'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
  });
}

function invalidateFitResult() {
  lastFitResult = null;
  lastFitModel = null;
  lastFitContext = null;
  _fitSeq += 1;
  hideFitResult();
}

function fitContextMatches() {
  if (!lastFitContext || !simRunId) return false;
  const agentSel = document.getElementById('fitAgent');
  const modelSel = document.getElementById('fitModel');
  const agentId = agentSel ? (agentSel.value || null) : null;
  const model = modelSel ? modelSel.value : null;
  return lastFitContext.run_id === simRunId
    && lastFitContext.agent_id === agentId
    && lastFitContext.model === model;
}

function restoreStableViewStatus() {
  if (lastFitResult && fitContextMatches()) {
    const r2 = lastFitResult.summary?.r_squared;
    const r2val = r2 !== null && r2 !== undefined ? Number(r2).toFixed(4) : '\u2014';
    setStatus('ok', t('status.fitDone', r2val), { kind: 'fitDone', r2: r2val });
  } else if (simData) {
    setStatus('ok', t('status.simDone'), { kind: 'simDone' });
  } else {
    setStatus('ready', t('status.ready'));
  }
}

function clearRunView() {
  simData = null;
  simRunId = null;
  selAgentId = null;
  modelInfo = {};
  modelInfoAgentId = null;
  modelInfoRunId = null;
  lastFitResult = null;
  lastFitModel = null;
  lastFitContext = null;
  fitModelTouched = false;
  _modelInfoSeq += 1;
  _fitSeq += 1;
  const fitBtn = document.getElementById('fitRunBtn');
  if (fitBtn) fitBtn.disabled = true;
  ['resultCard', 'agentSelectCard', 'timeseriesCard', 'nicheCard', 'fitResultCard', 'fitChartCard'].forEach(id => {
    const el = document.getElementById(id);
    if (el) el.style.display = 'none';
  });
  ['chartTimeSeries', 'chartNiche', 'chartFit'].forEach(id => {
    if (typeof Plotly !== 'undefined') Plotly.purge(id);
  });
  const networks = document.getElementById('networkCards');
  if (networks) networks.innerHTML = '';
}

// ── Parameters ─────────────────────────────────────────────────────────────
let paramDefaults = {};
let paramGroups = {};
let paramSpecs = {};
let simLimits = {};

async function loadParams() {
  const res = await api('/api/params');
  if (res.error || !res.defaults) {
    setStatus('error', res.error || t('setup.params_failed'));
    return;
  }
  paramDefaults = res.defaults;
  paramGroups = res.groups || {};
  paramSpecs = res.specs || {};
  simLimits = res.limits || {};
  applySimulationLimits();
  buildParams();
}

function applySimulationLimits() {
  const steps = document.getElementById('simSteps');
  const limit = simLimits.steps;
  if (!steps || !limit) return;
  steps.min = limit.min;
  steps.max = limit.max;
}

function buildParams() {
  const container = document.getElementById('paramGroups');
  let html = '';
  Object.entries(paramGroups).forEach(([group, keys]) => {
    html += `<div class="param-group"><h4 class="param-group-title" data-i18n="param.${group}">${t('param.' + group)}</h4><div class="param-items">`;
    keys.forEach(key => {
      const val = paramDefaults[key] !== undefined ? paramDefaults[key] : 0;
      const spec = paramSpecs[key] || { min: 0, max: 5, step: 0.001, type: 'number' };
      const step = spec.type === 'switch' ? 1 : spec.step;
      html += `<div class="param-item">
        <label data-i18n="param.${key}">${t('param.' + key)}</label>
        <input type="number" class="param-input" data-param="${key}" value="${val}" step="${step}" min="${spec.min}" max="${spec.max}">
      </div>`;
    });
    html += `</div></div>`;
  });
  container.innerHTML = html;
}

function readNumberInput(input, label, { min, max, integer = false } = {}) {
  const raw = input ? String(input.value).trim() : '';
  if (raw === '') throw new Error(t('setup.required_field', label));
  const value = Number(raw);
  if (!Number.isFinite(value)) throw new Error(t('setup.number_invalid', label));
  if (integer && !Number.isInteger(value)) throw new Error(t('setup.integer_invalid', label));
  if ((min !== undefined && value < min) || (max !== undefined && value > max)) {
    throw new Error(t('setup.range_invalid', label, min, max));
  }
  return value;
}

function getParams() {
  const params = {};
  document.querySelectorAll('.param-input').forEach(inp => {
    const key = inp.dataset.param;
    const spec = paramSpecs[key] || { min: 0, max: 5, type: 'number' };
    params[key] = readNumberInput(inp, t('param.' + key), {
      min: spec.min,
      max: spec.max,
      integer: spec.type === 'switch',
    });
  });
  return params;
}

window.resetParams = function() {
  document.querySelectorAll('.param-input').forEach(inp => {
    const key = inp.dataset.param;
    if (paramDefaults[key] !== undefined) inp.value = paramDefaults[key];
  });
};

// ── Simulation ─────────────────────────────────────────────────────────────
const defaultFamilies = [
  { name: 'Smith', members: [
    { name: 'Father', age: 40, gender: 'male', role_name: 'parent' },
    { name: 'Mother', age: 38, gender: 'female', role_name: 'parent' },
    { name: 'Child', age: 10, gender: 'male', role_name: 'child' },
  ]},
  { name: 'Jones', members: [
    { name: 'Mom', age: 35, gender: 'female', role_name: 'parent' },
    { name: 'Daughter', age: 8, gender: 'female', role_name: 'child' },
  ]},
];

function buildFamilyConfigs() {
  const container = document.getElementById('familyConfigs');
  let html = '';
  defaultFamilies.forEach((f, fi) => {
    html += `<div class="family-card" data-family-name="${f.name}"><h3>${f.name} ${t('setup.family')}</h3>`;
    f.members.forEach((m, mi) => {
      html += `<div class="member-line">
        <input value="${m.name}" data-fam="${fi}" data-mem="${mi}" data-key="name" placeholder="${t('setup.name')}">
        <input type="number" value="${m.age}" data-fam="${fi}" data-mem="${mi}" data-key="age" min="0" max="120" style="width:60px">
        <select data-fam="${fi}" data-mem="${mi}" data-key="gender">
          <option ${m.gender==='male'?'selected':''}>male</option>
          <option ${m.gender==='female'?'selected':''}>female</option>
        </select>
        <select data-fam="${fi}" data-mem="${mi}" data-key="role_name">
          <option ${m.role_name==='parent'?'selected':''}>parent</option>
          <option ${m.role_name==='child'?'selected':''}>child</option>
          <option ${m.role_name==='adult'?'selected':''}>adult</option>
          <option ${m.role_name==='elder'?'selected':''}>elder</option>
        </select>
      </div>`;
    });
    html += '</div>';
  });
  container.innerHTML = html;
}

function getFamilyConfigs() {
  const families = [];
  document.querySelectorAll('.family-card').forEach(card => {
    const name = card.dataset.familyName;
    const members = [];
    card.querySelectorAll('.member-line').forEach(line => {
      const inputs = line.querySelectorAll('input');
      const selects = line.querySelectorAll('select');
      members.push({
        name: inputs[0].value,
        age: readNumberInput(inputs[1], t('setup.age'), { min: 0, max: 120 }),
        gender: selects[0].value,
        role_name: selects[1].value,
      });
    });
    families.push({ name, members });
  });
  return families;
}

async function runSimulation() {
  const runBtn = document.getElementById('runSimBtn');
  if (runBtn) runBtn.disabled = true;
  runInFlight = true;
  setStatus('running', t('status.running'), { kind: 'simRunning' });
  try {
    let cfg;
    try {
      const stepLimit = simLimits.steps || { min: 1, max: 5000 };
      cfg = {
        steps: readNumberInput(
          document.getElementById('simSteps'), t('setup.steps'),
          { min: stepLimit.min, max: stepLimit.max, integer: true },
        ),
        // 随机种子：同一配置 + 同一种子可复现（含智能体初始化）
        seed: readNumberInput(
          document.getElementById('simSeed'), t('setup.seed'),
          { min: 0, max: 999999, integer: true },
        ),
        params: getParams(),
        families: getFamilyConfigs(),
      };
    } catch (err) {
      setStatus('error', err.message);
      return;
    }

    const seq = ++_runSeq;
    clearRunView();
    const res = await api('/api/run', { method: 'POST', body: JSON.stringify(cfg) });
    if (seq !== _runSeq) return;
    if (res.error) { setStatus('error', res.error); return; }

    const runId = res.run_id || null;
    simRunId = runId;
    const data = await api(withRunId('/api/data', runId));
    if (seq !== _runSeq) return;
    if (data.error) { setStatus('error', data.error); return; }
    simData = data;

    document.getElementById('resultCard').style.display = 'block';
    document.getElementById('agentSelectCard').style.display = 'block';
    document.getElementById('resultKPIs').innerHTML = `
      <div class="result-kpi"><div class="value">${res.steps}</div><div class="label">${t('setup.kpi_steps')}</div></div>
      <div class="result-kpi"><div class="value">${res.agents}</div><div class="label">${t('setup.kpi_agents')}</div></div>
      <div class="result-kpi"><div class="value">${res.observations}</div><div class="label">${t('setup.kpi_records')}</div></div>
    `;

    buildAgentList();
    // 至少一个模型可拟合才算真正可用；全禁用时状态栏必须说明原因，
    // 不能被下面那句"仿真完成"覆盖（复核指出这正是原因说明不可见的原因）。
    const infoState = await loadModelInfo();
    if (seq !== _runSeq) return;
    if (infoState === 'ready' || infoState === 'stale') {
      // 运行本身已经成功；模型可拟合性只影响拟合页，不应把状态栏卡在 Running。
      setStatus('ok', t('status.simDone'), { kind: 'simDone' });
    } else if (infoState === 'none') {
      setStatus('error', t('fitting.none_available'));
    }
    document.querySelector('#tabNav button[data-tab="charts"]').click();
  } finally {
    runInFlight = false;
    if (runBtn) runBtn.disabled = false;
  }
}

// 模型可映射性：抽象模型（square_law/influence/...）的状态名与 ABM 列名没有默认
// 对应关系，必须显式给出 state_mapping。此前前端只发 model_name/agent_id/robust，
// 导致 7 个模型里有 6 个在界面上永远返回 400。
let modelInfo = {};
let modelInfoAgentId = null;   // 当前 modelInfo 是按哪个 agent 评估的
let modelInfoRunId = null;     // 当前 modelInfo 属于哪个运行
let fitModelTouched = false;   // 用户是否主动选择过模型
let _modelInfoSeq = 0;         // 请求序号：丢弃乱序返回的陈旧响应
let _modelInfoDebounce = null;
let _fitSeq = 0;

/**
 * 按当前选中的 agent 拉取模型可拟合性，并渲染模型下拉。
 *
 * 返回三态之一（不要把"陈旧"与"不可拟合"混为一谈）：
 *   'ready' —— 已按最新选择加载完成
 *   'none'  —— 加载成功但没有任何模型可拟合
 *   'error' —— 请求失败
 *   'stale' —— 期间发起了更新的请求，本次结果被丢弃
 */
async function loadModelInfo() {
  // 拟合到单个 agent 时用的是该 agent 自己的序列，
  // "整体有变化但该 agent 恒定"的列必须按子集重新判定。
  const seq = ++_modelInfoSeq;
  const requestedRunId = simRunId;
  const agentSel = document.getElementById('fitAgent');
  const agentId = agentSel ? (agentSel.value || '') : '';
  const query = [];
  if (agentId) query.push(`agent_id=${encodeURIComponent(agentId)}`);
  if (requestedRunId) query.push(`run_id=${encodeURIComponent(requestedRunId)}`);
  const qs = query.join('&');
  let res;
  try {
    res = await api('/api/models' + (qs ? `?${qs}` : ''));
  } catch (err) {
    if (seq !== _modelInfoSeq) return 'stale';
    setStatus('error', String(err));
    return 'error';
  }
  // 期间又发起了更新的请求或运行：本次结果已陈旧，直接丢弃。
  if (seq !== _modelInfoSeq || requestedRunId !== simRunId) return 'stale';
  if (res.error || !res.models) {
    setStatus('error', res.error || t('fitting.models_failed'));
    return 'error';
  }
  modelInfo = {};
  res.models.forEach(m => { modelInfo[m.name] = m; });
  modelInfoAgentId = agentId;
  modelInfoRunId = requestedRunId;

  const sel = document.getElementById('fitModel');
  const previousSelection = sel.value;
  const options = res.models.map(m => {
    // 无法直接映射、且候选列不足以自动给出映射的模型：置灰不可选。
    // 此前只标注"需人工指定"但页面上没有映射输入控件，等于给用户一个死路。
    if (m.needs_manual_mapping) {
      return `<option value="${m.name}" disabled>${m.name}${t('fitting.manual_suffix')}</option>`;
    }
    // 后缀必须区分"原生映射"与"自动选取的替代列"：两者此前共用「需映射」，
    // 而后者是字母序任取的，用户看不出模型被拟到了无关列上。
    let suffix = '';
    if (m.mapping_kind === 'auto') suffix = t('fitting.mapping_auto_suffix');
    else if (!m.directly_fittable) suffix = t('fitting.mapping_suffix');
    return `<option value="${m.name}">${m.name}${suffix}</option>`;
  });
  sel.innerHTML = options.join('');
  const preferred = ['wellbeing', 'influence', 'logistic', 'square_law', 'linear_law', 'lotka_volterra', 'resource_competition'];
  const previous = modelInfo[previousSelection];
  const keepPrevious = previousSelection
    && previous
    && !previous.needs_manual_mapping
    && (fitModelTouched || previous.directly_fittable);
  const pick = keepPrevious
    ? previousSelection
    : preferred.find(n => modelInfo[n] && !modelInfo[n].needs_manual_mapping);
  if (pick) sel.value = pick;

  // 全部模型都不可用时：下拉会停在空值，此时必须禁用拟合按钮并说明原因，
  // 否则用户点击会发出 model_name="" 并收到一条"未知模型名"的原始错误。
  const anySelectable = res.models.some(m => !m.needs_manual_mapping);
  const btn = document.getElementById('fitRunBtn');
  if (btn) btn.disabled = !anySelectable;
  sel.dataset.allDisabled = anySelectable ? '' : '1';
  // 状态栏由调用方决定（runSimulation 成功后会写"仿真完成"，此处若也写状态会被覆盖）
  return anySelectable ? 'ready' : 'none';
}

/** agent 下拉的防抖包装：避免快速切换产生并发请求与乱序覆盖。 */
function scheduleLoadModelInfo() {
  if (_modelInfoDebounce) clearTimeout(_modelInfoDebounce);
  _modelInfoDebounce = setTimeout(() => { loadModelInfo(); }, 200);
}

/** 下拉被置灰/全禁用时不允许发起拟合。 */
function fitSelectionBlocked() {
  const sel = document.getElementById('fitModel');
  if (!sel || sel.dataset.allDisabled === '1') return true;
  const option = sel.options[sel.selectedIndex];
  return !option || option.disabled;
}

function currentStateMapping(modelName) {
  const info = modelInfo[modelName];
  if (!info) return null;
  if (info.directly_fittable) return null; // 走默认约定即可
  if (info.needs_manual_mapping) return undefined; // 信号：必须人工指定
  return info.suggested_mapping || null;
}

function buildAgentList() {
  if (!simData) return;
  const list = document.getElementById('agentsList');
  list.innerHTML = '';
  simData.agents.forEach(a => {
    const chip = document.createElement('span');
    chip.className = 'agent-chip' + (selAgentId === a.id ? ' sel' : '');
    chip.dataset.id = a.id;
    chip.textContent = `${a.name} (${a.role})`;
    chip.addEventListener('click', () => selAgent(chip, a.id));
    list.appendChild(chip);
  });

  const sel = document.getElementById('fitAgent');
  const previousAgent = sel.value;
  sel.innerHTML = '';
  const aggregate = document.createElement('option');
  aggregate.value = '';
  aggregate.textContent = t('fitting.aggregate');
  sel.appendChild(aggregate);
  simData.agents.forEach(a => {
    const option = document.createElement('option');
    option.value = a.id;
    option.textContent = `${a.name} (${a.role})`;
    sel.appendChild(option);
  });
  if (previousAgent && Array.from(sel.options).some(o => o.value === previousAgent)) {
    sel.value = previousAgent;
  }
  // 拟合对象变化会改变"哪些状态列有变化"，需要重新评估模型可拟合性
  sel.onchange = () => {
    invalidateFitResult();
    restoreStableViewStatus();
    scheduleLoadModelInfo();
  };
}

let selAgentId = null;
function selAgent(el, id) {
  selAgentId = (selAgentId === id) ? null : id;
  document.querySelectorAll('.agent-chip').forEach(c => c.classList.remove('sel'));
  if (selAgentId) el.classList.add('sel');
  buildCharts();
}

// ── Charts ─────────────────────────────────────────────────────────────────
function buildCharts() {
  const warn = document.getElementById('chartWarning');
  if (!simData) {
    warn.textContent = t('charts.warn');
    warn.style.display = 'block';
    return;
  }
  if (!hasPlotly()) {
    warn.textContent = t('charts.plotly_failed');
    warn.style.display = 'block';
    return;
  }
  warn.textContent = '';
  warn.style.display = 'none';

  document.getElementById('timeseriesCard').style.display = 'block';
  document.getElementById('nicheCard').style.display = 'block';

  buildTimeSeries();
  buildNicheChart();
}

function buildTimeSeries() {
  if (!hasPlotly()) {
    showPlotlyFailure('chartTimeSeries');
    return;
  }
  const df = simData.data;
  let series = df;
  if (selAgentId) series = series.filter(r => r.agent_id === selAgentId);

  const stateCols = simData.columns.filter(c => c.startsWith('state_'));
  const traces = stateCols.map(col => {
    const byTime = {};
    series.forEach(r => {
      const v = r[col];
      // 缺失值必须是 null（不是 0）：Household 行没有成员状态列，
      // 用 `|| 0` 会把"不存在"伪造成 0，使均值比真实值低约 28.6%。
      if (v === null || v === undefined || Number.isNaN(v)) return;
      byTime[r.time] = byTime[r.time] || [];
      byTime[r.time].push(v);
    });
    const t = Object.keys(byTime).map(Number).sort((a, b) => a - b);
    const vals = t.map(ti => byTime[ti].reduce((a, b) => a + b, 0) / byTime[ti].length);
    if (!t.length) return null;
    return { x: t, y: vals, type: 'scatter', mode: 'lines', name: col.replace('state_', '') };
  }).filter(Boolean);
  if (!traces.length) {
    Plotly.purge('chartTimeSeries');
    document.getElementById('chartTimeSeries').innerHTML =
      `<div class="loading">${t('charts.no_data')}</div>`;
    return;
  }

  Plotly.newPlot('chartTimeSeries', traces, {
    ...CHART_THEME, title: t('chart.agent_series'),
    xaxis: { title: t('chart.time') }, yaxis: { title: t('chart.value'), range: [0, 1] },
  }, { responsive: true });
}

async function buildNicheChart() {
  const warningEl = document.getElementById('nicheWarning');
  const chartEl = document.getElementById('chartNiche');
  const requestRunId = simRunId;
  const res = await api(withRunId('/api/niche', requestRunId));
  if (requestRunId !== simRunId) return;
  if (!hasPlotly()) {
    warningEl.textContent = t('charts.plotly_failed');
    warningEl.style.display = 'block';
    chartEl.textContent = '';
    return;
  }
  if (res.error || !res.niches) {
    if (hasPlotly()) Plotly.purge('chartNiche');
    chartEl.textContent = '';
    warningEl.textContent = res.error || t('charts.niche_no_points');
    warningEl.style.display = 'block';
    return;
  }

  const valid = res.niches.filter(n =>
    n.position && Number.isFinite(n.position.economic) && Number.isFinite(n.position.social)
  );
  const missing = [...new Set(res.niches.flatMap(n => n.missing_dimensions || []))];
  const clipped = [...new Set(res.niches.flatMap(n => n.clipped_dimensions || []))];
  const warnings = [];
  if (missing.length) warnings.push(t('charts.niche_missing_dims', missing.join(', ')));
  if (clipped.length) warnings.push(t('charts.niche_clipped_dims', clipped.join(', ')));
  warningEl.textContent = warnings.join(' ');
  warningEl.style.display = warnings.length ? 'block' : 'none';

  if (!valid.length) {
    Plotly.purge('chartNiche');
    chartEl.innerHTML = `<div class="loading">${t('charts.niche_no_points')}</div>`;
    return;
  }

  const roleColors = { parent: '#e74c3c', child: '#3498db', adult: '#f39c12', elder: '#2ecc71' };
  const traces = [{
    x: valid.map(n => n.position.economic),
    y: valid.map(n => n.position.social),
    text: valid.map(n => n.name),
    type: 'scatter', mode: 'markers+text', textposition: 'top center',
    marker: { size: 14, color: valid.map(n => roleColors[n.role] || '#95a5a6'), line: { width: 1, color: '#fff' } },
  }];
  Plotly.newPlot('chartNiche', traces, {
    ...CHART_THEME, title: t('chart.niche_title'),
    xaxis: { title: t('chart.economic'), range: [0, 1] }, yaxis: { title: t('chart.social'), range: [0, 1] },
  }, { responsive: true });
}

// ── Fitting ────────────────────────────────────────────────────────────────
function buildFittingView() {
  document.getElementById('fitWarning').style.display = 'none';
  document.getElementById('fitControlCard').style.display = 'block';
  // 若当前数据下没有可拟合的模型，切换到此页时也要说明原因
  // （否则用户只看到按钮灰掉却不知道为何）
  const sel = document.getElementById('fitModel');
  if (sel && sel.dataset.allDisabled === '1') {
    setStatus('error', t('fitting.none_available'));
  }
  // 若模型信息属于别的 agent（防抖未落定或曾失败），在此补一次加载
  const agentSel = document.getElementById('fitAgent');
  const selectedAgent = agentSel ? (agentSel.value || '') : '';
  if (modelInfoAgentId !== selectedAgent || modelInfoRunId !== simRunId) {
    loadModelInfo().then((state) => {
      if (state === 'none') setStatus('error', t('fitting.none_available'));
    });
  }
}

async function runFitting() {
  const fitBtn = document.getElementById('fitRunBtn');
  if (fitBtn) fitBtn.disabled = true;
  try {
    await _runFittingImpl();
  } finally {
    if (fitBtn) {
      fitBtn.disabled = runInFlight || !simRunId || fitSelectionBlocked();
    }
  }
}

async function _runFittingImpl() {
  if (runInFlight) {
    setStatus('error', t('fitting.run_in_progress'));
    return;
  }
  if (!simRunId) {
    setStatus('error', t('fitting.warn'));
    return;
  }
  setStatus('running', t('status.fitting'), { kind: 'fitRunning' });
  const fitSeq = ++_fitSeq;
  const requestRunId = simRunId;
  const agentSel = document.getElementById('fitAgent');
  const selectedAgent = agentSel ? (agentSel.value || '') : '';

  // 防抖意味着"切换 agent/运行后立刻点拟合"时，modelInfo 可能仍属于旧状态，
  // 此时 state_mapping 会指向错误的数据列。这里按需同步重载。
  if (modelInfoAgentId !== selectedAgent || modelInfoRunId !== requestRunId) {
    const state = await loadModelInfo();
    if (fitSeq !== _fitSeq || requestRunId !== simRunId) return;
    if (state === 'stale') {
      restoreStableViewStatus();
      return;
    }
    if (modelInfoAgentId !== selectedAgent || modelInfoRunId !== requestRunId) {
      if (state === 'none') setStatus('error', t('fitting.none_available'));
      return;
    }
  }

  if (fitSelectionBlocked()) {
    setStatus('error', t('fitting.none_available'));
    return;
  }
  const model = document.getElementById('fitModel').value;
  const agent = selectedAgent || null;
  const mapping = currentStateMapping(model);
  if (mapping === undefined) {
    // 候选状态列不足以覆盖该模型的状态数：必须由用户显式指定映射，不能瞎猜
    setStatus('error', t('fitting.need_mapping'));
    return;
  }

  lastFitResult = null;
  lastFitModel = null;
  lastFitContext = null;
  hideFitResult();

  const res = await api('/api/fit', {
    method: 'POST',
    body: JSON.stringify({
      model_name: model,
      agent_id: agent,
      robust: true,
      run_id: requestRunId,
      state_mapping: mapping,
    }),
  });
  if (fitSeq !== _fitSeq || requestRunId !== simRunId) return;
  if (res.error) { setStatus('error', res.error); return; }

  document.getElementById('fitResultCard').style.display = 'block';
  document.getElementById('fitChartCard').style.display = 'block';
  lastFitResult = res;
  lastFitModel = model;
  lastFitContext = { run_id: requestRunId, agent_id: agent, model };
  renderFitResult(res, model, lastFitContext);

  const r2val = res.summary.r_squared !== null ? res.summary.r_squared.toFixed(4) : '\u2014';
  setStatus('ok', t('status.fitDone', r2val), { kind: 'fitDone', r2: r2val });
}

function renderFitResult(res, model, context = null) {
  if (!res || !res.summary) return;
  const s = res.summary;
  // 告警必须可见：贴边参数表示该方向可能不可辨识；哨兵命中表示解本身无效。
  const warnings = [];
  if (res.warning) warnings.push(res.warning);
  if (s.hit_sentinel) warnings.push(t('fitting.warn_sentinel'));
  if (s.params_at_bounds && s.params_at_bounds.length) {
    warnings.push(t('fitting.warn_bounds', s.params_at_bounds.join(', ')));
  }
  // 自动映射必须显式告警：该模型的"原生状态"没有对应列，实际拟合的是替代列，
  // 结果只反映这些列之间的关系（此前 UI 对此完全静默）。
  const info = modelInfo[model];
  if (info && info.mapping_kind === 'auto') {
    warnings.push(t('fitting.mapping_auto_warn'));
  }
  // R² 非正时也要显式提示：converged 只说明优化器跑完了，不代表模型适用
  const r2NonPositive = s.r_squared !== null && s.r_squared <= 0;
  if (r2NonPositive) {
    warnings.push(t('fitting.warn_r2_nonpositive'));
  }
  // 实际使用的状态列：后端已返回 state_columns 对象，用户需要看到究竟拟合了哪些变量。
  const usedCols = res.state_columns && typeof res.state_columns === 'object'
    ? Object.values(res.state_columns).join(', ')
    : '';
  const colsLine = usedCols
    ? `<div class="fit-columns">${t('fitting.uses_columns', usedCols)}</div>`
    : '';
  const perState = s.per_state && typeof s.per_state === 'object'
    ? Object.entries(s.per_state)
    : [];
  const perStateLine = perState.length
    ? `<div class="fit-metrics"><div class="fit-metrics-title">${t('fitting.state_metrics')}</div>`
      + perState.map(([state, metric]) => {
        const r2 = typeof metric.r_squared === 'number' ? metric.r_squared.toFixed(4) : '\u2014';
        const rmse = typeof metric.rmse === 'number' ? metric.rmse.toFixed(4) : '\u2014';
        return `<div class="fit-metric"><span class="key">${state}${metric.column ? ` (${metric.column})` : ''}</span>`
          + ` R<sup>2</sup>=${r2} ${t('fitting.rmse')}=${rmse} n=${metric.n ?? '\u2014'}</div>`;
      }).join('')
      + '</div>'
    : '';
  // R² 非正时不能把 Converged 作为独立的"通过"指标并排展示
  const convergedText = r2NonPositive
    ? t('fitting.converged_not_meaningful')
    : (s.converged ? t('fitting.converged_yes') : t('fitting.converged_no'));
  document.getElementById('fitKPIs').innerHTML = `
    <div class="result-kpi"><div class="value">${s.r_squared !== null ? s.r_squared.toFixed(4) : '\u2014'}</div><div class="label">R^2</div></div>
    <div class="result-kpi${r2NonPositive ? ' muted' : ''}"><div class="value">${convergedText}</div><div class="label">Converged</div></div>
  ` + colsLine + perStateLine + (warnings.length
    ? `<div class="fit-warning">${warnings.map(w => `<div>\u26a0 ${w}</div>`).join('')}</div>`
    : '');
  document.getElementById('fitParams').innerHTML = Object.entries(s.params || {}).map(([k, v]) =>
    `<span class="fit-param"><span class="key">${k}</span> <span class="val">${typeof v === 'number' ? v.toFixed(4) : v}</span></span>`
  ).join('');

  buildFitChart(res, context ? context.agent_id : undefined);
}

function buildFitChart(res, agentId = null) {
  if (!simData) return;
  if (!hasPlotly()) {
    showPlotlyFailure('chartFit');
    return;
  }
  const df = simData.data;
  let series = df;
  if (agentId) series = series.filter(r => r.agent_id === agentId);

  const mapping = res.state_columns && typeof res.state_columns === 'object'
    ? res.state_columns
    : {};
  const stateNames = Array.isArray(res.state_names) && res.state_names.length
    ? res.state_names
    : Object.keys(mapping);
  const colors = ['#0984e3', '#e17055', '#00b894', '#6c5ce7', '#d63031', '#fdcb6e'];
  const traces = [];

  stateNames.forEach((stateName, i) => {
    const col = mapping[stateName];
    if (!col) return;
    const byTime = {};
    series.forEach(r => {
      const v = r[col];
      // 同 buildTimeSeries：null 表示"该 agent 没有这个状态"，不能当 0 参与均值
      if (v === null || v === undefined || Number.isNaN(v)) return;
      byTime[r.time] = byTime[r.time] || [];
      byTime[r.time].push(v);
    });
    // 变量名不要用 t：它会遮蔽上面的 i18n 函数 t()。
    const timeKeys = Object.keys(byTime).map(Number).sort((a, b) => a - b);
    if (!timeKeys.length) return;
    const vals = timeKeys.map(ti => byTime[ti].reduce((a, b) => a + b, 0) / byTime[ti].length);
    traces.push({
      x: timeKeys, y: vals, type: 'scatter', mode: 'markers',
      name: `${stateName}${t('fitting.data_suffix')}`,
      marker: { size: 4, color: colors[i % colors.length] }, opacity: 0.6,
    });
  });

  if (Array.isArray(res.predict_trace) && res.predict_trace.length > 0) {
    res.predict_trace.forEach((tr, i) => {
      const stateName = stateNames[i] || `state ${i + 1}`;
      traces.push({
        x: tr.t, y: tr.y, type: 'scatter', mode: 'lines',
        name: `${stateName} ${t('fitting.ode_fit')}`,
        line: { width: 2, dash: 'solid', color: colors[i % colors.length] },
      });
    });
  }

  Plotly.newPlot('chartFit', traces, {
    ...CHART_THEME, title: t('chart.fit_title'),
    xaxis: { title: t('chart.time') }, yaxis: { title: t('chart.value') },
  }, { responsive: true });
}

// ── Network ────────────────────────────────────────────────────────────────
async function buildNetwork() {
  const warn = document.getElementById('netWarning');
  if (!simData) {
    warn.textContent = t('network.warn');
    warn.style.display = 'block';
    return;
  }
  warn.textContent = '';
  warn.style.display = 'none';

  const requestRunId = simRunId;
  const res = await api(withRunId('/api/network', requestRunId));
  if (requestRunId !== simRunId) return;
  if (res.error || !res.networks) {
    document.getElementById('networkCards').innerHTML = '';
    warn.textContent = res.error || t('network.failed');
    warn.style.display = 'block';
    return;
  }

  const container = document.getElementById('networkCards');
  container.innerHTML = '';
  res.networks.forEach((net, i) => {
    const card = document.createElement('div');
    card.className = 'card';
    const header = document.createElement('div');
    header.className = 'card-header';
    const heading = document.createElement('h2');
    heading.textContent = net.name;
    header.appendChild(heading);
    const chart = document.createElement('div');
    chart.className = 'chart-container';
    chart.id = `networkChart${i}`;
    card.appendChild(header);
    card.appendChild(chart);
    container.appendChild(card);
  });

  if (!hasPlotly()) {
    warn.textContent = t('charts.plotly_failed');
    warn.style.display = 'block';
    return;
  }

  setTimeout(() => {
    res.networks.forEach((net, i) => {
      const n = net.nodes.length;
      const nodeTrace = {
        x: [], y: [], text: [], type: 'scatter', mode: 'markers+text',
        textposition: 'top center', hoverinfo: 'text',
        marker: { size: 20, color: [], line: { width: 1, color: '#fff' } },
      };
      const roleColors = { parent: '#e74c3c', adult: '#f39c12', child: '#3498db', elder: '#2ecc71' };
      net.nodes.forEach((node, j) => {
        const angle = (2 * Math.PI * j) / n - Math.PI / 2;
        nodeTrace.x.push(Math.cos(angle));
        nodeTrace.y.push(Math.sin(angle));
        nodeTrace.text.push(node.name);
        nodeTrace.marker.color.push(roleColors[node.role] || '#95a5a6');
      });
      const edgeTraces = net.edges.map(e => {
        const si = net.nodes.findIndex(nn => nn.id === e.source);
        const ti = net.nodes.findIndex(nn => nn.id === e.target);
        return si >= 0 && ti >= 0 ? {
          x: [nodeTrace.x[si], nodeTrace.x[ti]], y: [nodeTrace.y[si], nodeTrace.y[ti]],
          type: 'scatter', mode: 'lines',
          line: { width: Math.max(0.5, e.weight * 4),
            color: ['#27ae60', '#e67e22', '#e74c3c'][Math.min(2, Math.floor(e.conflict * 3))] },
          hovertext: `${t('network.trust')}: ${e.trust}, ${t('network.conflict')}: ${e.conflict}`,
        } : null;
      }).filter(Boolean);

      Plotly.newPlot('networkChart' + i, [nodeTrace, ...edgeTraces], {
        ...CHART_THEME, title: net.name,
        xaxis: { visible: false, range: [-1.3, 1.3] },
        yaxis: { visible: false, range: [-1.3, 1.3] },
        showlegend: false,
      }, { responsive: true });
    });
  }, 200);
}

// ── Utils ──────────────────────────────────────────────────────────────────
function applyStatus(state, msg) {
  const dot = document.getElementById('statusDot');
  dot.className = 'dot' + (state === 'ok' ? ' ok' : '');
  document.getElementById('statusText').textContent = msg;
}

function setStatus(state, msg, meta = {}) {
  statusInfo = {
    state,
    message: msg,
    kind: meta.kind || null,
    r2: meta.r2 ?? null,
  };
  applyStatus(state, msg);
}

function refreshStatusI18n() {
  const info = statusInfo;
  if (info.kind === 'simRunning' || info.kind === 'fitRunning') {
    applyStatus(info.state, t(info.kind === 'simRunning' ? 'status.running' : 'status.fitting'));
  } else if (info.kind === 'simDone') {
    applyStatus(info.state, t('status.simDone'));
  } else if (info.kind === 'fitDone') {
    applyStatus(info.state, t('status.fitDone', info.r2 ?? '\u2014'));
  } else if (info.state === 'ready') {
    applyStatus('ready', t('status.ready'));
  } else {
    applyStatus(info.state, info.message);
  }
}

// ── Init ───────────────────────────────────────────────────────────────────
const fitModelSelect = document.getElementById('fitModel');
if (fitModelSelect) {
  fitModelSelect.addEventListener('change', () => {
    fitModelTouched = true;
    invalidateFitResult();
    restoreStableViewStatus();
  });
}
buildFamilyConfigs();
loadParams();
refreshI18n();
setLang(currentLang);
