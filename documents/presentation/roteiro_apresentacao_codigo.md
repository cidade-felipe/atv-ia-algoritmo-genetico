# Roteiro para explicar as funções do código

Este roteiro é para apresentar o projeto abrindo os arquivos do código, sem slides.

A ideia é simples: você não precisa ler cada linha. Abra a função, explique o papel dela no fluxo e conecte com o algoritmo genético.

## Frase de abertura

```text
O projeto tem duas partes principais.
O `src/motor_algoritmo_genetico.py` é onde fica o algoritmo genético.
O `streamlit_app.py` é onde fica a interface, que coleta os parâmetros, chama o motor e mostra os resultados.
```

Ordem recomendada:

```text
1. Explicar o motor do algoritmo genético.
2. Explicar como o Streamlit usa esse motor.
3. Fechar mostrando onde fica o fitness e como o resultado aparece na interface.
```

## Parte 1, funções do motor genético

Arquivo:

```text
src/motor_algoritmo_genetico.py
```

Comece falando:

```text
Aqui está a parte mais importante do projeto.
Este arquivo transforma canais de marketing e orçamento em uma otimização genética.
Cada indivíduo é uma lista de investimentos, e o algoritmo evolui esses planos ao longo das gerações.
```

## Constantes e classes, explicação rápida

### `COLUNAS_OBRIGATORIAS`

Fala curta:

```text
Essa constante define o schema mínimo da base de canais.
Antes de otimizar, o código confere se todas essas colunas existem.
Isso evita rodar o algoritmo com dados incompletos.
```

### `SINERGIAS`

Fala curta:

```text
Aqui ficam pares de canais que funcionam melhor juntos.
Se os dois canais do par recebem investimento, o plano ganha um bônus de receita.
Isso deixa o problema mais realista, porque marketing não é só canal isolado, é combinação de canais.
```

### `ConfigMarketingAG`

Fala curta:

```text
Essa dataclass guarda os parâmetros do algoritmo genético.
Ela tem orçamento, tamanho da população, número de gerações, descendentes, taxa de crossover, taxa de mutação, peso do risco e semente aleatória.
```

Complemento se precisar:

```text
População e gerações controlam o tamanho da busca.
Crossover e mutação controlam como novos planos são criados.
Peso do risco controla o quanto o sistema evita planos arriscados na recomendação final.
```

### `MetricasPlano`

Fala curta:

```text
Essa classe guarda os indicadores de um plano.
Ela armazena investimento total, receita estimada, lucro, risco ponderado e sinergia.
```

### `ResultadoMarketingAG`

Fala curta:

```text
Essa classe empacota tudo que o motor devolve para a interface.
Ela inclui o plano recomendado, métricas, histórico de evolução, fronteira de Pareto e tabela detalhada por canal.
```

## Funções de entrada e validação

### `carregar_canais`

Onde abrir:

```python
def carregar_canais(caminho_csv: str | Path) -> pd.DataFrame:
```

Fala principal:

```text
Essa função carrega a base de canais a partir de um CSV.
Ela verifica se o arquivo existe, lê com pandas, valida a estrutura e converte os tipos das colunas.
```

Por que existe:

```text
Ela prepara uma entrada confiável para o algoritmo.
Sem isso, o motor poderia receber texto em coluna numérica ou uma base sem campos obrigatórios.
```

### `validar_canais`

Onde abrir:

```python
def validar_canais(canais: pd.DataFrame) -> None:
```

Fala principal:

```text
Essa função é a barreira de qualidade dos dados.
Ela valida colunas obrigatórias, base vazia, valores nulos, IDs duplicados, números inválidos, limites de investimento, receita, saturação e risco.
```

Ponto forte:

```text
Isso é importante porque algoritmo genético pode gerar uma resposta bonita em cima de dados ruins.
Então a validação protege o resultado.
```

### `validar_orcamento`

Onde abrir:

```python
def validar_orcamento(canais: pd.DataFrame, orcamento_mil: int) -> None:
```

Fala principal:

```text
Essa função confere se o orçamento é viável.
O orçamento precisa ser maior ou igual à soma dos mínimos e menor ou igual à soma dos máximos.
```

Exemplo para falar:

```text
Se os mínimos somam 80 mil, não existe plano possível com orçamento de 50 mil.
Se os máximos somam 200 mil, também não existe plano possível com orçamento de 300 mil.
```

## Funções que montam os indivíduos

### `preparar_creator_deap`

Onde abrir:

```python
def preparar_creator_deap() -> None:
```

Fala principal:

```text
Essa função registra no DEAP o tipo de fitness e o tipo de indivíduo.
O fitness tem pesos `(1.0, -1.0)`, ou seja, maximiza lucro e minimiza risco.
```

Ponto que vale destacar:

```text
A checagem com `hasattr` evita erro no Streamlit, porque a página pode rodar mais de uma vez e o DEAP não gosta de recriar a mesma classe global.
```

### `gerar_alocacao_inicial`

Onde abrir:

```python
def gerar_alocacao_inicial(canais: pd.DataFrame, orcamento_mil: int) -> list[int]:
```

Fala principal:

```text
Essa função cria um indivíduo inicial válido.
Ela começa colocando o investimento mínimo em todos os canais e distribui o orçamento restante aleatoriamente, sem passar do máximo de cada canal.
```

Ligação com algoritmo genético:

```text
Cada retorno dessa função é um plano candidato da população inicial.
Então, se eu tenho 12 canais, o indivíduo é uma lista com 12 investimentos.
```

### `reparar_alocacao`

Onde abrir:

```python
def reparar_alocacao(...)
```

Fala principal:

```text
Essa função corrige um indivíduo que ficou inválido.
Depois de crossover ou mutação, a soma pode ficar diferente do orçamento ou algum canal pode passar do limite.
O reparo ajusta tudo para voltar a respeitar mínimo, máximo e orçamento total.
```

Frase fácil de decorar:

```text
O reparo garante que o algoritmo evolua planos possíveis, não soluções que só funcionam no papel.
```

## Funções que calculam o resultado de um plano

### `calcular_receitas_por_canal`

Onde abrir:

```python
def calcular_receitas_por_canal(...)
```

Fala principal:

```text
Essa função calcula a receita estimada de cada canal.
Ela usa o investimento, a receita por mil e um fator de saturação.
```

Explicação de negócio:

```text
A saturação representa que colocar mais dinheiro no mesmo canal não gera retorno infinito.
Quanto mais perto do máximo, menor tende a ser o ganho marginal.
```

### `calcular_sinergia`

Onde abrir:

```python
def calcular_sinergia(...)
```

Fala principal:

```text
Essa função calcula bônus de receita para pares de canais complementares.
Ela percorre o dicionário `SINERGIAS` e, se os dois canais do par receberam investimento, soma um percentual sobre a menor receita do par.
```

Por que usa a menor receita:

```text
Isso evita exagerar a sinergia quando um canal está muito forte e o outro quase não contribui.
```

### `calcular_metricas_plano`

Onde abrir:

```python
def calcular_metricas_plano(...)
```

Fala principal:

```text
Essa função consolida as métricas de um plano.
Ela calcula receita por canal, soma sinergia, calcula investimento total, lucro e risco ponderado.
```

Ligação com fitness:

```text
Essa função não é o fitness diretamente, mas ela calcula os valores que o fitness usa.
```

### `avaliar_individuo`

Onde abrir:

```python
def avaliar_individuo(individuo: Sequence[int], canais: pd.DataFrame) -> tuple[float, float]:
```

Fala principal:

```text
Aqui está a função de fitness.
Ela recebe um indivíduo, calcula suas métricas e retorna dois objetivos: lucro estimado e risco ponderado.
```

Trecho para apontar:

```python
return metricas.lucro_estimado_mil, metricas.risco_ponderado_mil
```

Depois aponte:

```python
creator.create('FitnessMarketing', base.Fitness, weights=(1.0, -1.0))
```

Fala para memorizar:

```text
O fitness é multiobjetivo.
O lucro é maximizado por causa do peso positivo.
O risco é minimizado por causa do peso negativo.
```

## Funções dos operadores genéticos

### `cruzamento_com_reparo`

Onde abrir:

```python
def cruzamento_com_reparo(...)
```

Fala principal:

```text
Essa função aplica crossover de dois pontos.
Ela mistura dois planos candidatos e depois chama o reparo nos dois filhos.
```

Explicação simples:

```text
O crossover tenta combinar partes boas de dois planos.
O reparo entra logo depois para garantir que os filhos continuem válidos.
```

### `mutacao_redistribuir`

Onde abrir:

```python
def mutacao_redistribuir(...)
```

Fala principal:

```text
Essa função aplica mutação redistribuindo verba.
Ela escolhe um canal de origem, tira uma pequena quantia, escolhe um destino e coloca essa verba lá.
```

Por que é uma boa mutação:

```text
Ela combina com o domínio do problema.
Na prática, mutar o indivíduo significa testar uma redistribuição de orçamento entre canais.
```

Frase fácil:

```text
Crossover mistura planos. Mutação testa mudanças novas. Reparo mantém tudo viável.
```

## Funções da execução evolutiva

### `criar_toolbox`

Onde abrir:

```python
def criar_toolbox(canais: pd.DataFrame, config: ConfigMarketingAG) -> base.Toolbox:
```

Fala principal:

```text
Essa função configura a toolbox da DEAP.
Ela registra como criar indivíduos, como criar população, como avaliar fitness, como cruzar, como mutar e como selecionar.
```

Trecho importante:

```python
toolbox.register('select', tools.selNSGA2)
```

Fala:

```text
A seleção usa NSGA-II, que é uma técnica própria para problemas multiobjetivo.
Ela ajuda a preservar bons trade-offs entre lucro e risco.
```

### `registrar_historico`

Onde abrir:

```python
def registrar_historico(geracao: int, populacao: Sequence) -> dict[str, float | int]:
```

Fala principal:

```text
Essa função registra o desempenho de cada geração.
Ela calcula lucro máximo, lucro médio, risco mínimo e risco médio da população.
```

Por que existe:

```text
Esses dados alimentam o gráfico de convergência, mostrando se o algoritmo melhorou com o tempo.
```

### `executar_algoritmo_genetico`

Onde abrir:

```python
def executar_algoritmo_genetico(...)
```

Fala principal:

```text
Essa é a função principal do motor.
Ela executa o ciclo completo do algoritmo genético.
```

Explique em ordem:

```text
1. Valida o orçamento.
2. Define a semente aleatória.
3. Cria a toolbox.
4. Gera a população inicial.
5. Avalia o fitness dos indivíduos.
6. Atualiza a fronteira de Pareto.
7. Para cada geração, cria descendentes com crossover e mutação.
8. Avalia os descendentes.
9. Seleciona a nova população com NSGA-II.
10. Escolhe o plano recomendado e monta os resultados.
```

Frase fácil:

```text
Essa função amarra tudo: população, fitness, operadores genéticos, seleção, Pareto e saída final.
```

## Funções que transformam evolução em resultado

### `escolher_plano_recomendado`

Onde abrir:

```python
def escolher_plano_recomendado(...)
```

Fala principal:

```text
A fronteira de Pareto pode ter vários planos bons.
Essa função escolhe uma recomendação única usando um score de decisão.
```

Trecho para apontar:

```python
lucro - peso_risco * risco
```

Fala:

```text
Quanto maior o lucro, melhor.
Quanto maior o risco, maior a penalização.
O usuário controla essa penalização pelo peso do risco.
```

### `montar_fronteira_pareto`

Onde abrir:

```python
def montar_fronteira_pareto(...)
```

Fala principal:

```text
Essa função transforma a fronteira de Pareto em uma tabela.
Ela calcula métricas para cada plano da fronteira e adiciona o score de decisão.
```

Por que existe:

```text
Essa tabela é usada para explicar os trade-offs e gerar o gráfico de Pareto na interface.
```

### `montar_plano_detalhado`

Onde abrir:

```python
def montar_plano_detalhado(...)
```

Fala principal:

```text
Essa função monta a tabela final por canal.
Ela mostra quanto investir, receita estimada, lucro bruto e risco ponderado em cada canal.
```

Por que existe:

```text
É essa tabela que vira o plano recomendado mostrado no Streamlit e exportado em CSV ou Excel.
```

### `criar_alocacao_referencia`

Onde abrir:

```python
def criar_alocacao_referencia(...)
```

Fala principal:

```text
Essa função cria uma alocação baseline sem aleatoriedade.
Ela distribui o orçamento restante em rodízio entre os canais.
```

Como explicar:

```text
Ela serve como uma referência simples para testes ou comparação, não como a solução otimizada principal.
```

## Parte 2, funções da interface Streamlit

Arquivo:

```text
streamlit_app.py
```

Comece falando:

```text
Agora que o motor está explicado, este arquivo mostra como o usuário interage com ele.
O Streamlit coleta parâmetros, permite editar canais, chama o motor e apresenta os resultados.
```

## Funções de dados e normalização

### `carregar_canais_padrao`

Fala curta:

```text
Carrega o CSV padrão de canais usado inicialmente na interface.
```

### `normalizar_canais`

Fala principal:

```text
Normaliza os dados editados antes de mandar para o motor.
Ela padroniza ID, converte rótulos visuais para valores internos e transforma colunas numéricas.
```

Por que é importante:

```text
A interface pode mostrar texto bonito com acento, mas o motor precisa receber valores consistentes.
```

## Funções de opções e rótulos

### `montar_opcoes_funil`

Fala curta:

```text
Monta as opções disponíveis para a coluna de funil no editor.
```

### `montar_opcoes_categoria`

Fala curta:

```text
Monta as opções disponíveis para categoria, juntando valores conhecidos e valores já existentes na tabela.
```

### `montar_opcoes_canal`

Fala curta:

```text
Monta as opções disponíveis para canal, evitando que o usuário tenha que digitar tudo manualmente.
```

### `formatar_canal`

Fala curta:

```text
Transforma o nome interno do canal em um rótulo mais bonito para exibir na tela.
```

### `formatar_categoria`

Fala curta:

```text
Transforma categorias internas, como `midia_paga`, em textos mais legíveis, como `Mídia paga`.
```

### `formatar_funil`

Fala curta:

```text
Formata etapas do funil, como `aquisicao`, para aparecer como `Aquisição`.
```

Frase para esse bloco:

```text
Essas funções separam valor interno de rótulo visual.
Isso deixa a interface bonita sem bagunçar o motor.
```

## Funções de exportação e resultado visual

### `gerar_excel_plano`

Fala curta:

```text
Gera o arquivo Excel do plano otimizado em memória, sem precisar salvar arquivo temporário no disco.
```

### `preparar_plano_recomendado_para_exibicao`

Fala principal:

```text
Prepara uma cópia do plano para exibir na tela.
Ela formata canal, categoria, funil e renomeia colunas técnicas para nomes mais amigáveis.
```

### `limpar_resultado_otimizacao`

Fala curta:

```text
Limpa o resultado salvo na sessão quando o usuário quer começar um novo cenário.
```

## Funções de layout e entrada

### `configurar_pagina`

Fala curta:

```text
Configura título, ícone, layout largo e logo do app no Streamlit.
```

### `renderizar_cabecalho`

Fala curta:

```text
Mostra o logo, o nome MixGen e uma descrição curta do objetivo do app.
```

### `renderizar_parametros`

Fala principal:

```text
Renderiza os controles da barra lateral.
O usuário escolhe orçamento, população, gerações, descendentes, taxa de crossover, taxa de mutação, peso do risco e semente.
No final, a função retorna um `ConfigMarketingAG`, que é exatamente a configuração esperada pelo motor.
```

Ponto importante:

```text
Essa função é a ponte entre os controles visuais e os parâmetros reais do algoritmo genético.
```

### `renderizar_editor_canais`

Fala principal:

```text
Renderiza a tabela editável de canais.
O usuário consegue alterar limites, retorno, saturação e risco antes de calcular.
```

Ponto importante:

```text
Essa função permite simular cenários sem alterar diretamente o CSV padrão.
```

## Funções de gráficos

### `grafico_alocacao_canal`

Fala curta:

```text
Mostra a alocação recomendada por canal em barras horizontais.
```

### `grafico_alocacao_categoria`

Fala curta:

```text
Agrupa o plano por categoria e mostra quanto investimento foi para cada grupo estratégico.
```

### `grafico_alocacao_funil`

Fala curta:

```text
Agrupa o plano por etapa do funil, mostrando se o orçamento foi mais para aquisição, conversão, nutrição ou retenção.
```

### `grafico_fronteira`

Fala principal:

```text
Mostra a fronteira de Pareto.
No eixo X fica o risco, no eixo Y fica o lucro, e o plano escolhido aparece destacado.
```

Ponto importante:

```text
Esse gráfico ajuda a explicar que existem vários trade-offs possíveis, não só uma resposta mágica.
```

### `grafico_convergencia`

Fala curta:

```text
Mostra como o melhor lucro e o lucro médio evoluíram ao longo das gerações.
```

## Funções finais da interface

### `renderizar_resultado`

Fala principal:

```text
Essa função mostra tudo que vem depois do cálculo.
Ela exibe métricas, plano recomendado, botões de download, botão de novo cenário e os gráficos.
```

Ponto para citar:

```text
Os downloads usam o resultado salvo, então exportar CSV ou Excel não apaga o cálculo da tela.
```

### `main`

Fala principal:

```text
Essa é a função que orquestra a interface inteira.
Ela configura a página, carrega os dados, renderiza parâmetros e editor, espera o clique no botão de cálculo, normaliza e valida os dados, chama o algoritmo genético e mostra o resultado.
```

Trecho para apontar:

```python
resultado = executar_algoritmo_genetico(canais, config)
```

Fala para fechar:

```text
Esse trecho mostra a integração das duas partes do projeto.
A interface coleta e prepara os dados, mas a decisão de otimização é feita pelo motor genético.
```

## Sequência curta para apresentar sem se perder

Use esta sequência se quiser algo fácil de decorar:

```text
1. `ConfigMarketingAG`, parâmetros do algoritmo.
2. `gerar_alocacao_inicial`, cria indivíduos válidos.
3. `calcular_metricas_plano`, calcula receita, lucro, risco e sinergia.
4. `avaliar_individuo`, é o fitness.
5. `cruzamento_com_reparo`, mistura planos.
6. `mutacao_redistribuir`, redistribui verba.
7. `criar_toolbox`, registra tudo na DEAP.
8. `executar_algoritmo_genetico`, roda as gerações.
9. `escolher_plano_recomendado`, escolhe o plano final.
10. `main`, mostra como o Streamlit chama o motor.
```

## Versão de fala em 2 minutos

```text
O motor começa validando os canais e o orçamento.
Depois, `ConfigMarketingAG` define os parâmetros da busca, como população, gerações, crossover, mutação e peso do risco.

Cada indivíduo é uma lista de investimentos por canal.
`gerar_alocacao_inicial` cria planos válidos e `reparar_alocacao` garante que qualquer plano alterado continue respeitando orçamento, mínimo e máximo.

As métricas vêm de `calcular_metricas_plano`, que usa receita com saturação, sinergia entre canais, lucro e risco ponderado.
O fitness está em `avaliar_individuo`, que retorna lucro e risco.
Como o DEAP usa pesos `(1.0, -1.0)`, o algoritmo maximiza lucro e minimiza risco.

Depois entram os operadores genéticos.
`cruzamento_com_reparo` mistura dois planos, `mutacao_redistribuir` move verba entre canais e `criar_toolbox` registra tudo na DEAP com seleção NSGA-II.
`executar_algoritmo_genetico` roda as gerações, atualiza a fronteira de Pareto e monta o resultado.

Por fim, o `streamlit_app.py` funciona como interface.
Ele coleta parâmetros, permite editar canais, chama `executar_algoritmo_genetico` dentro da `main` e renderiza métricas, tabela, gráficos e exportações.
```

## Perguntas rápidas

### Qual função é o fitness?

```text
`avaliar_individuo`, em `src/motor_algoritmo_genetico.py`.
Ela retorna lucro estimado e risco ponderado.
```

### Onde o algoritmo maximiza lucro e minimiza risco?

```text
Em `preparar_creator_deap`, com `weights=(1.0, -1.0)`.
```

### Onde acontece a evolução?

```text
Em `executar_algoritmo_genetico`.
Ela cria população, gera descendentes, avalia fitness, seleciona com NSGA-II e atualiza Pareto.
```

### Onde ficam crossover e mutação?

```text
Crossover fica em `cruzamento_com_reparo`.
Mutação fica em `mutacao_redistribuir`.
```

### Onde o app chama o motor?

```text
Na `main` do `streamlit_app.py`, no trecho que chama `executar_algoritmo_genetico(canais, config)`.
```
