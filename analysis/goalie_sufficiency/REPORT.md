# Goalie sufficiency check and modeling decision

September 27, 2026.

**Decision: use a partially pooled shooter model with season adjustment as the main take-home analysis.** Preserve this goalie comparison as a sensitivity check. The supplied sample supports fitting a pooled opponent term, but the test finds no consistent, practically meaningful forecast gain, and shooter estimates change very little when that term is included.

This conclusion applies to the supplied 35-shooter extract and the models tested. It supports concentrating the take-home on shooters. It does not establish that NHL goalies have equal ability or that the larger NHL archive lacks useful goalie information.

## What was checked

1. Counted goalie and shooter exposure, scored goals, repeated seasons, and opponent overlap independently.
2. Compared a pooled shooter model with the same model allowing a separately pooled goalie effect.
3. Selected pooling strengths using earlier seasons, then evaluated predictions on later observations.
4. Checked an alternative season-intercept convention, alternative scoring weights, score uncertainty, and the effect on standardized shooter comparisons.

All 13,269 supplied attempts remain in the analysis, including 2,560 blocks, misses, and the 48 outcome-blank rows whose goal indicator is one. There are 997 goals. The original CSV was read without modification.

**Relationship to the final notebook:** this earlier sensitivity check fits Gaussian-penalized logistic models (ridge/MAP point estimates) to all 13,269 original rows. The final notebook fits a Bayesian hierarchical model to 13,224 cleaned rows, after removing 45 repeated attribute records. The check provides supporting evidence for the modeling choice within the historical specification; a direct goalie comparison for the final Bayesian specification would require a separate fit. The historical results and row selection are preserved here.

## Available information

| Measure | Goalies | Shooters |
| --- | ---: | ---: |
| Distinct identities | 123 | 35 |
| Median attempts across all four season labels | 80 | 284 |
| Median goals across all four season labels | 6 | 20 |
| Identities associated with fewer than 10 goals | 78 | 6 |
| Median attempts per observed identity-season | 32 | 72 |
| Median goals per observed identity-season | 2 | 5 |

Fourteen goalies have zero recorded goals against. At the sample's average goal rate, an independent-binomial reference gives a standard error of approximately 2.95 percentage points for 80 attempts. This illustrates sampling noise in raw conversion; it is not an adjusted goalie-ability interval.

Opponent overlap is sufficient to connect all shooter and goalie identities. The median goalie faces 22 distinct shooters, and the median shooter faces 71 goalies. The median individual pairing has only three attempts. In 2024, 58 of the 59 goalies have earlier history, covering 1,197 of 1,199 attempts. Sparse information per goalie is more limiting than missing identity recurrence.

## Historical prediction comparison

Both model families predict goals per all recorded attempts:

```
Shooter model: logit P(goal) = season intercept + pooled shooter effect
Goalie model:  logit P(goal) = season intercept + pooled shooter effect + pooled goalie effect
```

The objective sums binomial negative log likelihood and adds separate Gaussian quadratic penalties for shooter and goalie effects. Each family tunes its shooter penalty. The goalie family also tunes its goalie penalty and includes complete goalie pooling as a candidate. The grid was 0.3, 1, 3, 10, 30, 100, 300, 1000, and complete pooling. These are predictive regularization parameters, not an estimate of the population variance of goalie skill.

For the 2023 test, tuning uses training 2021 and validation 2022, then refits on 2021–2022. For the 2024 test, tuning averages the preceding 2022 and 2023 validation losses, then refits on 2021–2023. Every prediction uses only earlier outcomes. The primary rule carries forward the latest training-season intercept; an exposure-weighted training-intercept sensitivity gives the same substantive conclusion. New identities receive a zero effect in this plug-in forecast.

| Evaluation season label | Attempts | Shooter-only log loss | With goalie effects | Relative change in loss |
| --- | ---: | ---: | ---: | ---: |
| 2023 | 4,204 | 0.262360 | 0.262367 | 0.0028% higher |
| 2024 | 1,199 | 0.271500 | 0.271584 | 0.0310% higher |
| Combined | 5,403 | 0.264388 | 0.264412 | 0.0092% higher |

Lower loss is better. These differences are negligible. The primary combined Brier score changes from 0.06870448 to 0.06870767. Giving every shooter equal weight instead produces a very small improvement: mean log loss changes from 0.25039259 to 0.25035393. The evidence therefore supports **no consistent or material gain**, rather than deterioration under every scoring convention.

The selected goalie penalties were 30 for the 2023 test and 100 for the 2024 test. Thus tuning allows small goalie effects, but their small validation gains do not produce useful later gains. Finite selected penalties alone do not establish identifiable or persistent goalie talent.

For the combined primary log-loss difference (goalie model minus shooter model), the approximate 95% resampling interval is:

- Resampling goalies: −0.000412 to +0.000481.
- Resampling shooters: −0.000386 to +0.000466.

These are separate dependence sensitivities conditional on the fitted models and selected penalties. They include both small benefits and small harms. They omit tuning/refitting uncertainty and cannot account fully for dependence within games because game identifiers are absent.

## Effect on the shooter conclusions

For this descriptive sensitivity, refit all supplied observations with the shooter penalty fixed at 30, the value chosen in earlier validation. Standardize every shooter's probability over the identical observed joint goalie-season distribution. This comparison measures the change from opponent adjustment, keeping the amount of shooter regularization fixed.

| Assumed goalie-effect prior SD on log-odds scale | Goalie penalty | Median absolute change, goals per 100 attempts | Largest absolute change | Shooter rank correlation |
| --- | ---: | ---: | ---: | ---: |
| 0.10, the final validation-selected penalty | 100 | 0.0046 | 0.0144 | 0.9994 |
| 0.25 sensitivity | 16 | 0.0179 | 0.0482 | 0.9978 |
| 0.50 sensitivity | 4 | 0.0336 | 0.0923 | 0.9964 |
| 1.00 sensitivity | 1 | 0.0425 | 0.1292 | 0.9885 |

At the final selected strength, even the largest shooter adjustment is only 0.014 goals per 100 attempts. Much looser goalie pooling also leaves the shooter comparisons highly similar. Rank correlations describe point estimates and do not establish confident player ordering.

At penalty 100, the median local conditional goalie variance reduction is about 5.2% relative to the specified Gaussian prior, and no individual approximate 95% goalie-effect interval excludes zero. These calculations are conditional on the working model and assumed penalty; they are not estimates of data-driven skill reliability. They illustrate how strongly the individual estimates depend on pooling in this specification.

## Interpretation and scope

- The primary decision is about useful opponent adjustment for the take-home. A goalie-associated effect here also contains team defense, opponent selection and shot mix; the all-attempt endpoint includes blocked and missed shots.
- The source supplies season labels but no game dates. These checks evaluate persistence between supplied seasons. A within-season take-home comparison needs additional metadata. The final notebook presents its NHL comparisons as separate analyses.
- The final supplied season has only 1,199 attempts and may be incomplete. Report it separately; the combined result gives about 78% of its weight to 2023.
- These years have been explored previously, so this is historical validation. The small number of temporal comparisons limits conclusions about other periods.
- This comparison keeps season treatment identical across candidate families. It evaluates a stable additive goalie term. It supplies no evidence for or against more detailed goalie specialization in richer NHL data.
- Pooling can be performed with these observations. The practical finding is that its goalie-specific contribution is too small and uncertain to justify featuring goalie strengths in the main assessment.
- The predictive shooter penalty belongs to this bounded historical comparison. The final notebook's Bayesian model learns its shooter pooling scale separately and includes NHL comparisons as additional context.

## Verification and reproducibility

The numerical optimizer converged for every candidate fit; the largest absolute final score gradient was 8.3 × 10⁻⁸. Independent review checked the grouped-binomial likelihood, gradient, Hessian, chronological selection and interpretation. Source totals and overlap were also independently audited.

From the repository root, use the Python environment installed from `requirements-notebook.txt`. These commands write regenerated evidence to a separate directory:

```sh
python analysis/goalie_sufficiency/check_goalies.py --output-dir /tmp/penguins-goalie-check
python analysis/goalie_sufficiency/support_audit.py --output-dir /tmp/penguins-goalie-check
```

The scripts locate the bundled raw CSV relative to their own paths and verify its SHA-256 before analysis. The optional `--output-dir` controls generated outputs; its default is this evidence directory. Only NumPy and pandas are needed for these two scripts.

Supporting artifacts in this directory:

- `protocol.json`: frozen design and source checksum, written before candidate fitting; the bundled copy uses a portable source path and adds the final-notebook comparison note.
- `results.json`: test losses, resampling intervals and shooter sensitivity.
- `candidate_scores.json`: every tested regularization setting and diagnostic.
- `predictions.csv.gz`: paired historical predictions.
- `support_audit.md`: independent exposure and overlap check.

Source: [bundled original shot data](../../data/raw/shot-data.csv). SHA-256: `25e5ea674e57f838f21062059630db795699d8499cf6af03699628df1b5c8af2`. This is the byte-identical supplied CSV used for the historical analysis.
