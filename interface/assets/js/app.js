const INITIAL_CHANNELS = [
    { id: 'SEARCH', canal: 'Search Ads', funil: 'conversão', min: 6, max: 26, receita: 3.20, saturacao: 0.46, risco: 0.34 },
    { id: 'RETARGET', canal: 'Retargeting', funil: 'conversão', min: 4, max: 18, receita: 3.65, saturacao: 0.55, risco: 0.28 },
    { id: 'CRM', canal: 'CRM e e-mail', funil: 'retenção', min: 3, max: 16, receita: 4.10, saturacao: 0.38, risco: 0.16 },
    { id: 'SEO', canal: 'Conteúdo SEO', funil: 'aquisição', min: 5, max: 24, receita: 2.55, saturacao: 0.22, risco: 0.18 },
    { id: 'INFLU_MICRO', canal: 'Influenciadores micro', funil: 'aquisição', min: 2, max: 14, receita: 2.85, saturacao: 0.48, risco: 0.45 },
    { id: 'TIKTOK', canal: 'TikTok Ads', funil: 'aquisição', min: 3, max: 20, receita: 3.05, saturacao: 0.62, risco: 0.52 },
    { id: 'LINKEDIN', canal: 'LinkedIn Ads', funil: 'aquisição', min: 2, max: 15, receita: 2.70, saturacao: 0.42, risco: 0.40 },
    { id: 'REFERRAL', canal: 'Programa de indicação', funil: 'retenção', min: 4, max: 17, receita: 3.75, saturacao: 0.30, risco: 0.20 },
    { id: 'YOUTUBE', canal: 'YouTube Shorts', funil: 'aquisição', min: 2, max: 16, receita: 2.60, saturacao: 0.50, risco: 0.39 },
    { id: 'MARKETPLACE', canal: 'Promoções marketplace', funil: 'conversão', min: 5, max: 22, receita: 3.35, saturacao: 0.58, risco: 0.36 },
    { id: 'WEBINAR', canal: 'Webinars B2B', funil: 'nutrição', min: 1, max: 12, receita: 3.15, saturacao: 0.34, risco: 0.27 },
    { id: 'CRO', canal: 'Otimização de conversão', funil: 'conversão', min: 4, max: 18, receita: 4.35, saturacao: 0.24, risco: 0.14 },
];

const FUNNEL_OPTIONS = ['aquisição', 'conversão', 'nutrição', 'retenção'];
const API_BASE_URL = window.location.protocol === 'file:' ? 'http://127.0.0.1:8000' : '';

const state = {
    channels: structuredClone(INITIAL_CHANNELS),
    lastResult: null,
    isLoading: false,
};

const currency = new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
});

function byId(id) {
    return document.getElementById(id);
}

function formatMil(value) {
    return `R$ ${currency.format(Number(value || 0))} mil`;
}

function setStatus(message, type = 'info') {
    const box = byId('statusBox');
    box.textContent = message;
    box.classList.remove('error', 'success');
    if (type !== 'info') {
        box.classList.add(type);
    }
}

function setLoading(isLoading) {
    state.isLoading = isLoading;
    ['calculateButton', 'chartsButton', 'exportButton'].forEach((id) => {
        byId(id).disabled = isLoading;
    });
}

function renderChannels() {
    const body = byId('channelsBody');
    body.innerHTML = '';

    state.channels.forEach((channel, index) => {
        const row = document.createElement('tr');
        row.innerHTML = `
            <td><input class="channel-name" data-field="canal" data-index="${index}" value="${channel.canal}"></td>
            <td>
                <select data-field="funil" data-index="${index}">
                    ${FUNNEL_OPTIONS.map((option) => `<option value="${option}" ${option === channel.funil ? 'selected' : ''}>${option}</option>`).join('')}
                </select>
            </td>
            <td><input data-field="min" data-index="${index}" type="number" min="0" step="1" value="${channel.min}"></td>
            <td><input data-field="max" data-index="${index}" type="number" min="0" step="1" value="${channel.max}"></td>
            <td><input data-field="receita" data-index="${index}" type="number" min="0.01" step="0.05" value="${channel.receita}"></td>
            <td><input data-field="saturacao" data-index="${index}" type="number" min="0" max="1" step="0.01" value="${channel.saturacao}"></td>
            <td><input data-field="risco" data-index="${index}" type="number" min="0" max="1" step="0.01" value="${channel.risco}"></td>
            <td><button class="icon-button" data-remove="${index}" type="button" aria-label="Remover canal">x</button></td>
        `;
        body.appendChild(row);
    });
}

function syncChannelsFromTable() {
    document.querySelectorAll('[data-field]').forEach((field) => {
        const index = Number(field.dataset.index);
        const key = field.dataset.field;
        const rawValue = field.value;

        if (key === 'canal' || key === 'funil') {
            state.channels[index][key] = rawValue.trim();
            return;
        }

        state.channels[index][key] = Number(rawValue);
    });
}

function readConfig() {
    return {
        budget: Number(byId('budgetInput').value),
        population: Number(byId('populationInput').value),
        generations: Number(byId('generationsInput').value),
        offspring: Number(byId('offspringInput').value),
        crossover: Number(byId('crossoverInput').value),
        mutation: Number(byId('mutationInput').value),
        riskWeight: Number(byId('riskWeightInput').value),
        seed: Number(byId('seedInput').value),
    };
}

function validateInputs(channels, config) {
    if (!Number.isFinite(config.budget) || config.budget <= 0) {
        throw new Error('Orçamento precisa ser maior que zero.');
    }

    if (channels.length < 2) {
        throw new Error('Use pelo menos dois canais.');
    }

    if (config.population < 20 || config.generations < 5 || config.offspring < 20) {
        throw new Error('População, gerações e descendentes estão baixos demais.');
    }

    if (config.crossover < 0 || config.crossover > 1 || config.mutation < 0 || config.mutation > 1) {
        throw new Error('Crossover e mutação precisam estar entre 0 e 1.');
    }

    channels.forEach((channel, index) => {
        if (!channel.canal) {
            throw new Error(`Canal ${index + 1} está sem nome.`);
        }

        if (!Number.isFinite(channel.min) || !Number.isFinite(channel.max) || channel.min < 0 || channel.max < channel.min) {
            throw new Error(`Limites inválidos em ${channel.canal}.`);
        }

        if (!Number.isFinite(channel.receita) || channel.receita <= 0) {
            throw new Error(`Receita inválida em ${channel.canal}.`);
        }

        if (channel.saturacao < 0 || channel.saturacao > 1 || channel.risco < 0 || channel.risco > 1) {
            throw new Error(`Saturação e risco precisam ficar entre 0 e 1 em ${channel.canal}.`);
        }
    });

    const minimum = channels.reduce((total, channel) => total + Math.round(channel.min), 0);
    const maximum = channels.reduce((total, channel) => total + Math.round(channel.max), 0);

    if (config.budget < minimum) {
        throw new Error(`Orçamento menor que o mínimo viável de R$ ${minimum} mil.`);
    }

    if (config.budget > maximum) {
        throw new Error(`Orçamento maior que o máximo viável de R$ ${maximum} mil.`);
    }
}

function buildPayload() {
    syncChannelsFromTable();
    const config = readConfig();
    validateInputs(state.channels, config);

    return {
        canais: state.channels,
        config,
    };
}

function parseApiError(errorBody) {
    if (typeof errorBody?.detail === 'string') {
        return errorBody.detail;
    }

    if (Array.isArray(errorBody?.detail)) {
        return errorBody.detail
            .map((item) => `${item.loc?.join('.') || 'campo'}: ${item.msg}`)
            .join(' | ');
    }

    return 'Não foi possível concluir o cálculo.';
}

async function requestOptimization() {
    const payload = buildPayload();
    const response = await fetch(`${API_BASE_URL}/api/otimizar`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
        },
        body: JSON.stringify(payload),
    });

    const body = await response.json().catch(() => ({}));
    if (!response.ok) {
        throw new Error(parseApiError(body));
    }

    return {
        ...body,
        channels: structuredClone(state.channels),
        config: payload.config,
    };
}

function renderMetrics(result) {
    byId('metricRevenue').textContent = formatMil(result.metricas.receita);
    byId('metricProfit').textContent = formatMil(result.metricas.lucro);
    byId('metricRisk').textContent = formatMil(result.metricas.risco);
    byId('metricSynergy').textContent = formatMil(result.metricas.sinergia);
    byId('scorePill').textContent = `Score ${currency.format(result.metricas.score)}`;
    byId('frontierPill').textContent = `${result.fronteira.length} planos`;
}

function renderPlan(result) {
    const body = byId('resultBody');
    body.innerHTML = '';

    result.plano.forEach((row) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${row.canal}</td>
            <td>${formatMil(row.investimento)}</td>
            <td>${formatMil(row.receita)}</td>
            <td>${formatMil(row.lucroBruto)}</td>
            <td>${formatMil(row.risco)}</td>
        `;
        body.appendChild(tr);
    });
}

async function calculate() {
    if (state.isLoading) {
        return null;
    }

    try {
        setLoading(true);
        setStatus('Calculando no backend Python...');
        const result = await requestOptimization();
        state.lastResult = result;
        renderMetrics(result);
        renderPlan(result);
        setStatus('Cálculo finalizado com sucesso.', 'success');
        return result;
    } catch (error) {
        setStatus(error.message, 'error');
        return null;
    } finally {
        setLoading(false);
    }
}

function ensurePlotly() {
    if (!window.Plotly) {
        setStatus('Plotly não carregou. Verifique o arquivo assets/js/plotly.min.js.', 'error');
        return false;
    }
    return true;
}

async function renderCharts() {
    const result = state.lastResult || await calculate();
    if (!result || !ensurePlotly()) {
        return;
    }

    const planRows = [...result.plano].reverse();
    Plotly.newPlot('allocationChart', [{
        type: 'bar',
        orientation: 'h',
        x: planRows.map((row) => row.investimento),
        y: planRows.map((row) => row.canal),
        marker: {
            color: planRows.map((row) => row.lucroBruto),
            colorscale: 'Viridis',
        },
        hovertemplate: '<b>%{y}</b><br>Investimento: R$ %{x:.0f} mil<extra></extra>',
    }], {
        title: 'Alocação recomendada',
        margin: { l: 150, r: 20, t: 48, b: 40 },
        xaxis: { title: 'Investimento (R$ mil)' },
        template: 'plotly_white',
    }, { responsive: true, displaylogo: false });

    Plotly.newPlot('frontierChart', [{
        type: 'scatter',
        mode: 'markers',
        x: result.fronteira.map((item) => item.risco_ponderado_mil),
        y: result.fronteira.map((item) => item.lucro_estimado_mil),
        text: result.fronteira.map((item) => `Score ${currency.format(item.score_decisao)}`),
        marker: {
            size: result.fronteira.map((item) => Math.max(9, Math.min(24, item.receita_estimada_mil / 14))),
            color: result.fronteira.map((item) => item.score_decisao),
            colorscale: 'Portland',
            showscale: true,
        },
        hovertemplate: 'Risco: R$ %{x:.1f} mil<br>Lucro: R$ %{y:.1f} mil<br>%{text}<extra></extra>',
    }, {
        type: 'scatter',
        mode: 'markers',
        x: [result.metricas.risco],
        y: [result.metricas.lucro],
        marker: { size: 16, color: '#be123c', symbol: 'diamond' },
        name: 'Plano escolhido',
        hovertemplate: 'Plano escolhido<br>Risco: R$ %{x:.1f} mil<br>Lucro: R$ %{y:.1f} mil<extra></extra>',
    }], {
        title: 'Lucro versus risco',
        margin: { l: 58, r: 24, t: 48, b: 48 },
        xaxis: { title: 'Risco ponderado (R$ mil)' },
        yaxis: { title: 'Lucro estimado (R$ mil)' },
        template: 'plotly_white',
    }, { responsive: true, displaylogo: false });

    Plotly.newPlot('convergenceChart', [{
        type: 'scatter',
        mode: 'lines',
        name: 'Melhor lucro',
        x: result.historico.map((item) => item.geracao),
        y: result.historico.map((item) => item.lucro_max_mil),
        line: { color: '#0f766e', width: 3 },
    }, {
        type: 'scatter',
        mode: 'lines',
        name: 'Lucro médio',
        x: result.historico.map((item) => item.geracao),
        y: result.historico.map((item) => item.lucro_medio_mil),
        line: { color: '#b45309', width: 2, dash: 'dot' },
    }], {
        title: 'Convergência',
        margin: { l: 58, r: 24, t: 48, b: 48 },
        xaxis: { title: 'Geração' },
        yaxis: { title: 'Lucro estimado (R$ mil)' },
        template: 'plotly_white',
    }, { responsive: true, displaylogo: false });

    setStatus('Gráficos gerados.', 'success');
}

function addChannel() {
    syncChannelsFromTable();
    const index = state.channels.length + 1;
    state.channels.push({
        id: `CUSTOM_${index}`,
        canal: `Novo canal ${index}`,
        funil: 'aquisição',
        min: 1,
        max: 10,
        receita: 2.5,
        saturacao: 0.35,
        risco: 0.30,
    });
    renderChannels();
    state.lastResult = null;
}

function clearCharts() {
    ['allocationChart', 'frontierChart', 'convergenceChart'].forEach((id) => {
        const element = byId(id);
        if (window.Plotly && element.data) {
            Plotly.purge(element);
        }
        element.innerHTML = '';
    });
}

function resetInterface() {
    state.channels = structuredClone(INITIAL_CHANNELS);
    state.lastResult = null;
    byId('budgetInput').value = 100;
    byId('populationInput').value = 140;
    byId('generationsInput').value = 110;
    byId('offspringInput').value = 140;
    byId('crossoverInput').value = 0.68;
    byId('mutationInput').value = 0.32;
    byId('riskWeightInput').value = 0.55;
    byId('seedInput').value = 42;
    renderChannels();
    byId('resultBody').innerHTML = '';
    clearCharts();
    renderMetrics({
        metricas: { receita: 0, lucro: 0, risco: 0, sinergia: 0, score: 0 },
        fronteira: [],
    });
    setStatus('Valores restaurados.');
}

async function exportCsv() {
    const result = state.lastResult || await calculate();
    if (!result) {
        return;
    }

    const rows = [
        ['canal', 'funil', 'investimento_mil', 'receita_estimada_mil', 'lucro_bruto_mil', 'risco_ponderado_mil'],
        ...result.plano.map((row) => [
            row.canal,
            row.funil,
            row.investimento,
            Number(row.receita).toFixed(2),
            Number(row.lucroBruto).toFixed(2),
            Number(row.risco).toFixed(2),
        ]),
    ];
    const csv = rows.map((row) => row.map((value) => `"${String(value).replaceAll('"', '""')}"`).join(',')).join('\n');
    const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8' }));
    const link = document.createElement('a');
    link.href = url;
    link.download = 'plano_marketing_otimizado_interativo.csv';
    link.click();
    URL.revokeObjectURL(url);
}

function invalidateResult() {
    state.lastResult = null;
}

function attachEvents() {
    byId('calculateButton').addEventListener('click', calculate);
    byId('chartsButton').addEventListener('click', renderCharts);
    byId('addChannelButton').addEventListener('click', addChannel);
    byId('resetButton').addEventListener('click', resetInterface);
    byId('exportButton').addEventListener('click', exportCsv);

    [
        'budgetInput',
        'populationInput',
        'generationsInput',
        'offspringInput',
        'crossoverInput',
        'mutationInput',
        'riskWeightInput',
        'seedInput',
    ].forEach((id) => {
        byId(id).addEventListener('input', invalidateResult);
    });

    byId('channelsBody').addEventListener('input', invalidateResult);

    byId('channelsBody').addEventListener('click', (event) => {
        const removeIndex = event.target.dataset.remove;
        if (removeIndex === undefined) {
            return;
        }

        syncChannelsFromTable();
        state.channels.splice(Number(removeIndex), 1);
        state.lastResult = null;
        renderChannels();
    });
}

document.addEventListener('DOMContentLoaded', () => {
    renderChannels();
    attachEvents();
});
