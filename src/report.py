import math
import os

import pandas as pd

import pipeline as dc


def _brl(value: float | None, decimals: int = 0) -> str:
    if value is None or not math.isfinite(float(value)):
        return "N/D"
    formatted = f"{float(value):,.{decimals}f}"
    formatted = formatted.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {formatted}"


def _pct(value: float | None, decimals: int = 1) -> str:
    if value is None or not math.isfinite(float(value)):
        return "N/D"
    return f"{float(value) * 100:.{decimals}f}%".replace(".", ",")


def _p(value: float | None) -> str:
    if value is None or not math.isfinite(float(value)):
        return "N/D"
    return f"{value:.4f}" if value >= 1e-4 else f"{value:.2e}"


def _append_metrics_table(
    lines: list[str],
    metrics: pd.DataFrame,
    leader: str | None,
) -> None:
    lines.extend(
        [
            "| Variante | Compradores | GMV | Cashback | Margem líquida | "
            "Margem/dia | Margem/comprador | Cashback % |",
            "|---|---:|---:|---:|---:|---:|---:|---:|",
        ]
    )

    for group, row in metrics.iterrows():
        label = str(group)
        if leader and str(group) == leader:
            label += " (líder)"
        buyers = f"{int(row['buyers']):,}".replace(",", ".")
        lines.append(
            f"| {label} | {buyers} | {_brl(row['gmv'])} | "
            f"{_brl(row['cashback'])} | {_brl(row['net_margin'])} | "
            f"{_brl(row['daily_mean_net_margin'])} | "
            f"{_brl(row['margin_per_buyer'], 2)} | "
            f"{_pct(row['cashback_pct'])} |"
        )


def _append_rate_stability(lines: list[str], quality: dict) -> None:
    lines.extend(
        [
            "### Estabilidade da oferta",
            "",
            "| Variante | Cashback mediano | Variação P95-P05 | Estável? |",
            "|---|---:|---:|---:|",
        ]
    )
    stability = quality.get("cashback_rate_stability", {})
    for group, item in stability.items():
        span = item.get("span_pp")
        span_text = (
            "N/D"
            if span is None
            else f"{span:.2f}".replace(".", ",") + " p.p."
        )
        lines.append(
            f"| {group} | {_pct(item.get('median_rate'))} | "
            f"{span_text} | {'Sim' if item.get('stable') else 'Não'} |"
        )


def build_report(
    df: pd.DataFrame,
    metrics: pd.DataFrame,
    decision: dict,
    quality: dict,
    test_name: str | None = None,
) -> str:
    partner = str(df[dc.COL_PARTNER].iloc[0])
    start = df[dc.COL_DATE].min().date()
    end = df[dc.COL_DATE].max().date()
    n_variants = int(df[dc.COL_GROUP].nunique())
    test_name = test_name or f"Teste de cashback - {partner}"

    lines = [
        f"# Relatório A/B — {test_name}",
        "",
        f"**Parceiro:** {partner}  ",
        f"**Período:** {start} a {end}  ",
        f"**Variantes:** {n_variants}",
        "",
        "## Resumo executivo",
        "",
        f"**Decisão: {decision['decision']}**",
        "",
        decision["recommendation"],
        "",
    ]

    if not decision.get("valid_test", False):
        lines.extend(
            [
                "## Problemas identificados",
                "",
            ]
        )
        for reason in quality.get("invalid_reasons", []):
            lines.append(f"- {reason.capitalize()}.")
        lines.extend(
            [
                "",
                "## Métricas descritivas",
                "",
                (
                    "As métricas abaixo são apenas descritivas e não devem "
                    "ser usadas para escalar uma variante enquanto o desenho "
                    "do experimento estiver inválido."
                ),
                "",
            ]
        )
        _append_metrics_table(lines, metrics, leader=None)
        lines.extend(["", "## Diagnóstico da qualidade", ""])
        _append_rate_stability(lines, quality)
        lines.extend(
            [
                "",
                "## Próxima ação recomendada",
                "",
                (
                    "Executar um novo teste com percentuais de cashback fixos "
                    "durante todo o período, ou separar a análise por fases "
                    "homogêneas definidas antes de observar o resultado."
                ),
                "",
            ]
        )
    else:
        winner = decision["winner"]
        lines.extend(["## Métricas por variante", ""])
        _append_metrics_table(lines, metrics, leader=winner)

        lines.extend(["", "## Evidência estatística", ""])
        omnibus = decision.get("omnibus")
        if omnibus:
            verdict = (
                "há evidência de diferença entre pelo menos duas variantes"
                if omnibus["p_value"] < 0.05
                else "não foi detectada diferença global entre as variantes"
            )
            lines.append(
                f"- **{omnibus['test']}:** p={_p(omnibus['p_value'])}; "
                f"{verdict}."
            )

        for comparison in decision.get("leader_comparisons", []):
            ci_low, ci_high = comparison["ci95"]
            lines.append(
                f"- **{winner} vs. {comparison['alternative']}:** "
                f"ganho médio diário de {_brl(comparison['mean_diff'])}; "
                f"IC 95% [{_brl(ci_low)}; {_brl(ci_high)}]; "
                f"p ajustado por Holm={_p(comparison['p_value_adjusted'])}; "
                f"{comparison['n_paired_days']} dias pareados."
            )

        pairwise = decision["pairwise_test"]
        lift = pairwise.get("lift_pct")
        lift_text = (
            "N/D, pois a margem do comparador é zero"
            if lift == float("inf")
            else _pct(lift)
        )
        lines.append(
            f"- **Lift do líder sobre o segundo colocado:** {lift_text}."
        )

        guardrail = decision["guardrail"]
        lines.extend(["", "## Guardrails de negócio", ""])
        if guardrail["has_trade_off"]:
            lines.append(
                f"- O líder de margem é {guardrail['margin_leader']}; "
                f"o líder de GMV é {guardrail['gmv_leader']}; "
                f"o líder de compradores é {guardrail['buyers_leader']}."
            )
            lines.append(
                "- Há trade-off de volume; monitorar GMV e compradores após "
                "a decisão."
            )
        else:
            lines.append(
                "- A variante líder em margem também lidera GMV e compradores."
            )

        lines.extend(["", "## Diagnóstico da qualidade", ""])
        _append_rate_stability(lines, quality)
        lines.append("")

    lines.extend(
        [
            "## Saúde dos dados",
            "",
            f"- Linhas lidas: {quality['rows_read']}.",
            f"- Linhas válidas: {quality['rows_valid']}.",
            f"- Linhas descartadas: {quality['rows_dropped']}.",
            (
                f"- Datas comuns entre variantes: "
                f"{quality.get('common_dates', 0)}."
            ),
            (
                f"- Duplicatas de data/variante: "
                f"{quality.get('duplicate_group_dates', 0)}."
            ),
            "",
            "## Limitações",
            "",
            (
                "O dataset contém compradores, mas não informa o número total "
                "de usuários expostos a cada variante. Portanto, não é possível "
                "calcular conversão nem confirmar o balanceamento do tráfego. "
                "A comparação assume alocação comparável entre as variantes."
            ),
            "",
        ]
    )

    return "\n".join(lines)


def save_report(markdown: str, out_dir: str, partner: str) -> str:
    os.makedirs(out_dir, exist_ok=True)
    safe_partner = str(partner).replace(" ", "_")
    path = os.path.join(out_dir, f"relatorio_{safe_partner}.md")
    with open(path, "w", encoding="utf-8") as file:
        file.write(markdown)
    return path