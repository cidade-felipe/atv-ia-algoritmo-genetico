# Documentacao tecnica detalhada do projeto

## Visao geral

O projeto passou a usar o nome `MixGen`, com o subtitulo
`Otimizador evolutivo de mix de marketing`.

Fato: a aplicacao Streamlit foi publicada em:

```text
https://mixgen.streamlit.app/
```

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
`validar_orcamento`, dentro de `src/motor_algoritmo_genetico.py`.

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

## Motor do algoritmo genetico

O motor do algoritmo genetico foi separado no arquivo
`src/motor_algoritmo_genetico.py`.

Esse arquivo deve ser considerado a parte central do projeto. Ele nao gera HTML,
nao escreve CSS, nao monta telas e nao depende das interfaces. A responsabilidade
dele e receber uma base de canais, receber uma configuracao de execucao e
devolver um `ResultadoMarketingAG` com:

- plano recomendado;
- metricas consolidadas;
- historico das geracoes;
- fronteira de Pareto;
- plano detalhado por canal;
- configuracao usada.

Fato: a separacao foi feita para deixar a explicacao principal focada no
algoritmo genetico em si, principalmente populacao, individuos, fitness,
sinergias, operadores geneticos, reparo e selecao.

Opiniao tecnica: essa arquitetura e mais profissional porque reduz acoplamento.
O mesmo motor pode ser usado pela API FastAPI, pela interface Streamlit, pelos
testes automatizados e pelo script de relatorios sem duplicar a regra de
otimizacao.

### Configuracao do algoritmo

`ConfigMarketingAG` concentra os parametros evolutivos:

- `orcamento_mil`: soma total que todo individuo precisa respeitar.
- `tamanho_populacao`: quantidade de planos mantidos em cada geracao.
- `geracoes`: quantidade de ciclos evolutivos.
- `descendentes_por_geracao`: quantidade de novos individuos criados por ciclo.
- `taxa_crossover`: probabilidade de gerar descendentes por cruzamento.
- `taxa_mutacao`: probabilidade de gerar descendentes por mutacao.
- `peso_risco_decisao`: peso usado depois da evolucao para escolher um plano
  recomendado dentro da fronteira de Pareto.
- `semente`: valor que torna a execucao reprodutivel.

Fato: o `DEAP` usa esses parametros na toolbox criada por `criar_toolbox`.

### Populacao inicial

A funcao `gerar_alocacao_inicial` cria individuos viaveis desde o inicio. Ela
parte dos investimentos minimos de todos os canais e distribui o restante do
orcamento aleatoriamente, sempre respeitando o maximo de cada canal.

Impacto pratico: com isso, a primeira populacao ja nasce executavel. O algoritmo
nao perde tempo avaliando planos impossiveis, como orcamentos abaixo do minimo
contratual ou acima da capacidade de um canal.

### Fitness no motor

A funcao `avaliar_individuo` chama `calcular_metricas_plano` e devolve:

```text
(lucro_estimado_mil, risco_ponderado_mil)
```

No `DEAP`, o fitness foi configurado com pesos `(1.0, -1.0)`. Isso significa:

- maximizar lucro;
- minimizar risco.

O lucro estimado e calculado como:

```text
lucro = receita_total_com_sinergia - investimento_total
```

O risco ponderado e calculado como:

```text
risco_ponderado = soma(investimento_do_canal * risco_do_canal)
```

Fato: por ser multiobjetivo, o algoritmo nao procura apenas uma solucao unica.
Ele constroi uma fronteira de Pareto com diferentes compromissos entre retorno e
risco.

### Saturacao no motor

A funcao `calcular_receitas_por_canal` reduz o retorno marginal quando um canal
recebe investimento proximo do seu limite maximo. O fator de saturacao evita que
o algoritmo concentre verba demais em um canal so porque ele possui boa receita
media.

Opiniao tecnica: essa escolha melhora o realismo do exemplo. Em marketing,
principalmente em midia paga, aumentar verba indefinidamente costuma reduzir a
eficiencia marginal.

### Sinergias no motor

A funcao `calcular_sinergia` aplica bonus quando dois canais complementares
recebem investimento no mesmo plano. O bonus usa o menor valor de receita entre
os dois canais como base, porque a sinergia fica limitada pelo lado mais fraco do
par.

Exemplos de pares:

- Search Ads com Conteudo SEO;
- Retargeting com CRM;
- Programa de indicacao com CRO;
- LinkedIn Ads com Webinars B2B;
- YouTube Shorts com TikTok Ads;
- Promocoes marketplace com Search Ads.

Inferencia: essas sinergias sao plausiveis em marketing, mas continuam sendo
simuladas. Em um uso real, elas deveriam ser calibradas com experimento,
historico de campanhas ou modelo estatistico.

### Cruzamento no motor

O cruzamento usa `tools.cxTwoPoint`. Esse operador combina trechos de dois
planos, criando descendentes que herdam partes de solucoes diferentes.

Depois do cruzamento, `cruzamento_com_reparo` chama `reparar_alocacao`. Isso e
necessario porque a simples troca de genes pode quebrar a soma do orcamento ou
ultrapassar limites por canal.

### Mutacao no motor

A mutacao usa `mutacao_redistribuir`. Ela escolhe um canal de origem que esta
acima do minimo e transfere uma pequena quantidade de verba para outro canal que
ainda esta abaixo do maximo.

Impacto pratico: a mutacao introduz exploracao. Sem ela, a populacao poderia
ficar presa em combinacoes parecidas demais depois de algumas geracoes.

### Reparo no motor

`reparar_alocacao` e uma das funcoes mais importantes do motor. Ela garante:

- valores inteiros;
- investimento minimo por canal;
- investimento maximo por canal;
- soma final exatamente igual ao orcamento.

Opiniao tecnica: para este problema, reparar individuos e melhor do que apenas
descartar individuos invalidos. Descartar desperdicaria muito processamento,
principalmente porque cruzamento e mutacao frequentemente alteram a soma total
do orcamento.

### Selecao e fronteira de Pareto no motor

A selecao usa `tools.selNSGA2`. O NSGA-II preserva solucoes nao dominadas e
mantem diversidade entre alternativas. O resultado e uma fronteira de Pareto,
onde cada plano representa uma troca diferente entre lucro e risco.

A funcao `escolher_plano_recomendado` escolhe uma solucao dentro da fronteira
usando:

```text
score = lucro_estimado - peso_risco_decisao * risco_ponderado
```

Fato: esse score nao substitui a otimizacao multiobjetivo. Ele e usado somente
depois da evolucao para selecionar um plano recomendado para exibicao.

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
│   ├── api.py
│   ├── algoritmo_genetico_marketing.py
│   ├── motor_algoritmo_genetico.py
│   └── relatorios_marketing.py
├── tests/
│   ├── test_api.py
│   └── test_algoritmo_genetico_marketing.py
├── interface/
│   ├── index.html
│   └── assets/
│       ├── css/
│       │   └── app.css
│       └── js/
│           ├── app.js
│           └── plotly.min.js
├── streamlit_app.py
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

## Interface interativa

Foi adicionada uma interface web estatica em `interface/index.html`.

A interface permite alterar os principais parametros do problema diretamente no
navegador:

- orcamento total;
- tamanho da populacao;
- quantidade de geracoes;
- descendentes por geracao;
- taxa de crossover;
- taxa de mutacao;
- peso do risco;
- semente aleatoria;
- minimo, maximo, receita, saturacao e risco de cada canal.

Ela tambem permite adicionar canais, restaurar a base original, calcular o plano
recomendado, gerar graficos e exportar o resultado em CSV.

Estrutura:

```text
interface/
├── index.html
└── assets/
    ├── css/
    │   └── app.css
    └── js/
        ├── app.js
        └── plotly.min.js
```

`index.html` contem a estrutura da tela. `app.css` contem o layout e a aparencia.
`app.js` contem a logica interativa, incluindo leitura dos inputs, validacao
visual, chamada da API, renderizacao dos resultados, chamada dos graficos Plotly
e exportacao de CSV.

Fato: a interface agora consome o backend Python em `POST /api/otimizar`.

Opiniao tecnica: essa arquitetura e mais sustentavel do que manter o algoritmo
replicado em JavaScript, porque centraliza a regra de otimizacao no Python e
deixa o front-end responsavel por coleta de dados, exibicao de resultados e
graficos.

## Backend Python

Foi criado o arquivo `src/api.py` com uma API FastAPI.

Endpoints:

- `GET /`: serve `interface/index.html`.
- `GET /api/health`: retorna status simples da API.
- `POST /api/otimizar`: recebe canais e parametros, executa o algoritmo genetico
  com o motor em `src/motor_algoritmo_genetico.py` e devolve metricas, plano
  recomendado, fronteira de Pareto e historico de evolucao.

Para subir o servidor:

```powershell
python -m uvicorn src.api:app --reload
```

Depois, a interface fica disponivel em:

```text
http://127.0.0.1:8000
```

O backend tambem serve os assets da interface em `/assets`, usando os arquivos em
`interface/assets/`.

## Interface Streamlit

Foi criado o arquivo `streamlit_app.py` como alternativa de interface em Python.

Para executar:

```powershell
streamlit run streamlit_app.py
```

A interface Streamlit permite:

- editar a tabela de canais com `st.data_editor`;
- alterar parametros do algoritmo na barra lateral;
- executar o algoritmo genetico com `src/motor_algoritmo_genetico.py`;
- visualizar metricas de receita, lucro, risco e sinergia;
- ver a tabela do plano recomendado;
- gerar graficos de alocacao, fronteira de Pareto e convergencia;
- baixar o plano final em CSV.

Fato: diferente da interface HTML/JS, o Streamlit chama diretamente
`executar_algoritmo_genetico`, sem passar pela API FastAPI.

Opiniao tecnica: o Streamlit e a opcao mais rapida para prototipagem e
apresentacao, porque reduz a quantidade de codigo de front-end. A interface
FastAPI + HTML/CSS/JS segue sendo mais flexivel quando o objetivo e simular uma
aplicacao web mais customizada.

## Saidas

`plano_marketing_otimizado.csv` mostra o plano recomendado com investimento,
receita estimada, lucro bruto e risco ponderado por canal.

`fronteira_pareto.html` mostra os planos nao dominados em um grafico de lucro
versus risco. Esse grafico ajuda a comparar estrategias mais agressivas e mais
conservadoras.

`alocacao_orcamento.html` mostra a distribuicao do orcamento recomendado.

`resumo_execucao.txt` traz parametros, metricas agregadas e o plano final.

### Estrutura dos relatorios HTML

Os relatorios HTML foram ajustados para separar estrutura, estilo e
comportamento:

```text
outputs/
├── assets/
│   ├── css/
│   │   └── relatorios.css
│   └── js/
│       ├── plotly.min.js
│       ├── fronteira_pareto.js
│       └── alocacao_orcamento.js
├── fronteira_pareto.html
└── alocacao_orcamento.html
```

`fronteira_pareto.html` e `alocacao_orcamento.html` ficam responsaveis apenas
pela estrutura da pagina. O visual comum fica em `relatorios.css`. A biblioteca
Plotly fica em `plotly.min.js`, e cada grafico recebe um arquivo JavaScript
proprio com os dados e a chamada de renderizacao.

Essa separacao melhora manutencao, reduz acoplamento entre layout e logica de
grafico e evita relatorios com HTML monolitico gerado diretamente por
`figura.write_html`.

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
- separacao dos relatorios HTML em arquivos externos de CSS e JavaScript.

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
Depois da refatoracao de arquitetura, a manutencao ficou ainda mais direta:
alteracoes no algoritmo ficam concentradas em `src/motor_algoritmo_genetico.py`,
alteracoes em relatorios estaticos ficam em `src/relatorios_marketing.py`, e o
script `src/algoritmo_genetico_marketing.py` apenas coordena a execucao.

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

## Atualizacao de relatorios em 11_06_2026

Os relatorios interativos deixaram de ser gerados como HTML monolitico do Plotly.
Agora a funcao de exportacao cria:

- HTML estrutural para cada relatorio;
- CSS compartilhado em `outputs/assets/css/relatorios.css`;
- biblioteca Plotly local em `outputs/assets/js/plotly.min.js`;
- JavaScript especifico por grafico em `outputs/assets/js/`.

Tambem foi adicionado teste automatizado para garantir que os HTMLs apontam para
CSS e JS externos e que os arquivos de assets sao criados corretamente.

## Atualizacao de interface em 11_06_2026

Foi criada uma interface web estatica para exploracao interativa do problema. A
tela permite editar valores dos canais e parametros do algoritmo, executar o
calculo pelo botao `Calcular`, gerar graficos pelo botao `Gerar graficos` e
exportar um CSV com o plano recomendado.

A interface usa `plotly.min.js` local, copiado para `interface/assets/js/`, para
evitar depender de internet durante apresentacoes. Essa escolha aumenta um pouco
o tamanho do projeto, mas reduz risco de falha por indisponibilidade de rede.

## Atualizacao de backend em 15_06_2026

Foi criado um backend Python com FastAPI para executar a otimizacao usada pela
interface. A versao anterior calculava no navegador com JavaScript. A nova versao
envia os dados da tela para `POST /api/otimizar`, executa o motor Python em
`src/motor_algoritmo_genetico.py` e retorna JSON com:

- metricas consolidadas;
- plano recomendado por canal;
- alocacao final;
- fronteira de Pareto;
- historico das geracoes.

Tambem foram adicionadas dependencias `fastapi`, `uvicorn` e `httpx`, alem de
testes automatizados para `GET /api/health`, sucesso em `POST /api/otimizar` e
rejeicao de orcamento inviavel.

## Atualizacao Streamlit em 15_06_2026

Foi adicionada uma interface alternativa em Streamlit no arquivo
`streamlit_app.py`. Essa versao usa diretamente o motor Python do algoritmo
genetico, sem duplicar a regra no navegador e sem exigir chamadas HTTP.

A dependencia `streamlit` foi adicionada ao `requirements.txt` e instalada no
ambiente virtual `venv`.

## Atualizacao gramatical da interface em 15_06_2026

Os textos visiveis da interface foram revisados para corrigir acentuacao,
grafia e pequenas escolhas de escrita em portugues do Brasil. A revisao incluiu:

- rotulos e botoes do HTML;
- nomes iniciais dos canais;
- opcoes de funil;
- mensagens de validacao;
- mensagens de status;
- titulos e eixos dos graficos Plotly.

Essa mudanca nao alterou a logica do algoritmo, os parametros numericos nem os
dados usados no calculo. O objetivo foi melhorar apresentacao, clareza e
qualidade visual da interface.

## Atualizacao de arquitetura em 16_06_2026

O arquivo `src/algoritmo_genetico_marketing.py` foi refatorado para separar o
motor do algoritmo genetico das partes de front-end, relatorios e orquestracao.

Nova divisao:

- `src/motor_algoritmo_genetico.py`: contem somente o algoritmo genetico e suas
  regras de negocio, incluindo validacao, individuos, fitness, saturacao,
  sinergias, populacao, cruzamento, mutacao, reparo, selecao NSGA-II, fronteira
  de Pareto e montagem do resultado.
- `src/relatorios_marketing.py`: contem somente a geracao de relatorios
  estaticos, assets de CSS, assets de JavaScript, Plotly e resumo textual.
- `src/algoritmo_genetico_marketing.py`: ficou como script de orquestracao para
  carregar o CSV, chamar o motor e gerar outputs.
- `src/api.py`: passou a importar o motor diretamente.
- `streamlit_app.py`: passou a importar o motor diretamente.
- `tests/test_algoritmo_genetico_marketing.py`: passou a testar o motor e os
  relatorios por modulos separados.

Fato: a regra evolutiva nao depende mais dos modulos de relatorio.

Inferencia: essa separacao facilita a apresentacao academica, porque a
explicacao principal pode se concentrar em `src/motor_algoritmo_genetico.py`
sem misturar detalhes de HTML, CSS, JavaScript ou Plotly.

Opiniao tecnica: essa e a melhor estrutura para evoluir o projeto. Ela reduz
risco de regressao, deixa a API e o Streamlit consumindo a mesma fonte de regra
e permite trocar a camada de apresentacao sem reescrever o algoritmo genetico.

## Correcao do funil no Streamlit em 16_06_2026

Foi corrigida a exibicao da coluna `funil` no editor de canais do Streamlit.

Fato: o arquivo `data/canais_marketing.csv` usa valores sem acento na coluna
`funil`, como `aquisicao`, `conversao`, `nutricao` e `retencao`.

Fato: a interface Streamlit estava configurando essa coluna como
`SelectboxColumn` com opcoes acentuadas, como `aquisição`, `conversão`,
`nutrição` e `retenção`. Como os valores do CSV nao batiam exatamente com as
opcoes do selectbox, o Streamlit mostrava a coluna vazia no carregamento
inicial.

A correcao manteve os valores internos iguais aos do CSV e adicionou uma funcao
de formatacao visual:

- internamente, o DataFrame continua usando `aquisicao`, `conversao`,
  `nutricao` e `retencao`;
- visualmente, o usuario ve `Aquisição`, `Conversão`, `Nutrição` e `Retenção`;
- se o CSV trouxer algum funil novo, ele tambem entra nas opcoes da coluna para
  evitar perda visual de dados.

Opiniao tecnica: essa solucao e melhor do que alterar diretamente o CSV, porque
preserva compatibilidade com o motor do algoritmo genetico e resolve o problema
na camada correta, que e a camada de apresentacao.

## Tooltips da interface Streamlit em 16_06_2026

Foram adicionados tooltips curtos na interface Streamlit para explicar os campos
destacados na tela.

Campos da barra lateral que receberam explicacao:

- `Orçamento (R$ mil)`: explica que e o valor total distribuido entre os canais.
- `População`: explica que e a quantidade de planos candidatos avaliados por
  geracao.
- `Gerações`: explica que e a quantidade de ciclos evolutivos.
- `Descendentes por geração`: explica quantos novos planos sao criados em cada
  ciclo.
- `Taxa de crossover`: explica a probabilidade de combinar dois planos.
- `Taxa de mutação`: explica a probabilidade de redistribuir verba para explorar
  alternativas.
- `Peso do risco`: explica quanto o risco pesa na escolha final do plano
  recomendado.
- `Semente aleatória`: explica que permite reproduzir a mesma sequencia
  aleatoria.

Colunas da tabela que receberam explicacao:

- `ID`;
- `Canal`;
- `Categoria`;
- `Funil`;
- `Mínimo`;
- `Máximo`;
- `Receita por R$ mil`;
- `Saturação`;
- `Risco`.

Fato: no Streamlit, os tooltips foram implementados pelo parametro `help` dos
widgets e das configuracoes de coluna do `st.data_editor`.

Opiniao tecnica: essa melhoria reduz friccao para quem esta usando a interface
pela primeira vez e ajuda a conectar cada parametro visual ao comportamento do
algoritmo genetico.

## Atualizacao dos resultados no Streamlit em 16_06_2026

A interface Streamlit foi ajustada para enriquecer a area de resultados do plano
otimizado.

Mudancas incorporadas:

- o grafico de alocacao por canal foi mantido como visao principal do plano;
- foi adicionada uma aba de alocacao por categoria, agrupando investimento e
  lucro bruto por `categoria`;
- foi adicionada uma aba de alocacao por etapa do funil, agrupando investimento
  e lucro bruto por `funil`;
- o grafico de fronteira de Pareto e o grafico de convergencia continuam
  disponiveis em abas separadas;
- alem do download em CSV, a interface passou a oferecer download em Excel
  (`.xlsx`).

Fato: a primeira implementacao do download em Excel usava
`DataFrame.to_excel(..., excel_writer=None)`. Esse uso e invalido, porque
`to_excel` precisa receber um caminho de arquivo, um buffer ou um writer.

Fato: o erro exibido na interface era:

```text
Invalid file path or buffer object type: <class 'NoneType'>
```

A correcao criou a funcao `gerar_excel_plano`, que usa `BytesIO` e
`pd.ExcelWriter` com engine `openpyxl` para gerar o arquivo Excel em memoria
antes de enviar os bytes para `st.download_button`.

Tambem foi adicionada a dependencia `openpyxl>=3.1` em `requirements.txt`,
porque ela e necessaria para criar arquivos `.xlsx` com pandas.

Opiniao tecnica: gerar o Excel em memoria e a melhor opcao para Streamlit, porque
evita criar arquivo temporario no disco, reduz risco de conflito entre usuarios e
mantem a exportacao acoplada apenas ao clique de download.

## Ajuste visual dos downloads no Streamlit em 16_06_2026

Foram analisadas novas alteracoes feitas na area de resultados da interface
Streamlit.

Fato: a interface passou a exibir a secao `Graficos` depois da tabela do plano
recomendado, separando melhor a leitura dos resultados numericos e visuais.

Fato: os botoes de download agora exportam:

- `plano_otimizado.csv`;
- `plano_otimizado.xlsx`.

Fato: os botoes estavam usando `st.columns([1, 1, 1])`, o que dividia a linha em
tres blocos iguais. Como cada botao ficava no inicio de uma coluna grande, o
botao de Excel aparecia distante do botao de CSV.

A correcao alterou o layout para colunas proporcionais menores no inicio da
linha, usando `st.columns([0.26, 0.27, 0.49], gap='small')`, e aplicou
`use_container_width=True` nos dois botoes. Assim, os botoes ficam lado a lado,
com pouco espaco entre eles, e a area restante fica como respiro a direita.

Opiniao tecnica: essa abordagem e mais simples e sustentavel do que usar CSS
customizado para esse caso. O proprio Streamlit continua controlando a
responsividade, enquanto o layout fica visualmente mais proximo do que se espera
em botoes relacionados.

## Categorias formatadas no Streamlit em 16_06_2026

Foram analisadas novas alteracoes feitas no editor de canais da interface
Streamlit.

Fato: a coluna `categoria` deixou de ser um campo de texto livre simples e passou
a usar `st.column_config.SelectboxColumn`.

Fato: foram adicionados mapas de rotulos para exibir categorias com escrita mais
amigavel na interface:

- `midia_paga` aparece como `Mídia paga`;
- `relacionamento` aparece como `Relacionamento`;
- `organico` aparece como `Orgânico`;
- `marca` aparece como `Marca`;
- `produto` aparece como `Produto`;
- `b2b` aparece como `B2B`;
- `trade` aparece como `Trade`.

A funcao `montar_opcoes_categoria` monta as opcoes do selectbox usando as
categorias conhecidas e tambem qualquer categoria nova que exista na tabela
editada. Isso evita perder valores caso a pessoa adicione uma categoria que ainda
nao esta no mapa fixo.

A funcao `formatar_categoria` cuida da exibicao visual. O valor interno continua
podendo ser `midia_paga`, mas a pessoa ve `Mídia paga` na tela.

A funcao `normalizar_canais` tambem passou a converter rotulos visuais de volta
para os identificadores internos antes de validar e executar o algoritmo. Por
exemplo, se a interface devolver `Mídia paga`, o codigo normaliza para
`midia_paga`.

Inferencia: essa mudanca foi feita para melhorar a qualidade visual da tabela e
reduzir erros de digitacao em categorias, sem alterar o CSV default
`data/canais_marketing.csv`.

Opiniao tecnica: manter o CSV com valores internos simples e fazer a traducao na
interface e uma boa decisao. Isso preserva compatibilidade com o motor do
algoritmo genetico, melhora a experiencia de uso e evita que detalhes de
apresentacao vazem para os dados base.

## Canais formatados no Streamlit em 16_06_2026

Foram analisadas novas alteracoes feitas no editor de canais da interface
Streamlit.

Fato: a coluna `canal` tambem deixou de ser apenas um campo de texto livre e
passou a usar `st.column_config.SelectboxColumn`.

Fato: foi adicionado o dicionario `CANAL_ROTULOS`, que traduz nomes internos ou
sem acentuacao para rotulos mais apresentaveis na interface. Exemplos:

- `Otimizacao de conversao` aparece como `Otimização de conversão`;
- `Programa de indicacao` aparece como `Programa de indicação`;
- `Conteudo SEO` aparece como `Conteúdo SEO`;
- `CRM e email` aparece como `CRM e Email`;
- `Promocoes marketplace` aparece como `Promoções marketplace`.

Tambem foram adicionadas as funcoes:

- `montar_opcoes_canal`, que monta as opcoes do selectbox a partir dos canais
  conhecidos e dos canais existentes na tabela editada;
- `formatar_canal`, que controla a exibicao visual do nome do canal;
- a normalizacao em `normalizar_canais`, que converte rotulos visuais de volta
  para os valores internos antes da validacao e da execucao do algoritmo.

Fato: essa mudanca segue o mesmo padrao ja usado para `funil` e `categoria`.

Inferencia: a intencao e manter o CSV default simples, sem precisar reescrever os
dados base, enquanto a interface mostra textos mais corretos e agradaveis para a
apresentacao.

Opiniao tecnica: essa separacao entre valor interno e rotulo visual e saudavel.
Ela reduz erros de digitacao, melhora a leitura da tabela e evita que ajustes de
acentuacao ou apresentacao afetem diretamente o motor do algoritmo genetico.

## Plano recomendado formatado no Streamlit em 16_06_2026

Foi melhorada a exibicao da tabela `Plano recomendado` na interface Streamlit.

Fato: anteriormente essa tabela exibia diretamente o `DataFrame`
`resultado.plano_detalhado`, com nomes tecnicos de colunas como
`investimento_mil`, `receita_estimada_mil`, `lucro_bruto_mil` e
`risco_ponderado_mil`.

Fato: foi adicionada a funcao `preparar_plano_recomendado_para_exibicao`, que
cria uma copia do plano apenas para apresentacao visual.

A exibicao agora aplica:

- `formatar_canal` na coluna de canal;
- `formatar_categoria` na coluna de categoria;
- `formatar_funil` na coluna de funil;
- renomeacao das colunas para rotulos amigaveis, como `Investimento (R$ mil)`,
  `Receita estimada (R$ mil)`, `Lucro bruto (R$ mil)` e
  `Risco ponderado (R$ mil)`;
- `st.column_config.NumberColumn` para mostrar os valores monetarios com
  prefixo `R$` e unidade `mil`.

Fato: essa formatacao afeta apenas a tabela exibida na tela. Os downloads em CSV
e XLSX continuam usando `resultado.plano_detalhado`, preservando os nomes de
colunas tecnicos e os valores internos para reuso em analises.

Opiniao tecnica: essa e a melhor separacao para este caso. A interface fica mais
clara para apresentacao, mas os dados exportados continuam previsiveis para quem
quiser abrir em outra ferramenta, automatizar analises ou comparar resultados.

## Logo do MixGen em 16_06_2026

Foi criado um logo visual para o projeto `MixGen` e integrado na interface
Streamlit.

Fato: o logo final foi salvo em:

```text
assets/images/mixgen-logo.png
```

Fato: o asset foi gerado como imagem raster com fundo chroma-key e depois teve o
fundo removido localmente, resultando em um PNG com transparencia (`RGBA`).
O arquivo intermediario com fundo chroma-key fica em `tmp/imagegen/`, pasta que
foi adicionada ao `.gitignore` por conter apenas artefatos temporarios de
geracao.

O logo representa visualmente os conceitos centrais do projeto:

- DNA ou evolucao, conectando com algoritmo genetico;
- barras de crescimento, conectando com marketing e receita;
- curva de fronteira/otimizacao, conectando com Pareto e trade-off entre lucro e
  risco.

A interface Streamlit passou a usar o logo em tres pontos:

- `page_icon`, para o icone da aba do navegador;
- `st.logo`, para exibir a marca na sidebar quando suportado pelo Streamlit;
- cabecalho principal, ao lado do titulo `MixGen`.

Opiniao tecnica: foi mantido o nome `MixGen` como texto renderizado pelo proprio
Streamlit, e nao dentro da imagem. Essa escolha evita risco de texto distorcido
em imagem gerada, melhora nitidez em diferentes tamanhos e deixa a marca mais
facil de ajustar futuramente.

## Persistencia do resultado no Streamlit em 16_06_2026

Foi corrigido o comportamento em que a tela perdia o plano calculado ao clicar
nos botoes de exportacao.

Fato: `st.download_button` executa um rerun por padrao. Como o resultado estava
guardado apenas em uma variavel local dentro do fluxo do botao `Calcular plano
otimizado`, o Streamlit recalculava a pagina e a area de resultados desaparecia
apos o download.

A correcao adicionou:

- a constante `CHAVE_RESULTADO_OTIMIZACAO`;
- persistencia do ultimo resultado bem-sucedido em `st.session_state`;
- leitura do resultado salvo para renderizar novamente a tela apos reruns;
- `on_click='ignore'` nos botoes `Exportar CSV` e `Exportar XLSX`, evitando rerun
  desnecessario durante o download;
- o botao `Novo cenário`, que limpa o resultado salvo e permite iniciar outra
  simulacao.

Inferencia: o nome `Novo cenário` foi escolhido como alternativa mais natural a
`Restaurar`, porque a acao real nao restaura um estado antigo, mas limpa o
resultado atual para preparar uma nova analise.

Opiniao tecnica: combinar `st.session_state` com `on_click='ignore'` e a solucao
mais robusta aqui. O download deixa de apagar visualmente o resultado e, mesmo
quando algum rerun acontecer por outro motivo, o ultimo plano calculado continua
disponivel ate a pessoa clicar em `Novo cenário`.
