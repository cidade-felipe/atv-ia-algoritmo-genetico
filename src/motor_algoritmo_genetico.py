from __future__ import annotations

import random
from dataclasses import dataclass
from pathlib import Path
from statistics import mean
from typing import Sequence

import pandas as pd
from deap import algorithms, base, creator, tools


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
        if canal_a not in indice_por_id or canal_b not in indice_por_id:
            continue

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
        destinos_validos = [indice for indice in destinos if indice != origem]
        if not destinos_validos:
            break

        destino = random.choice(destinos_validos)
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

    linhas.extend(
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
        for investimento, receita, canal in zip(
            alocacao, receitas, canais.itertuples(index=False)
        )
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
