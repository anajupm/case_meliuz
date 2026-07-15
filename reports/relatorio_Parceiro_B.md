# Relatório A/B — Cashback Parceiro B

**Parceiro:** Parceiro B  
**Período:** 2011-05-01 a 2011-06-30  
**Variantes:** 3

## Resumo executivo

**Decisão: ESCALAR Grupo 1**

Escalar Grupo 1 para 100% do tráfego. A variante lidera em margem líquida diária e supera todas as alternativas após correção de Holm.

## Métricas por variante

| Variante | Compradores | GMV | Cashback | Margem líquida | Margem/dia | Margem/comprador | Cashback % |
|---|---:|---:|---:|---:|---:|---:|---:|
| Grupo 1 (líder) | 7.990 | R$ 4.093.818 | R$ 163.751 | R$ 286.570 | R$ 4.698 | R$ 35,87 | 4,0% |
| Grupo 2 | 5.452 | R$ 2.863.019 | R$ 171.778 | R$ 143.157 | R$ 2.347 | R$ 26,26 | 6,0% |
| Grupo 3 | 5.029 | R$ 2.629.963 | R$ 236.697 | R$ 52.593 | R$ 862 | R$ 10,46 | 9,0% |

## Evidência estatística

- **Friedman para medidas pareadas:** p=3.22e-27; há evidência de diferença entre pelo menos duas variantes.
- **Grupo 1 vs. Grupo 2:** ganho médio diário de R$ 2.351; IC 95% [R$ 2.045; R$ 2.657]; p ajustado por Holm=3.36e-22; 61 dias pareados.
- **Grupo 1 vs. Grupo 3:** ganho médio diário de R$ 3.836; IC 95% [R$ 3.416; R$ 4.256]; p ajustado por Holm=1.03e-25; 61 dias pareados.
- **Lift do líder sobre o segundo colocado:** 100,2%.

## Guardrails de negócio

- A variante líder em margem também lidera GMV e compradores.

## Diagnóstico da qualidade

### Estabilidade da oferta

| Variante | Cashback mediano | Variação P95-P05 | Estável? |
|---|---:|---:|---:|
| Grupo 1 | 4,0% | 0,00 p.p. | Sim |
| Grupo 2 | 6,0% | 0,00 p.p. | Sim |
| Grupo 3 | 9,0% | 0,00 p.p. | Sim |

## Saúde dos dados

- Linhas lidas: 183.
- Linhas válidas: 183.
- Linhas descartadas: 0.
- Datas comuns entre variantes: 61.
- Duplicatas de data/variante: 0.

## Limitações

O dataset contém compradores, mas não informa o número total de usuários expostos a cada variante. Portanto, não é possível calcular conversão nem confirmar o balanceamento do tráfego. A comparação assume alocação comparável entre as variantes.
