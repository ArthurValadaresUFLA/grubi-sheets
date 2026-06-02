# grubi-sheets

Ferramenta em Python para executar simulações Java em lote, coletar os logs gerados, extrair eventos de
envio/recebimento de pacotes e produzir saídas em **CSV** e **ODS** para análise.

O projeto foi pensado para automatizar um fluxo comum de experimentação:

1. executar uma classe Java principal;
2. repetir a simulação várias vezes;
3. salvar os logs individuais de cada execução;
4. interpretar os eventos relevantes encontrados na saída;
5. consolidar os dados em planilha e CSV.


## Visão geral

O pacote expõe um comando de linha de comando chamado `simulate`, que:

- localiza o binário do Java automaticamente ou usa um binário informado;
- executa uma classe principal Java com `classpath` configurável;
- permite passar argumentos para a simulação;
- executa múltiplas repetições em paralelo;
- salva um log por execução;
- extrai eventos dos logs;
- gera:
    - um arquivo **CSV** com os eventos;
    - um arquivo **ODS** com relatório tabular e fórmulas estatísticas.

## Estrutura do projeto

```text
grubi-sheets/
├── src/
│   └── simulator/
│       ├── __init__.py
│       ├── cli.py
│       ├── parser.py
│       ├── report.py
│       └── runner.py
├── tests/
├── pyproject.toml
└── README.md
```

### Descrição das pastas e arquivos

#### `src/simulator/`

Contém o código principal da aplicação.

- **`cli.py`**  
  Define a ‘interface’ de linha de comando com `click`.  
  É o ponto de entrada do comando `simulate`.

- **`runner.py`**  
  Responsável por:
    - localizar o Java;
    - montar o comando de execução;
    - executar a simulação;
    - tratar timeout;
    - executar repetições em paralelo;
    - salvar logs individuais.

- **`parser.py`**  
  Faz a leitura dos logs e extrai eventos relevantes usando expressões regulares.

- **`report.py`**  
  Gera o relatório em formato **ODS**, incluindo colunas com fórmulas para média, desvio padrão e desvio padrão
  relativo.

#### `logs/`

Diretório sugerido para armazenar os logs das execuções.  
Cada simulação gera um arquivo como:

```text
sim_0001.log
sim_0002.log
sim_0003.log
```

#### `tests/`

Pasta reservada para testes automatizados do projeto.

#### `pyproject.toml`

Arquivo de configuração do projeto Python.  
Nele estão definidos:

- nome do projeto;
- versão;
- dependências;
- requisito de versão do Python;
- script de entrada `simulate`.

## Como o projeto funciona

O fluxo principal é:

1. o usuário executa o comando `simulate`;
2. a ferramenta monta um comando Java com:
    - binário Java;
    - opções da JVM;
    - classpath;
    - classe principal;
    - argumentos da simulação;
3. a execução é repetida o número de vezes solicitado;
4. as execuções podem ocorrer em paralelo;
5. o stdout de cada execução é salvo em arquivo de log;
6. os logs bem-sucedidos são processados;
7. os eventos extraídos são exportados para CSV;
8. um relatório ODS é gerado a partir desses eventos.

## Requisitos

## Python

O projeto declara compatibilidade com:

- **Python >= 3.14 e < 4.0**

## Java

É necessário ter Java disponível de uma das formas abaixo:

- configurado via variável de ambiente `JAVA_HOME`; ou
- disponível no `PATH` como `java`.

Se o Java não for encontrado, a execução falhará.

## Instalação

### Uso

#### Opção 1: Instalar com o pipx (Recomendado)

O `pipx` é a ferramenta ideal para instalar aplicativos CLI feitos em Python, pois ele instala o pacote em um ambiente isolado, mas expõe o comando globalmente no seu terminal, evitando conflitos com outras dependências do sistema.

```bash
pipx install . # Se clonou o projeto
pipx install git+https://github.com/ArthurValadaresUFLA/grubi-sheets.git # Se somente quer instalar
pipx install git+https://github.com/ArthurValadaresUFLA/grubi-sheets.git@v0.1.0 # Se somente quer instalar uma versão específica
```

#### Opção 2: Instalar com pip

Se quiser instalar o projeto como pacote local:

Você pode instalar diretamente usando o gerenciador de pacotes padrão do Python.

> ⚠️ **Nota:** Se estiver em distribuições Linux modernas (como Ubuntu 23.04+, Debian 12+, etc.), o `pip` global pode bloquear a instalação devido à regra de ambiente gerenciado externamente (PEP 668). Nesse caso, prefira o `pipx` acima ou use um ambiente virtual (`venv`).

```bash
pip install . # Se clonou o projeto
pip install git+https://github.com/ArthurValadaresUFLA/grubi-sheets.git # Se somente quer instalar
pip install git+https://github.com/ArthurValadaresUFLA/grubi-sheets.git@v0.1.0 # Se somente quer instalar uma versão específica
```

Depois disso, o comando pode ficar disponível como:

```bash
simulate --help
```

### Desenvolvimento

#### Opção 1: Instalar com Poetry

Se você usa Poetry:

```bash
poetry install
```

Para executar o comando dentro do ambiente Poetry:

```bash
poetry run simulate --help
```

### Opção 2: Instalar com o Pip

Se quiser instalar em modo editável:

```bash
pip install -e .
```

## Configuração do ambiente

### Verificar Python

```bash
python --version
```

### Verificar Java

```bash
java -version
```

### Configurar `JAVA_HOME` se necessário

Exemplo em Linux/macOS:

```bash
export JAVA_HOME=/caminho/para/java
export PATH="$JAVA_HOME/bin:$PATH"
```

Exemplo em Windows PowerShell:

```powershell
$env:JAVA_HOME="C:\caminho\para\java"
$env:Path="$env:JAVA_HOME\bin;$env:Path"
```

## Uso

## Comando principal

```bash
simulate --help
```

### Parâmetros disponíveis

- `--java-bin`  
  Caminho para o executável Java.  
  Opcional. Se omitido, o sistema tenta localizar automaticamente.

- `--main-class`  
  Classe principal Java a ser executada.  
  Obrigatório.

- `--class-path`  
  Classpath usado na execução Java.  
  Obrigatório.

- `--java-opt`  
  Opções adicionais da JVM.  
  Pode ser informado múltiplas vezes.

- `--simulation-args`  
  String com os argumentos passados para a simulação.

- `--repeat`  
  Número de repetições da simulação.  
  Padrão: `1`.

- `--threads`  
  Quantidade de execuções paralelas.  
  Por padrão usa a quantidade de CPUs disponíveis.

- `--timeout`  
  Timeout por execução, em segundos.

- `--output`  
  Caminho do arquivo `.ods` de saída.  
  Obrigatório.

- `--logs`  
  Diretório onde os logs serão salvos.  
  Obrigatório.

- `--csv-output`  
  Caminho do arquivo `.csv` de saída.  
  Obrigatório.

- `--regex-file`
  Caminho para o arquivo de texto simples contendo os padrões regex.
  Obrigatório.

- `--group-by`
  Colunas para agrupar no ODS
  Obrigatório.

- `--calc-col`
  Coluna numérica para aplicar as fórmular no ODS.
  Obrigatória.

## Exemplo de uso

```bash
simulate \
      --main-class Main \
      --class-path ./src \
      --class-path ./bin \
      --class-path "./lib/**/*.jar" \
      --regex-file "./regex.env" \
      --group-by simulation \
      --group-by send_id \
      --group-by packet_type \
      --calc-col timestamp \
      --repeat 5 \
      --threads 8 \
      --java-opt="-Xmx128m" \
      --java-opt="-XX:+TieredCompilation" \
      --java-opt="-XX:TieredStopAtLevel=1" \
      --output "./output/resultado.ods" \
      --csv-output "./output/dados.csv" \
      --logs "./logs"
```

## Saídas geradas

## Logs

Cada execução gera um log individual no diretório informado em `--logs`.

Exemplo:

```text
logs/
├── sim_0001.log
├── sim_0002.log
├── sim_0003.log
└── ...
```

## CSV

O CSV contém uma linha por evento extraído do log, com as colunas:

- `simulation`
- `send_id`
- `packet_type`
- `hop_index`
- `sender`
- `receiver`
- `timestamp`

Esse arquivo é útil para:

- análise em scripts;
- importação em pandas;
- geração de gráficos;
- auditoria dos dados extraídos.

## ODS

O relatório ODS contém colunas para análise tabular:

- **Simulação**
- **Envio**
- **Tipo**
- **Hop**
- **Origem**
- **Destino**
- **Tempo**
- **Diferença**
- **Média**
- **Desvio Padrão**
- **DP Relativo**

Além dos dados extraídos, o relatório inclui fórmulas para:

- diferença temporal entre hops;
- média das diferenças;
- desvio padrão;
- desvio padrão relativo.

## Formato esperado dos logs

O parser procura padrões específicos na saída da simulação.

Ele identifica:

1. eventos de envio, usados para incrementar o contador de envio;
2. eventos de pacote recebidos, usados para gerar os registros da planilha.

Como a extração depende de expressões regulares, é necessário fornecer o arquivo contendo as expressões regulares e os grupos de captura

## Processamento dos dados

Cada evento extraído representa um pacote com os seguintes campos:

- `simulation`: identificador da simulação;
- `send_id`: identificador sequencial do envio;
- `packet_type`: tipo do pacote;
- `sender`: nó de origem;
- `receiver`: nó de destino;
- `timestamp`: tempo do evento;
- `hop_index`: índice do hop dentro do agrupamento.

Os eventos são agrupados por:

- simulação;
- envio;
- tipo de pacote.

A partir disso, o relatório calcula estatísticas por grupo.

## Execução paralela

As simulações podem ser executadas em paralelo por meio de threads.

Isso é controlado pelo parâmetro:

```bash
--threads
```

### Recomendações

- use valores maiores para aumentar throughput quando as execuções forem independentes;
- reduza a quantidade de threads se houver contenção de CPU, memória ou disco;
- ajuste o `--timeout` para evitar execuções travadas por muito tempo.

## Tratamento de falhas

Se uma simulação falhar:

- ela será marcada como falha;
- o retorno da execução será exibido no terminal;
- o log ainda será salvo;
- os dados dessa execução não serão incluídos na extração de eventos.

Também há tratamento para timeout: execuções que excedem o limite informado em `--timeout` retornam como falha.

## Desenvolvimento

## Executar o comando localmente

Via Poetry:

```bash
poetry run simulate --help
```

Ou, se o pacote estiver instalado em modo editável:

```bash
simulate --help
```

## Estrutura modular

O projeto está separado por responsabilidade:

- **CLI**: entrada e argumentos;
- **Runner**: execução do Java e paralelismo;
- **Parser**: interpretação dos logs;
- **Report**: geração do ODS.

Essa separação facilita manutenção e evolução.

## Possíveis melhorias futuras

Algumas evoluções naturais para o projeto:

- adicionar testes automatizados;
- validar melhor os argumentos de entrada;
- suportar outros formatos de relatório, como XLSX;
- tornar o parser configurável;
- incluir barras de progresso e métricas de execução;
- adicionar perfis de execução para diferentes cenários de simulação.

## Solução de problemas

### `Java não encontrado`

Verifique se:

- `JAVA_HOME` está configurado corretamente; ou
- o comando `java` está disponível no `PATH`.

Teste com:

```bash
java -version
```

### Nenhum evento aparece no CSV/ODS

Verifique se:

- a simulação está produzindo saída no formato esperado;
- os logs foram realmente gerados;
- as execuções não falharam;
- o parser está compatível com o texto emitido pela aplicação Java.

### Classpath incorreto

Se a classe principal não for encontrada, revise:

- o valor de `--classpath`;
- o nome informado em `--main-class`;

### Execuções muito lentas

Tente:

- reduzir `--repeat`;
- ajustar `--threads`;
- revisar opções de JVM com `--java-opt`;
- limitar cenários muito pesados na simulação.

## Autor

Projeto configurado com autoria de:

- Arthur Valadares Campideli

