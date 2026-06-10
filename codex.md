# Documentacao tecnica detalhada do projeto

## Visao geral

Este projeto implementa um exemplo didatico de algoritmo genetico aplicado a
alocacao de orcamento de marketing. A versao atual substitui o exemplo anterior
de roteirizacao de entregas por um problema menos comum em aulas introdutorias:
decidir quanto investir em diferentes canais de marketing respeitando um
orcamento fixo, limites por canal, retorno esperado, saturacao, risco e sinergias
entre canais.

O projeto foi inspirado pelo material em
`documents/source/AlgoritmoGenetico.pdf`. O PDF apresenta algoritmos geneticos
como tecnicas de busca e otimizacao inspiradas na evolucao natural, destacando
populacao, funcao fitness, selecao, cruzamento e mutacao. A implementacao atual
mantem esses conceitos, mas usa uma biblioteca especializada para executar o
processo evolutivo.

## Uso de biblioteca especifica

Fato: existem bibliotecas especificas para algoritmos geneticos e computacao
evolutiva em Python. Exemplos conhecidos incluem `DEAP`, `PyGAD`, `inspyred` e
`pymoo`.

Fato: este projeto usa `DEAP`.

Opiniao tecnica: `DEAP` foi escolhida porque e uma biblioteca madura, flexivel e
muito usada para prototipos evolutivos. Ela permite configurar individuos,
fitness, operadores de selecao, cruzamento e mutacao sem esconder totalmente o
funcionamento do algoritmo. Isso e bom para uma atividade de Inteligencia
Artificial, porque ainda da para explicar o que acontece em cada etapa.

## Problema modelado

A empresa simulada possui R$ 100 mil para investir em 12 canais de marketing. O
objetivo nao e simplesmente jogar todo o dinheiro no canal com maior retorno
medio, porque canais saturam, alguns sao mais arriscados e certas combinacoes
geram sinergia.

O algoritmo busca planos de investimento que equilibrem dois objetivos:

1. maximizar lucro estimado;
2. minimizar risco ponderado.

Esse formato e mais realista do que um objetivo unico. Em uma empresa real, o
plano com maior lucro esperado pode ser arriscado demais, enquanto o plano mais
seguro pode deixar receita na mesa. A fronteira de Pareto mostra alternativas
competitivas para apoiar decisao.

## Dados de entrada

O arquivo `data/canais_marketing.csv` contem os canais simulados.

Colunas:

- `id`: identificador unico do canal.
- `canal`: nome legivel do canal.
- `categoria`: agrupamento de marketing.
- `funil`: etapa principal do funil.
- `investimento_min_mil`: investimento minimo em milhares de reais.
- `investimento_max_mil`: investimento maximo em milhares de reais.
- `receita_por_mil`: receita esperada por R$ 1 mil investidos antes da saturacao.
- `saturacao`: intensidade de perda de eficiencia conforme o investimento cresce.
- `risco`: risco relativo entre 0 e 1.

Antes da execucao, o codigo valida:

- colunas obrigatorias;
- base nao vazia;
- valores nulos;
- IDs duplicados;
- campos numericos;
- limites minimos e maximos coerentes;
- receita positiva;
- saturacao entre 0 e 1;
- risco entre 0 e 1;
- orcamento total dentro do minimo e maximo viavel.

Fato: essa validacao esta implementada em `validar_canais` e
`validar_orcamento`.

Impacto pratico: em ambiente real, validacao de entrada reduz risco de gerar um
plano impossivel, como investir abaixo do minimo contratual de um canal ou acima
da capacidade operacional combinada.

## Representacao dos individuos

Cada individuo e uma lista de inteiros. Cada posicao representa um canal e o
valor representa o investimento naquele canal em milhares de reais.

Exemplo:

```text
[13, 9, 12, 16, 4, 8, 3, 11, 5, 10, 2, 7]
```

Nesse exemplo, se a primeira posicao for `SEARCH`, o algoritmo esta investindo
R$ 13 mil em Search Ads. A soma de todos os genes precisa ser exatamente igual ao
orcamento definido em `ConfigMarketingAG.orcamento_mil`.

## Funcao fitness

O projeto usa fitness multiobjetivo com `DEAP`:

```python
creator.create('FitnessMarketing', base.Fitness, weights=(1.0, -1.0))
```

O primeiro objetivo e maximizar lucro estimado. O segundo objetivo e minimizar
risco ponderado.

O lucro estimado considera:

- receita por canal;
- perda de eficiencia por saturacao;
- sinergias entre pares de canais;
- investimento total.

O risco ponderado considera:

```text
risco_ponderado = soma(investimento_do_canal * risco_do_canal)
```

Inferencia: o modelo de receita e simplificado. Ele serve para demonstrar a
tecnica, nao para substituir um modelo econometrico real.

## Saturacao

Cada canal perde eficiencia quando recebe investimento perto do seu limite
maximo. Isso evita uma solucao ingenua que colocaria quase todo o dinheiro no
canal de maior retorno unitario.

Opiniao tecnica: incluir saturacao deixa o exemplo mais proximo de marketing
real. Na pratica, canais como midia paga tendem a sofrer queda de retorno
marginal quando se aumenta muito o investimento.

## Sinergias

O projeto define algumas combinacoes que geram bonus de receita:

- Search Ads com Conteudo SEO;
- Retargeting com CRM;
- Programa de indicacao com CRO;
- LinkedIn Ads com Webinars B2B;
- YouTube Shorts com TikTok Ads;
- Promocoes marketplace com Search Ads.

Inferencia: essas sinergias sao plausiveis, mas simuladas. Em uma empresa real,
elas deveriam ser estimadas com dados historicos, experimentos ou modelos
estatisticos.

## Operadores geneticos

### Selecao

A selecao usa NSGA-II (`tools.selNSGA2`), uma tecnica adequada para problemas
multiobjetivo. Ela preserva individuos nao dominados e usa diversidade para
manter diferentes solucoes na fronteira de Pareto.

### Cruzamento

O cruzamento usa `tools.cxTwoPoint`, seguido de reparo. O reparo e necessario
porque um crossover simples pode quebrar a soma do orcamento ou violar limites
minimos e maximos por canal.

### Mutacao

A mutacao redistribui verba entre canais. Ela remove uma quantidade pequena de
um canal que esta acima do minimo e transfere para outro canal que ainda esta
abaixo do maximo. Depois disso, o individuo tambem passa por reparo.

### Reparo

A funcao `reparar_alocacao` garante:

- genes inteiros;
- respeito aos limites minimo e maximo;
- soma igual ao orcamento.

Essa etapa e fundamental. Sem ela, o algoritmo poderia gerar planos
matematicamente invalidos, mesmo que os operadores geneticos estivessem
funcionando corretamente.

## Estrutura dos arquivos

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

## Dependencias

As dependencias estao em `requirements.txt`:

- `deap`: biblioteca de algoritmos geneticos e computacao evolutiva.
- `pandas`: leitura, validacao e manipulacao tabular.
- `plotly`: visualizacoes interativas em HTML.
- `pytest`: testes automatizados.

O projeto deve usar ambiente virtual chamado `venv`, criado com:

```powershell
python -m venv venv
```

## Execucao

Com o ambiente virtual ativo:

```powershell
python src\algoritmo_genetico_marketing.py
```

O script gera:

- `outputs/plano_marketing_otimizado.csv`;
- `outputs/fronteira_pareto.html`;
- `outputs/alocacao_orcamento.html`;
- `outputs/resumo_execucao.txt`.

A pasta `outputs/` fica ignorada pelo Git porque contem artefatos gerados.

## Saidas

`plano_marketing_otimizado.csv` mostra o plano recomendado com investimento,
receita estimada, lucro bruto e risco ponderado por canal.

`fronteira_pareto.html` mostra os planos nao dominados em um grafico de lucro
versus risco. Esse grafico ajuda a comparar estrategias mais agressivas e mais
conservadoras.

`alocacao_orcamento.html` mostra a distribuicao do orcamento recomendado.

`resumo_execucao.txt` traz parametros, metricas agregadas e o plano final.

## Testes

Os testes ficam em `tests/test_algoritmo_genetico_marketing.py`.

Eles verificam:

- carregamento e validacao dos dados;
- rejeicao de limites inconsistentes;
- reparo de individuos invalidos;
- plano final respeitando orcamento;
- fronteira de Pareto nao vazia;
- historico com quantidade esperada de geracoes;
- comparacao contra uma referencia distribuida simples.

Fato: os testes nao provam que o algoritmo encontrou o otimo global.

Opiniao tecnica: os testes cobrem os riscos mais importantes para este tipo de
exemplo, que sao violar restricoes, quebrar dados de entrada ou perder o
comportamento evolutivo esperado.

## Trade-offs tecnicos

Complexidade: maior do que uma heuristica gulosa, mas justificada por ser um
problema multiobjetivo com restricoes.

Custo de implementacao: moderado-baixo, porque `DEAP` fornece a infraestrutura
evolutiva.

Escalabilidade: suficiente para o dataset didatico. Para uso real, a avaliacao
de fitness poderia ser paralelizada e calibrada com dados historicos.

Manutencao: a separacao em funcoes torna simples trocar a funcao de receita,
adicionar canais, mudar parametros ou testar outro operador genetico.

Performance: o algoritmo nao enumera todas as combinacoes possiveis. Ele troca
garantia de otimalidade global por busca eficiente em um espaco grande de
solucoes.

## Riscos e cuidados

Overfitting: se parametros e retornos forem calibrados em uma janela historica
muito especifica, o plano pode nao generalizar para novas campanhas.

Data leakage: em um modelo real, seria preciso garantir que dados futuros nao
entrem na estimativa de retorno.

Viés: canais com melhor mensuracao podem parecer melhores do que canais de marca
cujo impacto e mais dificil de atribuir.

Generalizacao: o dataset atual e simulado. Em producao, seria necessario usar
dados reais de spend, receita incremental, atribuicao, sazonalidade e restricoes
contratuais.

Monitoramento: uma versao real deveria acompanhar receita realizada, CAC, ROAS,
payback, risco de concentracao e diferenca entre previsto e realizado.

## Possiveis evolucoes

- Usar dados historicos reais de campanhas.
- Adicionar incerteza por canal e simular cenarios pessimista, medio e otimista.
- Incluir restricoes por categoria, como limite maximo em midia paga.
- Criar dashboard interativo para ajustar orcamento e aversao a risco.
- Comparar `DEAP` com `PyGAD` ou `pymoo`.
- Adicionar otimizacao de tres objetivos, lucro, risco e diversificacao.
- Criar testes de sensibilidade para entender quais canais mudam mais quando o
  orcamento aumenta ou diminui.

## Estado atual

O projeto esta funcional com `DEAP`, ambiente virtual `venv`, dados simulados,
validacoes, algoritmo genetico multiobjetivo, geracao de CSV, graficos
interativos e testes automatizados.

## Atualizacao de documentacao em 10_06_2026

O `README.md` foi reestruturado para explicar melhor o problema antes da solucao
tecnica. A nova versao descreve com mais clareza:

- o cenario de negocio de alocacao de orcamento de marketing;
- a pergunta central que o algoritmo tenta responder;
- as variaveis de decisao;
- os objetivos de lucro e risco;
- as restricoes de orcamento, minimo e maximo por canal;
- o motivo de usar algoritmo genetico;
- o papel da biblioteca `DEAP`;
- a interpretacao da fronteira de Pareto;
- as limitacoes do modelo didatico.

Essa mudanca nao alterou a implementacao Python nem os dados de entrada. O foco
foi tornar o projeto mais claro para apresentacao, avaliacao academica e leitura
por pessoas que querem entender o problema de negocio antes dos detalhes de
codigo.
