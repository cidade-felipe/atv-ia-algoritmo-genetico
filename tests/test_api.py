from fastapi.testclient import TestClient

from src.api import app


client = TestClient(app)


def canais_exemplo() -> list[dict]:
    return [
        {
            'id': 'SEARCH',
            'canal': 'Search Ads',
            'funil': 'conversão',
            'min': 6,
            'max': 26,
            'receita': 3.2,
            'saturacao': 0.46,
            'risco': 0.34,
        },
        {
            'id': 'CRM',
            'canal': 'CRM e e-mail',
            'funil': 'retenção',
            'min': 3,
            'max': 16,
            'receita': 4.1,
            'saturacao': 0.38,
            'risco': 0.16,
        },
        {
            'id': 'SEO',
            'canal': 'Conteúdo SEO',
            'funil': 'aquisição',
            'min': 5,
            'max': 24,
            'receita': 2.55,
            'saturacao': 0.22,
            'risco': 0.18,
        },
        {
            'id': 'CRO',
            'canal': 'Otimização de conversão',
            'funil': 'conversão',
            'min': 4,
            'max': 18,
            'receita': 4.35,
            'saturacao': 0.24,
            'risco': 0.14,
        },
    ]


def test_healthcheck_retorna_ok() -> None:
    resposta = client.get('/api/health')

    assert resposta.status_code == 200
    assert resposta.json() == {'status': 'ok'}


def test_otimizar_retorna_plano_valido() -> None:
    resposta = client.post(
        '/api/otimizar',
        json={
            'canais': canais_exemplo(),
            'config': {
                'budget': 45,
                'population': 30,
                'generations': 8,
                'offspring': 30,
                'crossover': 0.68,
                'mutation': 0.32,
                'riskWeight': 0.55,
                'seed': 7,
            },
        },
    )

    corpo = resposta.json()

    assert resposta.status_code == 200
    assert corpo['metricas']['lucro'] > 0
    assert sum(corpo['alocacao']) == 45
    assert len(corpo['plano']) == 4
    assert corpo['fronteira']
    assert len(corpo['historico']) == 9


def test_otimizar_rejeita_orcamento_inviavel() -> None:
    resposta = client.post(
        '/api/otimizar',
        json={
            'canais': canais_exemplo(),
            'config': {
                'budget': 3,
                'population': 30,
                'generations': 8,
                'offspring': 30,
                'crossover': 0.68,
                'mutation': 0.32,
                'riskWeight': 0.55,
                'seed': 7,
            },
        },
    )

    assert resposta.status_code == 422
