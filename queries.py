"""Exemplos de consulta ao dataset conteudos-cespe usando DuckDB.

Uso:
    source venv/bin/activate
    python queries.py

Requer: pip install duckdb pandas
"""

import duckdb

con = duckdb.connect()

# ── Carrega o dataset (Parquet é o formato mais eficiente) ────────
con.execute("CREATE TABLE conteudos AS SELECT * FROM 'conteudo_dataset.parquet'")


def show(title, sql):
    """Executa a query e exibe os resultados formatados."""
    print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")
    rows = con.execute(sql).fetchall()
    desc = con.description
    col_w = [len(d[0]) for d in desc]
    for row in rows:
        for i, val in enumerate(row):
            col_w[i] = max(col_w[i], len(str(val)))
    fmt = "  " + "  ".join(f"{{:<{w}s}}" for w in col_w)
    header = tuple(d[0] for d in desc)
    print(fmt.format(*header))
    print("  " + "  ".join("-" * w for w in col_w))
    for row in rows:
        print(fmt.format(*(str(v) for v in row)))
    print(f"  ({len(rows)} rows)")


# ── 1. Top 10 assuntos mais cobrados ─────────────────────────────
show(
    "1. Top 10 assuntos específicos mais cobrados",
    """
    SELECT disciplina, assunto_especifico, quantidade_encontrada
    FROM conteudos
    WHERE nivel_profundidade >= 1
    ORDER BY quantidade_encontrada DESC
    LIMIT 10
    """,
)

# ── 2. Distribuição de questões por disciplina ───────────────────
show(
    "2. Distribuição por disciplina (raízes)",
    """
    SELECT disciplina,
           quantidade_encontrada AS questoes,
           ROUND(porcentagem_encontrada, 2) AS pct_global
    FROM conteudos
    WHERE nivel_profundidade = 0
    ORDER BY quantidade_encontrada DESC
    """,
)

# ── 3. Subtópicos de Direito Administrativo (N1) ────────────────
show(
    "3. Tópicos N1 de Direito Administrativo",
    """
    SELECT assunto_nivel_1 AS topico,
           COUNT(*) AS subdivisoes,
           SUM(quantidade_encontrada) AS questoes
    FROM conteudos
    WHERE disciplina LIKE 'Direito Administrativo%'
      AND nivel_profundidade = 1
    GROUP BY assunto_nivel_1
    ORDER BY questoes DESC
    """,
)

# ── 4. Distribuição treino/teste ────────────────────────────────
show(
    "4. Split treino/teste por disciplina",
    """
    SELECT disciplina,
           COUNT(*) AS total,
           SUM(CASE WHEN split = 'train' THEN 1 ELSE 0 END) AS treino,
           SUM(CASE WHEN split = 'test'  THEN 1 ELSE 0 END) AS teste,
           ROUND(100.0 * SUM(CASE WHEN split = 'test' THEN 1 ELSE 0 END) / COUNT(*), 1) AS pct_teste
    FROM conteudos
    GROUP BY disciplina
    ORDER BY disciplina
    """,
)

# ── 5. Estrutura de Raciocínio Lógico ────────────────────────────
show(
    "5. Estrutura hierárquica de Raciocínio Lógico",
    """
    SELECT printf('%*s', nivel_profundidade * 2, '') || CASE
        WHEN nivel_profundidade = 0 THEN assunto_especifico
        WHEN nivel_profundidade = 1 THEN '├─ ' || assunto_nivel_1
        WHEN nivel_profundidade = 2 THEN '└─ ' || assunto_nivel_2
        ELSE '  └─ ' || assunto_nivel_3
    END AS arvore,
    quantidade_encontrada AS qtd
    FROM conteudos
    WHERE disciplina = 'Raciocínio Lógico'
    ORDER BY hierarquia_codigo
    """,
)

# ── 6. Profundidade por disciplina ──────────────────────────────
show(
    "6. Profundidade máxima por disciplina",
    """
    SELECT disciplina,
           MAX(nivel_profundidade) AS profundidade_max,
           COUNT(DISTINCT assunto_nivel_1) AS topicos_n1,
           COUNT(*) AS total_linhas
    FROM conteudos
    GROUP BY disciplina
    ORDER BY profundidade_max DESC, topicos_n1 DESC
    """,
)

# ── 7. Fontes dos dados ─────────────────────────────────────────
show(
    "7. Distribuição por fonte de origem",
    """
    SELECT fonte,
           COUNT(*) AS linhas,
           SUM(quantidade_encontrada) AS questoes,
           ROUND(100.0 * SUM(quantidade_encontrada) / (SELECT SUM(quantidade_encontrada) FROM conteudos WHERE nivel_profundidade = 0), 1) AS pct_global
    FROM conteudos
    GROUP BY fonte
    ORDER BY questoes DESC
    """,
)

con.close()
