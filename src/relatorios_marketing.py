from __future__ import annotations

import json
from html import escape
from pathlib import Path

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

try:
    from src.motor_algoritmo_genetico import ResultadoMarketingAG
except ModuleNotFoundError:  # pragma: no cover - compatibilidade com execucao direta
    from motor_algoritmo_genetico import ResultadoMarketingAG


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
