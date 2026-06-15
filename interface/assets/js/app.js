const INITIAL_CHANNELS = [
    { id: 'SEARCH', canal: 'Search Ads', funil: 'conversao', min: 6, max: 26, receita: 3.20, saturacao: 0.46, risco: 0.34 },
    { id: 'RETARGET', canal: 'Retargeting', funil: 'conversao', min: 4, max: 18, receita: 3.65, saturacao: 0.55, risco: 0.28 },
    { id: 'CRM', canal: 'CRM e email', funil: 'retencao', min: 3, max: 16, receita: 4.10, saturacao: 0.38, risco: 0.16 },
    { id: 'SEO', canal: 'Conteudo SEO', funil: 'aquisicao', min: 5, max: 24, receita: 2.55, saturacao: 0.22, risco: 0.18 },
    { id: 'INFLU_MICRO', canal: 'Influenciadores micro', funil: 'aquisicao', min: 2, max: 14, receita: 2.85, saturacao: 0.48, risco: 0.45 },
    { id: 'TIKTOK', canal: 'TikTok Ads', funil: 'aquisicao', min: 3, max: 20, receita: 3.05, saturacao: 0.62, risco: 0.52 },
    { id: 'LINKEDIN', canal: 'LinkedIn Ads', funil: 'aquisicao', min: 2, max: 15, receita: 2.70, saturacao: 0.42, risco: 0.40 },
    { id: 'REFERRAL', canal: 'Programa de indicacao', funil: 'retencao', min: 4, max: 17, receita: 3.75, saturacao: 0.30, risco: 0.20 },
    { id: 'YOUTUBE', canal: 'YouTube Shorts', funil: 'aquisicao', min: 2, max: 16, receita: 2.60, saturacao: 0.50, risco: 0.39 },
    { id: 'MARKETPLACE', canal: 'Promocoes marketplace', funil: 'conversao', min: 5, max: 22, receita: 3.35, saturacao: 0.58, risco: 0.36 },
    { id: 'WEBINAR', canal: 'Webinars B2B', funil: 'nutricao', min: 1, max: 12, receita: 3.15, saturacao: 0.34, risco: 0.27 },
    { id: 'CRO', canal: 'Otimizacao de conversao', funil: 'conversao', min: 4, max: 18, receita: 4.35, saturacao: 0.24, risco: 0.14 },
];

const SYNERGIES = new Map([
    ['SEARCH|SEO', 0.08],
    ['RETARGET|CRM', 0.07],
    ['REFERRAL|CRO', 0.09],
    ['LINKEDIN|WEBINAR', 0.10],
    ['YOUTUBE|TIKTOK', 0.06],
    ['MARKETPLACE|SEARCH', 0.05],
]);

const FUNNEL_OPTIONS = ['aquisicao', 'conversao', 'nutricao', 'retencao'];

const state = {
    channels: structuredClone(INITIAL_CHANNELS),
    lastResult: null,
};

const currency = new Intl.NumberFormat('pt-BR', {
    minimumFractionDigits: 1,
    maximumFractionDigits: 1,
});

function byId(id) {
    return document.getElementById(id);
}

function createRng(seed) {
    let value = Math.abs(Math.trunc(seed)) % 2147483647;
    if (value === 0) {
        value = 1;
    }

    return () => {
        value = (value * 48271) % 2147483647;
        return value / 2147483647;
    };
}

function randomInt(rng, min, max) {
    return Math.floor(rng() * (max - min + 1)) + min;
}

function pick(rng, items) {
    return items[Math.floor(rng() * items.length)];
}

function formatMil(value) {
    return `R$ ${currency.format(value)} mil`;
}

function setStatus(message, type = 'info') {
    const box = byId('statusBox');
    box.textContent = message;
    box.classList.remove('error', 'success');
    if (type !== 'info') {
        box.classList.add(type);
    }
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
        throw new Error('Orcamento precisa ser maior que zero.');
    }

    if (channels.length < 2) {
        throw new Error('Use pelo menos dois canais.');
    }

    if (config.population < 20 || config.generations < 5 || config.offspring < 20) {
        throw new Error('Populacao, geracoes e descendentes estao baixos demais.');
    }

    if (config.crossover < 0 || config.crossover > 1 || config.mutation < 0 || config.mutation > 1) {
        throw new Error('Crossover e mutacao precisam estar entre 0 e 1.');
    }

    channels.forEach((channel, index) => {
        if (!channel.canal) {
            throw new Error(`Canal ${index + 1} esta sem nome.`);
        }

        if (!Number.isFinite(channel.min) || !Number.isFinite(channel.max) || channel.min < 0 || channel.max < channel.min) {
            throw new Error(`Limites invalidos em ${channel.canal}.`);
        }

        if (!Number.isFinite(channel.receita) || channel.receita <= 0) {
            throw new Error(`Receita invalida em ${channel.canal}.`);
        }

        if (channel.saturacao < 0 || channel.saturacao > 1 || channel.risco < 0 || channel.risco > 1) {
            throw new Error(`Saturacao e risco precisam ficar entre 0 e 1 em ${channel.canal}.`);
        }
    });

    const minimum = channels.reduce((total, channel) => total + Math.round(channel.min), 0);
    const maximum = channels.reduce((total, channel) => total + Math.round(channel.max), 0);

    if (config.budget < minimum) {
        throw new Error(`Orcamento menor que o minimo viavel de R$ ${minimum} mil.`);
    }

    if (config.budget > maximum) {
        throw new Error(`Orcamento maior que o maximo viavel de R$ ${maximum} mil.`);
    }
}

function repairAllocation(allocation, channels, budget, rng) {
    const repaired = allocation.map((value, index) => {
        const min = Math.round(channels[index].min);
        const max = Math.round(channels[index].max);
        return Math.max(min, Math.min(max, Math.round(value)));
    });

    let difference = Math.round(budget) - repaired.reduce((total, value) => total + value, 0);
    let attempts = 0;
    const limit = Math.max(1000, channels.length * Math.abs(difference) * 20);

    while (difference !== 0 && attempts < limit) {
        attempts += 1;

        if (difference > 0) {
            const candidates = repaired
                .map((value, index) => ({ value, index }))
                .filter((item) => item.value < Math.round(channels[item.index].max));
            const selected = pick(rng, candidates);
            repaired[selected.index] += 1;
            difference -= 1;
        } else {
            const candidates = repaired
                .map((value, index) => ({ value, index }))
                .filter((item) => item.value > Math.round(channels[item.index].min));
            const selected = pick(rng, candidates);
            repaired[selected.index] -= 1;
            difference += 1;
        }
    }

    if (repaired.reduce((total, value) => total + value, 0) !== Math.round(budget)) {
        throw new Error('Nao foi possivel reparar a alocacao para o orcamento definido.');
    }

    return repaired;
}

function createIndividual(channels, budget, rng) {
    const allocation = channels.map((channel) => Math.round(channel.min));
    let remaining = Math.round(budget) - allocation.reduce((total, value) => total + value, 0);

    while (remaining > 0) {
        const candidates = allocation
            .map((value, index) => ({ value, index }))
            .filter((item) => item.value < Math.round(channels[item.index].max));
        const selected = pick(rng, candidates);
        const room = Math.round(channels[selected.index].max) - allocation[selected.index];
        const increment = randomInt(rng, 1, Math.min(remaining, room));
        allocation[selected.index] += increment;
        remaining -= increment;
    }

    return allocation;
}

function calculateChannelRevenue(investment, channel) {
    const usage = channel.max > 0 ? investment / channel.max : 0;
    const saturationFactor = Math.max(0.42, 1 - channel.saturacao * usage ** 1.35);
    return investment * channel.receita * saturationFactor;
}

function calculateSynergy(allocation, channels, revenues) {
    const indexById = new Map(channels.map((channel, index) => [channel.id, index]));
    let synergy = 0;

    SYNERGIES.forEach((percent, pair) => {
        const [first, second] = pair.split('|');
        if (!indexById.has(first) || !indexById.has(second)) {
            return;
        }

        const firstIndex = indexById.get(first);
        const secondIndex = indexById.get(second);
        if (allocation[firstIndex] > 0 && allocation[secondIndex] > 0) {
            synergy += Math.min(revenues[firstIndex], revenues[secondIndex]) * percent;
        }
    });

    return synergy;
}

function evaluateAllocation(allocation, channels, riskWeight) {
    const revenues = allocation.map((investment, index) => calculateChannelRevenue(investment, channels[index]));
    const investment = allocation.reduce((total, value) => total + value, 0);
    const synergy = calculateSynergy(allocation, channels, revenues);
    const revenue = revenues.reduce((total, value) => total + value, 0) + synergy;
    const risk = allocation.reduce((total, value, index) => total + value * channels[index].risco, 0);
    const profit = revenue - investment;
    const score = profit - riskWeight * risk;

    return { allocation, revenues, investment, synergy, revenue, risk, profit, score };
}

function crossover(parentA, parentB, channels, budget, rng) {
    if (parentA.length < 3) {
        return [parentA.slice(), parentB.slice()];
    }

    const first = randomInt(rng, 1, parentA.length - 2);
    const second = randomInt(rng, first + 1, parentA.length - 1);
    const childA = parentA.slice(0, first).concat(parentB.slice(first, second), parentA.slice(second));
    const childB = parentB.slice(0, first).concat(parentA.slice(first, second), parentB.slice(second));

    return [
        repairAllocation(childA, channels, budget, rng),
        repairAllocation(childB, channels, budget, rng),
    ];
}

function mutate(individual, channels, budget, rng) {
    const mutated = individual.slice();
    const rounds = randomInt(rng, 1, 4);

    for (let round = 0; round < rounds; round += 1) {
        const origins = mutated
            .map((value, index) => ({ value, index }))
            .filter((item) => item.value > Math.round(channels[item.index].min));
        const destinations = mutated
            .map((value, index) => ({ value, index }))
            .filter((item) => item.value < Math.round(channels[item.index].max));

        if (origins.length === 0 || destinations.length === 0) {
            break;
        }

        const origin = pick(rng, origins);
        const destination = pick(rng, destinations.filter((item) => item.index !== origin.index));
        if (!destination) {
            break;
        }

        const limit = Math.min(
            origin.value - Math.round(channels[origin.index].min),
            Math.round(channels[destination.index].max) - destination.value,
            8,
        );

        if (limit <= 0) {
            continue;
        }

        const amount = randomInt(rng, 1, limit);
        mutated[origin.index] -= amount;
        mutated[destination.index] += amount;
    }

    return repairAllocation(mutated, channels, budget, rng);
}

function tournament(population, rng) {
    const sample = [pick(rng, population), pick(rng, population), pick(rng, population)];
    return sample.sort((a, b) => b.score - a.score)[0].allocation;
}

function paretoFront(population) {
    return population.filter((candidate) => {
        return !population.some((other) => {
            const betterOrEqualProfit = other.profit >= candidate.profit;
            const lowerOrEqualRisk = other.risk <= candidate.risk;
            const strictlyBetter = other.profit > candidate.profit || other.risk < candidate.risk;
            return betterOrEqualProfit && lowerOrEqualRisk && strictlyBetter;
        });
    }).sort((a, b) => b.score - a.score);
}

function runGeneticAlgorithm(channels, config) {
    const rng = createRng(config.seed);
    let population = Array.from({ length: Math.round(config.population) }, () => {
        const allocation = createIndividual(channels, config.budget, rng);
        return evaluateAllocation(allocation, channels, config.riskWeight);
    });
    const history = [];

    for (let generation = 0; generation <= Math.round(config.generations); generation += 1) {
        population.sort((a, b) => b.score - a.score);
        history.push({
            generation,
            bestScore: population[0].score,
            averageScore: population.reduce((total, item) => total + item.score, 0) / population.length,
        });

        if (generation === Math.round(config.generations)) {
            break;
        }

        const next = population.slice(0, Math.min(4, population.length));
        while (next.length < Math.round(config.population)) {
            const parentA = tournament(population, rng);
            const parentB = tournament(population, rng);
            let children;

            if (rng() < config.crossover) {
                children = crossover(parentA, parentB, channels, config.budget, rng);
            } else {
                children = [parentA.slice(), parentB.slice()];
            }

            children.forEach((child) => {
                const allocation = rng() < config.mutation
                    ? mutate(child, channels, config.budget, rng)
                    : repairAllocation(child, channels, config.budget, rng);
                next.push(evaluateAllocation(allocation, channels, config.riskWeight));
            });
        }

        population = next.slice(0, Math.round(config.population));
    }

    population.sort((a, b) => b.score - a.score);
    return {
        recommended: population[0],
        population,
        frontier: paretoFront(population),
        history,
    };
}

function buildPlanRows(result, channels) {
    return result.recommended.allocation.map((investment, index) => {
        const revenue = result.recommended.revenues[index];
        return {
            channel: channels[index],
            investment,
            revenue,
            grossProfit: revenue - investment,
            risk: investment * channels[index].risco,
        };
    }).sort((a, b) => b.investment - a.investment);
}

function renderMetrics(result) {
    byId('metricRevenue').textContent = formatMil(result.recommended.revenue);
    byId('metricProfit').textContent = formatMil(result.recommended.profit);
    byId('metricRisk').textContent = formatMil(result.recommended.risk);
    byId('metricSynergy').textContent = formatMil(result.recommended.synergy);
    byId('scorePill').textContent = `Score ${currency.format(result.recommended.score)}`;
    byId('frontierPill').textContent = `${result.frontier.length} planos`;
}

function renderPlan(result, channels) {
    const body = byId('resultBody');
    body.innerHTML = '';

    buildPlanRows(result, channels).forEach((row) => {
        const tr = document.createElement('tr');
        tr.innerHTML = `
            <td>${row.channel.canal}</td>
            <td>${formatMil(row.investment)}</td>
            <td>${formatMil(row.revenue)}</td>
            <td>${formatMil(row.grossProfit)}</td>
            <td>${formatMil(row.risk)}</td>
        `;
        body.appendChild(tr);
    });
}

function calculate() {
    try {
        syncChannelsFromTable();
        const config = readConfig();
        validateInputs(state.channels, config);
        const result = runGeneticAlgorithm(state.channels, config);
        state.lastResult = { ...result, channels: structuredClone(state.channels), config };
        renderMetrics(state.lastResult);
        renderPlan(state.lastResult, state.lastResult.channels);
        setStatus('Calculo finalizado com sucesso.', 'success');
        return state.lastResult;
    } catch (error) {
        setStatus(error.message, 'error');
        return null;
    }
}

function renderCharts() {
    const result = state.lastResult || calculate();
    if (!result) {
        return;
    }

    if (!window.Plotly) {
        setStatus('Plotly nao carregou. Verifique o arquivo assets/js/plotly.min.js.', 'error');
        return;
    }

    const planRows = buildPlanRows(result, result.channels).reverse();
    Plotly.newPlot('allocationChart', [{
        type: 'bar',
        orientation: 'h',
        x: planRows.map((row) => row.investment),
        y: planRows.map((row) => row.channel.canal),
        marker: {
            color: planRows.map((row) => row.grossProfit),
            colorscale: 'Viridis',
        },
        hovertemplate: '<b>%{y}</b><br>Investimento: R$ %{x:.0f} mil<extra></extra>',
    }], {
        title: 'Alocacao recomendada',
        margin: { l: 150, r: 20, t: 48, b: 40 },
        xaxis: { title: 'Investimento (R$ mil)' },
        template: 'plotly_white',
    }, { responsive: true, displaylogo: false });

    Plotly.newPlot('frontierChart', [{
        type: 'scatter',
        mode: 'markers',
        x: result.frontier.map((item) => item.risk),
        y: result.frontier.map((item) => item.profit),
        text: result.frontier.map((item) => `Score ${currency.format(item.score)}`),
        marker: {
            size: result.frontier.map((item) => Math.max(9, Math.min(24, item.revenue / 14))),
            color: result.frontier.map((item) => item.score),
            colorscale: 'Portland',
            showscale: true,
        },
        hovertemplate: 'Risco: R$ %{x:.1f} mil<br>Lucro: R$ %{y:.1f} mil<br>%{text}<extra></extra>',
    }, {
        type: 'scatter',
        mode: 'markers',
        x: [result.recommended.risk],
        y: [result.recommended.profit],
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
        name: 'Melhor score',
        x: result.history.map((item) => item.generation),
        y: result.history.map((item) => item.bestScore),
        line: { color: '#0f766e', width: 3 },
    }, {
        type: 'scatter',
        mode: 'lines',
        name: 'Score medio',
        x: result.history.map((item) => item.generation),
        y: result.history.map((item) => item.averageScore),
        line: { color: '#b45309', width: 2, dash: 'dot' },
    }], {
        title: 'Convergencia',
        margin: { l: 58, r: 24, t: 48, b: 48 },
        xaxis: { title: 'Geracao' },
        yaxis: { title: 'Score' },
        template: 'plotly_white',
    }, { responsive: true, displaylogo: false });

    setStatus('Graficos gerados.', 'success');
}

function addChannel() {
    syncChannelsFromTable();
    const index = state.channels.length + 1;
    state.channels.push({
        id: `CUSTOM_${index}`,
        canal: `Novo canal ${index}`,
        funil: 'aquisicao',
        min: 1,
        max: 10,
        receita: 2.5,
        saturacao: 0.35,
        risco: 0.30,
    });
    renderChannels();
    state.lastResult = null;
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
    ['allocationChart', 'frontierChart', 'convergenceChart'].forEach((id) => byId(id).innerHTML = '');
    renderMetrics({
        recommended: { revenue: 0, profit: 0, risk: 0, synergy: 0, score: 0 },
        frontier: [],
    });
    setStatus('Valores restaurados.');
}

function exportCsv() {
    const result = state.lastResult || calculate();
    if (!result) {
        return;
    }

    const rows = [
        ['canal', 'funil', 'investimento_mil', 'receita_estimada_mil', 'lucro_bruto_mil', 'risco_ponderado_mil'],
        ...buildPlanRows(result, result.channels).map((row) => [
            row.channel.canal,
            row.channel.funil,
            row.investment,
            row.revenue.toFixed(2),
            row.grossProfit.toFixed(2),
            row.risk.toFixed(2),
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
        byId(id).addEventListener('input', () => {
            state.lastResult = null;
        });
    });

    byId('channelsBody').addEventListener('input', () => {
        state.lastResult = null;
    });

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
    calculate();
});
