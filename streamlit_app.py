from __future__ import annotations

from io import BytesIO
from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.motor_algoritmo_genetico import (
    ConfigMarketingAG,
    executar_algoritmo_genetico,
    validar_canais,
)


RAIZ_PROJETO = Path(__file__).resolve().parent
CAMINHO_DADOS = RAIZ_PROJETO / 'data' / 'canais_marketing.csv'

CANAL_ROTULOS = {
    'Otimizacao de conversao': 'Otimização de conversão',
    'Programa de indicacao': 'Programa de indicação',
    'Conteudo SEO': 'Conteúdo SEO',
    'Search Ads': 'Search Ads',
    'CRM e email': 'CRM e Email',
    'Retargeting': 'Retargeting',
    'Promocoes marketplace': 'Promoções marketplace',
    'Webinars B2B': 'Webinars B2B',
    'LinkedIn Ads': 'LinkedIn Ads',
    'TikTok Ads': 'TikTok Ads',
    'Influenciadores micro': 'Influenciadores micro',
    'YouTube Shorts': 'YouTube Shorts',
}

FUNIL_ROTULOS = {
    'aquisicao': 'Aquisição',
    'conversao': 'Conversão',
    'nutricao': 'Nutrição',
    'retencao': 'Retenção',
}

CATEGORIA_ROTULOS = {
    'midia_paga': 'Mídia paga',
    'relacionamento': 'Relacionamento',
    'organico': 'Orgânico',
    'marca': 'Marca',
    'produto': 'Produto',
    'b2b': 'B2B',
    'trade': 'Trade',
}

CANAL_VALORES_POR_ROTULO = {
    rotulo: valor
    for valor, rotulo in CANAL_ROTULOS.items()
}

FUNIL_VALORES_POR_ROTULO = {
    rotulo: valor
    for valor, rotulo in FUNIL_ROTULOS.items()
}

CATEGORIA_VALORES_POR_ROTULO = {
    rotulo: valor
    for valor, rotulo in CATEGORIA_ROTULOS.items()
}

TOOLTIPS_PARAMETROS = {
    'orcamento': 'Valor total disponível, em milhares de reais, que o algoritmo deve distribuir entre os canais.',
    'populacao': 'Quantidade de planos candidatos avaliados em cada geração do algoritmo genético.',
    'geracoes': 'Número de ciclos evolutivos usados para selecionar, cruzar e mutar os planos.',
    'descendentes': 'Quantidade de novos planos criados a cada geração por cruzamento ou mutação.',
    'crossover': 'Probabilidade de combinar dois planos para gerar novos planos candidatos.',
    'mutacao': 'Probabilidade de redistribuir parte da verba para explorar alternativas novas.',
    'peso_risco': 'Intensidade com que o risco reduz o score usado para escolher o plano recomendado.',
    'semente': 'Número usado para repetir a mesma sequência aleatória e reproduzir o resultado.',
}
TOOLTIPS_COLUNAS = {
    'id': 'Identificador único do canal usado nas regras de sinergia e nos resultados.',
    'canal': 'Nome visível do canal de marketing que receberá investimento.',
    'categoria': 'Grupo estratégico do canal, como mídia paga, orgânico, relacionamento ou produto.',
    'funil': 'Etapa do funil onde o canal atua principalmente, como aquisição, conversão, nutrição ou retenção.',
    'investimento_min_mil': 'Menor investimento permitido no canal, em milhares de reais.',
    'investimento_max_mil': 'Maior investimento permitido no canal antes de violar a capacidade definida.',
    'receita_por_mil': 'Receita estimada gerada por cada R$ 1 mil investido antes da saturação.',
    'saturacao': 'Quanto o retorno marginal do canal cai quando o investimento se aproxima do máximo.',
    'risco': 'Incerteza relativa do canal, usada para penalizar planos muito arriscados.',
}
COLUNAS_PLANO_RECOMENDADO = {
    'id': 'ID',
    'canal': 'Canal',
    'categoria': 'Categoria',
    'funil': 'Funil',
    'investimento_mil': 'Investimento (R$ mil)',
    'receita_estimada_mil': 'Receita estimada (R$ mil)',
    'lucro_bruto_mil': 'Lucro bruto (R$ mil)',
    'risco_ponderado_mil': 'Risco ponderado (R$ mil)',
}


def carregar_canais_padrao() -> pd.DataFrame:
    return pd.read_csv(CAMINHO_DADOS)


def normalizar_canais(canais: pd.DataFrame) -> pd.DataFrame:
    canais = canais.copy()
    canais['id'] = canais['id'].astype(str).str.strip().str.upper().str.replace(' ', '_')
    canais['canal'] = (
        canais['canal']
        .astype(str)
        .str.strip()
        .replace(CANAL_VALORES_POR_ROTULO)
    )
    canais['categoria'] = (
        canais['categoria']
        .astype(str)
        .str.strip()
        .replace(CATEGORIA_VALORES_POR_ROTULO)
    )
    canais['funil'] = (
        canais['funil']
        .astype(str)
        .str.strip()
        .replace(FUNIL_VALORES_POR_ROTULO)
    )

    for coluna in [
        'investimento_min_mil',
        'investimento_max_mil',
        'receita_por_mil',
        'saturacao',
        'risco',
    ]:
        canais[coluna] = pd.to_numeric(canais[coluna], errors='coerce')

    canais['investimento_min_mil'] = canais['investimento_min_mil'].round().astype('Int64')
    canais['investimento_max_mil'] = canais['investimento_max_mil'].round().astype('Int64')
    return canais


def montar_opcoes_funil(canais: pd.DataFrame) -> list[str]:
    funis_csv = [
        str(valor).strip()
        for valor in canais['funil'].dropna().unique()
        if str(valor).strip()
    ]
    return list(dict.fromkeys([*FUNIL_ROTULOS, *funis_csv]))


def montar_opcoes_categoria(canais: pd.DataFrame) -> list[str]:
    categorias_csv = [
        str(valor).strip()
        for valor in canais['categoria'].dropna().unique()
        if str(valor).strip()
    ]
    return list(dict.fromkeys([*CATEGORIA_ROTULOS, *categorias_csv]))


def montar_opcoes_canal(canais: pd.DataFrame) -> list[str]:
    canais_csv = [
        str(valor).strip()
        for valor in canais['canal'].dropna().unique()
        if str(valor).strip()
    ]
    return list(dict.fromkeys([*CANAL_ROTULOS, *canais_csv]))


def formatar_canal(valor: str) -> str:
    valor_normalizado = str(valor).strip()
    return CANAL_ROTULOS.get(
        valor_normalizado,
        valor_normalizado.replace('_', ' ').title(),
    )


def formatar_categoria(valor: str) -> str:
    valor_normalizado = str(valor).strip()
    return CATEGORIA_ROTULOS.get(
        valor_normalizado,
        valor_normalizado.replace('_', ' ').title(),
    )


def formatar_funil(valor: str) -> str:
    valor_normalizado = str(valor).strip()
    return FUNIL_ROTULOS.get(
        valor_normalizado,
        valor_normalizado.replace('_', ' ').title(),
    )


def gerar_excel_plano(plano: pd.DataFrame) -> bytes:
    buffer = BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        plano.to_excel(writer, index=False, sheet_name='Plano otimizado')
    return buffer.getvalue()


def preparar_plano_recomendado_para_exibicao(plano: pd.DataFrame) -> pd.DataFrame:
    plano_exibicao = plano.copy()
    plano_exibicao['canal'] = plano_exibicao['canal'].apply(formatar_canal)
    plano_exibicao['categoria'] = plano_exibicao['categoria'].apply(formatar_categoria)
    plano_exibicao['funil'] = plano_exibicao['funil'].apply(formatar_funil)
    return plano_exibicao.rename(columns=COLUNAS_PLANO_RECOMENDADO)


def configurar_pagina() -> None:
    st.set_page_config(
        page_title='Otimizador de mix de marketing',
        layout='wide',
    )   
    st.title('Otimizador de mix de marketing')
    st.caption(
        'Otimiza mixes de marketing com base em critérios de investimento, retorno e risco, utilizando um algoritmo genético.'
    )


def renderizar_parametros() -> ConfigMarketingAG:
    st.sidebar.header('Parâmetros')
    orcamento = st.sidebar.number_input(
        'Orçamento (R$ mil)',
        min_value=1,
        max_value=10_000,
        value=100,
        step=1,
        help=TOOLTIPS_PARAMETROS['orcamento'],
    )
    populacao = st.sidebar.number_input(
        'População',
        min_value=20,
        max_value=500,
        value=140,
        step=10,
        help=TOOLTIPS_PARAMETROS['populacao'],
    )
    geracoes = st.sidebar.number_input(
        'Gerações',
        min_value=5,
        max_value=300,
        value=110,
        step=5,
        help=TOOLTIPS_PARAMETROS['geracoes'],
    )
    descendentes = st.sidebar.number_input(
        'Descendentes por geração',
        min_value=20,
        max_value=500,
        value=140,
        step=10,
        help=TOOLTIPS_PARAMETROS['descendentes'],
    )
    crossover = st.sidebar.slider(
        'Taxa de crossover',
        0.0,
        1.0,
        0.68,
        0.01,
        help=TOOLTIPS_PARAMETROS['crossover'],
    )
    mutacao = st.sidebar.slider(
        'Taxa de mutação',
        0.0,
        1.0,
        0.32,
        0.01,
        help=TOOLTIPS_PARAMETROS['mutacao'],
    )
    peso_risco = st.sidebar.number_input(
        'Peso do risco',
        min_value=0.0,
        max_value=10.0,
        value=0.55,
        step=0.05,
        help=TOOLTIPS_PARAMETROS['peso_risco'],
    )
    semente = st.sidebar.number_input(
        'Semente aleatória',
        value=42,
        step=1,
        help=TOOLTIPS_PARAMETROS['semente'],
    )

    return ConfigMarketingAG(
        orcamento_mil=int(orcamento),
        tamanho_populacao=int(populacao),
        geracoes=int(geracoes),
        descendentes_por_geracao=int(descendentes),
        taxa_crossover=float(crossover),
        taxa_mutacao=float(mutacao),
        peso_risco_decisao=float(peso_risco),
        semente=int(semente),
    )


def renderizar_editor_canais(canais: pd.DataFrame) -> pd.DataFrame:
    st.subheader('Canais de marketing')
    st.write(
        'Ajuste limites de investimento, retorno esperado, saturação e risco antes de calcular.'
    )
    return st.data_editor(
        canais,
        num_rows='dynamic',
        use_container_width=True,
        hide_index=True,
        column_config={
            'id': st.column_config.TextColumn(
                'ID',
                help=TOOLTIPS_COLUNAS['id'],
                required=True,
            ),
            'canal': st.column_config.SelectboxColumn(
                'Canal',
                help=TOOLTIPS_COLUNAS['canal'],
                options=montar_opcoes_canal(canais),
                format_func=formatar_canal,
                required=True,
            ),
            'categoria': st.column_config.SelectboxColumn(
                'Categoria',
                help=TOOLTIPS_COLUNAS['categoria'],
                options=montar_opcoes_categoria(canais),
                format_func=formatar_categoria,
                required=True,
            ),
            'funil': st.column_config.SelectboxColumn(
                'Funil',
                help=TOOLTIPS_COLUNAS['funil'],
                options=montar_opcoes_funil(canais),
                format_func=formatar_funil,
                required=True,
            ),
            'investimento_min_mil': st.column_config.NumberColumn(
                'Mínimo (R$ mil)',
                help=TOOLTIPS_COLUNAS['investimento_min_mil'],
                min_value=0,
                step=1,
                required=True,
            ),
            'investimento_max_mil': st.column_config.NumberColumn(
                'Máximo (R$ mil)',
                help=TOOLTIPS_COLUNAS['investimento_max_mil'],
                min_value=0,
                step=1,
                required=True,
            ),
            'receita_por_mil': st.column_config.NumberColumn(
                'Receita por R$ mil',
                help=TOOLTIPS_COLUNAS['receita_por_mil'],
                min_value=0.01,
                step=0.05,
                format='%.2f',
                required=True,
            ),
            'saturacao': st.column_config.NumberColumn(
                'Saturação',
                help=TOOLTIPS_COLUNAS['saturacao'],
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                format='%.2f',
                required=True,
            ),
            'risco': st.column_config.NumberColumn(
                'Risco',
                help=TOOLTIPS_COLUNAS['risco'],
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                format='%.2f',
                required=True,
            ),
        },
    )


def grafico_alocacao_canal(plano: pd.DataFrame) -> go.Figure:
    plano_ordenado = plano.sort_values('investimento_mil')
    figura = go.Figure(
        go.Bar(
            x=plano_ordenado['investimento_mil'],
            y=plano_ordenado['canal'].apply(formatar_canal),
            orientation='h',
            marker={
                'color': plano_ordenado['lucro_bruto_mil'],
                'colorscale': 'Viridis',
            },
            hovertemplate=(
                '<b>%{y}</b><br>'
                'Investimento: R$ %{x:.0f} mil<br>'
                'Lucro bruto: R$ %{marker.color:.1f} mil<extra></extra>'
            ),
        )
    )
    figura.update_layout(
        title='Alocação recomendada',
        xaxis_title='Investimento (R$ mil)',
        yaxis_title='Canal',
        template='plotly_white',
        height=430,
    )
    return figura


def grafico_alocacao_categoria(plano: pd.DataFrame) -> go.Figure: # Igual ao de canal, mas agrupando por categoria e com gramatica correta (sem _ e com espaços no título e eixo y
    plano_agrupado = plano.groupby('categoria', as_index=False).agg({
        'investimento_mil': 'sum',
        'lucro_bruto_mil': 'sum',
    })
    plano_ordenado = plano_agrupado.sort_values('investimento_mil')
    figura = go.Figure(
        go.Bar(
            x=plano_ordenado['investimento_mil'],
            y=plano_ordenado['categoria'].apply(formatar_categoria),
            orientation='h',
            marker={
                'color': plano_ordenado['lucro_bruto_mil'],
                'colorscale': 'Viridis',
            },
            hovertemplate=(
                '<b>%{y}</b><br>'
                'Investimento: R$ %{x:.0f} mil<br>'
                'Lucro bruto: R$ %{marker.color:.1f} mil<extra></extra>'
            ),
        )
    )
    figura.update_layout(
        title='Alocação recomendada por categoria',
        xaxis_title='Investimento (R$ mil)',
        yaxis_title='Categoria',
        template='plotly_white',
        height=430,
    )
    return figura


def grafico_alocacao_funil(plano: pd.DataFrame) -> go.Figure: # Igual ao do por canal, mas agrupando por funil e ordenando pelo investimento
    plano_agrupado = plano.groupby('funil', as_index=False).agg({
        'investimento_mil': 'sum',
        'lucro_bruto_mil': 'sum',
    })
    plano_ordenado = plano_agrupado.sort_values('investimento_mil')
    figura = go.Figure(
        go.Bar(
            x=plano_ordenado['investimento_mil'],
            y=plano_ordenado['funil'].apply(formatar_funil),
            orientation='h',
            marker={
                'color': plano_ordenado['lucro_bruto_mil'],
                'colorscale': 'Viridis',
            },
            hovertemplate=(
                '<b>%{y}</b><br>'
                'Investimento: R$ %{x:.0f} mil<br>'
                'Lucro bruto: R$ %{marker.color:.1f} mil<extra></extra>'
            ),
        )
    )
    figura.update_layout(
        title='Alocação recomendada por etapa do funil',
        xaxis_title='Investimento (R$ mil)',
        yaxis_title='Etapa do funil',
        template='plotly_white',
        height=430,
    )
    return figura


def grafico_fronteira(fronteira: pd.DataFrame, lucro: float, risco: float) -> go.Figure:
    figura = px.scatter(
        fronteira,
        x='risco_ponderado_mil',
        y='lucro_estimado_mil',
        size='receita_estimada_mil',
        color='score_decisao',
        hover_data=['plano', 'sinergia_mil'],
        labels={
            'risco_ponderado_mil': 'Risco ponderado (R$ mil)',
            'lucro_estimado_mil': 'Lucro estimado (R$ mil)',
            'score_decisao': 'Score de decisão',
            'receita_estimada_mil': 'Receita estimada (R$ mil)',
        },
        title='Fronteira de Pareto',
        template='plotly_white',
        height=430,
    )
    figura.add_trace(
        go.Scatter(
            x=[risco],
            y=[lucro],
            mode='markers',
            marker={'size': 16, 'color': '#be123c', 'symbol': 'diamond'},
            name='Plano escolhido',
            hovertemplate=(
                'Plano escolhido<br>'
                'Risco: R$ %{x:.1f} mil<br>'
                'Lucro: R$ %{y:.1f} mil<extra></extra>'
            ),
        )
    )
    return figura


def grafico_convergencia(historico: pd.DataFrame) -> go.Figure:
    figura = go.Figure()
    figura.add_trace(
        go.Scatter(
            x=historico['geracao'],
            y=historico['lucro_max_mil'],
            mode='lines',
            name='Melhor lucro',
            line={'color': '#0f766e', 'width': 3},
        )
    )
    figura.add_trace(
        go.Scatter(
            x=historico['geracao'],
            y=historico['lucro_medio_mil'],
            mode='lines',
            name='Lucro médio',
            line={'color': '#b45309', 'width': 2, 'dash': 'dot'},
        )
    )
    figura.update_layout(
        title='Convergência do algoritmo',
        xaxis_title='Geração',
        yaxis_title='Lucro estimado (R$ mil)',
        template='plotly_white',
        height=360,
    )
    return figura


def renderizar_resultado(resultado) -> None:
    metricas = resultado.metricas

    colunas = st.columns(4)
    colunas[0].metric('Receita estimada', f'R$ {metricas.receita_estimada_mil:.1f} mil')
    colunas[1].metric('Lucro estimado', f'R$ {metricas.lucro_estimado_mil:.1f} mil')
    colunas[2].metric('Risco ponderado', f'R$ {metricas.risco_ponderado_mil:.1f} mil')
    colunas[3].metric('Sinergia', f'R$ {metricas.sinergia_mil:.1f} mil')

    st.subheader('Plano recomendado')
    plano_recomendado = preparar_plano_recomendado_para_exibicao(
        resultado.plano_detalhado
    )
    st.dataframe(
        plano_recomendado,
        use_container_width=True,
        hide_index=True,
        column_config={
            'Investimento (R$ mil)': st.column_config.NumberColumn(
                'Investimento (R$ mil)',
                format='R$ %.0f mil',
            ),
            'Receita estimada (R$ mil)': st.column_config.NumberColumn(
                'Receita estimada (R$ mil)',
                format='R$ %.2f mil',
            ),
            'Lucro bruto (R$ mil)': st.column_config.NumberColumn(
                'Lucro bruto (R$ mil)',
                format='R$ %.2f mil',
            ),
            'Risco ponderado (R$ mil)': st.column_config.NumberColumn(
                'Risco ponderado (R$ mil)',
                format='R$ %.2f mil',
            ),
        },
    )

    csv = resultado.plano_detalhado.to_csv(index=False).encode('utf-8')
    xlsx = gerar_excel_plano(resultado.plano_detalhado)
    col_download_csv, col_download_excel, _ = st.columns(
        [0.26, 0.27, 0.49],
        gap='small',
    )
    with col_download_csv:
        st.download_button(
            label='Exportar plano otimizado em CSV',
            data=csv,
            file_name='plano_otimizado.csv',
            mime='text/csv',
            use_container_width=True,
        )
    with col_download_excel:
        st.download_button(
            label='Exportar plano otimizado em XLSX',
            data=xlsx,
            file_name='plano_otimizado.xlsx',
            mime='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet',
            use_container_width=True,
        )

    st.subheader('Gráficos')

    aba_alocacao_canal, aba_alocacao_categoria, aba_alocacao_funil, aba_fronteira, aba_convergencia = st.tabs(
        ['Alocação por Canal', 'Alocação por Categoria', 'Alocação por Funil', 'Fronteira de Pareto', 'Convergência']
    )
    # aumentar fonte das abas para 18px e negrito usando CSS

    with aba_alocacao_canal:
        st.plotly_chart(grafico_alocacao_canal(resultado.plano_detalhado), use_container_width=True)

    with aba_alocacao_categoria:
        st.plotly_chart(grafico_alocacao_categoria(resultado.plano_detalhado), use_container_width=True)

    with aba_alocacao_funil:
        st.plotly_chart(grafico_alocacao_funil(resultado.plano_detalhado), use_container_width=True)

    with aba_fronteira:
        st.plotly_chart(
            grafico_fronteira(
                resultado.fronteira_pareto,
                metricas.lucro_estimado_mil,
                metricas.risco_ponderado_mil,
            ),
            use_container_width=True,
        )

    with aba_convergencia:
        st.plotly_chart(grafico_convergencia(resultado.historico), use_container_width=True)


def main() -> None:
    configurar_pagina()

    config = renderizar_parametros()
    canais_editados = renderizar_editor_canais(carregar_canais_padrao())

    if st.button('Calcular plano otimizado', type='primary'):
        try:
            canais = normalizar_canais(canais_editados)
            validar_canais(canais)
            with st.spinner('Calculando plano otimizado...'):
                resultado = executar_algoritmo_genetico(canais, config)
            st.success('Cálculo finalizado com sucesso.')
            renderizar_resultado(resultado)
        except Exception as erro:  # noqa: BLE001 - exibe erro amigavel na interface
            st.error(f'Não foi possível calcular: {erro}')
    else:
        st.info('Ajuste os valores e clique em "Calcular plano otimizado".')


if __name__ == '__main__':
    main()
