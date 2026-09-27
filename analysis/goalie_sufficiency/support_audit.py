"""Read-only count audit of goalie support in the supplied Penguins sample.

Reports exposure, recurrence, overlap and illustrative precision. Fits no
performance model and creates no player or goalie ranking.
"""
from pathlib import Path
from collections import defaultdict
import argparse
import hashlib
import json
import math
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
REPO_ROOT = OUT.parents[1]
SOURCE_RELATIVE = Path('data/raw/shot-data.csv')
SOURCE = REPO_ROOT / SOURCE_RELATIVE
SOURCE_SHA256 = '25e5ea674e57f838f21062059630db795699d8499cf6af03699628df1b5c8af2'


def quantiles(x):
    return {str(k): float(v) for k, v in x.quantile([0, .1, .25, .5, .75, .9, 1]).items()}


def components(frame):
    graph = defaultdict(set)
    for shooter, goalie in frame[['shooter_id', 'goalie_id']].drop_duplicates().itertuples(index=False, name=None):
        a, b = ('s', int(shooter)), ('g', int(goalie))
        graph[a].add(b)
        graph[b].add(a)
    unseen = set(graph)
    result = []
    while unseen:
        stack, comp = [unseen.pop()], []
        while stack:
            item = stack.pop()
            comp.append(item)
            nxt = graph[item] & unseen
            unseen -= nxt
            stack.extend(nxt)
        result.append({'shooters': sum(x[0] == 's' for x in comp),
                       'goalies': sum(x[0] == 'g' for x in comp)})
    return sorted(result, key=lambda x: -(x['shooters'] + x['goalies']))


def support(d, actor, other):
    s = d.groupby(actor).agg(n=('is_goal', 'size'), goals=('is_goal', 'sum'),
                            seasons=('season', 'nunique'), opponents=(other, 'nunique'))
    return {
        'entities': len(s), 'attempts_quantiles': quantiles(s.n),
        'goals_quantiles': quantiles(s.goals), 'opponents_quantiles': quantiles(s.opponents),
        'season_coverage_counts': {str(k): int(v) for k, v in s.seasons.value_counts().sort_index().items()},
        'attempts_below': {str(k): int((s.n < k).sum()) for k in [10, 25, 50, 100, 200, 300, 500]},
        'goals_below': {str(k): int((s.goals < k).sum()) for k in [1, 5, 10, 20, 30]},
        'entity_season_attempts_quantiles': quantiles(d.groupby([actor, 'season']).size()),
        'entity_season_goals_quantiles': quantiles(d.groupby([actor, 'season']).is_goal.sum()),
        'entity_season_count': int(d.groupby([actor, 'season']).ngroups),
        'entity_seasons_zero_goals': int((d.groupby([actor, 'season']).is_goal.sum() == 0).sum()),
    }


def main(output_dir=OUT):
    output_dir = Path(output_dir)
    source_sha256 = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if source_sha256 != SOURCE_SHA256:
        raise ValueError('Bundled raw source checksum differs from the historical analysis.')
    d = pd.read_csv(SOURCE)
    p = float(d.is_goal.mean())
    pair = d.groupby(['shooter_id', 'goalie_id']).size()
    r = {
        'source': SOURCE_RELATIVE.as_posix(), 'sha256': source_sha256,
        'population': 'All 13,269 supplied attempts, including blocks; private selection and season semantics remain unverified.',
        'n': len(d), 'goals': int(d.is_goal.sum()), 'pooled_goal_rate': p,
        'columns': list(d.columns), 'missing': {k: int(v) for k, v in d.isna().sum().items()},
        'goalies': support(d, 'goalie_id', 'shooter_id'),
        'shooters': support(d, 'shooter_id', 'goalie_id'),
        'overlap': {'observed_pairs': len(pair),
                    'possible_pairs': int(d.shooter_id.nunique() * d.goalie_id.nunique()),
                    'pair_exposure_quantiles': quantiles(pair),
                    'pairs_below': {str(k): int((pair < k).sum()) for k in [2, 5, 10, 20]},
                    'components': components(d)},
        'seasons': [], 'adjacent_seasons': [], 'cumulative_prior_support': [],
    }
    for season, part in d.groupby('season'):
        r['seasons'].append({'season': int(season), 'n': len(part), 'goals': int(part.is_goal.sum()),
                             'goalies': support(part, 'goalie_id', 'shooter_id'),
                             'shooters': support(part, 'shooter_id', 'goalie_id'),
                             'components': components(part)})
    seasons = sorted(d.season.unique())
    for before, after in zip(seasons[:-1], seasons[1:]):
        a, b = d[d.season == before], d[d.season == after]
        goalies_a, goalies_b = set(a.goalie_id), set(b.goalie_id)
        shooters_a, shooters_b = set(a.shooter_id), set(b.shooter_id)
        r['adjacent_seasons'].append({
            'from': int(before), 'to': int(after),
            'goalies_prior': len(goalies_a), 'goalies_later': len(goalies_b),
            'goalies_in_both': len(goalies_a & goalies_b),
            'goalies_later_without_previous_season': len(goalies_b - goalies_a),
            'later_attempts_with_previous_season_goalie': int(b.goalie_id.isin(goalies_a).sum()),
            'shooters_in_both': len(shooters_a & shooters_b),
        })
    for season in seasons[1:]:
        prior, later = d[d.season < season], d[d.season == season]
        n = prior.groupby('goalie_id').size()
        per_goalie = later.groupby('goalie_id').size().rename('later_n').to_frame()
        per_goalie['prior_n'] = per_goalie.index.map(n).fillna(0)
        r['cumulative_prior_support'].append({
            'test_season': int(season), 'test_attempts': len(later), 'test_goalies': len(per_goalie),
            'prior_n_for_test_goalies_quantiles': quantiles(per_goalie.prior_n),
            'test_goalies_with_prior_n_at_least': {str(k): int((per_goalie.prior_n >= k).sum()) for k in [1, 25, 50, 100, 200]},
            'test_attempts_with_goalie_prior_n_at_least': {str(k): int(per_goalie.loc[per_goalie.prior_n >= k, 'later_n'].sum()) for k in [1, 25, 50, 100, 200]},
        })
    reference = {}
    for who in ['goalies', 'shooters']:
        n = r[who]['attempts_quantiles']['0.5']
        se = math.sqrt(p * (1-p) / n)
        reference[who] = {'median_n': n, 'binomial_se_at_pooled_rate': se,
                          'normal_95_halfwidth_at_pooled_rate': 1.96 * se,
                          'known_baseline_logit_effect_se': 1 / math.sqrt(n*p*(1-p))}
    r['precision_reference'] = {
        'interpretation': 'Illustration using independent identical Bernoulli attempts at the pooled conversion rate. These are neither fitted ability intervals nor covariate-adjusted precision guarantees. Context, dependence, selection and joint parameter estimation change precision.',
        'at_median_exposure': reference,
        'n_needed_for_normal_95_rate_halfwidth': {str(v): math.ceil(1.96**2*p*(1-p)/(v*v)) for v in [.02, .03, .05]},
    }
    r['limits'] = [
        'IDs are anonymous and have no NHL crosswalk in this file.',
        'All-attempt goal conversion includes shooter mix, blocks and misses; it is not goalie save percentage.',
        'Graph connectivity allows comparisons under a constrained model; it establishes neither precise effects nor predictive improvement.',
        'Future goalie recurrence supports historical validation, but short histories and four season labels limit it.',
        'Counts can motivate strong pooling or a simpler scope; incremental forecast benefit requires a matched temporal comparison.',
    ]
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir/'support_audit.json').write_text(json.dumps(r, indent=2))
    md = ['# Goalie support in the supplied sample', '',
          f'Source: `{SOURCE_RELATIVE.as_posix()}`. SHA-256: `{r["sha256"]}`.', '',
          f'All-attempt denominator: {len(d):,} attempts and {int(d.is_goal.sum()):,} goals.', '',
          '| Measure | Goalies | Shooters |', '| --- | ---: | ---: |']
    for label, fn in [
        ('Distinct IDs', lambda z: str(z['entities'])),
        ('Median attempts', lambda z: str(z['attempts_quantiles']['0.5'])),
        ('Attempt range', lambda z: f"{z['attempts_quantiles']['0.0']:g}–{z['attempts_quantiles']['1.0']:g}"),
        ('Median goals', lambda z: str(z['goals_quantiles']['0.5'])),
        ('IDs with fewer than 50 attempts', lambda z: str(z['attempts_below']['50'])),
        ('IDs with fewer than 10 goals', lambda z: str(z['goals_below']['10'])),
        ('Median entity-season attempts', lambda z: str(z['entity_season_attempts_quantiles']['0.5'])),
    ]:
        md.append(f"| {label} | {fn(r['goalies'])} | {fn(r['shooters'])} |")
    md += ['', 'The observed shooter–goalie graph has one connected component. This supports model identifiability after constraints, while sparse observations still limit precision.', '',
           '## Cumulative history available for later seasons', '',
           '| Test season | Goalies | Goalies with prior history | Goalies with at least 100 prior attempts | Later attempts covered by at least 100 prior attempts |',
           '| --- | ---: | ---: | ---: | ---: |']
    for z in r['cumulative_prior_support']:
        md.append(f"| {z['test_season']} | {z['test_goalies']} | {z['test_goalies_with_prior_n_at_least']['1']} | {z['test_goalies_with_prior_n_at_least']['100']} | {z['test_attempts_with_goalie_prior_n_at_least']['100']} / {z['test_attempts']} |")
    md += ['', '## Precision interpretation', '', r['precision_reference']['interpretation'], '']
    for who, z in reference.items():
        md.append(f"At the {who} median of {z['median_n']:g} attempts, the independent-binomial reference SE is {100*z['binomial_se_at_pooled_rate']:.2f} percentage points; the normal 95% reference half-width is {100*z['normal_95_halfwidth_at_pooled_rate']:.2f} points.")
    md += ['', '## Decision implication', '',
           'The sample supports treating unpooled goalie effects as imprecise. It also supports a connected, partially pooled comparison if opponent adjustment is important. Exposure counts alone cannot determine whether adding a shared goalie effect improves shooting forecasts. Compare a pooled shooter model against the same model with one strongly pooled goalie term on identical later attempts; preserve a no-individual-goalie model as the default when improvement is too small or uncertain for the intended use.', '',
           'No performance model was fitted and no shooter or goalie ranking was produced.', '']
    (output_dir/'support_audit.md').write_text('\n'.join(md))
    print(json.dumps({k: v for k, v in r.items() if k != 'seasons'}, indent=2))


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=OUT,
                        help='Directory for regenerated evidence (default: script directory).')
    main(parser.parse_args().output_dir)
