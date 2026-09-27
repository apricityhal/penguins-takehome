"""Bounded historical test of goalie adjustment in the supplied take-home.

Source is read-only. All recorded attempts, including blocks, form the target.
Ridge logistic effects implement Gaussian partial pooling; tuning estimates
predictive regularization, not a population variance or pure goalie talent.
"""
from pathlib import Path
import argparse
import hashlib
import json
import numpy as np
import pandas as pd

OUT = Path(__file__).resolve().parent
REPO_ROOT = OUT.parents[1]
SOURCE_RELATIVE = Path('data/raw/shot-data.csv')
SOURCE = REPO_ROOT / SOURCE_RELATIVE
SOURCE_SHA256 = '25e5ea674e57f838f21062059630db795699d8499cf6af03699628df1b5c8af2'
GRID = [0.3, 1., 3., 10., 30., 100., 300., 1000., None]
SEED = 20260927


def sigmoid(z):
    return 1 / (1 + np.exp(-np.clip(z, -35, 35)))


def loss(y, p):
    return -(y*np.log(np.clip(p, 1e-12, 1)) +
             (1-y)*np.log(np.clip(1-p, 1e-12, 1)))


def fit(d, shooter_penalty, goalie_penalty):
    a = d.groupby(['season', 'shooter_id', 'goalie_id']).is_goal.agg(['sum', 'size']).reset_index()
    seasons = sorted(a.season.unique())
    shooters = sorted(a.shooter_id.unique()) if shooter_penalty is not None else []
    goalies = sorted(a.goalie_id.unique()) if goalie_penalty is not None else []
    categories = [seasons, shooters, goalies]
    fields = ['season', 'shooter_id', 'goalie_id']
    columns, penalties, maps = [], [], []
    k = 0
    for vals, field, penalty in zip(categories, fields, [0, shooter_penalty, goalie_penalty]):
        m = {v:i+k for i,v in enumerate(vals)}
        maps.append(m)
        if vals:
            columns.append(a[field].map(m).to_numpy(dtype=int))
            penalties.extend([penalty]*len(vals))
        k += len(vals)
    pen = np.array(penalties, float)
    y, n = a['sum'].to_numpy(float), a['size'].to_numpy(float)
    b = np.zeros(k)
    for s, i in maps[0].items():
        rate = d.loc[d.season==s, 'is_goal'].mean()
        b[i] = np.log(rate/(1-rate))

    def state(beta, hessian=False):
        z = sum(beta[c] for c in columns)
        p = sigmoid(z)
        objective = float((n*np.logaddexp(0,z)-y*z).sum()+.5*(pen*beta*beta).sum())
        residual = n*p-y
        grad = sum(np.bincount(c, weights=residual, minlength=k) for c in columns)+pen*beta
        if not hessian:
            return objective, grad
        w = n*p*(1-p)
        h = np.diag(pen.copy())
        for c in columns:
            h[np.diag_indices(k)] += np.bincount(c, weights=w, minlength=k)
        for i,c in enumerate(columns):
            for e in columns[i+1:]:
                block = np.bincount(c*k+e, weights=w, minlength=k*k).reshape(k,k)
                h += block+block.T
        return objective, grad, h

    for iteration in range(60):
        objective, grad, h = state(b, True)
        if np.max(np.abs(grad)) < 1e-7:
            break
        step = np.linalg.solve(h, grad)
        scale = 1.
        while scale > 1e-9:
            candidate = b-scale*step
            if state(candidate)[0] <= objective+1e-10:
                b = candidate
                break
            scale *= .5
        else:
            raise RuntimeError('Newton line search failed')
    _, grad, h = state(b, True)
    error = float(np.max(np.abs(grad)))
    if error > 1e-5:
        raise RuntimeError(f'Fit failed to converge: {error}')
    return {'beta':b, 'maps':maps, 'hessian':h, 'penalty':pen,
            'season_weights':d.groupby('season').size().to_dict(),
            'max_abs_gradient':error, 'iterations':iteration+1}


def predict(d, model, intercept_policy='latest'):
    b, maps = model['beta'], model['maps']
    if intercept_policy == 'latest':
        intercept = b[maps[0][max(maps[0])]]
    else:
        weights = model['season_weights']
        intercept = sum(b[i]*weights[s] for s,i in maps[0].items())/sum(weights.values())
    z = np.full(len(d), intercept)
    for field, m in zip(['shooter_id','goalie_id'], maps[1:]):
        z += d[field].map({v:b[i] for v,i in m.items()}).fillna(0).to_numpy()
    return sigmoid(z)


def metrics(d, p):
    ll = loss(d.is_goal.to_numpy(), p)
    br = (d.is_goal.to_numpy()-p)**2
    temp = d[['shooter_id']].copy()
    temp['ll'], temp['br'] = ll, br
    return {'logloss':float(ll.mean()), 'brier':float(br.mean()),
            'equal_shooter_logloss':float(temp.groupby('shooter_id').ll.mean().mean()),
            'equal_shooter_brier':float(temp.groupby('shooter_id').br.mean().mean())}


def pick(records):
    # Prefer stronger pooling only for losses equal to numerical precision.
    return min(records, key=lambda x:(round(x['validation_loss'],12),
                    -(1e12 if x['goalie_penalty'] is None else x['goalie_penalty']),
                    -(1e12 if x['shooter_penalty'] is None else x['shooter_penalty'])))


def interval(d, delta, cluster):
    a = d[[cluster]].copy()
    a['delta'] = delta
    g = a.groupby(cluster).delta.agg(['sum','size'])
    rng = np.random.default_rng(SEED)
    ix = rng.integers(len(g),size=(6000,len(g)))
    boot = g['sum'].to_numpy()[ix].sum(1)/g['size'].to_numpy()[ix].sum(1)
    return [float(x) for x in np.quantile(boot,[.025,.975])]


def main(output_dir=OUT):
    output_dir = Path(output_dir)
    source_sha256 = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
    if source_sha256 != SOURCE_SHA256:
        raise ValueError('Bundled raw source checksum differs from the historical analysis.')
    d = pd.read_csv(SOURCE)
    assert len(d)==13269 and int(d.is_goal.sum())==997
    assert set(d.is_goal.unique())=={0,1}
    protocol = {
        'source':SOURCE_RELATIVE.as_posix(), 'sha256':source_sha256,
        'source_note':'Original supplied CSV, retained byte-for-byte in the bundle. This historical ridge/MAP analysis uses all 13,269 rows; the final notebook uses 13,224 cleaned rows and a Bayesian model.',
        'target':'Goal probability per recorded attempt, including blocks and misses.',
        'model':'logit(p) = training-season intercept + pooled shooter effect + optional pooled goalie effect.',
        'objective':'Binomial negative log likelihood + 0.5 * penalty * sum(effect squared).',
        'grid':GRID, 'seed':SEED,
        'validation':'Expanding windows. Test 2023 after tuning on 2021->2022. Test 2024 after tuning on 2021->2022 and 2021:2022->2023; equal fold weighting. Each arm tunes shooter penalty separately. Primary loss: mean shot log loss.',
        'future_intercept':'Carry latest training-season intercept; exposure-weighted average intercept sensitivity.',
        'unknown_identity':'Zero identity effect, with the same training-only intercept.',
        'limitations':['Exploratory historical validation; these years were previously inspected.',
        'Only four season labels and no dates/games; within-season forecasting is unavailable.',
        '2024 coverage is smaller and may be incomplete.',
        'Missing shot context and team means a goalie effect is an opponent association, not isolated stopping talent.',
        'Cluster intervals condition on fitted models/selection, resample one identity dimension at a time, and cannot recover missing game dependence.',
        'Ridge strengths selected for prediction are not estimates of population talent variance.']}
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir/'protocol.json').write_text(json.dumps(protocol,indent=2))
    all_fits = {}
    records = []
    for year in [2022,2023,2024]:
        train, test = d[d.season<year], d[d.season==year]
        for sp in GRID:
            for gp in GRID:
                f = fit(train, sp, gp)
                all_fits[(year,sp,gp)] = f
                for policy in ['latest','average']:
                    p = predict(test,f,policy)
                    records.append({'year':year,'shooter_penalty':sp,'goalie_penalty':gp,
                        'intercept_policy':policy,**metrics(test,p),
                        'max_abs_gradient':f['max_abs_gradient']})
        print(f'Completed candidate fits for {year}',flush=True)
    (output_dir/'candidate_scores.json').write_text(json.dumps(records,indent=2))
    results = {'protocol':protocol, 'tests':[], 'combined':[], 'sensitivity':[]}
    predicted = []
    frozen = {}
    for policy in ['latest','average']:
        for year in [2023,2024]:
            candidates = []
            for sp in GRID:
                for gp in GRID:
                    old = [r for r in records if r['year']<year and r['shooter_penalty']==sp
                        and r['goalie_penalty']==gp and r['intercept_policy']==policy]
                    candidates.append({'shooter_penalty':sp,'goalie_penalty':gp,
                                       'validation_loss':float(np.mean([r['logloss'] for r in old]))})
            base = pick([c for c in candidates if c['goalie_penalty'] is None])
            pooled = pick(candidates)
            # A finite-only comparator ensures the observed question is visible if pooling chooses zero effect.
            finite = pick([c for c in candidates if c['goalie_penalty'] is not None])
            selected = {'shooter_only':base,'goalie_allowed':pooled,'finite_goalie':finite}
            if year==2024 and policy=='latest':
                frozen=selected
            test = d[d.season==year].copy()
            ps={}
            for arm, c in selected.items():
                ps[arm]=predict(test,all_fits[(year,c['shooter_penalty'],c['goalie_penalty'])],policy)
            z={'test_season':year,'intercept_policy':policy,'n':len(test), 'goals':int(test.is_goal.sum()),
               'selected':selected,'scores':{arm:metrics(test,p) for arm,p in ps.items()},'comparisons':{}}
            for arm in ['goalie_allowed','finite_goalie']:
                delta=loss(test.is_goal.to_numpy(),ps[arm])-loss(test.is_goal.to_numpy(),ps['shooter_only'])
                z['comparisons'][arm]={'delta_logloss':float(delta.mean()),
                    'relative_improvement_pct':float(-100*delta.mean()/z['scores']['shooter_only']['logloss']),
                    'goalie_cluster_interval':interval(test,delta,'goalie_id'),
                    'shooter_cluster_interval':interval(test,delta,'shooter_id')}
            for arm,p in ps.items():
                test['p_'+arm]=p
            test['intercept_policy']=policy
            predicted.append(test)
            results['tests'].append(z)
            print(json.dumps(z),flush=True)
    pred=pd.concat(predicted)
    pred[['shooter_id','goalie_id','season','is_goal','intercept_policy','p_shooter_only','p_goalie_allowed','p_finite_goalie']].to_csv(output_dir/'predictions.csv.gz',index=False)
    for policy, test in pred.groupby('intercept_policy'):
        baseline=metrics(test,test.p_shooter_only.to_numpy())
        z={'intercept_policy':policy,'n':len(test),'baseline':baseline,'comparisons':{}}
        for arm in ['goalie_allowed','finite_goalie']:
            p=test['p_'+arm].to_numpy()
            delta=loss(test.is_goal.to_numpy(),p)-loss(test.is_goal.to_numpy(),test.p_shooter_only.to_numpy())
            z['comparisons'][arm]={'scores':metrics(test,p),'delta_logloss':float(delta.mean()),
                'relative_improvement_pct':float(-100*delta.mean()/baseline['logloss']),
                'goalie_cluster_interval':interval(test,delta,'goalie_id'),
                'shooter_cluster_interval':interval(test,delta,'shooter_id')}
        results['combined'].append(z)

    # Full-sample sensitivity, separate from forecasting. Standardize every shooter
    # to the identical observed joint goalie-season distribution.
    sp=frozen['shooter_only']['shooter_penalty']
    scenarios=[('no_goalie',None),('goalie_sd_0.1',100.),('goalie_sd_0.25',16.),('goalie_sd_0.5',4.),('goalie_sd_1',1.)]
    standardized={}
    profiles=[]
    for name,gp in scenarios:
        f=fit(d,sp,gp)
        b,m=f['beta'],f['maps']
        context=d.season.map({v:b[i] for v,i in m[0].items()}).to_numpy(copy=True)
        context+=d.goalie_id.map({v:b[i] for v,i in m[2].items()}).fillna(0).to_numpy()
        standardized[name]=np.array([sigmoid(context+(b[m[1][s]] if s in m[1] else 0)).mean() for s in sorted(d.shooter_id.unique())])
        if gp is not None:
            covariance=np.linalg.inv(f['hessian'])
            prior_var=1/gp
            for goalie,i in m[2].items():
                profiles.append({'scenario':name,'goalie_id':int(goalie),'effect':float(b[i]),
                    'conditional_sd':float(np.sqrt(covariance[i,i])),
                    'conditional_variance_reduction':float(1-covariance[i,i]/prior_var),
                    'interval_excludes_zero':bool(abs(b[i])>1.96*np.sqrt(covariance[i,i]))})
    baseline=standardized['no_goalie']
    for name,gp in scenarios:
        shift=100*(standardized[name]-baseline)
        prof=[x for x in profiles if x['scenario']==name]
        results['sensitivity'].append({'scenario':name,'goalie_penalty':gp,'shooter_penalty':sp,
            'median_absolute_goals_per_100_change':float(np.median(abs(shift))),
            'maximum_absolute_goals_per_100_change':float(abs(shift).max()),
            'rank_correlation':float(pd.Series(baseline).rank().corr(pd.Series(standardized[name]).rank())),
            'median_conditional_goalie_variance_reduction':float(np.median([x['conditional_variance_reduction'] for x in prof])) if prof else None,
            'goalie_intervals_excluding_zero':sum(x['interval_excludes_zero'] for x in prof) if prof else None})
    pd.DataFrame({'shooter_id':sorted(d.shooter_id.unique()),**{k:100*v for k,v in standardized.items()}}).to_csv(output_dir/'shooter_sensitivity.csv',index=False)
    pd.DataFrame(profiles).to_csv(output_dir/'goalie_conditional_sensitivity.csv',index=False)
    results['max_fit_gradient']=max(r['max_abs_gradient'] for r in records)
    (output_dir/'results.json').write_text(json.dumps(results,indent=2))
    print(json.dumps({'combined':results['combined'],'sensitivity':results['sensitivity'],'max_fit_gradient':results['max_fit_gradient']}),flush=True)


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output-dir', type=Path, default=OUT,
                        help='Directory for regenerated evidence (default: script directory).')
    main(parser.parse_args().output_dir)
