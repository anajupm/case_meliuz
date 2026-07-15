import pandas as pd

# CSV column names, kept in Portuguese because they must match the raw file
# header exactly (single source of truth).
COL_DATE = "Data"
COL_GROUP = "Grupos de usuários"
COL_PARTNER = "Parceiro"
COL_BUYERS = "compradores"
COL_COMMISSION = "comissão"
COL_CASHBACK = "cashback"
COL_SALES = "vendas totais"

MONETARY_COLS = [COL_COMMISSION, COL_CASHBACK, COL_SALES]


def _parse_brl_currency(series: pd.Series) -> pd.Series:

    cleaned = (
        series.astype(str)
        .str.replace("R$", "", regex=False)
        .str.replace(".", "", regex=False)   # drop thousands separator
        .str.replace(",", ".", regex=False)  # decimal comma -> dot
        .str.strip()
    )
    return pd.to_numeric(cleaned, errors="coerce")


def load_and_clean(csv_path: str) -> tuple[pd.DataFrame, dict]:

    df = pd.read_csv(csv_path, encoding="utf-8")

    # Check minimum schema.
    expected = {COL_DATE, COL_GROUP, COL_PARTNER,
                COL_BUYERS, COL_COMMISSION, COL_CASHBACK, COL_SALES}
    missing = expected - set(df.columns)
    if missing:
        raise ValueError(f"CSV is missing expected columns: {missing}")

    n_raw = len(df)

    # Type coercion.
    df[COL_DATE] = pd.to_datetime(df[COL_DATE], errors="coerce")
    df[COL_BUYERS] = pd.to_numeric(df[COL_BUYERS], errors="coerce")
    for c in MONETARY_COLS:
        df[c] = _parse_brl_currency(df[c])

    # Quality rules: a row is bad if any essential field is NaN or if
    # buyers <= 0 (a day with no valid observation).
    numeric_cols = [COL_BUYERS] + MONETARY_COLS
    mask_nan = df[[COL_DATE] + numeric_cols].isna().any(axis=1)
    mask_non_positive = df[COL_BUYERS].fillna(0) <= 0
    bad = mask_nan | mask_non_positive

    quality_report = {
        "rows_read": n_raw,
        "rows_dropped": int(bad.sum()),
        "rows_valid": int((~bad).sum()),
        "reasons": {
            "empty_or_unparseable_fields": int(mask_nan.sum()),
            "non_positive_buyers": int(mask_non_positive.sum()),
        },
    }

    clean_df = df.loc[~bad].copy()
    # Daily-level derived metric (needed by the statistical tests in step 2).
    clean_df["net_margin"] = clean_df[COL_COMMISSION] - clean_df[COL_CASHBACK]
    return clean_df, quality_report

def metrics_by_group(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate per variant DYNAMICALLY (does not assume the number of groups).

    Discovers the groups from the data -> works with 2, 3 or N variants.
    """
    g = df.groupby(COL_GROUP)
    m = pd.DataFrame({
        "days": g[COL_DATE].nunique(),
        "buyers": g[COL_BUYERS].sum(),
        "gmv": g[COL_SALES].sum(),
        "commission": g[COL_COMMISSION].sum(),
        "cashback": g[COL_CASHBACK].sum(),
    })
    # Derived metrics (business meaning of each is documented in the README).
    m["net_margin"] = m["commission"] - m["cashback"]
    m["cashback_pct"] = m["cashback"] / m["gmv"]
    m["commission_pct"] = m["commission"] / m["gmv"]   # partner take-rate
    m["margin_pct"] = m["net_margin"] / m["gmv"]        # margin over GMV
    m["avg_ticket"] = m["gmv"] / m["buyers"]
    m["margin_per_buyer"] = m["net_margin"] / m["buyers"]
    return m.sort_index()


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python src/pipeline.py <caminho_do_csv>")
        sys.exit(1)
    path = sys.argv[1]
    df, quality = load_and_clean(path)
    print("QUALITY:", quality)
    print(metrics_by_group(df).round(4).to_string())