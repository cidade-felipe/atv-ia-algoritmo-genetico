from __future__ import annotations

from pathlib import Path

try:
    from src.motor_algoritmo_genetico import (
        ResultadoMarketingAG,
        carregar_canais,
        executar_algoritmo_genetico,
    )
    from src.relatorios_marketing import (
        gerar_grafico_alocacao,
        gerar_grafico_fronteira,
        salvar_resumo_execucao,
    )
except ModuleNotFoundError:  # pragma: no cover - compatibilidade com execucao direta
    from motor_algoritmo_genetico import (
        ResultadoMarketingAG,
        carregar_canais,
        executar_algoritmo_genetico,
    )
    from relatorios_marketing import (
        gerar_grafico_alocacao,
        gerar_grafico_fronteira,
        salvar_resumo_execucao,
    )


def caminho_raiz_projeto() -> Path:
    return Path(__file__).resolve().parents[1]


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
