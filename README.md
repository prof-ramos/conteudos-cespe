---
configs:
  - config_name: default
    data_files:
      - split: train
        path: conteudo_dataset.csv
license: cc-by-4.0
dataset_info:
  features:
    - name: linha_original
      dtype: int64
    - name: disciplina
      dtype: string
    - name: hierarquia_codigo
      dtype: string
    - name: nivel_profundidade
      dtype: int64
    - name: assunto_nivel_1
      dtype: string
    - name: assunto_nivel_2
      dtype: string
    - name: assunto_nivel_3
      dtype: string
    - name: assunto_nivel_4
      dtype: string
    - name: assunto_especifico
      dtype: string
    - name: quantidade_encontrada
      dtype: int64
    - name: porcentagem_encontrada
      dtype: float64
    - name: quantidade_caderno
      dtype: int64
    - name: porcentagem_caderno
      dtype: float64
  citation: |-
    @misc{gabriel-ramos-conteudos-cespe,
      author       = {Gabriel Ramos},
      title        = {conteudos-cespe: Distribuição de Conteúdos CESPE/Cebraspe},
      year         = {2026},
      publisher    = {Hugging Face},
      journal      = {Hugging Face Datasets},
      howpublished = {https://huggingface.co/datasets/profgabrielramos/conteudos-cespe}
    }
---

[![CC BY 4.0](https://img.shields.io/badge/License-CC%20BY%204.0-lightgrey.svg)](https://creativecommons.org/licenses/by/4.0/)
[![Hugging Face Dataset](https://img.shields.io/badge/%F0%9F%A4%97-Dataset%20Hub-yellow)](https://huggingface.co/datasets/profgabrielramos/conteudos-cespe)
[![Python 3.12+](https://img.shields.io/badge/Python-3.12%2B-blue)](https://www.python.org/)

# conteúdos-cespe

Dataset contendo a análise e distribuição de conteúdos programáticos (Direito Administrativo, Direito Constitucional, Língua Portuguesa e Raciocínio Lógico) da banca CESPE/Cebraspe.

Este dataset foi gerado a partir do arquivo original `conteudo.xlsx` e estruturado hierarquicamente para facilitar o agrupamento, filtragem e análise de dados.

## Estrutura do Dataset

O dataset possui uma hierarquia detalhada dividida em até 4 níveis de assuntos/tópicos:

| Coluna | Descrição |
|---|---|
| `id` | Identificador único SHA-256 truncado (16 chars), estável entre fontes. |
| `linha_original` | Índice da linha no arquivo Excel de origem. |
| `fonte` | Arquivo de origem (`conteudo.xlsx`, `adm_detalhado`, `const_detalhado`). |
| `disciplina` | Disciplina principal (ex: Direito Administrativo, Língua Portuguesa). |
| `nivel_profundidade` | Nível de profundidade (0 = raiz da disciplina, 1 a 4 = subníveis). |
| `hierarquia_codigo` | Código numérico hierárquico (ex: `01`, `01.02`, `03.02.04.01`). Vazio para níveis raiz. |
| `assunto_nivel_1` a `assunto_nivel_4` | Tópicos e subtópicos propagados do ancestral mais próximo. |
| `assunto_especifico` | Nome do tópico correspondente a esta linha específica. |
| `quantidade_encontrada` | Número total de questões encontradas daquele tópico. |
| `porcentagem_encontrada` | Percentual de questões sobre o **total geral** (absoluto, não relativo ao pai). |
| `quantidade_caderno` / `porcentagem_caderno` | Quantidade e percentual considerando apenas o caderno de origem. |
| `ano` | Ano da prova (ex: 2024). |
| `banca` | Banca organizadora (CESPE/Cebraspe). |
| `cargo` | Cargo do concurso (ex: Diplomata). |
| `split` | Partição treino/teste estratificada por disciplina (`train` = 80%, `test` = 20%). |

> As porcentagens (`porcentagem_encontrada` e `porcentagem_caderno`) são **absolutas** em relação ao total geral de questões. A soma das porcentagens dos filhos de um mesmo pai pode ultrapassar a porcentagem do pai — isso é esperado, pois cada valor é calculado sobre o total da amostra, não como fração do nó superior.

## Notas sobre a Origem dos Dados

O dataset é gerado a partir de **três arquivos Excel** processados pelo `generate_dataset.py`:

| Fonte | Disciplina | Subdivisões | Linhas |
|---|---|---|---|
| `conteudo.xlsx` | Língua Portuguesa (Português) | N1 a N4 | 85 |
| `conteudo.xlsx` | Raciocínio Lógico | N1 a N3 | 29 |
| `5ed5ac0a...xlsx` | Direito Administrativo (Doutrina e Leis Federais) | N1 a N3 | 263 |
| `a005733c...xlsx` | Direito Constitucional (CF/1988 e Doutrina) | N1 a N4 | 200 |

As planilhas detalhadas de Direito Administrativo e Direito Constitucional foram fornecidas em arquivos complementares e integradas ao pipeline. O script de geração (`generate_dataset.py`) processa os três arquivos e consolida em um único dataset.

## Arquivos Disponíveis neste Repositório

* `conteudo_dataset.csv`: Dataset limpo e delimitado por vírgulas (577 linhas, 4 disciplinas).
* `conteudo_dataset.json`: Dataset estruturado em formato JSON.
* `conteudo_dataset.parquet`: Dataset otimizado em formato colunar Parquet.
* `conteudo_dataset.xlsx`: Dataset em formato de planilha limpa do Excel.
* `conteudo.xlsx`: Planilha Excel original (Português + Raciocínio Lógico).
* `generate_dataset.py`: Script Python para reprodução do pipeline de dados (processa os 3 arquivos Excel).

## Licença

Este dataset é disponibilizado sob a licença **Creative Commons Attribution 4.0 International (CC BY 4.0)**.
