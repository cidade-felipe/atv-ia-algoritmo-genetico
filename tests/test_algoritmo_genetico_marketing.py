from pathlib import Path

import pandas as pd
import pytest

from src.algoritmo_genetico_marketing import (
    ConfigMarketingAG,
    avaliar_individuo,
    carregar_canais,
    criar_alocacao_referencia,
    executar_algoritmo_genetico,
    reparar_alocacao,
    validar_canais,
)


RAIZ = Path(__file__).resolve().parents[1]
CAMINHO_DADOS = RAIZ / 'data' / 'canais_marketing.csv'


def test_carregar_canais_valida_dados_obrigatorios() -> None:
    canais = carregar_canais(CAMINHO_DADOS)

    assert len(canais) == 12
    assert set(canais.columns) == {
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
    assert not canais.isna().any().any()
    assert canais['risco'].between(0, 1).all()
    assert canais['saturacao'].between(0, 1).all()


def test_validar_canais_rejeita_maximo_menor_que_minimo() -> None:
    canais = pd.DataFrame(
        {
            'id': ['SEARCH'],
            'canal': ['Search Ads'],
            'categoria': ['midia_paga'],
            'funil': ['conversao'],
            'investimento_min_mil': [10],
            'investimento_max_mil': [5],
            'receita_por_mil': [3.2],
            'saturacao': [0.4],
            'risco': [0.3],
        }
    )

    with pytest.raises(ValueError, match='Investimento maximo'):
        validar_canais(canais)


def test_reparar_alocacao_respeita_orcamento_e_limites() -> None:
    canais = carregar_canais(CAMINHO_DADOS)
    alocacao_quebrada = [50] * len(canais)

    alocacao = reparar_alocacao(alocacao_quebrada, canais, orcamento_mil=100)

    assert sum(alocacao) == 100
    assert all(alocacao >= canais['investimento_min_mil'])
    assert all(alocacao <= canais['investimento_max_mil'])


def test_algoritmo_gera_plano_valido_e_fronteira_pareto() -> None:
    canais = carregar_canais(CAMINHO_DADOS)
    config = ConfigMarketingAG(
        tamanho_populacao=80,
        geracoes=45,
        descendentes_por_geracao=80,
        semente=17,
    )

    resultado = executar_algoritmo_genetico(canais, config)

    assert sum(resultado.plano_recomendado) == config.orcamento_mil
    assert len(resultado.plano_recomendado) == len(canais)
    assert not resultado.fronteira_pareto.empty
    assert len(resultado.historico) == config.geracoes + 1
    assert resultado.metricas.lucro_estimado_mil > 0


def test_plano_otimizado_supera_referencia_distribuida() -> None:
    canais = carregar_canais(CAMINHO_DADOS)
    config = ConfigMarketingAG(
        tamanho_populacao=90,
        geracoes=55,
        descendentes_por_geracao=90,
        semente=21,
    )

    resultado = executar_algoritmo_genetico(canais, config)
    referencia = criar_alocacao_referencia(canais, config.orcamento_mil)
    lucro_referencia, _ = avaliar_individuo(referencia, canais)

    assert resultado.metricas.lucro_estimado_mil > lucro_referencia
