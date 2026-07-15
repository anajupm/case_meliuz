# Relatório A/B — Cashback Parceiro C

**Parceiro:** Parceiro C  
**Período:** 2011-07-01 a 2011-08-14  
**Variantes:** 2

## Resumo executivo

**Decisão: ESCALAR Grupo 1**

Escalar Grupo 1 para 100% do tráfego. A variante lidera em margem líquida diária e supera todas as alternativas após correção de Holm.

## Métricas por variante

| Variante | Compradores | GMV | Cashback | Margem líquida | Margem/dia | Margem/comprador | Cashback % |
|---|---:|---:|---:|---:|---:|---:|---:|
| Grupo 1 (líder) | 4.549 | R$ 1.738.460 | R$ 86.924 | R$ 34.769 | R$ 773 | R$ 7,64 | 5,0% |
| Grupo 2 | 4.522 | R$ 1.685.235 | R$ 117.967 | R$ 0 | R$ 0 | R$ 0,00 | 7,0% |

## Evidência estatística

- **Grupo 1 vs. Grupo 2:** ganho médio diário de R$ 773; IC 95% [R$ 713; R$ 833]; p ajustado por Holm=2.60e-28; 45 dias pareados.
- **Lift do líder sobre o segundo colocado:** N/D, pois a margem do comparador é zero.

## Guardrails de negócio

- A variante líder em margem também lidera GMV e compradores.

## Diagnóstico da qualidade

### Estabilidade da oferta

| Variante | Cashback mediano | Variação P95-P05 | Estável? |
|---|---:|---:|---:|
| Grupo 1 | 5,0% | 0,00 p.p. | Sim |
| Grupo 2 | 7,0% | 0,00 p.p. | Sim |

## Saúde dos dados

- Linhas lidas: 90.
- Linhas válidas: 90.
- Linhas descartadas: 0.
- Datas comuns entre variantes: 45.
- Duplicatas de data/variante: 0.

## Limitações

O dataset contém compradores, mas não informa o número total de usuários expostos a cada variante. Portanto, não é possível calcular conversão nem confirmar o balanceamento do tráfego. A comparação assume alocação comparável entre as variantes.
