# Relatório A/B — Cashback Parceiro A

**Parceiro:** Parceiro A  
**Período:** 2011-01-01 a 2011-04-02  
**Variantes:** 3

## Resumo executivo

**Decisão: TESTE INVÁLIDO — NÃO ESCALAR**

Não escalar nenhuma variante. A taxa de cashback muda dentro de pelo menos uma variante. Recomenda-se corrigir o desenho do experimento ou analisar separadamente apenas fases com tratamentos estáveis.

## Problemas identificados

- A taxa de cashback muda dentro de pelo menos uma variante.

## Métricas descritivas

As métricas abaixo são apenas descritivas e não devem ser usadas para escalar uma variante enquanto o desenho do experimento estiver inválido.

| Variante | Compradores | GMV | Cashback | Margem líquida | Margem/dia | Margem/comprador | Cashback % |
|---|---:|---:|---:|---:|---:|---:|---:|
| Grupo 1 | 9.633 | R$ 5.605.173 | R$ 233.424 | R$ 404.711 | R$ 4.399 | R$ 42,01 | 4,2% |
| Grupo 2 | 10.814 | R$ 6.423.096 | R$ 370.659 | R$ 357.519 | R$ 3.886 | R$ 33,06 | 5,8% |
| Grupo 3 | 11.410 | R$ 6.785.856 | R$ 503.600 | R$ 264.287 | R$ 2.873 | R$ 23,16 | 7,4% |

## Diagnóstico da qualidade

### Estabilidade da oferta

| Variante | Cashback mediano | Variação P95-P05 | Estável? |
|---|---:|---:|---:|
| Grupo 1 | 3,1% | 2,08 p.p. | Não |
| Grupo 2 | 5,5% | 0,54 p.p. | Não |
| Grupo 3 | 8,0% | 4,00 p.p. | Não |

## Próxima ação recomendada

Executar um novo teste com percentuais de cashback fixos durante todo o período, ou separar a análise por fases homogêneas definidas antes de observar o resultado.

## Saúde dos dados

- Linhas lidas: 276.
- Linhas válidas: 276.
- Linhas descartadas: 0.
- Datas comuns entre variantes: 92.
- Duplicatas de data/variante: 0.

## Limitações

O dataset contém compradores, mas não informa o número total de usuários expostos a cada variante. Portanto, não é possível calcular conversão nem confirmar o balanceamento do tráfego. A comparação assume alocação comparável entre as variantes.
