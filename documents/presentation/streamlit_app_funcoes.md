# Explicação das funções do app Streamlit

Este documento explica as funções definidas em `streamlit_app.py`, que é o arquivo responsável pela interface web do MixGen no Streamlit.

Fato: o algoritmo genético em si fica em `src/motor_algoritmo_genetico.py`. O `streamlit_app.py` não implementa seleção, crossover, mutação ou cálculo de fitness diretamente. Ele coleta entradas, prepara os dados, chama o motor do algoritmo e apresenta os resultados.

Inferência: a separação foi feita para deixar a explicação principal do algoritmo genético concentrada no motor, enquanto o app Streamlit cuida da experiência de uso.

Opinião técnica: essa separação é uma boa decisão porque evita misturar regra de negócio com interface. Na prática, isso facilita manutenção, testes, troca de interface e uso futuro do motor em outros contextos, como API, notebook ou script.

## Visão geral do fluxo

O app segue este fluxo principal:

1. Configura a página e mostra o cabeçalho do MixGen.
2. Carrega o CSV padrão de canais em `data/canais_marketing.csv`.
3. Exibe parâmetros do algoritmo genético na barra lateral.
4. Exibe uma tabela editável com canais, categorias, funil, limites, retorno, saturação e risco.
5. Quando o usuário clica em `Calcular plano otimizado`, normaliza os dados editados.
6. Valida os canais e chama `executar_algoritmo_genetico`.
7. Salva o resultado em `st.session_state`, renderiza métricas, tabela, gráficos e botões de exportação.

Essa lógica aparece principalmente na função `main`, mas cada etapa foi quebrada em funções menores para manter o código legível.

## Constantes e estruturas auxiliares

Antes das funções, o arquivo define algumas constantes que controlam caminhos, rótulos e textos de ajuda.

### `RAIZ_PROJETO`

Guarda o caminho absoluto da pasta onde está o `streamlit_app.py`.

Impacto prático: evita depender do diretório em que o comando `streamlit run` foi executado. Isso reduz risco de erro ao rodar localmente ou no deploy.

### `CAMINHO_DADOS`

Aponta para `data/canais_marketing.csv`, que é a base padrão carregada pelo app.

Impacto prático: permite que o app sempre encontre o CSV inicial com os canais de marketing.

### `CAMINHO_LOGO`

Aponta para `assets/images/mixgen-logo.png`.

Impacto prático: centraliza o uso do logo no app, tanto no ícone da página quanto no cabeçalho.

### `CHAVE_RESULTADO_OTIMIZACAO`

Define a chave usada no `st.session_state` para guardar o último resultado calculado.

Impacto prático: impede que o resultado desapareça quando o Streamlit reroda a página, por exemplo após exportar CSV ou XLSX.

### `CANAL_ROTULOS`, `FUNIL_ROTULOS` e `CATEGORIA_ROTULOS`

Mapeiam valores internos para rótulos mais bonitos na interface.

Exemplo:

```text
conversao -> Conversão
midia_paga -> Mídia paga
Otimizacao de conversao -> Otimização de conversão
```

Impacto prático: o motor pode trabalhar com valores simples e estáveis, enquanto o usuário vê textos com acentuação e formatação adequada.

### `CANAL_VALORES_POR_ROTULO`, `FUNIL_VALORES_POR_ROTULO` e `CATEGORIA_VALORES_POR_ROTULO`

São dicionários reversos. Eles convertem o rótulo visual de volta para o valor interno.

Impacto prático: se o usuário seleciona `Conversão` no Streamlit, o app consegue mandar `conversao` para o motor.

### `TOOLTIPS_PARAMETROS` e `TOOLTIPS_COLUNAS`

Guardam explicações curtas exibidas nos campos da interface.

Impacto prático: ajudam o usuário a entender o que cada parâmetro significa sem poluir a tela com textos longos.

### `COLUNAS_PLANO_RECOMENDADO`

Mapeia nomes técnicos do resultado para nomes mais legíveis na tabela final.

Exemplo:

```text
lucro_bruto_mil -> Lucro bruto (R$ mil)
risco_ponderado_mil -> Risco ponderado (R$ mil)
```

Impacto prático: melhora a apresentação do plano recomendado, principalmente para leitura executiva.

## Funções de carregamento e preparação dos dados

### `carregar_canais_padrao() -> pd.DataFrame`

Carrega o CSV padrão de canais de marketing.

Entrada: não recebe parâmetros.

Saída: retorna um `DataFrame` do pandas com os canais definidos em `data/canais_marketing.csv`.

Uso no app: chamada dentro de `main`, antes de renderizar o editor de canais.

Por que existe: centraliza o carregamento da base padrão em uma função pequena. Se futuramente a fonte mudar para banco de dados, upload ou API, o ponto de alteração fica claro.

### `normalizar_canais(canais: pd.DataFrame) -> pd.DataFrame`

Prepara os dados editados no Streamlit antes de enviar para validação e para o motor do algoritmo genético.

Entrada: um `DataFrame` com os canais editados pelo usuário.

Saída: um novo `DataFrame` normalizado.

O que ela faz:

- copia o `DataFrame`, evitando alterar o objeto original diretamente;
- padroniza `id` com texto em maiúsculas, sem espaços nas pontas e com espaços convertidos para `_`;
- converte rótulos visuais de canal, categoria e funil para valores internos;
- converte colunas numéricas com `pd.to_numeric`;
- arredonda investimentos mínimo e máximo;
- usa o tipo inteiro anulável `Int64` nas colunas de investimento.

Impacto prático: reduz erros de entrada antes da otimização. Isso é importante porque o algoritmo depende de limites, retornos e riscos coerentes para gerar planos válidos.

Opinião técnica: essa função é uma camada de proteção entre interface e motor. Ela evita que detalhes visuais do Streamlit vazem para a regra do algoritmo.

## Funções de opções e rótulos da interface

### `montar_opcoes_funil(canais: pd.DataFrame) -> list[str]`

Monta a lista de opções disponíveis na coluna `funil` do editor.

Entrada: o `DataFrame` atual de canais.

Saída: uma lista de strings com valores possíveis para o funil.

Como funciona:

- pega os funis já conhecidos no dicionário `FUNIL_ROTULOS`;
- adiciona valores que já existam no CSV ou na tabela editada;
- remove duplicatas preservando a ordem.

Impacto prático: permite usar opções padrão e, ao mesmo tempo, preservar valores já existentes na base.

### `montar_opcoes_categoria(canais: pd.DataFrame) -> list[str]`

Monta a lista de opções disponíveis na coluna `categoria`.

Entrada: o `DataFrame` atual de canais.

Saída: uma lista de categorias possíveis.

Impacto prático: evita que o usuário precise digitar categorias manualmente, reduzindo erro de digitação e inconsistência.

### `montar_opcoes_canal(canais: pd.DataFrame) -> list[str]`

Monta a lista de opções disponíveis na coluna `canal`.

Entrada: o `DataFrame` atual de canais.

Saída: uma lista de nomes de canais possíveis.

Impacto prático: mantém os canais já conhecidos disponíveis no editor, mas sem travar completamente a evolução da base caso novos canais sejam adicionados.

### `formatar_canal(valor: str) -> str`

Formata o nome interno de um canal para exibição visual.

Entrada: um nome de canal.

Saída: o rótulo amigável do canal.

Exemplo:

```text
Conteudo SEO -> Conteúdo SEO
Promocoes marketplace -> Promoções marketplace
```

Se o valor não estiver em `CANAL_ROTULOS`, a função troca `_` por espaço e aplica `.title()`.

Impacto prático: melhora a leitura da interface sem obrigar o CSV padrão a guardar tudo com acentuação.

### `formatar_categoria(valor: str) -> str`

Formata a categoria interna para exibição visual.

Entrada: uma categoria.

Saída: o rótulo amigável da categoria.

Exemplo:

```text
midia_paga -> Mídia paga
organico -> Orgânico
```

Impacto prático: deixa tabelas e gráficos mais apresentáveis.

### `formatar_funil(valor: str) -> str`

Formata a etapa interna do funil para exibição visual.

Entrada: uma etapa do funil.

Saída: o rótulo amigável da etapa.

Exemplo:

```text
aquisicao -> Aquisição
retencao -> Retenção
```

Impacto prático: padroniza como o funil aparece na tabela, nos gráficos e nos selectboxes.

## Funções de exportação e preparação do resultado

### `gerar_excel_plano(plano: pd.DataFrame) -> bytes`

Gera um arquivo Excel em memória a partir do plano otimizado.

Entrada: um `DataFrame` com o plano detalhado.

Saída: bytes do arquivo `.xlsx`.

Como funciona:

- cria um buffer com `BytesIO`;
- usa `pd.ExcelWriter` com engine `openpyxl`;
- escreve o plano na aba `Plano otimizado`;
- retorna o conteúdo binário do arquivo.

Impacto prático: permite oferecer download em Excel sem criar arquivo temporário no disco. Isso é mais limpo para deploy em Streamlit Cloud.

### `preparar_plano_recomendado_para_exibicao(plano: pd.DataFrame) -> pd.DataFrame`

Cria uma versão visualmente formatada do plano recomendado.

Entrada: o `DataFrame` técnico retornado pelo motor.

Saída: um novo `DataFrame` pronto para exibição no Streamlit.

O que ela faz:

- copia o plano;
- aplica `formatar_canal` na coluna `canal`;
- aplica `formatar_categoria` na coluna `categoria`;
- aplica `formatar_funil` na coluna `funil`;
- renomeia as colunas com `COLUNAS_PLANO_RECOMENDADO`.

Impacto prático: a tabela na tela fica mais bonita e clara, mas o resultado bruto continua disponível para exportação.

Opinião técnica: é melhor preparar uma cópia para exibição do que alterar o resultado original. Assim, a visualização e a exportação não brigam entre si.

### `limpar_resultado_otimizacao() -> None`

Remove o resultado salvo da sessão do Streamlit.

Entrada: não recebe parâmetros.

Saída: não retorna valor.

Efeito colateral: remove a chave `CHAVE_RESULTADO_OTIMIZACAO` de `st.session_state`.

Uso no app: é chamada pelo botão `Novo cenário`.

Impacto prático: permite limpar o resultado atual e começar uma nova simulação sem manter na tela o plano calculado anteriormente.

## Funções de layout e entrada do usuário

### `configurar_pagina() -> None`

Configura a página do Streamlit.

Entrada: não recebe parâmetros.

Saída: não retorna valor.

O que ela faz:

- define o título da aba como `MixGen`;
- usa o logo como ícone da página;
- ativa layout largo com `layout='wide'`;
- exibe o logo na sidebar com `st.logo`.

Impacto prático: deixa o app com identidade visual consistente e mais espaço horizontal para a tabela e os gráficos.

### `renderizar_cabecalho() -> None`

Renderiza o cabeçalho principal do app.

Entrada: não recebe parâmetros.

Saída: não retorna valor.

O que ela mostra:

- logo do MixGen;
- título `MixGen`;
- texto curto explicando que o app otimiza mixes de marketing com investimento, retorno, risco e algoritmo genético.

Impacto prático: ajuda o usuário a entender rapidamente o propósito do app antes de mexer nos parâmetros.

### `renderizar_parametros() -> ConfigMarketingAG`

Renderiza os controles da barra lateral e transforma as escolhas em uma configuração do algoritmo genético.

Entrada: não recebe parâmetros.

Saída: retorna um objeto `ConfigMarketingAG`.

Campos exibidos:

- `Orçamento (R$ mil)`;
- `População`;
- `Gerações`;
- `Descendentes por geração`;
- `Taxa de crossover`;
- `Taxa de mutação`;
- `Peso do risco`;
- `Semente aleatória`.

Como cada campo afeta o algoritmo:

- orçamento define quanto o algoritmo pode distribuir;
- população define quantos planos candidatos existem em cada geração;
- gerações define por quanto tempo o processo evolutivo roda;
- descendentes define quantos novos planos são criados em cada ciclo;
- crossover controla quanto o algoritmo combina soluções existentes;
- mutação controla quanto ele explora alternativas novas;
- peso do risco penaliza planos mais arriscados no score de decisão;
- semente permite reproduzir o mesmo resultado.

Impacto prático: dá controle sobre a qualidade e o custo computacional da otimização. Mais população e mais gerações podem melhorar a busca, mas aumentam o tempo de cálculo.

### `renderizar_editor_canais(canais: pd.DataFrame) -> pd.DataFrame`

Renderiza a tabela editável de canais de marketing.

Entrada: um `DataFrame` com os canais carregados do CSV padrão.

Saída: um `DataFrame` com os dados editados pelo usuário.

Campos configurados no editor:

- `ID`;
- `Canal`;
- `Categoria`;
- `Funil`;
- `Mínimo (R$ mil)`;
- `Máximo (R$ mil)`;
- `Receita por R$ mil`;
- `Saturação`;
- `Risco`.

Recursos usados:

- `st.data_editor`, para permitir edição direta;
- `num_rows='dynamic'`, para permitir adicionar ou remover linhas;
- `SelectboxColumn`, para canal, categoria e funil;
- `NumberColumn`, para limites, retorno, saturação e risco;
- tooltips, para explicar cada coluna.

Impacto prático: permite simular cenários sem alterar o CSV padrão. Isso é útil para testar campanhas, novos canais, mudanças de risco e restrições de orçamento.

Opinião técnica: o editor é uma boa escolha para esse tipo de problema porque marketing mix é naturalmente uma tabela de alternativas com restrições.

## Funções de gráficos

### `grafico_alocacao_canal(plano: pd.DataFrame) -> go.Figure`

Cria um gráfico de barras horizontais com a alocação recomendada por canal.

Entrada: o plano detalhado retornado pelo motor.

Saída: uma figura Plotly.

O que o gráfico mostra:

- eixo X, investimento em R$ mil;
- eixo Y, canal formatado;
- cor da barra, lucro bruto do canal.

Impacto prático: mostra rapidamente quais canais receberam mais verba e quais têm maior contribuição de lucro.

### `grafico_alocacao_categoria(plano: pd.DataFrame) -> go.Figure`

Cria um gráfico de barras horizontais com a alocação agrupada por categoria.

Entrada: o plano detalhado retornado pelo motor.

Saída: uma figura Plotly.

Como funciona:

- agrupa o plano por `categoria`;
- soma investimento e lucro bruto;
- ordena pelo investimento;
- usa rótulos formatados para exibição.

Impacto prático: ajuda a enxergar a estratégia macro do plano, por exemplo quanto foi para mídia paga, relacionamento, orgânico, produto, B2B ou trade.

### `grafico_alocacao_funil(plano: pd.DataFrame) -> go.Figure`

Cria um gráfico de barras horizontais com a alocação agrupada por etapa do funil.

Entrada: o plano detalhado retornado pelo motor.

Saída: uma figura Plotly.

Como funciona:

- agrupa o plano por `funil`;
- soma investimento e lucro bruto;
- ordena pelo investimento;
- aplica rótulos como `Aquisição`, `Conversão`, `Nutrição` e `Retenção`.

Impacto prático: mostra se o plano está concentrado em topo, meio ou fundo de funil. Isso é útil para discutir equilíbrio entre geração de demanda, conversão e retenção.

### `grafico_fronteira(fronteira: pd.DataFrame, lucro: float, risco: float) -> go.Figure`

Cria o gráfico da fronteira de Pareto.

Entrada:

- `fronteira`, `DataFrame` com planos candidatos da fronteira;
- `lucro`, lucro do plano escolhido;
- `risco`, risco do plano escolhido.

Saída: uma figura Plotly.

O que o gráfico mostra:

- eixo X, risco ponderado;
- eixo Y, lucro estimado;
- tamanho dos pontos, receita estimada;
- cor dos pontos, score de decisão;
- marcador em formato de losango para o plano escolhido.

Impacto prático: ajuda a explicar o trade-off entre retorno e risco. Um plano pode ter lucro alto, mas também risco alto. A fronteira torna essa troca mais visível.

Opinião técnica: esse é um dos gráficos mais importantes para apresentação, porque mostra que a escolha não é apenas maximizar receita, mas equilibrar retorno, risco e sinergia.

### `grafico_convergencia(historico: pd.DataFrame) -> go.Figure`

Cria o gráfico de convergência do algoritmo genético.

Entrada: histórico de evolução por geração.

Saída: uma figura Plotly.

O que o gráfico mostra:

- melhor lucro encontrado por geração;
- lucro médio da população por geração.

Impacto prático: ajuda a verificar se o algoritmo evoluiu de fato ou se ficou estagnado. Se a curva melhora e depois estabiliza, isso sugere que a busca encontrou uma região boa de solução.

Cuidados:

- convergência não garante solução global ótima;
- poucas gerações podem gerar resultado fraco;
- mutação muito baixa pode reduzir exploração;
- mutação muito alta pode dificultar estabilização.

## Funções de resultado e orquestração

### `renderizar_resultado(resultado) -> None`

Renderiza toda a área de resultado após o cálculo.

Entrada: objeto de resultado retornado por `executar_algoritmo_genetico`.

Saída: não retorna valor.

O que ela renderiza:

- métricas principais;
- tabela `Plano recomendado`;
- botões de exportação;
- botão `Novo cenário`;
- abas de gráficos.

Métricas exibidas:

- receita estimada;
- lucro estimado;
- risco ponderado;
- sinergia.

Exportações:

- CSV, gerado a partir de `resultado.plano_detalhado`;
- XLSX, gerado por `gerar_excel_plano`.

Detalhe importante: os botões de download usam `on_click='ignore'`. Isso evita rerun desnecessário no Streamlit durante o download.

Impacto prático: o usuário consegue analisar o plano, comparar gráficos e exportar os dados sem perder o resultado calculado.

### `main() -> None`

É a função principal do app.

Entrada: não recebe parâmetros.

Saída: não retorna valor.

Responsabilidades:

- chama `configurar_pagina`;
- chama `renderizar_cabecalho`;
- coleta a configuração com `renderizar_parametros`;
- carrega os canais padrão;
- renderiza o editor de canais;
- cria o botão `Calcular plano otimizado`;
- quando o botão é clicado, normaliza e valida os dados;
- executa o algoritmo genético;
- salva o resultado em `st.session_state`;
- renderiza o resultado salvo;
- mostra uma mensagem inicial quando ainda não há cálculo.

Tratamento de erro:

- a execução fica dentro de `try/except`;
- se algo falhar, a interface mostra `Não foi possível calcular: ...`.

Impacto prático: concentra a ordem de execução do app em um único lugar, mas delega os detalhes para funções menores.

Opinião técnica: `main` funciona como uma camada de orquestração. Isso deixa o código mais fácil de explicar, porque cada parte tem um papel claro.

## Relação com o motor do algoritmo genético

O `streamlit_app.py` importa três itens do motor:

```python
from src.motor_algoritmo_genetico import (
    ConfigMarketingAG,
    executar_algoritmo_genetico,
    validar_canais,
)
```

### `ConfigMarketingAG`

É a estrutura de configuração do algoritmo.

No app, ela é criada em `renderizar_parametros`.

### `validar_canais`

Valida se a tabela de canais está coerente antes da otimização.

No app, ela é chamada em `main`, depois de `normalizar_canais`.

Impacto prático: evita rodar o algoritmo com IDs duplicados, limites inválidos, valores nulos ou outras inconsistências.

### `executar_algoritmo_genetico`

Executa a otimização de fato.

No app, ela é chamada em `main`, dentro do spinner `Calculando plano otimizado...`.

Impacto prático: recebe os canais normalizados e a configuração do usuário, depois devolve o plano recomendado, métricas, fronteira de Pareto e histórico de convergência.

## Resumo das responsabilidades

| Função | Responsabilidade principal |
| --- | --- |
| `carregar_canais_padrao` | Ler o CSV padrão |
| `normalizar_canais` | Preparar dados editados para validação e cálculo |
| `montar_opcoes_funil` | Montar opções do selectbox de funil |
| `montar_opcoes_categoria` | Montar opções do selectbox de categoria |
| `montar_opcoes_canal` | Montar opções do selectbox de canal |
| `formatar_canal` | Exibir canal com rótulo amigável |
| `formatar_categoria` | Exibir categoria com rótulo amigável |
| `formatar_funil` | Exibir funil com rótulo amigável |
| `gerar_excel_plano` | Criar arquivo XLSX em memória |
| `preparar_plano_recomendado_para_exibicao` | Formatar tabela final para leitura |
| `limpar_resultado_otimizacao` | Limpar resultado salvo da sessão |
| `configurar_pagina` | Configurar página, logo e layout |
| `renderizar_cabecalho` | Mostrar identidade e descrição do app |
| `renderizar_parametros` | Coletar parâmetros do algoritmo |
| `renderizar_editor_canais` | Permitir edição dos canais |
| `grafico_alocacao_canal` | Visualizar investimento por canal |
| `grafico_alocacao_categoria` | Visualizar investimento por categoria |
| `grafico_alocacao_funil` | Visualizar investimento por funil |
| `grafico_fronteira` | Visualizar trade-off entre risco e lucro |
| `grafico_convergencia` | Visualizar evolução do algoritmo |
| `renderizar_resultado` | Mostrar métricas, tabela, downloads e gráficos |
| `main` | Orquestrar todo o app |

## Leitura final

Fato: o `streamlit_app.py` é a camada de aplicação visual do MixGen.

Inferência: ele foi desenhado para permitir que uma pessoa altere premissas de marketing sem precisar mexer no código ou no CSV padrão.

Opinião técnica: a parte mais forte do desenho atual é a separação entre valor interno e rótulo visual. Isso preserva a consistência necessária para o algoritmo genético e, ao mesmo tempo, deixa o produto mais agradável para apresentação e deploy.
