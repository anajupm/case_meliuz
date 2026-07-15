# Relatório A/B - Cashback Parceiro A

Parceiro: Parceiro A | Período: 2011-01-01 a 2011-04-02 | Variantes: 3

## Decisão

INCONCLUSIVO (favorece Grupo 1)

Grupo 1 tem a maior margem líquida no ponto estimado, mas a diferença sobre Grupo 2 NÃO é estatisticamente significativa (p=0.1315). Recomenda-se estender o teste ou decidir por métrica secundária antes de escalar.

## Métricas por variante

| Variante | Compradores | GMV | Comissão | Cashback | Margem líquida | Cashback % | Margem % |
|---|---|---|---|---|---|---|---|
| Grupo 1 (vencedor) | 9.633 | R$ 5.605.173 | R$ 638.135 | R$ 233.424 | R$ 404.711 | 4,2% | 7,2% |
| Grupo 2 | 10.814 | R$ 6.423.096 | R$ 728.178 | R$ 370.659 | R$ 357.519 | 5,8% | 5,6% |
| Grupo 3 | 11.410 | R$ 6.785.856 | R$ 767.887 | R$ 503.600 | R$ 264.287 | 7,4% | 3,9% |

## Evidência estatística

- Teste global (ANOVA): p = 2.57e-06 - há diferença real entre as variantes.
- Grupo 1 vs. Grupo 2 (Welch t-test): p = 0.1315 (alpha corrigido = 0.0250).
- IC 95% da diferença diária de margem: [R$ -155 ; R$ 1.181].
- Lift do vencedor sobre o vice: +13,2%.
- Observação: o IC cruza zero; não é possível afirmar que o líder supera o vice com 95% de confiança.

## Trade-off de negócio

O líder em margem (Grupo 1) não lidera volume: maior GMV e Grupo 3 e mais compradores e Grupo 3. A decisão assume margem líquida como objetivo; escalar por ela sacrifica volume.

## Saúde dos dados

- Linhas: 276 lidas, 276 válidas, 0 descartadas.
