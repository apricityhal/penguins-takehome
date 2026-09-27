# NHL snapshot coverage and source notes

The notebook uses these compact snapshots from the saved NHL data collection. Season integers identify the starting year: `2024` means 2024–25. Goals per attempt include blocked attempts in the denominator.

| File | Coverage | Rows |
| --- | --- | ---: |
| `nhl_2024_player_games.csv` | 2024–25 five-on-five player-game counts; 920 skaters and 1,312 games | 47,224 |
| `nhl_seasons.csv` | 2018–19 through 2025–26 five-on-five player-season counts | 7,440 |
| `nhl_all_situations_halves.csv` | 2021–22 through 2025–26 player-season-half counts, all situations | 8,542 |
| `nhl_birth_dates.csv` | NHL player birth dates used for age controls | 2,011 |

Game and season counts come from the saved MoneyPuck skater tables; birth dates come from saved NHL player bios. `nhl_sources.json` preserves extraction queries and CSV checksums. The half-season table aggregates the original all-situations player-game counts; the delivered notebook sums the halves into season histories. `nhl_match_rng.json` preserves the starting generator state for the 20,000 matched-forward samples; the notebook recomputes the samples.

The opportunity-generation comparison uses five-on-five counts. The NHL pooling and variation comparisons use all-situations counts. Within each pooling table column, all forecast methods use the same players. The one-season and four-season columns have different eligible cohorts because the 61–1,033 prior-attempt filter is applied to each history separately: 395 and 312 returners, with 261 in common.

## Known source limitations

The snapshots preserve source counts and player identities. An earlier reconciliation against saved official NHL records identified a missing Chicago team side for game `2025020964` on March 3, 2026: 18 skater appearances, 42 attempts, and two goals are absent from the MoneyPuck game-derived data. Across audited 2025–26 games, the net discrepancy is 38 fewer attempts and two fewer goals after other small differences are included.

The earlier reconciliation also identified player-attribution discrepancies in 2021–22 and 2022–23. Seventeen flagged player-seasons remain in the all-situations snapshot; nine forward player-seasons across seven identities enter the four-season training population. The final notebook uses the preserved source counts. Its current results therefore retain these source limitations; the effect of correcting or excluding those records has not been established for these exact notebook comparisons.

The broader source database, collection scripts, event/roster archive, and earlier source-quality investigations are separate research materials. This package supplies every NHL input read by the notebook and supports reproducing its reported calculations from these fixed snapshots.
