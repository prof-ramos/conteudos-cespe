"""
Pipeline de geração do dataset conteúdos-cespe.

Processa 3 arquivos Excel fonte e produz dataset consolidado em CSV, JSON,
Parquet e XLSX com ID estável (hash SHA-256), hierarquia propagada e
porcentagens normalizadas sobre o total geral.

Uso:
    python3 generate_dataset.py
"""
import hashlib
import pandas as pd

# ── Constantes ───────────────────────────────────────────────────────────────
OVERALL_TOTAL = 22854 + 15063 + 26458 + 2382  # = 66757 (soma das raízes)

# Metadados do edital
METADATA = {
    "ano": 2026,
    "banca": "CESPE/Cebraspe",
    "cargo": "Concursos Públicos (Geral)",
}

# Source files: (path, scale_pct_to_overall, source_label)
# Os arquivos novos têm % relativa à disciplina (root=100%); o original já tem % global.
FILES = [
    ("conteudo.xlsx", False, "conteudo.xlsx"),                                                                     # Português + RL
    ("/Users/gabrielramos/Downloads/5ed5ac0a-4bfc-47d7-83b7-20a860f62c9e.xlsx", True, "adm_detalhado"),            # Direito Administrativo
    ("/Users/gabrielramos/Downloads/a005733c-d53d-4219-8bb7-43c38c12948d.xlsx", True, "const_detalhado"),           # Direito Constitucional
]

# Disciplinas que vêm dos arquivos novos (remover duplicatas do original)
SUBSTITUTED_DISCIPLINAS = [
    "Direito Administrativo (Doutrina e Leis Federais)",
    "Direito Constitucional (CF/1988 e Doutrina)",
]

# Ordem de exibição das disciplinas
DISCIPLINA_ORDER = {
    "Direito Administrativo (Doutrina e Leis Federais)": 0,
    "Direito Constitucional (CF/1988 e Doutrina)": 1,
    "Língua Portuguesa (Português)": 2,
    "Raciocínio Lógico": 3,
}


# ── Helpers ──────────────────────────────────────────────────────────────────

def make_id(disciplina, hierarquia_codigo, assunto_especifico):
    """Gera um ID estável (SHA-256 truncado) a partir da identidade conceitual
    do registro: disciplina + código hierárquico + nome do tópico.

    Se hierarquia_codigo e assunto_especifico forem vazios (nó raiz), usa
    apenas a disciplina."""
    raw = f"{disciplina}|{hierarquia_codigo}|{assunto_especifico}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:16]


def parse_percentage(val):
    if pd.isna(val):
        return 0.0
    val_str = str(val).replace("%", "").strip()
    try:
        return float(val_str)
    except ValueError:
        return 0.0


def process_excel(filepath, scale_pct_to_overall=False, source_label=""):
    """Processa uma planilha Excel e retorna registros como lista de dicts.

    Args:
        filepath: Caminho para o .xlsx (deve ter sheet 'Índice do Caderno').
        scale_pct_to_overall: Se True, recalcula % de disciplina-relativa
                              para global.
        source_label: Identificador da fonte (ex: "adm_detalhado").

    Returns:
        list[dict] com os campos normalizados do dataset.
    """
    df = pd.read_excel(filepath, sheet_name="Índice do Caderno")
    active_path = {0: None, 1: None, 2: None, 3: None, 4: None}
    records = []

    for idx, row in df.iterrows():
        h = row["Hierarquia"]
        indice = row["Índice"]

        # Atualiza caminho hierárquico
        if pd.isna(h):
            active_path[0] = indice
            for l in range(1, 5):
                active_path[l] = None
            level = 0
        else:
            parts = str(h).split(".")
            level = len(parts)
            active_path[level] = indice
            for l in range(level + 1, 5):
                active_path[l] = None

        pct_enc = parse_percentage(row["Porcentagem"])
        pct_cad = parse_percentage(row["Porcentagem.1"])
        qty_enc = int(row["Quantidade encontrada"])
        qty_cad = int(row["Quantidade no caderno"])

        # Escala % de disciplina-relativa para global
        if scale_pct_to_overall and qty_enc > 0:
            pct_enc = round(qty_enc / OVERALL_TOTAL * 100, 2)
            pct_cad = round(qty_cad / OVERALL_TOTAL * 100, 2)

        disciplina = active_path[0]
        hierarquia_codigo = h if pd.notna(h) else ""

        records.append(
            {
                "id": make_id(disciplina, hierarquia_codigo, indice),
                "linha_original": idx,
                "fonte": source_label,
                "disciplina": disciplina,
                "hierarquia_codigo": hierarquia_codigo,
                "nivel_profundidade": level,
                "assunto_nivel_1": active_path[1] if active_path[1] else "",
                "assunto_nivel_2": active_path[2] if active_path[2] else "",
                "assunto_nivel_3": active_path[3] if active_path[3] else "",
                "assunto_nivel_4": active_path[4] if active_path[4] else "",
                "assunto_especifico": indice,
                "quantidade_encontrada": qty_enc,
                "porcentagem_encontrada": pct_enc,
                "quantidade_caderno": qty_cad,
                "porcentagem_caderno": pct_cad,
            }
        )

    return records


# ── Pipeline principal ──────────────────────────────────────────────────────

def main():
    all_records = []

    for filepath, scale_pct, source_label in FILES:
        label = filepath.split("/")[-1]
        print(f"Processing: {label}")
        records = process_excel(filepath, scale_pct, source_label)
        print(f"  -> {len(records)} rows")
        all_records.extend(records)

    # Remove as linhas raiz do arquivo original que foram substituídas
    # pelos arquivos detalhados. A coluna `fonte` identifica a origem.
    for disc in SUBSTITUTED_DISCIPLINAS:
        all_records = [
            r
            for r in all_records
            if not (
                r["disciplina"] == disc
                and r["hierarquia_codigo"] == ""
                and r["fonte"] == "conteudo.xlsx"
            )
        ]

    print(f"\nAfter dedup: {len(all_records)} rows")

    # Monta DataFrame e adiciona metadados
    df = pd.DataFrame(all_records)
    for key, val in METADATA.items():
        df[key] = val

    # Ordenação estável
    df["_sort"] = df["disciplina"].map(DISCIPLINA_ORDER)
    df = df.sort_values(["_sort", "nivel_profundidade", "hierarquia_codigo"])
    df = df.drop(columns=["_sort"]).reset_index(drop=True)

    # ── Split treino/teste ─────────────────────────────────────────────────
    # Estratificado por disciplina: 80% treino, 20% teste.
    # Usamos random_state fixo para reprodutibilidade.
    test_indices = (
        df.groupby("disciplina")
        .apply(lambda g: g.sample(frac=0.2, random_state=42).index)
        .values
    )
    # .apply pode retornar numpy array aninhado; achata
    flat_indices = []
    for v in test_indices:
        if hasattr(v, "__iter__"):
            flat_indices.extend(v)
        else:
            flat_indices.append(v)

    df["split"] = "train"
    df.loc[flat_indices, "split"] = "test"

    print("\nSplit distribution:")
    print(df.groupby(["disciplina", "split"]).size().to_string())
    print()

    # ── Export ─────────────────────────────────────────────────────────────
    outputs = {
        "csv": ("conteudo_dataset.csv", lambda d, p: d.to_csv(p, index=False, encoding="utf-8-sig")),
        "json": ("conteudo_dataset.json", lambda d, p: d.to_json(p, orient="records", indent=2, force_ascii=False)),
        "parquet": ("conteudo_dataset.parquet", lambda d, p: d.to_parquet(p, index=False)),
        "xlsx": ("conteudo_dataset.xlsx", lambda d, p: d.to_excel(p, index=False)),
    }

    for fmt, (path, saver) in outputs.items():
        saver(df, path)
        print(f"  {fmt.upper():6s} -> {path}")

    print(f"\nTotal rows: {len(df)}")
    print(f"Columns: {list(df.columns)}")
    print()

    # Sumário por disciplina
    print("Per-discipline summary:")
    for disc in sorted(df["disciplina"].unique()):
        sub = df[df["disciplina"] == disc]
        max_depth = sub["nivel_profundidade"].max()
        n1_count = len(sub[sub["nivel_profundidade"] == 1])
        total_qty = sub["quantidade_encontrada"].sum()
        n_train = (sub["split"] == "train").sum()
        n_test = (sub["split"] == "test").sum()
        print(
            f"  {disc}: rows={len(sub)}"
            f" (train={n_train}, test={n_test}),"
            f" depth=0..{max_depth}, N1={n1_count},"
            f" qty={int(total_qty)}"
        )

    grand = int(df[df["nivel_profundidade"] == 0]["quantidade_encontrada"].sum())
    print(f"\nGrand total (root sums): {grand}")


if __name__ == "__main__":
    main()
