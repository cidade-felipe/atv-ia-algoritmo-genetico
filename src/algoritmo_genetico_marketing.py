from __future__ import annotations

import json
import random
from dataclasses import dataclass
from html import escape
from pathlib import Path
from statistics import mean
from typing import Sequence

import pandas as pd
from deap import algorithms, base, creator, tools

try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.offline import get_plotlyjs
    from plotly.utils import PlotlyJSONEncoder
except ImportError:  # pragma: no cover - usado apenas sem dependencia opcional
    px = None
    go = None
    get_plotlyjs = None
    PlotlyJSONEncoder = None


COLUNAS_OBRIGATORIAS = {
    'id',
    'canal',
    'categoria',
    'funil',
    'investimento_min_mil',
    'investimento_max_mil',
    'receita_por_mil',
    'saturacao',
    'risco',
}

SINERGIAS = {
    ('SEARCH', 'SEO'): 0.08,
    ('RETARGET', 'CRM'): 0.07,
    ('REFERRAL', 'CRO'): 0.09,
    ('LINKEDIN', 'WEBINAR'): 0.10,
    ('YOUTUBE', 'TIKTOK'): 0.06,
    ('MARKETPLACE', 'SEARCH'): 0.05,
}

RELATORIOS_CSS = """
:root {
    color-scheme: light;
    --background: #f5f7fb;
    --surface: #ffffff;
    --text: #1f2937;
    --muted: #64748b;
    --border: #d9e2ec;
    --accent: #2563eb;
}

* {
    box-sizing: border-box;
}

body {
    margin: 0;
    min-height: 100vh;
    background: var(--background);
    color: var(--text);
    font-family: Arial, Helvetica, sans-serif;
}

.report-shell {
    width: min(1180px, calc(100% - 32px));
    margin: 0 auto;
    padding: 32px 0;
}

.report-header {
    margin-bottom: 20px;
}

.eyebrow {
    margin: 0 0 8px;
    color: var(--accent);
    font-size: 0.78rem;
    font-weight: 700;
    letter-spacing: 0.08em;
    text-transform: uppercase;
}

h1 {
    margin: 0;
    font-size: clamp(1.8rem, 3vw, 2.8rem);
    line-height: 1.1;
}

.report-description {
    max-width: 760px;
    margin: 12px 0 0;
    color: var(--muted);
    line-height: 1.55;
}

.chart-panel {
    min-height: 640px;
    padding: 16px;
    border: 1px solid var(--border);
    border-radius: 8px;
    background: var(--surface);
    box-shadow: 0 18px 45px rgb(15 23 42 / 8%);
}

.chart {
    width: 100%;
    min-height: 600px;
}

@media (max-width: 720px) {
    .report-shell {
        width: min(100% - 20px, 1180px);
        padding: 20px 0;
    }

    .chart-panel {
        min-height: 520px;
        padding: 8px;
    }

    .chart {
        min-height: 500px;
    }
}
""".strip()


@dataclass(frozen=True)
class ConfigMarketingAG:
    orcamento_mil: int = 100
    tamanho_populacao: int = 140
    geracoes: int = 110
    descendentes_por_geracao: int = 140
    taxa_crossover: float = 0.68
    taxa_mutacao: float = 0.32
    peso_risco_decisao: float = 0.55
    semente: int = 42


@dataclass(frozen=True)
class MetricasPlano:
    investimento_total_mil: float
    receita_estimada_mil: float
    lucro_estimado_mil: float
    risco_ponderado_mil: float
    sinergia_mil: float


@dataclass(frozen=True)
class ResultadoMarketingAG:
    plano_recomendado: tuple[int, ...]
    metricas: MetricasPlano
    historico: pd.DataFrame
    fronteira_pareto: pd.DataFrame
    plano_detalhado: pd.DataFrame
    config: ConfigMarketingAG


def caminho_raiz_projeto() -> Path:
    return Path(__file__).resolve().parents[1]


def carregar_canais(caminho_csv: str | Path) -> pd.DataFrame:
    caminho = Path(caminho_csv)
    if not caminho.exists():
        raise FileNotFoundError(f'Arquivo de canais nao encontrado: {caminho}')

    canais = pd.read_csv(caminho)
    validar_canais(canais)

    canais = canais.copy()
    canais['id'] = canais['id'].astype(str)
    canais['canal'] = canais['canal'].astype(str)
    canais['categoria'] = canais['categoria'].astype(str)
    canais['funil'] = canais['funil'].astype(str)

    colunas_numericas = [
        'investimento_min_mil',
        'investimento_max_mil',
        'receita_por_mil',
        'saturacao',
        'risco',
    ]
    for coluna in colunas_numericas:
        canais[coluna] = pd.to_numeric(canais[coluna])

    canais['investimento_min_mil'] = canais['investimento_min_mil'].astype(int)
    canais['investimento_max_mil'] = canais['investimento_max_mil'].astype(int)
    return canais


def validar_canais(canais: pd.DataFrame) -> None:
    colunas_faltantes = COLUNAS_OBRIGATORIAS.difference(canais.columns)
    if colunas_faltantes:
        raise ValueError(
            'Colunas obrigatorias ausentes: '
            + ', '.join(sorted(colunas_faltantes))
        )

    if canais.empty:
        raise ValueError('A base de canais esta vazia.')

    if canais[list(COLUNAS_OBRIGATORIAS)].isna().any().any():
        raise ValueError('A base de canais contem valores nulos.')

    if canais['id'].astype(str).duplicated().any():
        duplicados = canais.loc[canais['id'].astype(str).duplicated(), 'id'].tolist()
        raise ValueError(f'IDs de canal duplicados: {duplicados}')

    colunas_numericas = [
        'investimento_min_mil',
        'investimento_max_mil',
        'receita_por_mil',
        'saturacao',
        'risco',
    ]
    for coluna in colunas_numericas:
        valores = pd.to_numeric(canais[coluna], errors='coerce')
        if valores.isna().any():
            raise ValueError(f'A coluna {coluna} contem valores nao numericos.')

    if (pd.to_numeric(canais['investimento_min_mil']) < 0).any():
        raise ValueError('Investimento minimo nao pode ser negativo.')

    if (
        pd.to_numeric(canais['investimento_max_mil'])
        < pd.to_numeric(canais['investimento_min_mil'])
    ).any():
        raise ValueError('Investimento maximo precisa ser maior ou igual ao minimo.')

    if (pd.to_numeric(canais['receita_por_mil']) <= 0).any():
        raise ValueError('Receita por mil precisa ser positiva.')

    if not pd.to_numeric(canais['saturacao']).between(0, 1).all():
        raise ValueError('Saturacao precisa estar entre 0 e 1.')

    if not pd.to_numeric(canais['risco']).between(0, 1).all():
        raise ValueError('Risco precisa estar entre 0 e 1.')


def validar_orcamento(canais: pd.DataFrame, orcamento_mil: int) -> None:
    minimo = int(canais['investimento_min_mil'].sum())
    maximo = int(canais['investimento_max_mil'].sum())
    if orcamento_mil < minimo:
        raise ValueError(
            f'Orcamento de {orcamento_mil} mil e menor que o minimo viavel de {minimo} mil.'
        )
    if orcamento_mil > maximo:
        raise ValueError(
            f'Orcamento de {orcamento_mil} mil e maior que o maximo viavel de {maximo} mil.'
        )


def preparar_creator_deap() -> None:
    if not hasattr(creator, 'FitnessMarketing'):
        creator.create('FitnessMarketing', base.Fitness, weights=(1.0, -1.0))
    if not hasattr(creator, 'IndividualMarketing'):
        creator.create('IndividualMarketing', list, fitness=creator.FitnessMarketing)


def gerar_alocacao_inicial(canais: pd.DataFrame, orcamento_mil: int) -> list[int]:
    validar_orcamento(canais, orcamento_mil)

    minimos = canais['investimento_min_mil'].astype(int).tolist()
    maximos = canais['investimento_max_mil'].astype(int).tolist()
    alocacao = minimos[:]
    restante = orcamento_mil - sum(alocacao)

    while restante > 0:
        elegiveis = [
            indice
            for indice, investimento in enumerate(alocacao)
            if investimento < maximos[indice]
        ]
        indice = random.choice(elegiveis)
        incremento = random.randint(1, min(restante, maximos[indice] - alocacao[indice]))
        alocacao[indice] += incremento
        restante -= incremento

    return alocacao


def reparar_alocacao(
    individuo: Sequence[float | int],
    canais: pd.DataFrame,
    orcamento_mil: int,
) -> list[int]:
    validar_orcamento(canais, orcamento_mil)

    minimos = canais['investimento_min_mil'].astype(int).tolist()
    maximos = canais['investimento_max_mil'].astype(int).tolist()
    alocacao = [
        max(minimos[indice], min(maximos[indice], int(round(valor))))
        for indice, valor in enumerate(individuo)
    ]

    diferenca = orcamento_mil - sum(alocacao)
    tentativas = 0
    limite_tentativas = max(1000, len(alocacao) * abs(diferenca) * 20)

    while diferenca != 0 and tentativas < limite_tentativas:
        tentativas += 1

        if diferenca > 0:
            elegiveis = [
                indice
                for indice, investimento in enumerate(alocacao)
                if investimento < maximos[indice]
            ]
            indice = random.choice(elegiveis)
            alocacao[indice] += 1
            diferenca -= 1
        else:
            elegiveis = [
                indice
                for indice, investimento in enumerate(alocacao)
                if investimento > minimos[indice]
            ]
            indice = random.choice(elegiveis)
            alocacao[indice] -= 1
            diferenca += 1

    if sum(alocacao) != orcamento_mil:
        raise RuntimeError('Nao foi possivel reparar a alocacao para o orcamento definido.')

    return alocacao


def calcular_receitas_por_canal(
    alocacao: Sequence[int],
    canais: pd.DataFrame,
) -> list[float]:
    receitas = []

    for investimento, canal in zip(alocacao, canais.itertuples(index=False)):
        uso_relativo = investimento / canal.investimento_max_mil
        fator_saturacao = max(0.42, 1 - canal.saturacao * (uso_relativo**1.35))
        receitas.append(investimento * canal.receita_por_mil * fator_saturacao)

    return receitas


def calcular_sinergia(
    alocacao: Sequence[int],
    canais: pd.DataFrame,
    receitas: Sequence[float],
) -> float:
    indice_por_id = {
        str(canal.id): indice
        for indice, canal in enumerate(canais.itertuples(index=False))
    }
    sinergia_total = 0.0

    for (canal_a, canal_b), percentual in SINERGIAS.items():
        indice_a = indice_por_id[canal_a]
        indice_b = indice_por_id[canal_b]
        if alocacao[indice_a] > 0 and alocacao[indice_b] > 0:
            base_sinergia = min(receitas[indice_a], receitas[indice_b])
            sinergia_total += base_sinergia * percentual

    return sinergia_total


def calcular_metricas_plano(
    alocacao: Sequence[int],
    canais: pd.DataFrame,
) -> MetricasPlano:
    receitas = calcular_receitas_por_canal(alocacao, canais)
    investimento_total = float(sum(alocacao))
    sinergia = calcular_sinergia(alocacao, canais, receitas)
    receita_total = float(sum(receitas) + sinergia)
    risco_ponderado = float(
        sum(
            investimento * canal.risco
            for investimento, canal in zip(alocacao, canais.itertuples(index=False))
        )
    )
    lucro = receita_total - investimento_total

    return MetricasPlano(
        investimento_total_mil=investimento_total,
        receita_estimada_mil=receita_total,
        lucro_estimado_mil=lucro,
        risco_ponderado_mil=risco_ponderado,
        sinergia_mil=sinergia,
    )


def avaliar_individuo(individuo: Sequence[int], canais: pd.DataFrame) -> tuple[float, float]:
    metricas = calcular_metricas_plano(individuo, canais)
    return metricas.lucro_estimado_mil, metricas.risco_ponderado_mil


def cruzamento_com_reparo(
    individuo_a,
    individuo_b,
    canais: pd.DataFrame,
    orcamento_mil: int,
):
    tools.cxTwoPoint(individuo_a, individuo_b)
    individuo_a[:] = reparar_alocacao(individuo_a, canais, orcamento_mil)
    individuo_b[:] = reparar_alocacao(individuo_b, canais, orcamento_mil)
    return individuo_a, individuo_b


def mutacao_redistribuir(
    individuo,
    canais: pd.DataFrame,
    orcamento_mil: int,
):
    minimos = canais['investimento_min_mil'].astype(int).tolist()
    maximos = canais['investimento_max_mil'].astype(int).tolist()

    for _ in range(random.randint(1, 4)):
        origens = [
            indice
            for indice, investimento in enumerate(individuo)
            if investimento > minimos[indice]
        ]
        destinos = [
            indice
            for indice, investimento in enumerate(individuo)
            if investimento < maximos[indice]
        ]

        if not origens or not destinos:
            break

        origem = random.choice(origens)
        destino = random.choice([indice for indice in destinos if indice != origem])
        limite = min(
            individuo[origem] - minimos[origem],
            maximos[destino] - individuo[destino],
            8,
        )

        if limite <= 0:
            continue

        valor = random.randint(1, limite)
        individuo[origem] -= valor
        individuo[destino] += valor

    individuo[:] = reparar_alocacao(individuo, canais, orcamento_mil)
    return (individuo,)


def criar_toolbox(canais: pd.DataFrame, config: ConfigMarketingAG) -> base.Toolbox:
    preparar_creator_deap()
    toolbox = base.Toolbox()
    toolbox.register(
        'individual',
        tools.initIterate,
        creator.IndividualMarketing,
        lambda: gerar_alocacao_inicial(canais, config.orcamento_mil),
    )
    toolbox.register('population', tools.initRepeat, list, toolbox.individual)
    toolbox.register('evaluate', avaliar_individuo, canais=canais)
    toolbox.register(
        'mate',
        cruzamento_com_reparo,
        canais=canais,
        orcamento_mil=config.orcamento_mil,
    )
    toolbox.register(
        'mutate',
        mutacao_redistribuir,
        canais=canais,
        orcamento_mil=config.orcamento_mil,
    )
    toolbox.register('select', tools.selNSGA2)
    return toolbox


def registrar_historico(geracao: int, populacao: Sequence) -> dict[str, float | int]:
    lucros = [individuo.fitness.values[0] for individuo in populacao]
    riscos = [individuo.fitness.values[1] for individuo in populacao]
    return {
        'geracao': geracao,
        'lucro_max_mil': max(lucros),
        'lucro_medio_mil': mean(lucros),
        'risco_min_mil': min(riscos),
        'risco_medio_mil': mean(riscos),
    }


def executar_algoritmo_genetico(
    canais: pd.DataFrame,
    config: ConfigMarketingAG | None = None,
) -> ResultadoMarketingAG:
    config = config or ConfigMarketingAG()
    validar_orcamento(canais, config.orcamento_mil)
    random.seed(config.semente)

    toolbox = criar_toolbox(canais, config)
    populacao = toolbox.population(n=config.tamanho_populacao)
    fronteira = tools.ParetoFront()
    historico = []

    invalidos = [individuo for individuo in populacao if not individuo.fitness.valid]
    for individuo, fitness in zip(invalidos, map(toolbox.evaluate, invalidos)):
        individuo.fitness.values = fitness

    populacao = toolbox.select(populacao, len(populacao))
    fronteira.update(populacao)
    historico.append(registrar_historico(0, populacao))

    for geracao in range(1, config.geracoes + 1):
        descendentes = algorithms.varOr(
            populacao,
            toolbox,
            lambda_=config.descendentes_por_geracao,
            cxpb=config.taxa_crossover,
            mutpb=config.taxa_mutacao,
        )

        invalidos = [individuo for individuo in descendentes if not individuo.fitness.valid]
        for individuo, fitness in zip(invalidos, map(toolbox.evaluate, invalidos)):
            individuo.fitness.values = fitness

        populacao = toolbox.select(populacao + descendentes, config.tamanho_populacao)
        fronteira.update(populacao)
        historico.append(registrar_historico(geracao, populacao))

    plano = escolher_plano_recomendado(fronteira, config)
    metricas = calcular_metricas_plano(plano, canais)
    plano_detalhado = montar_plano_detalhado(plano, canais)
    fronteira_df = montar_fronteira_pareto(fronteira, config, canais)

    return ResultadoMarketingAG(
        plano_recomendado=tuple(plano),
        metricas=metricas,
        historico=pd.DataFrame(historico),
        fronteira_pareto=fronteira_df,
        plano_detalhado=plano_detalhado,
        config=config,
    )


def escolher_plano_recomendado(
    fronteira: tools.ParetoFront,
    config: ConfigMarketingAG,
) -> list[int]:
    if not fronteira:
        raise RuntimeError('A fronteira de Pareto esta vazia.')

    return list(
        max(
            fronteira,
            key=lambda individuo: (
                individuo.fitness.values[0]
                - config.peso_risco_decisao * individuo.fitness.values[1]
            ),
        )
    )


def montar_fronteira_pareto(
    fronteira: tools.ParetoFront,
    config: ConfigMarketingAG,
    canais: pd.DataFrame,
) -> pd.DataFrame:
    linhas = []

    for indice, individuo in enumerate(fronteira, start=1):
        metricas = calcular_metricas_plano(individuo, canais)
        linhas.append(
            {
                'plano': indice,
                'lucro_estimado_mil': metricas.lucro_estimado_mil,
                'risco_ponderado_mil': metricas.risco_ponderado_mil,
                'receita_estimada_mil': metricas.receita_estimada_mil,
                'sinergia_mil': metricas.sinergia_mil,
                'score_decisao': (
                    metricas.lucro_estimado_mil
                    - config.peso_risco_decisao * metricas.risco_ponderado_mil
                ),
            }
        )

    return pd.DataFrame(linhas).sort_values('score_decisao', ascending=False)


def montar_plano_detalhado(alocacao: Sequence[int], canais: pd.DataFrame) -> pd.DataFrame:
    receitas = calcular_receitas_por_canal(alocacao, canais)
    linhas = []

    for investimento, receita, canal in zip(alocacao, receitas, canais.itertuples(index=False)):
        linhas.append(
            {
                'id': canal.id,
                'canal': canal.canal,
                'categoria': canal.categoria,
                'funil': canal.funil,
                'investimento_mil': investimento,
                'receita_estimada_mil': receita,
                'lucro_bruto_mil': receita - investimento,
                'risco_ponderado_mil': investimento * canal.risco,
            }
        )

    return (
        pd.DataFrame(linhas)
        .sort_values('investimento_mil', ascending=False)
        .reset_index(drop=True)
    )


def criar_alocacao_referencia(canais: pd.DataFrame, orcamento_mil: int) -> list[int]:
    alocacao = canais['investimento_min_mil'].astype(int).tolist()
    maximos = canais['investimento_max_mil'].astype(int).tolist()
    restante = orcamento_mil - sum(alocacao)

    indice = 0
    while restante > 0:
        if alocacao[indice] < maximos[indice]:
            alocacao[indice] += 1
            restante -= 1
        indice = (indice + 1) % len(alocacao)

    return alocacao


def garantir_assets_relatorios(pasta_saida: str | Path) -> dict[str, Path]:
    if get_plotlyjs is None:
        raise RuntimeError('Plotly nao esta instalado. Instale as dependencias do projeto.')

    pasta = Path(pasta_saida)
    pasta_css = pasta / 'assets' / 'css'
    pasta_js = pasta / 'assets' / 'js'
    pasta_css.mkdir(parents=True, exist_ok=True)
    pasta_js.mkdir(parents=True, exist_ok=True)

    (pasta_css / 'relatorios.css').write_text(RELATORIOS_CSS, encoding='utf-8')
    (pasta_js / 'plotly.min.js').write_text(get_plotlyjs(), encoding='utf-8')

    return {
        'css': pasta_css,
        'js': pasta_js,
    }


def escrever_js_grafico(figura, div_id: str, caminho_js: str | Path) -> Path:
    if PlotlyJSONEncoder is None:
        raise RuntimeError('Plotly nao esta instalado. Instale as dependencias do projeto.')

    figura_json = json.dumps(
        figura.to_plotly_json(),
        cls=PlotlyJSONEncoder,
        ensure_ascii=False,
    )
    conteudo = f"""
document.addEventListener('DOMContentLoaded', () => {{
    const figure = {figura_json};
    const config = {{
        displaylogo: false,
        responsive: true,
    }};

    Plotly.newPlot('{div_id}', figure.data, figure.layout, config);
}});
""".strip()

    caminho = Path(caminho_js)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    caminho.write_text(conteudo, encoding='utf-8')
    return caminho


def escrever_html_relatorio(
    caminho_html: str | Path,
    titulo: str,
    descricao: str,
    div_id: str,
    arquivo_js: str,
) -> Path:
    caminho = Path(caminho_html)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    conteudo = f"""<!doctype html>
<html lang="pt-BR">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <title>{escape(titulo)}</title>
    <link rel="stylesheet" href="assets/css/relatorios.css">
    <script defer src="assets/js/plotly.min.js"></script>
    <script defer src="assets/js/{escape(arquivo_js)}"></script>
</head>
<body>
    <main class="report-shell">
        <header class="report-header">
            <p class="eyebrow">Algoritmo genetico</p>
            <h1>{escape(titulo)}</h1>
            <p class="report-description">{escape(descricao)}</p>
        </header>
        <section class="chart-panel" aria-label="{escape(titulo)}">
            <div id="{escape(div_id)}" class="chart"></div>
        </section>
    </main>
</body>
</html>
"""
    caminho.write_text(conteudo, encoding='utf-8')
    return caminho


def gerar_grafico_fronteira(resultado: ResultadoMarketingAG, caminho_saida: str | Path) -> Path:
    if px is None:
        raise RuntimeError('Plotly nao esta instalado. Instale as dependencias do projeto.')

    caminho = Path(caminho_saida)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    assets = garantir_assets_relatorios(caminho.parent)

    figura = px.scatter(
        resultado.fronteira_pareto,
        x='risco_ponderado_mil',
        y='lucro_estimado_mil',
        size='receita_estimada_mil',
        color='score_decisao',
        hover_data=['plano', 'sinergia_mil'],
        labels={
            'risco_ponderado_mil': 'Risco ponderado (R$ mil)',
            'lucro_estimado_mil': 'Lucro estimado (R$ mil)',
            'score_decisao': 'Score de decisao',
            'receita_estimada_mil': 'Receita estimada (R$ mil)',
        },
        title='Fronteira de Pareto: lucro versus risco',
        template='plotly_white',
    )
    escrever_js_grafico(
        figura,
        div_id='grafico-fronteira-pareto',
        caminho_js=assets['js'] / 'fronteira_pareto.js',
    )
    escrever_html_relatorio(
        caminho,
        titulo='Fronteira de Pareto',
        descricao=(
            'Comparacao dos planos nao dominados pelo algoritmo genetico. '
            'Planos mais acima tendem a gerar mais lucro, enquanto planos mais '
            'a esquerda concentram menos risco ponderado.'
        ),
        div_id='grafico-fronteira-pareto',
        arquivo_js='fronteira_pareto.js',
    )
    return caminho


def gerar_grafico_alocacao(resultado: ResultadoMarketingAG, caminho_saida: str | Path) -> Path:
    if go is None:
        raise RuntimeError('Plotly nao esta instalado. Instale as dependencias do projeto.')

    caminho = Path(caminho_saida)
    caminho.parent.mkdir(parents=True, exist_ok=True)
    assets = garantir_assets_relatorios(caminho.parent)
    plano = resultado.plano_detalhado.sort_values('investimento_mil')

    figura = go.Figure(
        go.Bar(
            x=plano['investimento_mil'],
            y=plano['canal'],
            orientation='h',
            marker={'color': plano['lucro_bruto_mil'], 'colorscale': 'Viridis'},
            hovertemplate=(
                '<b>%{y}</b><br>'
                'Investimento: R$ %{x:.0f} mil<br>'
                'Lucro bruto: R$ %{marker.color:.1f} mil<extra></extra>'
            ),
        )
    )
    figura.update_layout(
        title='Alocacao recomendada de orcamento',
        xaxis_title='Investimento (R$ mil)',
        yaxis_title='Canal',
        template='plotly_white',
    )
    escrever_js_grafico(
        figura,
        div_id='grafico-alocacao-orcamento',
        caminho_js=assets['js'] / 'alocacao_orcamento.js',
    )
    escrever_html_relatorio(
        caminho,
        titulo='Alocacao recomendada de orcamento',
        descricao=(
            'Distribuicao sugerida do orcamento entre canais. A cor das barras '
            'representa o lucro bruto estimado de cada canal no plano escolhido.'
        ),
        div_id='grafico-alocacao-orcamento',
        arquivo_js='alocacao_orcamento.js',
    )
    return caminho


def salvar_resumo_execucao(
    resultado: ResultadoMarketingAG,
    caminho_saida: str | Path,
) -> Path:
    caminho = Path(caminho_saida)
    caminho.parent.mkdir(parents=True, exist_ok=True)

    linhas = [
        'Resumo da execucao do algoritmo genetico com DEAP',
        '',
        f'Orcamento: R$ {resultado.config.orcamento_mil:.0f} mil',
        f'Populacao: {resultado.config.tamanho_populacao}',
        f'Geracoes: {resultado.config.geracoes}',
        f'Descendentes por geracao: {resultado.config.descendentes_por_geracao}',
        f'Taxa de crossover: {resultado.config.taxa_crossover:.0%}',
        f'Taxa de mutacao: {resultado.config.taxa_mutacao:.0%}',
        f'Semente aleatoria: {resultado.config.semente}',
        '',
        f'Receita estimada: R$ {resultado.metricas.receita_estimada_mil:.2f} mil',
        f'Lucro estimado: R$ {resultado.metricas.lucro_estimado_mil:.2f} mil',
        f'Risco ponderado: R$ {resultado.metricas.risco_ponderado_mil:.2f} mil',
        f'Sinergia estimada: R$ {resultado.metricas.sinergia_mil:.2f} mil',
        '',
        'Plano recomendado:',
    ]

    for linha in resultado.plano_detalhado.itertuples(index=False):
        linhas.append(
            f'- {linha.canal}: R$ {linha.investimento_mil:.0f} mil '
            f'(receita R$ {linha.receita_estimada_mil:.1f} mil, '
            f'risco R$ {linha.risco_ponderado_mil:.1f} mil)'
        )

    caminho.write_text('\n'.join(linhas), encoding='utf-8')
    return caminho


def executar_exemplo() -> ResultadoMarketingAG:
    raiz = caminho_raiz_projeto()
    canais = carregar_canais(raiz / 'data' / 'canais_marketing.csv')
    resultado = executar_algoritmo_genetico(canais)
    pasta_saida = raiz / 'outputs'

    resultado.plano_detalhado.to_csv(
        pasta_saida / 'plano_marketing_otimizado.csv',
        index=False,
    )
    gerar_grafico_fronteira(resultado, pasta_saida / 'fronteira_pareto.html')
    gerar_grafico_alocacao(resultado, pasta_saida / 'alocacao_orcamento.html')
    salvar_resumo_execucao(resultado, pasta_saida / 'resumo_execucao.txt')
    return resultado


def main() -> None:
    resultado = executar_exemplo()
    print('Algoritmo genetico com DEAP finalizado com sucesso.')
    print(f'Receita estimada: R$ {resultado.metricas.receita_estimada_mil:.2f} mil')
    print(f'Lucro estimado: R$ {resultado.metricas.lucro_estimado_mil:.2f} mil')
    print(f'Risco ponderado: R$ {resultado.metricas.risco_ponderado_mil:.2f} mil')
    print('Arquivos gerados em: outputs/')


if __name__ == '__main__':
    main()
