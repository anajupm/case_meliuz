from itertools import combinations
from typing import Any

import numpy as np
import pandas as pd
from scipy import stats

import pipeline as p


PRIMARY_METRIC = "net_margin"
ALPHA = 0.05

METRIC_LABELS = {
    "net_margin": "margem líquida diária",
    "gmv": "GMV diário",
    "buyers": "compradores por dia",
}

RANKING_COLUMNS = {
    "net_margin": "daily_mean_net_margin",
    "gmv": "daily_mean_gmv",
    "buyers": "daily_mean_buyers",
}


def _pct_lift(leader_value: float, reference_value: float) -> float:
    if reference_value == 0:
        return float("inf") if leader_value > 0 else 0.0
    return (leader_value - reference_value) / abs(reference_value)


def _holm_adjust(p_values: list[float]) -> list[float]:
    """Ajuste de Holm sem dependência de statsmodels."""
    m = len(p_values)
    if m == 0:
        return []

    clean = [
        1.0 if not np.isfinite(value) else min(max(float(value), 0.0), 1.0)
        for value in p_values
    ]
    order = np.argsort(clean)
    adjusted = [1.0] * m
    running_max = 0.0

    for rank, index in enumerate(order):
        candidate = (m - rank) * clean[index]
        running_max = max(running_max, candidate)
        adjusted[index] = min(running_max, 1.0)

    return adjusted


def _paired_comparison(
    wide: pd.DataFrame,
    group_a: str,
    group_b: str,
    metric: str,
    alpha: float,
) -> dict[str, Any]:
    paired = wide[[group_a, group_b]].dropna()
    difference = paired[group_a] - paired[group_b]
    n = int(len(difference))

    if n < 2:
        return {
            "group_a": group_a,
            "group_b": group_b,
            "metric": metric,
            "n_paired_days": n,
            "t_statistic": None,
            "p_value": 1.0,
            "p_value_adjusted": 1.0,
            "mean_diff": None,
            "ci95": [None, None],
        }

    mean_diff = float(difference.mean())

    if np.isclose(float(difference.std(ddof=1)), 0.0):
        if np.isclose(mean_diff, 0.0):
            statistic, p_value = 0.0, 1.0
        else:
            statistic = float("inf") if mean_diff > 0 else float("-inf")
            p_value = 0.0
        ci_low = ci_high = mean_diff
    else:
        test = stats.ttest_rel(
            paired[group_a],
            paired[group_b],
            nan_policy="omit",
        )
        statistic = float(test.statistic)
        p_value = float(test.pvalue)

        standard_error = float(stats.sem(difference))
        ci_low, ci_high = stats.t.interval(
            confidence=1 - alpha,
            df=n - 1,
            loc=mean_diff,
            scale=standard_error,
        )

    return {
        "group_a": group_a,
        "group_b": group_b,
        "metric": metric,
        "n_paired_days": n,
        "t_statistic": statistic,
        "p_value": p_value,
        "p_value_adjusted": None,
        "mean_diff": mean_diff,
        "ci95": [float(ci_low), float(ci_high)],
    }


def _leader_view(comparison: dict, leader: str) -> dict:
    """Normaliza uma comparação para diferença líder - alternativa."""
    if comparison["group_a"] == leader:
        other = comparison["group_b"]
        mean_diff = comparison["mean_diff"]
        ci_low, ci_high = comparison["ci95"]
    else:
        other = comparison["group_a"]
        mean_diff = (
            None if comparison["mean_diff"] is None
            else -comparison["mean_diff"]
        )
        raw_low, raw_high = comparison["ci95"]
        if raw_low is None or raw_high is None:
            ci_low, ci_high = None, None
        else:
            ci_low, ci_high = -raw_high, -raw_low

    return {
        "alternative": other,
        "n_paired_days": comparison["n_paired_days"],
        "mean_diff": mean_diff,
        "ci95": [ci_low, ci_high],
        "p_value": comparison["p_value"],
        "p_value_adjusted": comparison["p_value_adjusted"],
    }


def _invalid_decision(
    metrics: pd.DataFrame,
    quality: dict,
    metric: str,
) -> dict:
    ranking_col = RANKING_COLUMNS.get(metric, metric)
    ranking = (
        metrics[ranking_col].sort_values(ascending=False).round(2).to_dict()
        if ranking_col in metrics
        else {}
    )
    reasons = quality.get("invalid_reasons") or [
        "a validação de qualidade não aprovou o experimento"
    ]

    return {
        "valid_test": False,
        "primary_metric": metric,
        "ranking": ranking,
        "winner": None,
        "runner_up": None,
        "significant": False,
        "significant_vs_all": False,
        "omnibus": None,
        "pairwise_tests": [],
        "leader_comparisons": [],
        "pairwise_test": None,
        "guardrail": {},
        "decision": "TESTE INVÁLIDO — NÃO ESCALAR",
        "recommendation": (
            "Não escalar nenhuma variante. "
            + "; ".join(reasons).capitalize()
            + ". Recomenda-se corrigir o desenho do experimento ou analisar "
              "separadamente apenas fases com tratamentos estáveis."
        ),
    }


def decide(
    df: pd.DataFrame,
    metrics: pd.DataFrame,
    quality: dict,
    metric: str = PRIMARY_METRIC,
    alpha: float = ALPHA,
) -> dict:
    """Valida o experimento, compara variantes por data e recomenda ação."""
    if not quality.get("valid_experiment", False):
        return _invalid_decision(metrics, quality, metric)

    ranking_col = RANKING_COLUMNS.get(metric)
    if ranking_col is None or ranking_col not in metrics.columns:
        raise ValueError(f"Métrica não suportada para decisão: {metric}")

    ranking = metrics[ranking_col].sort_values(ascending=False)
    ordered_groups = [str(group) for group in ranking.index]
    if len(ordered_groups) < 2:
        raise ValueError("São necessárias pelo menos duas variantes.")

    leader = ordered_groups[0]
    runner_up = ordered_groups[1]
    label = METRIC_LABELS.get(metric, metric)

    wide = df.pivot(
        index=p.COL_DATE,
        columns=p.COL_GROUP,
        values=metric,
    ).sort_index()

    complete = wide[ordered_groups].dropna()

    if len(ordered_groups) >= 3 and len(complete) >= 2:
        try:
            omnibus_result = stats.friedmanchisquare(
                *[complete[group] for group in ordered_groups]
            )
            omnibus = {
                "test": "Friedman para medidas pareadas",
                "statistic": float(omnibus_result.statistic),
                "p_value": float(omnibus_result.pvalue),
            }
        except ValueError:
            omnibus = None
    else:
        omnibus = None

    pairwise_tests = [
        _paired_comparison(wide, group_a, group_b, metric, alpha)
        for group_a, group_b in combinations(ordered_groups, 2)
    ]
    adjusted = _holm_adjust(
        [comparison["p_value"] for comparison in pairwise_tests]
    )
    for comparison, adjusted_p in zip(pairwise_tests, adjusted):
        comparison["p_value_adjusted"] = float(adjusted_p)

    leader_comparisons = [
        _leader_view(comparison, leader)
        for comparison in pairwise_tests
        if leader in (comparison["group_a"], comparison["group_b"])
    ]

    significant_vs_all = bool(
        leader_comparisons
        and all(
            comparison["mean_diff"] is not None
            and comparison["mean_diff"] > 0
            and comparison["p_value_adjusted"] < alpha
            for comparison in leader_comparisons
        )
    )

    runner_comparison = next(
        comparison
        for comparison in leader_comparisons
        if comparison["alternative"] == runner_up
    )

    leader_value = float(metrics.loc[leader, ranking_col])
    runner_value = float(metrics.loc[runner_up, ranking_col])
    lift = _pct_lift(leader_value, runner_value)

    gmv_leader = str(metrics["daily_mean_gmv"].idxmax())
    buyers_leader = str(metrics["daily_mean_buyers"].idxmax())
    trade_off = (leader != gmv_leader) or (leader != buyers_leader)

    if significant_vs_all:
        decision = f"ESCALAR {leader}"
        recommendation = (
            f"Escalar {leader} para 100% do tráfego. A variante lidera em "
            f"{label} e supera todas as alternativas após correção de Holm."
        )
        if trade_off:
            recommendation += (
                " Há trade-off de volume; monitorar GMV e compradores após "
                "a implementação."
            )
    else:
        decision = f"INCONCLUSIVO — NÃO ESCALAR (líder: {leader})"
        recommendation = (
            f"Não escalar ainda. {leader} lidera no ponto estimado de "
            f"{label}, mas não supera todas as alternativas com evidência "
            "estatística suficiente após correção por múltiplas comparações."
        )

    return {
        "valid_test": True,
        "primary_metric": metric,
        "ranking": ranking.round(2).to_dict(),
        "winner": leader,
        "runner_up": runner_up,
        "significant": significant_vs_all,
        "significant_vs_all": significant_vs_all,
        "omnibus": omnibus,
        "pairwise_tests": pairwise_tests,
        "leader_comparisons": leader_comparisons,
        # Mantido por compatibilidade com tracking e integrações simples.
        "pairwise_test": {
            **runner_comparison,
            "test": "t pareado por data, com p-valor ajustado por Holm",
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
    import json
    import sys

    cleaned, quality = p.load_and_clean(sys.argv[1])
    group_metrics = p.metrics_by_group(cleaned)
    print(
        json.dumps(
            decide(cleaned, group_metrics, quality),
            indent=2,
            ensure_ascii=False,
        )
    )