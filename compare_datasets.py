"""Compara a distribuição de conteúdos entre os datasets CESPE (geral) e CACD.

Cruzamento disciplinas compartilhadas:
  - Direito Administrativo (Doutrina e Leis Federais)
  - Direito Constitucional (CF/1988 e Doutrina)
  - Língua Portuguesa (Português)

Uso:
    source venv/bin/activate
    python compare_datasets.py

Gera: compare_report.md (relatório markdown)
"""

import duckdb
import pandas as pd

# ── Carrega os dois datasets ─────────────────────────────────────
con = duckdb.connect()

con.execute(
    "CREATE TABLE cespe AS SELECT * FROM 'conteudo_dataset.parquet'"
)

con.execute(
    "CREATE TABLE cacd AS SELECT * FROM '/Users/gabrielramos/projetos/cespe-cacd/cacd_dataset.csv'"
)

# ── Disciplinas compartilhadas ───────────────────────────────────
SHARED = [
    "Direito Administrativo (Doutrina e Leis Federais)",
    "Direito Constitucional (CF/1988 e Doutrina)",
    "Língua Portuguesa (Português)",
]

report_lines = []
def w(line=""):
    report_lines.append(line)
    print(line)


w("# Comparação CESPE (Geral) vs CACD")
w()
w("Cruzamento das disciplinas compartilhadas entre o dataset geral")
w("CESPE/Cebraspe e o dataset específico do CACD (Diplomacia).")
w()
w(f"Gerado em: {pd.Timestamp.now().strftime('%Y-%m-%d %H:%M')}")
w()

# ── 1. Visão geral ───────────────────────────────────────────────
w("## 1. Visão Geral dos Datasets")
w()
cespe_total = con.execute("SELECT COUNT(*) FROM cespe").fetchone()[0]
cacd_total = con.execute("SELECT COUNT(*) FROM cacd").fetchone()[0]
w(f"| Dataset | Disciplinas | Linhas |")
w(f"|---------|------------|-------:|")
w(f"| CESPE (geral) | {con.execute('SELECT COUNT(DISTINCT disciplina) FROM cespe').fetchone()[0]} | {cespe_total} |")
w(f"| CACD          | {con.execute('SELECT COUNT(DISTINCT disciplina) FROM cacd').fetchone()[0]} | {cacd_total} |")
w()

w(f"Disciplinas compartilhadas: {', '.join(SHARED)}")
w()

# ── 2. Comparação por disciplina ─────────────────────────────────
w("## 2. Comparação por Disciplina")
w()
w("| Disciplina | Métrica | CESPE (geral) | CACD | Diferença |")
w("|------------|---------|--------------:|-----:|----------:|")

for disc in SHARED:
    for nivel in [0, 1]:
        label = "Raiz (total questões)" if nivel == 0 else "Tópicos N1"

        cespe_qty = con.execute("""
            SELECT SUM(quantidade_encontrada)
            FROM cespe
            WHERE disciplina = ? AND nivel_profundidade = ?
        """, [disc, nivel]).fetchone()[0] or 0

        cacd_qty = con.execute("""
            SELECT SUM(quantidade_encontrada)
            FROM cacd
            WHERE disciplina = ? AND nivel_profundidade = ?
        """, [disc, nivel]).fetchone()[0] or 0

        diff = cespe_qty - cacd_qty
        diff_pct = (diff / cacd_qty * 100) if cacd_qty else 0
        diff_str = f"{diff:+d} ({diff_pct:+.1f}%)" if cacd_qty else f"{diff:+d}"

        w(f"| {disc} | {label} | {int(cespe_qty):,} | {int(cacd_qty):,} | {diff_str} |")

    # N1 names overlap
    cespe_n1 = set(r[0] for r in con.execute("""
        SELECT DISTINCT assunto_nivel_1 FROM cespe WHERE disciplina = ? AND nivel_profundidade = 1
    """, [disc]).fetchall())

    cacd_n1 = set(r[0] for r in con.execute("""
        SELECT DISTINCT assunto_nivel_1 FROM cacd WHERE disciplina = ? AND nivel_profundidade = 1
    """, [disc]).fetchall())

    overlap = cespe_n1 & cacd_n1
    only_cespe = cespe_n1 - cacd_n1
    only_cacd = cacd_n1 - cespe_n1

    w(f"| {disc} | Tópicos N1 compartilhados | {len(overlap)} | — | {len(overlap)} |")
    w(f"| {disc} | Tópicos N1 só no CESPE | {len(only_cespe)} | — | — |")
    w(f"| {disc} | Tópicos N1 só no CACD | — | {len(only_cacd)} | — |")
    w()

# ── 3. Tópicos exclusivos de cada dataset ────────────────────────
w("## 3. Tópicos Exclusivos do CESPE (não mapeados no CACD)")
w()

for disc in SHARED:
    only_cespe = con.execute("""
        SELECT DISTINCT c.assunto_nivel_1
        FROM cespe c
        WHERE c.disciplina = ?
          AND c.nivel_profundidade = 1
          AND NOT EXISTS (
              SELECT 1 FROM cacd o
              WHERE o.disciplina = c.disciplina
                AND o.assunto_nivel_1 = c.assunto_nivel_1
          )
        ORDER BY c.assunto_nivel_1
    """, [disc]).fetchall()

    if only_cespe:
        w(f"**{disc}**")
        for (t,) in only_cespe:
            qty = con.execute("""
                SELECT SUM(quantidade_encontrada)
                FROM cespe
                WHERE disciplina = ? AND assunto_nivel_1 = ? AND nivel_profundidade >= 1
            """, [disc, t]).fetchone()[0] or 0
            w(f"- {t} ({int(qty):,} questões no CESPE)")
        w()

w("## 4. Tópicos Exclusivos do CACD (não mapeados no CESPE)")
w()

for disc in SHARED:
    only_cacd = con.execute("""
        SELECT DISTINCT c.assunto_nivel_1
        FROM cacd c
        WHERE c.disciplina = ?
          AND c.nivel_profundidade = 1
          AND NOT EXISTS (
              SELECT 1 FROM cespe o
              WHERE o.disciplina = c.disciplina
                AND o.assunto_nivel_1 = c.assunto_nivel_1
          )
        ORDER BY c.assunto_nivel_1
    """, [disc]).fetchall()

    if only_cacd:
        w(f"**{disc}**")
        for (t,) in only_cacd:
            qty = con.execute("""
                SELECT SUM(quantidade_encontrada)
                FROM cacd
                WHERE disciplina = ? AND assunto_nivel_1 = ? AND nivel_profundidade >= 1
            """, [disc, t]).fetchone()[0] or 0
            w(f"- {t} ({int(qty):,} questões no CACD)")
        w()

# ── 5. Distribuição de profundidade ──────────────────────────────
w("## 5. Profundidade da Hierarquia")
w()
w("| Disciplina | Dataset | Profundidade Máx | Tópicos N1 | Total Linhas |")
w("|------------|---------|-----------------:|-----------:|-------------:|")

for disc in SHARED:
    for src, table in [("CESPE", "cespe"), ("CACD", "cacd")]:
        info = con.execute(f"""
            SELECT MAX(nivel_profundidade), COUNT(DISTINCT assunto_nivel_1), COUNT(*)
            FROM {table}
            WHERE disciplina = ?
        """, [disc]).fetchone()
        w(f"| {disc} | {src} | {info[0]} | {info[1]} | {info[2]} |")
w()

# ── 6. Correlação de proporções ──────────────────────────────────
w("## 6. Proporção de Questões por Disciplina")
w()
w("Comparação de quanto cada disciplina representa dentro de cada dataset.")
w()

for disc in SHARED:
    cespe_pct = con.execute("""
        SELECT ROUND(100.0 * SUM(quantidade_encontrada) / (SELECT SUM(quantidade_encontrada) FROM cespe WHERE nivel_profundidade = 0), 2)
        FROM cespe WHERE disciplina = ? AND nivel_profundidade = 0
    """, [disc]).fetchone()[0] or 0

    cacd_pct = con.execute("""
        SELECT ROUND(100.0 * SUM(quantidade_encontrada) / (SELECT SUM(quantidade_encontrada) FROM cacd WHERE nivel_profundidade = 0), 2)
        FROM cacd WHERE disciplina = ? AND nivel_profundidade = 0
    """, [disc]).fetchone()[0] or 0

    w(f"| **{disc}** | CESPE: **{cespe_pct:.2f}%** | CACD: **{cacd_pct:.2f}%** |")
w()

# ── Salva relatório ──────────────────────────────────────────────
with open("compare_report.md", "w", encoding="utf-8") as f:
    f.write("\n".join(report_lines))

print(f"\nRelatório salvo: compare_report.md ({len(report_lines)} linhas)")
con.close()
