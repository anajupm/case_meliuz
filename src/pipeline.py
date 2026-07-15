import re
from typing import Any

import numpy as np
import pandas as pd


COL_DATE = "Data"
COL_GROUP = "Grupos de usuários"
COL_PARTNER = "Parceiro"
COL_BUYERS = "compradores"
COL_COMMISSION = "comissão"
COL_CASHBACK = "cashback"
COL_SALES = "vendas totais"

MONETARY_COLS = [COL_COMMISSION, COL_CASHBACK, COL_SALES]
EXPECTED_COLUMNS = {
    COL_DATE,
    COL_GROUP,
    COL_PARTNER,
    COL_BUYERS,
    COL_COMMISSION,
    COL_CASHBACK,
    COL_SALES,
}

# Variações menores que 0,25 p.p. são tratadas como arredondamento monetário.
RATE_STABILITY_TOLERANCE_PP = 0.25


def _parse_currency_value(value: Any) -> float:
    """Converte moeda brasileira e números comuns para float.

    Exemplos aceitos:
    - R$ 1.234
    - R$ 1.234,56
    - 1234.56
    - 1234
    """
    if pd.isna(value):
        return np.nan
    if isinstance(value, (int, float, np.number)):
        return float(value)

    text = str(value).strip()
    if not text:
        return np.nan

    text = re.sub(r"^\s*R\$\s*", "", text)
    text = text.replace(" ", "")

    if "," in text:
        # Formato brasileiro: ponto para milhar e vírgula para decimais.
        text = text.replace(".", "").replace(",", ".")
    elif "." in text:
        parts = text.split(".")
        # Um ou mais separadores seguidos por blocos de 3 dígitos => milhar.
        if len(parts) > 1 and all(len(part) == 3 for part in parts[1:]):
            text = "".join(parts)

    try:
        return float(text)
    except ValueError:
        return np.nan


def _parse_brl_currency(series: pd.Series) -> pd.Series:
    return series.map(_parse_currency_value).astype(float)


def _rate_stability(
    df: pd.DataFrame,
    rate_col: str,
    tolerance_pp: float = RATE_STABILITY_TOLERANCE_PP,
) -> dict[str, dict[str, float | bool | None]]:
    """Resume estabilidade da taxa por grupo usando P95 - P05."""
    output: dict[str, dict[str, float | bool | None]] = {}

    for group, sub in df.groupby(COL_GROUP, sort=True):
        rates = sub[rate_col].replace([np.inf, -np.inf], np.nan).dropna()
        if rates.empty:
            output[str(group)] = {
                "median_rate": None,
                "span_pp": None,
                "stable": False,
            }
            continue

        span_pp = float((rates.quantile(0.95) - rates.quantile(0.05)) * 100)
        output[str(group)] = {
            "median_rate": float(rates.median()),
            "span_pp": span_pp,
            "stable": bool(span_pp <= tolerance_pp),
        }

    return output


def load_and_clean(csv_path: str) -> tuple[pd.DataFrame, dict]:
    """Lê, valida e limpa um CSV de teste A/B."""
    df = pd.read_csv(csv_path, encoding="utf-8-sig")
    df.columns = [str(column).strip() for column in df.columns]

    missing = EXPECTED_COLUMNS - set(df.columns)
    if missing:
        raise ValueError(
            "CSV sem colunas obrigatórias: " + ", ".join(sorted(missing))
        )
    if df.empty:
        raise ValueError("O CSV está vazio.")

    n_raw = len(df)

    df[COL_GROUP] = df[COL_GROUP].astype("string").str.strip()
    df[COL_PARTNER] = df[COL_PARTNER].astype("string").str.strip()
    df[COL_DATE] = pd.to_datetime(df[COL_DATE], errors="coerce")
    df[COL_BUYERS] = pd.to_numeric(df[COL_BUYERS], errors="coerce")

    for column in MONETARY_COLS:
        df[column] = _parse_brl_currency(df[column])

    essential_cols = [
        COL_DATE,
        COL_GROUP,
        COL_PARTNER,
        COL_BUYERS,
        COL_COMMISSION,
        COL_CASHBACK,
        COL_SALES,
    ]
    mask_missing = df[essential_cols].isna().any(axis=1)
    mask_negative = (
        (df[COL_BUYERS].fillna(-1) < 0)
        | (df[COL_COMMISSION].fillna(-1) < 0)
        | (df[COL_CASHBACK].fillna(-1) < 0)
        | (df[COL_SALES].fillna(-1) <= 0)
    )
    mask_empty_strings = (
        df[COL_GROUP].fillna("").eq("")
        | df[COL_PARTNER].fillna("").eq("")
    )
    bad = mask_missing | mask_negative | mask_empty_strings

    clean_df = df.loc[~bad].copy()
    if clean_df.empty:
        raise ValueError("Nenhuma linha válida permaneceu após a limpeza.")

    clean_df["net_margin"] = (
        clean_df[COL_COMMISSION] - clean_df[COL_CASHBACK]
    )
    clean_df["cashback_rate"] = (
        clean_df[COL_CASHBACK] / clean_df[COL_SALES]
    )
    clean_df["commission_rate"] = (
        clean_df[COL_COMMISSION] / clean_df[COL_SALES]
    )

    partners = sorted(clean_df[COL_PARTNER].dropna().astype(str).unique().tolist())
    groups = sorted(clean_df[COL_GROUP].dropna().astype(str).unique().tolist())
    duplicate_group_dates = int(
        clean_df.duplicated([COL_DATE, COL_GROUP], keep=False).sum()
    )

    date_sets = [
        set(sub[COL_DATE].tolist())
        for _, sub in clean_df.groupby(COL_GROUP)
    ]
    same_dates_across_groups = bool(
        len(date_sets) >= 2
        and all(date_set == date_sets[0] for date_set in date_sets[1:])
    )
    common_dates = (
        len(set.intersection(*date_sets)) if len(date_sets) >= 2 else 0
    )

    cashback_stability = _rate_stability(clean_df, "cashback_rate")
    commission_stability = _rate_stability(clean_df, "commission_rate")
    treatment_stable = bool(
        cashback_stability
        and all(item["stable"] for item in cashback_stability.values())
    )

    invalid_reasons: list[str] = []
    if len(partners) != 1:
        invalid_reasons.append(
            "o arquivo contém mais de um parceiro"
        )
    if len(groups) < 2:
        invalid_reasons.append(
            "o arquivo contém menos de duas variantes"
        )
    if duplicate_group_dates > 0:
        invalid_reasons.append(
            "há linhas duplicadas para a mesma data e variante"
        )
    if not same_dates_across_groups:
        invalid_reasons.append(
            "as variantes não possuem exatamente as mesmas datas"
        )
    if not treatment_stable:
        invalid_reasons.append(
            "a taxa de cashback muda dentro de pelo menos uma variante"
        )

    quality_report = {
        "rows_read": n_raw,
        "rows_valid": int(len(clean_df)),
        "rows_dropped": int(bad.sum()),
        "reasons": {
            "empty_or_unparseable_fields": int(mask_missing.sum()),
            "negative_or_nonpositive_values": int(mask_negative.sum()),
            "empty_group_or_partner": int(mask_empty_strings.sum()),
        },
        "partners_found": partners,
        "groups_found": groups,
        "duplicate_group_dates": duplicate_group_dates,
        "same_dates_across_groups": same_dates_across_groups,
        "common_dates": int(common_dates),
        "cashback_rate_stability": cashback_stability,
        "commission_rate_stability": commission_stability,
        "treatment_stable": treatment_stable,
        "valid_experiment": len(invalid_reasons) == 0,
        "invalid_reasons": invalid_reasons,
    }

    return clean_df.sort_values([COL_DATE, COL_GROUP]), quality_report


def metrics_by_group(df: pd.DataFrame) -> pd.DataFrame:
    """Calcula métricas dinamicamente para 2, 3 ou N variantes."""
    grouped = df.groupby(COL_GROUP, sort=True)

    metrics = pd.DataFrame(
        {
            "days": grouped[COL_DATE].nunique(),
            "buyers": grouped[COL_BUYERS].sum(),
            "gmv": grouped[COL_SALES].sum(),
            "commission": grouped[COL_COMMISSION].sum(),
            "cashback": grouped[COL_CASHBACK].sum(),
            "daily_mean_buyers": grouped[COL_BUYERS].mean(),
            "daily_mean_gmv": grouped[COL_SALES].mean(),
            "daily_mean_net_margin": grouped["net_margin"].mean(),
        }
    )

    metrics["net_margin"] = metrics["commission"] - metrics["cashback"]
    metrics["cashback_pct"] = metrics["cashback"] / metrics["gmv"]
    metrics["commission_pct"] = metrics["commission"] / metrics["gmv"]
    metrics["margin_pct"] = metrics["net_margin"] / metrics["gmv"]
    metrics["avg_ticket"] = metrics["gmv"] / metrics["buyers"]
    metrics["margin_per_buyer"] = (
        metrics["net_margin"] / metrics["buyers"]
    )

    return metrics.sort_index()


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        raise SystemExit("Uso: python src/pipeline.py <caminho_do_csv>")

    cleaned, quality = load_and_clean(sys.argv[1])
    print("QUALIDADE:", quality)
    print(metrics_by_group(cleaned).round(4).to_string())