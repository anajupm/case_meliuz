from datetime import datetime

import pandas as pd

import pipeline as dc


# --- Brazilian formatting helpers -----------------------------------------
def _brl(value: float) -> str:
    """1234567 -> 'R$ 1.234.567'."""
    return "R$ " + f"{value:,.0f}".replace(",", ".")


def _pct(x: float, decimals: int = 1) -> str:
    """0.074 -> '7,4%'."""
    return f"{x * 100:.{decimals}f}%".replace(".", ",")


def _lift(x: float) -> str:
    """Relative lift, handling the divide-by-zero (inf) case."""
    if x == float("inf"):
        return "N/D (margem nula no comparador)"
    return ("+" if x >= 0 else "") + _pct(x)


def _p(value: float) -> str:
    """p-values, scientific notation when very small."""
    return f"{value:.4f}" if value >= 1e-4 else f"{value:.2e}"


def build_report(df: pd.DataFrame, metrics: pd.DataFrame, decision: dict,
                 quality: dict, test_name: str | None = None) -> str:
    """Return the full Markdown report as a string."""
    partner = df[dc.COL_PARTNER].iloc[0]
    start = df[dc.COL_DATE].min().date()
    end = df[dc.COL_DATE].max().date()
    n_variants = df[dc.COL_GROUP].nunique()
    test_name = test_name or f"Teste de cashback - {partner}"

    winner = decision["winner"]
    runner_up = decision["runner_up"]
    pw = decision["pairwise_test"]
    g = decision["guardrail"]

    L = []
    L.append(f"# Relatório A/B - {test_name}")
    L.append("")
    L.append(f"Parceiro: {partner} | Período: {start} a {end} | "
             f"Variantes: {n_variants}")
    L.append("")

    L.append("## Decisão")
    L.append("")
    L.append(f"{decision['decision']}")
    L.append("")
    L.append(decision["recommendation"])
    L.append("")

    L.append("## Métricas por variante")
    L.append("")
    L.append("| Variante | Compradores | GMV | Comissão | Cashback | "
             "Margem líquida | Cashback % | Margem % |")
    L.append("|---|---|---|---|---|---|---|---|")
    for grp, row in metrics.iterrows():
        name = f"{grp} (vencedor)" if grp == winner else str(grp)
        buyers = f"{int(row['buyers']):,}".replace(",", ".")
        L.append(
            f"| {name} | {buyers} | {_brl(row['gmv'])} | "
            f"{_brl(row['commission'])} | {_brl(row['cashback'])} | "
            f"{_brl(row['net_margin'])} | {_pct(row['cashback_pct'])} | "
            f"{_pct(row['margin_pct'])} |"
        )
    L.append("")

    L.append("## Evidência estatística")
    L.append("")
    if decision["omnibus"]:
        om = decision["omnibus"]
        verdict = ("há diferença real entre as variantes"
                   if om["p_value"] < 0.05
                   else "não há diferença detectável entre as variantes")
        L.append(f"- Teste global ({om['test']}): p = {_p(om['p_value'])} - {verdict}.")
    L.append(f"- {winner} vs. {runner_up} (Welch t-test): p = {_p(pw['p_value'])} "
             f"(alpha corrigido = {pw['corrected_alpha']:.4f}).")
    L.append(f"- IC 95% da diferença diária de margem: "
             f"[{_brl(pw['diff_ci95'][0])} ; {_brl(pw['diff_ci95'][1])}].")
    L.append(f"- Lift do vencedor sobre o vice: {_lift(pw['lift_pct'])}.")
    if not decision["significant"]:
        L.append("- Observação: o IC cruza zero; não é possível afirmar que o "
                 "líder supera o vice com 95% de confiança.")
    L.append("")

    if g["has_trade_off"]:
        L.append("## Trade-off de negócio")
        L.append("")
        L.append(f"O líder em margem ({g['margin_leader']}) não lidera volume: "
                 f"maior GMV e {g['gmv_leader']} e mais compradores e "
                 f"{g['buyers_leader']}. A decisão assume margem líquida como "
                 "objetivo; escalar por ela sacrifica volume.")
        L.append("")

    L.append("## Saúde dos dados")
    L.append("")
    L.append(f"- Linhas: {quality['rows_read']} lidas, {quality['rows_valid']} "
             f"válidas, {quality['rows_dropped']} descartadas.")
    L.append("")

    return "\n".join(L)


def save_report(markdown: str, out_dir: str, partner: str) -> str:
    """Write the report to out_dir and return the file path."""
    import os
    os.makedirs(out_dir, exist_ok=True)
    safe = str(partner).replace(" ", "_")
    path = os.path.join(out_dir, f"relatorio_{safe}.md")
    with open(path, "w", encoding="utf-8") as f:
        f.write(markdown)
    return path


if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Uso: python src/report.py <caminho_do_csv>")
        sys.exit(1)
    import decision as dec
    df, quality = dc.load_and_clean(sys.argv[1])
    metrics = dc.metrics_by_group(df)
    decision_result = dec.decide(df, metrics)
    print(build_report(df, metrics, decision_result, quality))