from __future__ import annotations

from pathlib import Path
from typing import Annotated

import pandas as pd
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, ConfigDict, Field

from src.algoritmo_genetico_marketing import (
    ConfigMarketingAG,
    ResultadoMarketingAG,
    calcular_receitas_por_canal,
    executar_algoritmo_genetico,
    validar_canais,
)


RAIZ_PROJETO = Path(__file__).resolve().parents[1]
PASTA_INTERFACE = RAIZ_PROJETO / 'interface'


class CanalEntrada(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    id: str | None = None
    canal: Annotated[str, Field(min_length=1)]
    funil: Annotated[str, Field(min_length=1)]
    minimo: Annotated[int, Field(alias='min', ge=0)]
    maximo: Annotated[int, Field(alias='max', ge=0)]
    receita: Annotated[float, Field(gt=0)]
    saturacao: Annotated[float, Field(ge=0, le=1)]
    risco: Annotated[float, Field(ge=0, le=1)]


class ConfigEntrada(BaseModel):
    budget: Annotated[int, Field(gt=0, le=10000)]
    population: Annotated[int, Field(ge=20, le=500)]
    generations: Annotated[int, Field(ge=5, le=300)]
    offspring: Annotated[int, Field(ge=20, le=500)]
    crossover: Annotated[float, Field(ge=0, le=1)]
    mutation: Annotated[float, Field(ge=0, le=1)]
    riskWeight: Annotated[float, Field(ge=0, le=10)]
    seed: int = 42


class OtimizacaoEntrada(BaseModel):
    canais: Annotated[list[CanalEntrada], Field(min_length=2, max_length=80)]
    config: ConfigEntrada


def criar_app() -> FastAPI:
    app = FastAPI(
        title='Otimizador de Mix de Marketing',
        version='1.0.0',
    )

    app.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=False,
        allow_methods=['*'],
        allow_headers=['*'],
    )

    if (PASTA_INTERFACE / 'assets').exists():
        app.mount(
            '/assets',
            StaticFiles(directory=PASTA_INTERFACE / 'assets'),
            name='assets',
        )

    @app.get('/')
    def interface() -> FileResponse:
        caminho = PASTA_INTERFACE / 'index.html'
        if not caminho.exists():
            raise HTTPException(status_code=404, detail='Interface nao encontrada.')
        return FileResponse(caminho)

    @app.get('/api/health')
    def healthcheck() -> dict[str, str]:
        return {'status': 'ok'}

    @app.post('/api/otimizar')
    def otimizar(entrada: OtimizacaoEntrada) -> dict:
        try:
            canais = montar_dataframe_canais(entrada.canais)
            validar_canais(canais)
            config = ConfigMarketingAG(
                orcamento_mil=entrada.config.budget,
                tamanho_populacao=entrada.config.population,
                geracoes=entrada.config.generations,
                descendentes_por_geracao=entrada.config.offspring,
                taxa_crossover=entrada.config.crossover,
                taxa_mutacao=entrada.config.mutation,
                peso_risco_decisao=entrada.config.riskWeight,
                semente=entrada.config.seed,
            )
            resultado = executar_algoritmo_genetico(canais, config)
        except ValueError as erro:
            raise HTTPException(status_code=422, detail=str(erro)) from erro
        except RuntimeError as erro:
            raise HTTPException(status_code=422, detail=str(erro)) from erro

        return serializar_resultado(resultado, canais)

    return app


def montar_dataframe_canais(canais: list[CanalEntrada]) -> pd.DataFrame:
    linhas = []
    ids_usados: set[str] = set()

    for indice, canal in enumerate(canais, start=1):
        canal_id = (canal.id or f'CANAL_{indice}').strip().upper().replace(' ', '_')
        if canal_id in ids_usados:
            canal_id = f'{canal_id}_{indice}'
        ids_usados.add(canal_id)

        linhas.append(
            {
                'id': canal_id,
                'canal': canal.canal.strip(),
                'categoria': canal.funil.strip(),
                'funil': canal.funil.strip(),
                'investimento_min_mil': canal.minimo,
                'investimento_max_mil': canal.maximo,
                'receita_por_mil': canal.receita,
                'saturacao': canal.saturacao,
                'risco': canal.risco,
            }
        )

    return pd.DataFrame(linhas)


def serializar_resultado(resultado: ResultadoMarketingAG, canais: pd.DataFrame) -> dict:
    receitas = calcular_receitas_por_canal(resultado.plano_recomendado, canais)
    ids_por_canal = {
        linha.canal: linha.id
        for linha in canais.itertuples(index=False)
    }
    plano = []

    for linha in resultado.plano_detalhado.itertuples(index=False):
        plano.append(
            {
                'id': ids_por_canal.get(linha.canal, linha.canal),
                'canal': linha.canal,
                'categoria': linha.categoria,
                'funil': linha.funil,
                'investimento': int(linha.investimento_mil),
                'receita': float(linha.receita_estimada_mil),
                'lucroBruto': float(linha.lucro_bruto_mil),
                'risco': float(linha.risco_ponderado_mil),
            }
        )

    return {
        'metricas': {
            'investimento': float(resultado.metricas.investimento_total_mil),
            'receita': float(resultado.metricas.receita_estimada_mil),
            'lucro': float(resultado.metricas.lucro_estimado_mil),
            'risco': float(resultado.metricas.risco_ponderado_mil),
            'sinergia': float(resultado.metricas.sinergia_mil),
            'score': (
                float(resultado.metricas.lucro_estimado_mil)
                - resultado.config.peso_risco_decisao * float(resultado.metricas.risco_ponderado_mil)
            ),
        },
        'plano': plano,
        'fronteira': normalizar_records(resultado.fronteira_pareto.to_dict(orient='records')),
        'historico': normalizar_records(resultado.historico.to_dict(orient='records')),
        'alocacao': [int(valor) for valor in resultado.plano_recomendado],
        'receitasPorCanal': [float(valor) for valor in receitas],
    }


def normalizar_records(records: list[dict]) -> list[dict]:
    normalizados = []
    for record in records:
        normalizados.append(
            {
                chave: valor.item() if hasattr(valor, 'item') else valor
                for chave, valor in record.items()
            }
        )
    return normalizados


app = criar_app()
