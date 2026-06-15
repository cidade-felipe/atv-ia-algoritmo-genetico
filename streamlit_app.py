from __future__ import annotations

from pathlib import Path

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from src.algoritmo_genetico_marketing import (
    ConfigMarketingAG,
    executar_algoritmo_genetico,
    validar_canais,
)


RAIZ_PROJETO = Path(__file__).resolve().parent
CAMINHO_DADOS = RAIZ_PROJETO / 'data' / 'canais_marketing.csv'


def carregar_canais_padrao() -> pd.DataFrame:
    return pd.read_csv(CAMINHO_DADOS)


def normalizar_canais(canais: pd.DataFrame) -> pd.DataFrame:
    canais = canais.copy()
    canais['id'] = canais['id'].astype(str).str.strip().str.upper().str.replace(' ', '_')
    canais['canal'] = canais['canal'].astype(str).str.strip()
    canais['categoria'] = canais['categoria'].astype(str).str.strip()
    canais['funil'] = canais['funil'].astype(str).str.strip()

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


def configurar_pagina() -> None:
    st.set_page_config(
        page_title='Otimizador de mix de marketing',
        layout='wide',
    )
    st.title('Otimizador de mix de marketing')
    st.caption(
        'Interface Streamlit usando o backend Python do algoritmo genético com DEAP.'
    )


def renderizar_parametros() -> ConfigMarketingAG:
    st.sidebar.header('Parâmetros')
    orcamento = st.sidebar.number_input(
        'Orçamento (R$ mil)',
        min_value=1,
        max_value=10_000,
        value=100,
        step=1,
    )
    populacao = st.sidebar.number_input(
        'População',
        min_value=20,
        max_value=500,
        value=140,
        step=10,
    )
    geracoes = st.sidebar.number_input(
        'Gerações',
        min_value=5,
        max_value=300,
        value=110,
        step=5,
    )
    descendentes = st.sidebar.number_input(
        'Descendentes por geração',
        min_value=20,
        max_value=500,
        value=140,
        step=10,
    )
    crossover = st.sidebar.slider('Taxa de crossover', 0.0, 1.0, 0.68, 0.01)
    mutacao = st.sidebar.slider('Taxa de mutação', 0.0, 1.0, 0.32, 0.01)
    peso_risco = st.sidebar.number_input(
        'Peso do risco',
        min_value=0.0,
        max_value=10.0,
        value=0.55,
        step=0.05,
    )
    semente = st.sidebar.number_input('Semente aleatória', value=42, step=1)

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
            'id': st.column_config.TextColumn('ID', required=True),
            'canal': st.column_config.TextColumn('Canal', required=True),
            'categoria': st.column_config.TextColumn('Categoria', required=True),
            'funil': st.column_config.SelectboxColumn(
                'Funil',
                options=['aquisição', 'conversão', 'nutrição', 'retenção'],
                required=True,
            ),
            'investimento_min_mil': st.column_config.NumberColumn(
                'Mínimo',
                min_value=0,
                step=1,
                required=True,
            ),
            'investimento_max_mil': st.column_config.NumberColumn(
                'Máximo',
                min_value=0,
                step=1,
                required=True,
            ),
            'receita_por_mil': st.column_config.NumberColumn(
                'Receita por R$ mil',
                min_value=0.01,
                step=0.05,
                format='%.2f',
                required=True,
            ),
            'saturacao': st.column_config.NumberColumn(
                'Saturação',
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                format='%.2f',
                required=True,
            ),
            'risco': st.column_config.NumberColumn(
                'Risco',
                min_value=0.0,
                max_value=1.0,
                step=0.01,
                format='%.2f',
                required=True,
            ),
        },
    )


def grafico_alocacao(plano: pd.DataFrame) -> go.Figure:
    plano_ordenado = plano.sort_values('investimento_mil')
    figura = go.Figure(
        go.Bar(
            x=plano_ordenado['investimento_mil'],
            y=plano_ordenado['canal'],
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
    st.dataframe(resultado.plano_detalhado, use_container_width=True, hide_index=True)

    csv = resultado.plano_detalhado.to_csv(index=False).encode('utf-8')
    st.download_button(
        'Baixar plano em CSV',
        data=csv,
        file_name='plano_marketing_otimizado_streamlit.csv',
        mime='text/csv',
    )

    aba_alocacao, aba_fronteira, aba_convergencia = st.tabs(
        ['Alocação', 'Fronteira de Pareto', 'Convergência']
    )

    with aba_alocacao:
        st.plotly_chart(grafico_alocacao(resultado.plano_detalhado), use_container_width=True)

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
            with st.spinner('Executando algoritmo genético...'):
                resultado = executar_algoritmo_genetico(canais, config)
            st.success('Cálculo finalizado com sucesso.')
            renderizar_resultado(resultado)
        except Exception as erro:  # noqa: BLE001 - exibe erro amigavel na interface
            st.error(f'Não foi possível calcular: {erro}')
    else:
        st.info('Ajuste os valores e clique em "Calcular plano otimizado".')


if __name__ == '__main__':
    main()
