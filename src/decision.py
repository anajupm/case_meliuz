from scipy import stats
import pandas as pd

import pipeline as dc

# --- Decision configuration (change here to swap the yardstick) -----------
# Primary metric = what Méliuz actually keeps. Rationale in the README.
PRIMARY_METRIC = "net_margin"
ALPHA = 0.05  # significance level (95% confidence)

# Human-readable labels for the (Portuguese) manager-facing output.
METRIC_LABELS = {
    "net_margin": "margem líquida",
    "gmv": "GMV",
    "buyers": "compradores",
    "margin_per_buyer": "margem por comprador",
}

def _daily_series(df: pd.DataFrame, daily_metric: str) -> dict:
    """Return {group: array of daily values} for the statistical test.

    The daily series is each variant's SAMPLE — significance is measured on
    it, not on the aggregated total.
    """
    return {
        group: sub[daily_metric].to_numpy()
        for group, sub in df.groupby(dc.COL_GROUP)
    }

def _pct_lift(leader_value: float, ref_value: float) -> float:
    """Relative gain of the leader over the reference (e.g. +12.4%)."""
    if ref_value == 0:
        return float("inf") if leader_value > 0 else 0.0
    return (leader_value - ref_value) / abs(ref_value)

def decide(df: pd.DataFrame, metrics: pd.DataFrame,
           metric: str = PRIMARY_METRIC, alpha: float = ALPHA) -> dict:
    """Rank by primary metric, test significance and apply the winner rule.

    Returns a structured dict, ready to feed the report and the tracking
    sheet in the next steps.
    """
    label = METRIC_LABELS.get(metric, metric)

    # 1) Rank by the (aggregated) primary metric.
    ranking = metrics[metric].sort_values(ascending=False)
    ordered_groups = list(ranking.index)
    leader = ordered_groups[0]
    runner_up = ordered_groups[1]

    # 2) Daily series for the test (the primary metric exists at daily level).
    series = _daily_series(df, metric)

    # 3) Omnibus test (ANOVA): is there ANY difference among the groups?
    if len(series) >= 3:
        f_stat, p_anova = stats.f_oneway(*series.values())
        omnibus = {"test": "ANOVA", "statistic": float(f_stat),
                   "p_value": float(p_anova)}
    else:
        omnibus = None  # with 2 groups the pairwise test already settles it

    # 4) Leader vs. runner-up — Welch (does not assume equal variances).
    t_res = stats.ttest_ind(series[leader], series[runner_up], equal_var=False)
    ci = t_res.confidence_interval(confidence_level=1 - alpha)

    # Bonferroni correction when more than one pairwise comparison is possible.
    n_comparisons = max(1, len(ordered_groups) - 1)
    corrected_alpha = alpha / n_comparisons
    significant = bool(t_res.pvalue < corrected_alpha)

    daily_mean_diff = float(series[leader].mean() - series[runner_up].mean())
    lift = _pct_lift(metrics.loc[leader, metric], metrics.loc[runner_up, metric])

    # 5) Guardrail: does the margin winner also lead on volume? Or a trade-off?
    gmv_leader = metrics["gmv"].idxmax()
    buyers_leader = metrics["buyers"].idxmax()
    trade_off = (leader != gmv_leader) or (leader != buyers_leader)

    # 6) Business-language recommendation (kept in Portuguese for the manager).
    if significant:
        recommendation = (
            f"Escalar {leader} para 100% do tráfego. Lidera em {label} com "
            f"diferença estatisticamente significativa sobre {runner_up} "
            f"(p={t_res.pvalue:.4f}, α corrigido={corrected_alpha:.4f})."
        )
        decision = "ESCALAR " + leader
    else:
        recommendation = (
            f"{leader} tem a maior {label} no ponto estimado, mas a diferença "
            f"sobre {runner_up} NÃO é estatisticamente significativa "
            f"(p={t_res.pvalue:.4f}). Recomenda-se estender o teste ou decidir "
            f"por métrica secundária antes de escalar."
        )
        decision = "INCONCLUSIVO (favorece " + leader + ")"

    return {
        "primary_metric": metric,
        "ranking": ranking.round(2).to_dict(),
        "winner": leader,
        "runner_up": runner_up,
        "significant": significant,
        "omnibus": omnibus,
        "pairwise_test": {
            "test": "Welch t-test (leader vs runner-up)",
            "t_statistic": float(t_res.statistic),
            "p_value": float(t_res.pvalue),
            "corrected_alpha": float(corrected_alpha),
            "n_comparisons": n_comparisons,
            "daily_mean_diff": daily_mean_diff,
            "diff_ci95": [float(ci.low), float(ci.high)],
            "lift_pct": lift,
        },
        "guardrail": {
            "has_trade_off": trade_off,
            "margin_leader": leader,
            "gmv_leader": gmv_leader,
            "buyers_leader": buyers_leader,
        },
        "decision": decision,
        "recommendation": recommendation,
    }


if __name__ == "__main__":
    import sys, json
    df, _ = dc.load_and_clean(sys.argv[1])
    metr = dc.metrics_by_group(df)
    print(json.dumps(decide(df, metr), indent=2, ensure_ascii=False))