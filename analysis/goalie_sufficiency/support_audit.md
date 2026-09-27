# Goalie support in the supplied sample

Source: `data/raw/shot-data.csv`. SHA-256: `25e5ea674e57f838f21062059630db795699d8499cf6af03699628df1b5c8af2`.

All-attempt denominator: 13,269 attempts and 997 goals.

| Measure | Goalies | Shooters |
| --- | ---: | ---: |
| Distinct IDs | 123 | 35 |
| Median attempts | 80.0 | 284.0 |
| Attempt range | 1–430 | 61–1039 |
| Median goals | 6.0 | 20.0 |
| IDs with fewer than 50 attempts | 49 | 0 |
| IDs with fewer than 10 goals | 78 | 6 |
| Median entity-season attempts | 32.0 | 72.0 |

The observed shooter–goalie graph has one connected component. This supports model identifiability after constraints, while sparse observations still limit precision.

## Cumulative history available for later seasons

| Test season | Goalies | Goalies with prior history | Goalies with at least 100 prior attempts | Later attempts covered by at least 100 prior attempts |
| --- | ---: | ---: | ---: | ---: |
| 2022 | 93 | 79 | 4 | 375 / 4164 |
| 2023 | 85 | 79 | 30 | 2101 / 4204 |
| 2024 | 59 | 58 | 42 | 917 / 1199 |

## Precision interpretation

Illustration using independent identical Bernoulli attempts at the pooled conversion rate. These are neither fitted ability intervals nor covariate-adjusted precision guarantees. Context, dependence, selection and joint parameter estimation change precision.

At the goalies median of 80 attempts, the independent-binomial reference SE is 2.95 percentage points; the normal 95% reference half-width is 5.78 points.
At the shooters median of 284 attempts, the independent-binomial reference SE is 1.56 percentage points; the normal 95% reference half-width is 3.07 points.

## Decision implication

The sample supports treating unpooled goalie effects as imprecise. It also supports a connected, partially pooled comparison if opponent adjustment is important. Exposure counts alone cannot determine whether adding a shared goalie effect improves shooting forecasts. Compare a pooled shooter model against the same model with one strongly pooled goalie term on identical later attempts; preserve a no-individual-goalie model as the default when improvement is too small or uncertain for the intended use.

No performance model was fitted and no shooter or goalie ranking was produced.
