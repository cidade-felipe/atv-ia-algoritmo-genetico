# Explicação das funções do motor do algoritmo genético

Este documento explica o arquivo `src/motor_algoritmo_genetico.py`, que concentra a lógica principal do algoritmo genético usado pelo MixGen.

Fato: este arquivo é o motor do projeto. Ele não monta interface, não renderiza Streamlit e não gera gráficos diretamente. A responsabilidade dele é transformar uma tabela de canais e uma configuração de algoritmo em um plano otimizado de investimento.

Inferência: a separação entre `streamlit_app.py` e `src/motor_algoritmo_genetico.py` foi feita para deixar a apresentação isolada da lógica de otimização.

Opinião técnica: essa é a melhor separação para o projeto, porque permite explicar o algoritmo genético sem misturar detalhes visuais, botões, tabelas editáveis e exportação.

## Como o problema é representado

O problema resolvido pelo motor é:

```text
Dado um orçamento total e vários canais de marketing com limites, retorno, saturação e risco,
encontrar uma distribuição de investimento que maximize lucro e reduza risco.
```

Na linguagem do algoritmo genético:

| Conceito | No MixGen |
| --- | --- |
| Gene | Investimento em um canal |
| Indivíduo | Lista de investimentos em todos os canais |
| População | Conjunto de planos candidatos |
| Fitness | Lucro estimado e risco ponderado |
| Crossover | Combinação de dois planos candidatos |
| Mutação | Redistribuição de verba entre canais |
| Reparo | Ajuste para respeitar orçamento, mínimo e máximo |
| Seleção | NSGA-II, mantendo bons trade-offs entre lucro e risco |
| Fronteira de Pareto | Planos que não são claramente piores que outros em lucro e risco |

Exemplo simplificado de indivíduo:

```python
[12, 10, 5, 8, 17]
```

Cada posição representa o investimento em um canal. Se os canais forem `SEO`, `Search Ads`, `TikTok`, `CRM` e `CRO`, então o indivíduo acima significa:

```text
SEO = R$ 12 mil
Search Ads = R$ 10 mil
TikTok = R$ 5 mil
CRM = R$ 8 mil
CRO = R$ 17 mil
```

## Constantes e estruturas principais

### `COLUNAS_OBRIGATORIAS`

Define as colunas mínimas que a base de canais precisa ter.

Colunas exigidas:

- `id`;
- `canal`;
- `categoria`;
- `funil`;
- `investimento_min_mil`;
- `investimento_max_mil`;
- `receita_por_mil`;
- `saturacao`;
- `risco`.

Impacto prático: impede que o algoritmo rode com dados incompletos. Isso reduz risco de cálculo errado, falha silenciosa ou resultado impossível de explicar.

### `SINERGIAS`

Define bônus de receita quando dois canais específicos aparecem juntos no plano.

Exemplos:

- `SEARCH` com `SEO` recebe bônus de 8%;
- `RETARGET` com `CRM` recebe bônus de 7%;
- `LINKEDIN` com `WEBINAR` recebe bônus de 10%.

Impacto prático: o algoritmo consegue valorizar combinações que fazem sentido no marketing real. Por exemplo, SEO e Search Ads podem reforçar presença em busca, enquanto CRM e retargeting podem aumentar recuperação e conversão.

Opinião técnica: esse ponto deixa o problema mais interessante do que apenas escolher canais isolados. O algoritmo passa a procurar mixes, não só vencedores individuais.

## Classes de dados

### `ConfigMarketingAG`

Guarda os parâmetros do algoritmo genético.

Campos:

- `orcamento_mil`;
- `tamanho_populacao`;
- `geracoes`;
- `descendentes_por_geracao`;
- `taxa_crossover`;
- `taxa_mutacao`;
- `peso_risco_decisao`;
- `semente`.

Uso no app: a interface Streamlit cria essa configuração a partir dos controles da barra lateral.

Impacto prático:

- mais população e mais gerações tendem a aumentar a chance de encontrar bons planos, mas aumentam o tempo de execução;
- mais mutação aumenta exploração, mas pode dificultar estabilidade;
- mais crossover aumenta recombinação entre bons planos;
- o peso do risco define o quanto planos arriscados são penalizados na escolha final.

### `MetricasPlano`

Guarda as métricas calculadas para um plano.

Campos:

- `investimento_total_mil`;
- `receita_estimada_mil`;
- `lucro_estimado_mil`;
- `risco_ponderado_mil`;
- `sinergia_mil`.

Impacto prático: concentra os indicadores que explicam por que um plano é bom ou ruim.

### `ResultadoMarketingAG`

Guarda o pacote final retornado pelo motor.

Campos:

- `plano_recomendado`;
- `metricas`;
- `historico`;
- `fronteira_pareto`;
- `plano_detalhado`;
- `config`.

Impacto prático: entrega tudo que a interface precisa para mostrar métricas, tabela, gráficos, exportações e explicação da convergência.

## Funções de carregamento e validação

### `carregar_canais(caminho_csv: str | Path) -> pd.DataFrame`

Carrega uma base de canais a partir de um CSV.

Entrada: caminho do arquivo CSV.

Saída: `DataFrame` validado e com tipos ajustados.

O que ela faz:

- verifica se o arquivo existe;
- lê o CSV com pandas;
- chama `validar_canais`;
- converte colunas de texto para `str`;
- converte colunas numéricas;
- força investimentos mínimo e máximo como inteiros.

Impacto prático: fornece uma entrada confiável para o algoritmo quando ele é usado fora do Streamlit.

### `validar_canais(canais: pd.DataFrame) -> None`

Valida se a base de canais está adequada para otimização.

Entrada: `DataFrame` de canais.

Saída: não retorna valor. Se encontrar problema, lança `ValueError`.

Validações feitas:

- colunas obrigatórias presentes;
- base não vazia;
- ausência de valores nulos;
- IDs únicos;
- colunas numéricas realmente numéricas;
- investimento mínimo não negativo;
- investimento máximo maior ou igual ao mínimo;
- receita por mil positiva;
- saturação entre 0 e 1;
- risco entre 0 e 1.

Impacto prático: evita que o algoritmo gere um plano incoerente ou quebre no meio da execução.

Opinião técnica: essa é uma das funções mais importantes do motor, porque algoritmo genético tende a amplificar problemas de dados. Se a base entra ruim, o resultado pode parecer sofisticado, mas ser inválido.

### `validar_orcamento(canais: pd.DataFrame, orcamento_mil: int) -> None`

Verifica se o orçamento total é viável.

Entrada:

- `canais`, com limites mínimos e máximos;
- `orcamento_mil`, orçamento escolhido.

Saída: não retorna valor. Se o orçamento for inviável, lança `ValueError`.

Regra:

- o orçamento não pode ser menor que a soma dos investimentos mínimos;
- o orçamento não pode ser maior que a soma dos investimentos máximos.

Impacto prático: impede otimizações impossíveis. Por exemplo, se todos os mínimos somam R\$ 80 mil, não dá para otimizar com orçamento de R$ 50 mil.

## Funções de criação e reparo dos indivíduos

### `preparar_creator_deap() -> None`

Configura as classes globais usadas pela biblioteca DEAP.

Entrada: não recebe parâmetros.

Saída: não retorna valor.

O que ela cria:

- `FitnessMarketing`, com pesos `(1.0, -1.0)`;
- `IndividualMarketing`, uma lista com atributo de fitness.

Interpretação dos pesos:

- `1.0` significa maximizar lucro;
- `-1.0` significa minimizar risco.

Impacto prático: define oficialmente qual é o objetivo evolutivo do algoritmo.

Detalhe técnico: a função verifica se as classes já existem antes de criá-las. Isso evita erro em reruns do Streamlit, porque o DEAP mantém essas classes em um registro global.

### `gerar_alocacao_inicial(canais: pd.DataFrame, orcamento_mil: int) -> list[int]`

Gera um indivíduo inicial válido.

Entrada:

- canais;
- orçamento total.

Saída: lista de inteiros representando investimento por canal.

Como funciona:

1. Valida se o orçamento é viável.
2. Começa colocando o investimento mínimo em todos os canais.
3. Calcula quanto ainda falta distribuir.
4. Enquanto houver verba restante, escolhe canais aleatoriamente que ainda não chegaram ao máximo.
5. Adiciona incrementos aleatórios até fechar exatamente o orçamento.

Impacto prático: a população inicial já nasce válida. Isso melhora a eficiência do algoritmo, porque ele não perde tempo avaliando planos impossíveis.

### `reparar_alocacao(individuo, canais, orcamento_mil) -> list[int]`

Corrige um indivíduo para respeitar limites e orçamento.

Entrada:

- um indivíduo, que pode ter valores quebrados, fora dos limites ou soma errada;
- canais;
- orçamento total.

Saída: lista de inteiros válida.

O que ela faz:

- arredonda valores;
- limita cada gene entre mínimo e máximo;
- calcula a diferença entre soma atual e orçamento;
- se falta verba, adiciona 1 em canais que ainda podem receber;
- se sobra verba, remove 1 de canais acima do mínimo;
- repete até a soma bater exatamente com o orçamento.

Impacto prático: garante que crossover e mutação possam ser usados sem quebrar as restrições do problema.

Opinião técnica: o reparo é essencial neste projeto. Sem ele, muitos filhos gerados pelo algoritmo teriam soma diferente do orçamento ou violariam limites por canal.

## Funções de cálculo de receita, risco, sinergia e fitness

## Onde fica a função de fitness

Fato: a função de fitness do algoritmo está em `src/motor_algoritmo_genetico.py`, na função:

```python
def avaliar_individuo(individuo: Sequence[int], canais: pd.DataFrame) -> tuple[float, float]:
    metricas = calcular_metricas_plano(individuo, canais)
    return metricas.lucro_estimado_mil, metricas.risco_ponderado_mil
```

No arquivo atual, ela aparece perto da linha 295.

Essa função é o ponto em que o algoritmo transforma um indivíduo em uma avaliação evolutiva. O indivíduo é uma lista de investimentos por canal, e a saída é uma tupla com dois objetivos:

```text
(lucro_estimado_mil, risco_ponderado_mil)
```

O primeiro objetivo é maximizado e o segundo é minimizado. Essa direção é definida em `preparar_creator_deap`, quando o fitness é criado com:

```python
creator.create('FitnessMarketing', base.Fitness, weights=(1.0, -1.0))
```

Interpretação:

- `1.0` no lucro significa que o algoritmo tenta aumentar esse valor;
- `-1.0` no risco significa que o algoritmo tenta reduzir esse valor.

Importante: `avaliar_individuo` é pequena de propósito. Ela não repete a fórmula inteira do problema. Em vez disso, chama `calcular_metricas_plano`, que concentra as regras de negócio:

- `calcular_receitas_por_canal`, para estimar receita considerando saturação;
- `calcular_sinergia`, para adicionar bônus quando canais complementares aparecem juntos;
- cálculo de risco ponderado por investimento;
- cálculo do lucro como receita total menos investimento total.

Inferência: para explicar em apresentação, o melhor caminho é dizer que o fitness fica em `avaliar_individuo`, mas que o cálculo real dos componentes do fitness vem de `calcular_metricas_plano`.

Opinião técnica: essa organização é boa porque separa o contrato evolutivo do cálculo de negócio. `avaliar_individuo` responde para o DEAP quais são os objetivos, enquanto `calcular_metricas_plano` explica por que aqueles objetivos têm aqueles valores.

### `calcular_receitas_por_canal(alocacao, canais) -> list[float]`

Calcula a receita estimada de cada canal.

Entrada:

- alocação de investimento;
- tabela de canais.

Saída: lista com receita estimada por canal.

Fórmula usada:

```text
uso_relativo = investimento / investimento_maximo
fator_saturacao = max(0.42, 1 - saturacao * uso_relativo ^ 1.35)
receita = investimento * receita_por_mil * fator_saturacao
```

Interpretação:

- quanto mais perto do máximo o canal fica, maior a chance de perder eficiência marginal;
- a saturação reduz a receita esperada;
- o piso `0.42` impede que a eficiência caia para zero.

Impacto prático: simula o comportamento real de canais de marketing, onde investir mais nem sempre aumenta retorno na mesma proporção.

### `calcular_sinergia(alocacao, canais, receitas) -> float`

Calcula o bônus de receita gerado por combinações de canais.

Entrada:

- alocação;
- canais;
- receitas já calculadas;

Saída: valor total de sinergia em R$ mil.

Como funciona:

1. Cria um índice para localizar canais pelo `id`.
2. Percorre os pares definidos em `SINERGIAS`.
3. Se os dois canais existem e recebem investimento, calcula um bônus.
4. O bônus usa como base a menor receita entre os dois canais do par.

Exemplo conceitual:

```text
Se SEARCH gera 30 e SEO gera 20, a base da sinergia é 20.
Com sinergia de 8%, o bônus é 1,6.
```

Impacto prático: favorece planos equilibrados quando determinados canais funcionam melhor juntos.

### `calcular_metricas_plano(alocacao, canais) -> MetricasPlano`

Calcula todas as métricas de um plano.

Entrada:

- alocação;
- canais.

Saída: objeto `MetricasPlano`.

Métricas calculadas:

- investimento total;
- receita estimada, já incluindo sinergia;
- risco ponderado;
- lucro estimado;
- sinergia.

Fórmulas principais:

```text
receita_total = soma(receitas_por_canal) + sinergia
risco_ponderado = soma(investimento_do_canal * risco_do_canal)
lucro = receita_total - investimento_total
```

Impacto prático: transforma uma lista de investimentos em indicadores de negócio.

### `avaliar_individuo(individuo, canais) -> tuple[float, float]`

Calcula o fitness de um indivíduo.

Entrada:

- indivíduo;
- canais.

Saída: tupla com dois valores:

```text
(lucro_estimado_mil, risco_ponderado_mil)
```

Como o DEAP interpreta isso:

- o lucro é maximizado;
- o risco é minimizado.

Impacto prático: essa é a ponte entre o problema de marketing e o algoritmo genético. É aqui que um plano vira uma pontuação evolutiva.

## Funções de operadores genéticos

### `cruzamento_com_reparo(individuo_a, individuo_b, canais, orcamento_mil)`

Aplica crossover entre dois indivíduos e repara os resultados.

Entrada:

- dois indivíduos pais;
- canais;
- orçamento.

Saída: dois indivíduos filhos.

Como funciona:

- aplica `tools.cxTwoPoint`, crossover de dois pontos da DEAP;
- repara o primeiro filho;
- repara o segundo filho;
- retorna os dois indivíduos ajustados.

Impacto prático: combina partes de dois planos diferentes, criando alternativas novas sem perder as restrições de orçamento.

### `mutacao_redistribuir(individuo, canais, orcamento_mil)`

Aplica mutação redistribuindo verba entre canais.

Entrada:

- indivíduo;
- canais;
- orçamento.

Saída: tupla contendo o indivíduo mutado.

Como funciona:

1. Escolhe de 1 a 4 redistribuições.
2. Procura canais de origem, que têm investimento acima do mínimo.
3. Procura canais de destino, que têm espaço abaixo do máximo.
4. Move uma quantia aleatória de 1 a 8 mil de um canal para outro.
5. Repara a alocação ao final.

Impacto prático: adiciona exploração ao algoritmo. Sem mutação, a população poderia ficar presa em combinações parecidas demais.

Opinião técnica: essa mutação é bem alinhada ao domínio do problema, porque ela não inventa valores aleatórios do nada. Ela simula uma decisão real de marketing: tirar verba de um canal e colocar em outro.

## Funções de configuração do DEAP e histórico

### `criar_toolbox(canais: pd.DataFrame, config: ConfigMarketingAG) -> base.Toolbox`

Cria a `toolbox` da DEAP, que registra como o algoritmo deve gerar, avaliar, cruzar, mutar e selecionar indivíduos.

Entrada:

- canais;
- configuração do algoritmo.

Saída: `base.Toolbox`.

Registros feitos:

- `individual`, cria um plano candidato;
- `population`, cria a população;
- `evaluate`, avalia lucro e risco;
- `mate`, faz crossover com reparo;
- `mutate`, faz mutação por redistribuição;
- `select`, usa `tools.selNSGA2`.

Impacto prático: concentra a configuração evolutiva em um único lugar.

### `registrar_historico(geracao: int, populacao: Sequence) -> dict[str, float | int]`

Resume o desempenho da população em uma geração.

Entrada:

- número da geração;
- população avaliada.

Saída: dicionário com métricas da geração.

Campos retornados:

- `geracao`;
- `lucro_max_mil`;
- `lucro_medio_mil`;
- `risco_min_mil`;
- `risco_medio_mil`.

Impacto prático: permite montar o gráfico de convergência no Streamlit e explicar se o algoritmo melhorou ao longo das gerações.

## Função principal do motor

### `executar_algoritmo_genetico(canais, config=None) -> ResultadoMarketingAG`

Executa todo o algoritmo genético.

Entrada:

- `canais`, tabela validada ou normalizada;
- `config`, configuração opcional.

Saída: objeto `ResultadoMarketingAG`.

Fluxo detalhado:

1. Usa uma configuração padrão se nenhuma for enviada.
2. Valida se o orçamento é viável.
3. Define a semente aleatória para reprodução dos resultados.
4. Cria a `toolbox`.
5. Gera a população inicial.
6. Cria uma `ParetoFront`.
7. Avalia indivíduos ainda sem fitness.
8. Aplica seleção NSGA-II na população inicial.
9. Registra o histórico da geração 0.
10. Para cada geração, cria descendentes com `algorithms.varOr`.
11. Avalia descendentes inválidos.
12. Seleciona a nova população a partir de pais e filhos.
13. Atualiza a fronteira de Pareto.
14. Registra o histórico da geração.
15. Escolhe o plano recomendado na fronteira.
16. Calcula métricas finais.
17. Monta plano detalhado e DataFrame da fronteira.
18. Retorna tudo em `ResultadoMarketingAG`.

Impacto prático: essa função é o coração do motor. Ela conecta validação, operadores genéticos, seleção multiobjetivo, Pareto, métricas e saída final.

Opinião técnica: o uso de NSGA-II é adequado porque o problema tem objetivos em conflito. Maximizar lucro e minimizar risco ao mesmo tempo geralmente não produz uma única resposta óbvia.

## Funções de escolha e montagem dos resultados

### `escolher_plano_recomendado(fronteira, config) -> list[int]`

Escolhe um plano final dentro da fronteira de Pareto.

Entrada:

- fronteira de Pareto;
- configuração do algoritmo.

Saída: lista de investimentos do plano escolhido.

Critério usado:

```text
score = lucro_estimado - peso_risco_decisao * risco_ponderado
```

Interpretação:

- planos com lucro maior tendem a subir;
- planos com risco maior são penalizados;
- `peso_risco_decisao` controla a força dessa penalização.

Impacto prático: transforma vários bons trade-offs em uma recomendação única para a interface.

Fato importante: esse score é usado para escolher o plano recomendado depois da evolução. O fitness evolutivo continua sendo multiobjetivo, com lucro e risco separados.

### `montar_fronteira_pareto(fronteira, config, canais) -> pd.DataFrame`

Converte a fronteira de Pareto em tabela.

Entrada:

- fronteira;
- configuração;
- canais.

Saída: `DataFrame` ordenado por `score_decisao`.

Colunas geradas:

- `plano`;
- `lucro_estimado_mil`;
- `risco_ponderado_mil`;
- `receita_estimada_mil`;
- `sinergia_mil`;
- `score_decisao`.

Impacto prático: alimenta o gráfico de fronteira de Pareto no Streamlit.

### `montar_plano_detalhado(alocacao, canais) -> pd.DataFrame`

Monta uma tabela detalhada do plano final por canal.

Entrada:

- alocação escolhida;
- canais.

Saída: `DataFrame` ordenado por investimento.

Colunas geradas:

- `id`;
- `canal`;
- `categoria`;
- `funil`;
- `investimento_mil`;
- `receita_estimada_mil`;
- `lucro_bruto_mil`;
- `risco_ponderado_mil`.

Impacto prático: é a tabela principal do plano recomendado, usada na tela e nas exportações.

### `criar_alocacao_referencia(canais: pd.DataFrame, orcamento_mil: int) -> list[int]`

Cria uma alocação determinística de referência.

Entrada:

- canais;
- orçamento.

Saída: lista de investimentos.

Como funciona:

- começa com os investimentos mínimos;
- distribui o restante de forma circular entre os canais que ainda não chegaram ao máximo.

Impacto prático: serve como baseline simples para comparar ou testar comportamentos do motor.

Opinião técnica: essa função é útil para validações, porque não depende de aleatoriedade. Quando algo parece estranho no algoritmo genético, uma referência determinística ajuda a comparar resultados.

## Resumo das responsabilidades

| Item | Responsabilidade principal |
| --- | --- |
| `COLUNAS_OBRIGATORIAS` | Definir o schema mínimo da base |
| `SINERGIAS` | Definir bônus entre canais complementares |
| `ConfigMarketingAG` | Guardar parâmetros do algoritmo |
| `MetricasPlano` | Guardar métricas de um plano |
| `ResultadoMarketingAG` | Guardar o resultado completo |
| `carregar_canais` | Ler e preparar CSV |
| `validar_canais` | Validar qualidade da base |
| `validar_orcamento` | Verificar se o orçamento é possível |
| `preparar_creator_deap` | Configurar classes da DEAP |
| `gerar_alocacao_inicial` | Criar indivíduo inicial válido |
| `reparar_alocacao` | Corrigir indivíduo após operadores genéticos |
| `calcular_receitas_por_canal` | Estimar receita com saturação |
| `calcular_sinergia` | Aplicar bônus por pares de canais |
| `calcular_metricas_plano` | Calcular receita, lucro, risco e sinergia |
| `avaliar_individuo` | Retornar fitness multiobjetivo |
| `cruzamento_com_reparo` | Cruzar dois planos e reparar |
| `mutacao_redistribuir` | Redistribuir verba entre canais |
| `criar_toolbox` | Registrar operadores da DEAP |
| `registrar_historico` | Guardar evolução por geração |
| `executar_algoritmo_genetico` | Orquestrar a otimização completa |
| `escolher_plano_recomendado` | Escolher um plano final da fronteira |
| `montar_fronteira_pareto` | Criar tabela da fronteira |
| `montar_plano_detalhado` | Criar tabela final por canal |
| `criar_alocacao_referencia` | Criar baseline determinístico |

## Explicação curta para apresentação

O MixGen representa cada plano como uma lista de investimentos, em que cada posição corresponde a um canal de marketing. A população inicial já nasce respeitando orçamento, mínimo e máximo por canal. A cada geração, o algoritmo combina planos por crossover e redistribui verba por mutação. Depois de cada alteração, uma função de reparo garante que o plano continue viável.

O fitness avalia dois objetivos ao mesmo tempo: aumentar lucro estimado e reduzir risco ponderado. A receita de cada canal considera saturação, então investir mais em um canal não gera retorno linear infinito. Além disso, algumas combinações de canais recebem bônus de sinergia, como Search Ads com SEO ou LinkedIn com Webinar.

A seleção usa NSGA-II, uma técnica multiobjetivo que preserva diferentes bons trade-offs na fronteira de Pareto. No final, o sistema escolhe uma recomendação única usando um score que penaliza risco de acordo com o peso definido pelo usuário. Isso permite entregar uma resposta prática para decisão de marketing, sem esconder que existem alternativas com diferentes combinações de retorno e risco.

## Cuidados e limitações

Fato: o algoritmo otimiza com base nas premissas fornecidas nas colunas de receita, saturação, risco e sinergia.

Inferência: se essas premissas estiverem mal calibradas, o plano pode parecer ótimo matematicamente, mas não necessariamente será o melhor no mundo real.

Opinião técnica: para uso em produção, o ideal seria calibrar `receita_por_mil`, `saturacao`, `risco` e `SINERGIAS` com dados históricos, testes A/B ou conhecimento de especialistas. O algoritmo genético melhora a decisão de alocação, mas não substitui a qualidade das premissas de negócio.
