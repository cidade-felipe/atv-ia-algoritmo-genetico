# Algoritmo genetico para otimizacao de mix de marketing

Este projeto implementa um exemplo de algoritmo genetico aplicado a uma decisao realista de negocio: distribuir um orcamento limitado entre varios canais de marketing.

A pergunta central do projeto e:

```text
Dado um orcamento fixo, quanto devo investir em cada canal para aumentar lucro
estimado sem concentrar risco demais?
```

Essa pergunta aparece com frequencia em areas de marketing, growth, e-commerce, SaaS e planejamento comercial. Na pratica, uma empresa raramente decide apenas qual canal e melhor. Ela precisa decidir quanto investir em cada canal, respeitar limites operacionais e equilibrar retorno, risco e diversificacao.

## Problema modelado

O projeto simula uma empresa com R$ 100 mil para investir em 12 canais de marketing, como Search Ads, CRM, SEO, TikTok Ads, LinkedIn Ads, Retargeting, Webinars e CRO.

Cada canal possui caracteristicas proprias:

- investimento minimo, porque alguns canais precisam de verba minima para operar;
- investimento maximo, porque todo canal tem capacidade, audiencia ou limite de
  eficiencia;
- receita esperada por R$ 1 mil investidos;
- saturacao, que reduz o retorno marginal quando o investimento cresce demais;
- risco, que representa incerteza, volatilidade ou dependencia operacional;
- etapa do funil, como aquisicao, conversao, nutricao ou retencao.

Fato: o dataset deste projeto e simulado, entao os resultados nao sao uma
recomendacao real de midia.

Inferencia: apesar dos dados serem simulados, a estrutura do problema e bem parecida com decisoes reais de alocacao de verba.

Opiniao tecnica: esse problema e melhor para demonstrar algoritmos geneticos do que uma otimizacao matematica abstrata, porque mostra impacto direto em receita, risco e eficiencia operacional.

## O que o algoritmo decide

Cada solucao candidata e um plano de investimento. O algoritmo precisa definir quanto dinheiro vai para cada canal.

Exemplo simplificado:

```text
Search Ads: R$ 10 mil
CRM e email: R$ 10 mil
Conteudo SEO: R$ 12 mil
CRO: R$ 17 mil
...
```

No codigo, esse plano e representado como uma lista de inteiros:

```text
[10, 8, 10, 12, 3, 5, 5, 13, 4, 8, 5, 17]
```

Cada posicao da lista e um gene. Cada gene representa o investimento, em milhares de reais, em um canal.

## Objetivos da otimizacao

O projeto usa uma otimizacao multiobjetivo. Em vez de tentar produzir uma unica resposta absoluta, o algoritmo procura planos que equilibram dois objetivos:

1. maximizar lucro estimado;
2. minimizar risco ponderado.

O lucro estimado considera:

- receita esperada por canal;
- perda de eficiencia causada por saturacao;
- sinergias entre canais;
- custo do investimento.

O risco ponderado considera quanto dinheiro foi colocado em canais mais
arriscados:

```text
risco_ponderado = soma(investimento_do_canal * risco_do_canal)
```

Impacto pratico: isso evita uma recomendacao ingenua que investe tudo no canal com maior retorno medio, mas ignora saturacao, incerteza e dependencia excessiva de poucos canais.

## Restricoes do problema

Todo plano gerado precisa obedecer a tres regras:

- a soma dos investimentos precisa ser exatamente R$ 100 mil;
- nenhum canal pode receber menos que seu investimento minimo;
- nenhum canal pode receber mais que seu investimento maximo.

Essas restricoes importam porque, em um ambiente real, um plano matematicamente bonito pode ser impossivel de executar. Por exemplo, um canal pode exigir verba minima contratual, enquanto outro pode nao conseguir absorver mais investimento sem perder eficiencia.

## Por que usar algoritmo genetico

Uma busca manual seria limitada. Uma busca exaustiva tambem fica ruim conforme o numero de canais, restricoes e faixas de investimento cresce.

O algoritmo genetico resolve isso explorando muitas combinacoes de investimento sem testar todas as possibilidades. Ele cria uma populacao de planos, seleciona os melhores, combina partes de planos bons e aplica pequenas mutacoes para encontrar alternativas melhores.

Fato: algoritmos geneticos nao garantem sempre o otimo global.

Opiniao tecnica: para esse tipo de problema com restricoes, trade-offs e espaco grande de combinacoes, eles sao uma boa escolha didatica e uma heuristica pratica interessante.

## Biblioteca usada

Fato: existem bibliotecas especificas para algoritmos geneticos e computacao evolutiva em Python. Exemplos conhecidos sao `DEAP`, `PyGAD`, `inspyred` e  `pymoo`.

Este projeto usa `DEAP`.

O `DEAP` foi escolhido porque permite configurar:

- individuos;
- funcao fitness;
- selecao;
- cruzamento;
- mutacao;
- otimizacao multiobjetivo com NSGA-II.

## Como o DEAP entra no projeto

O projeto usa NSGA-II para montar uma fronteira de Pareto. Essa fronteira contem planos que representam bons compromissos entre lucro e risco.

Operadores usados:

- selecao: `tools.selNSGA2`;
- cruzamento: `tools.cxTwoPoint`, seguido de reparo;
- mutacao: redistribuicao de verba entre canais;
- fitness: `(lucro_estimado, risco_ponderado)`, maximizando lucro e minimizando
  risco.

O reparo e essencial. Depois do cruzamento ou da mutacao, um individuo pode violar o orcamento ou os limites por canal. A funcao de reparo ajusta o plano para que ele volte a ser executavel.

## Como interpretar o resultado

O algoritmo gera um plano recomendado, mas tambem gera uma fronteira de Pareto.

Isso significa que existem varios planos bons, cada um com uma troca diferente entre retorno e risco. Um plano mais agressivo pode ter lucro maior, mas tambem risco maior. Um plano mais conservador pode reduzir risco, mas abrir mao de parte do retorno esperado.

Impacto pratico: essa visualizacao ajuda uma pessoa de negocio a escolher uma estrategia alinhada ao momento da empresa. Uma startup buscando crescimento pode preferir mais risco. Uma empresa com caixa apertado pode preferir previsibilidade.

## Estrutura

```text
.
├── data/
│   └── canais_marketing.csv
├── documents/
│   └── source/
│       └── AlgoritmoGenetico.pdf
├── src/
│   ├── __init__.py
│   └── algoritmo_genetico_marketing.py
├── tests/
│   └── test_algoritmo_genetico_marketing.py
├── pytest.ini
├── requirements.txt
├── README.md
└── codex.md
```

## Como rodar

Crie o ambiente virtual na raiz do projeto:

```powershell
python -m venv venv
```

Ative o ambiente:

```powershell
.\venv\Scripts\Activate.ps1
```

Instale as dependencias:

```powershell
python -m pip install -r requirements.txt
```

Execute o exemplo:

```powershell
python src\algoritmo_genetico_marketing.py
```

O script gera arquivos na pasta `outputs/`:

- `plano_marketing_otimizado.csv`, plano recomendado por canal;
- `fronteira_pareto.html`, grafico lucro versus risco;
- `alocacao_orcamento.html`, distribuicao do orcamento recomendado;
- `resumo_execucao.txt`, resumo textual da execucao.

## Rodando os testes

```powershell
pytest
```

Os testes verificam:

- validacao dos dados de canais;
- rejeicao de limites inconsistentes;
- reparo de individuos que violam orcamento ou limites;
- geracao de um plano valido pelo algoritmo;
- existencia da fronteira de Pareto;
- superacao de uma referencia distribuida simples.

## Principais trade-offs

Complexidade: maior do que uma regra simples de priorizar canais por ROI medio, mas mais adequada para restricoes reais e objetivos conflitantes.

Custo de implementacao: baixo a moderado, porque `DEAP` fornece a infraestrutura evolutiva.

Escalabilidade: suficiente para o exemplo didatico. Em producao, seria importante paralelizar a avaliacao e calibrar os parametros com dados historicos.

Manutencao: o codigo separa validacao, fitness, operadores geneticos, reparo e geracao de saidas.

Performance: o algoritmo nao testa todas as combinacoes possiveis, entao troca garantia de otimo global por uma busca eficiente em um espaco grande de planos.

## Limitacoes

O modelo atual e didatico. Ele nao considera sazonalidade, atribuicao real,
tempo de maturacao de canais, restricoes contratuais detalhadas, incerteza por cenario ou efeitos de canibalizacao entre canais.

Para uso em producao, seria necessario calibrar o retorno com dados reais,
monitorar diferenca entre previsto e realizado e revisar periodicamente os
parametros do modelo.
