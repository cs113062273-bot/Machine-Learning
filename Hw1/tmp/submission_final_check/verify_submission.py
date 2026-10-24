from pathlib import Path
import hashlib, json, shutil
import numpy as np
import pandas as pd
import nbformat
import pymupdf

ROOT=Path.cwd(); HERE=ROOT/'tmp/submission_final_check'; DATA=ROOT/'HW1_results_113062273'
report=pymupdf.open(ROOT/'HW1_final__report_113062273.pdf')
assert len(report)<=10
checks={'pdf_pages':len(report)}
profiles=pd.read_csv(DATA/'track_cluster_profiles_raw.csv',index_col=0)
counts=pd.read_csv(DATA/'track_cluster_counts.csv',index_col=0).tracks
ct=report[2].find_tables().tables[0].extract()
assert [int(v.split('\n')[1].split()[0].replace(',','')) for v in ct[0][1:]]==counts.tolist()
for row in ct[1:]:
    for c,value in enumerate(row[1:]): assert value==f'{profiles.loc[c,row[0]]:.4f}'
checks['seven_cluster_table']=True
reg=pd.read_csv(DATA/'regression_results.csv',index_col=0)
rt=report[3].find_tables().tables[0].extract()
for row,field in zip(rt[1:],['preregistered_rmse','OLS_test_rmse','mean_baseline_test_rmse']):
    for c,target in enumerate(['energy','popularity'],1): assert row[c]==f'{reg.loc[target,field]:.4f}'
art=pd.read_csv(DATA/'additional_artist_information.csv',index_col=0)
at=report[3].find_tables().tables[1].extract()
for row,subset in zip(at[1:],['all','seen_artist_string','unseen_artist_string']):
    assert int(row[1].replace(',',''))==art.loc[subset,'tracks']
    for col,field in [(2,'audio_only_rmse'),(3,'audio_plus_artists_rmse')]: assert row[col]==f'{art.loc[subset,field]:.4f}'
checks['regression_and_artists_tables']=True
metrics=pd.read_csv(DATA/'kmeans_selection.csv',index_col=0)
assert f'{100*(1-metrics.loc[7,"inertia"]/metrics.loc[2,"inertia"]):.2f}'=='40.46'
assert f'{100*(1-metrics.loc[7,"silhouette"]/metrics.loc[2,"silhouette"]):.2f}'=='21.73'
st=pd.read_csv(DATA/'cluster_stability.csv',index_col=0)
assert f'{100*st.loc["uniform_subsample_1","matched_changed_fraction"]:.2f}'=='1.51'
assert f'{100*st.loc["uniform_subsample_2","matched_changed_fraction"]:.2f}'=='0.79'
checks['k_selection_and_stability']=True
pv=pd.read_csv(DATA/'pca_variance.csv',index_col=0)
assert f'{100*pv.loc["PC7","standardized_cumulative"]:.2f}'=='94.86'
assert f'{100*pv.loc["PC6","standardized_cumulative"]:.2f}'=='89.77'
assert f'{100*pv.loc["PC1","raw_ratio"]:.2f}'=='97.13'
fv=pd.read_csv(DATA/'pca_feature_variance.csv',index_col=0)
assert f'{fv.loc["tempo","raw_variance"]:.4f}'=='882.4921'
assert f'{100*fv.loc["tempo","share_of_total_raw_variance"]:.2f}'=='96.99'
load=pd.read_csv(DATA/'pca_loadings_standardized.csv',index_col=0)
for pc,pos,neg in [('PC1',['loudness','energy'],['acousticness']),('PC2',['danceability','valence'],['instrumentalness','tempo']),('PC3',['liveness','speechiness'],[])]:
    assert load.loc[pos,pc].gt(0).all() and load.loc[neg,pc].lt(0).all()
checks['pca_values_and_loading_signs']=True
a=pd.read_csv(DATA/'genre_group_assignments.csv',index_col=0)
for config,genres in [('euclidean_average',['opera','classical','ambient']),('cityblock_average',['opera','honky-tonk','jazz']),('euclidean_average',['black-metal','death-metal','grindcore']),('cityblock_average',['black-metal','death-metal','grindcore','breakbeat','drum-and-bass']),('euclidean_average',['metal','heavy-metal','pop','dance','house']),('euclidean_complete',['metal','heavy-metal']),('euclidean_complete',['pop','dance','house']),('cityblock_complete',['black-metal','death-metal','grindcore','metal','heavy-metal'])]:
    assert a.loc[genres,config].nunique()==1
assert a.loc['metal','euclidean_complete']!=a.loc['pop','euclidean_complete']
assert a.loc['black-metal','cityblock_average']!=a.loc['metal','cityblock_average']
quality=pd.read_csv(DATA/'genre_quality_common_euclidean.csv',index_col=0).iloc[:,0]
assert [f'{quality.loc[c]:.4f}' for c in ['euclidean_average','euclidean_complete','cityblock_average','cityblock_complete']]==['0.2634','0.2079','0.2387','0.2032']
gp=pd.read_csv(DATA/'genre_group_profiles_euclidean_average.csv',index_col=0)
assert [f'{gp.loc[a.loc[g,"euclidean_average"],f]:.3f}' for g in ['black-metal','classical'] for f in ['energy','acousticness']]==['0.910','0.014','0.276','0.801']
checks['genre_comparisons']=True
q4=pd.read_csv(DATA/'ridge_correlated_summary.csv',index_col=0)
assert [f'{q4.loc[s,f]:.6f}' for s in ['full_polynomial','small_polynomial'] for f in ['OLS_test_rmse','selected_Ridge_test_rmse']]==['0.128638','0.128637','0.181219','0.145732']
assert f'{100*(1-q4.loc["small_polynomial","selected_Ridge_test_rmse"]/q4.loc["small_polynomial","OLS_test_rmse"]):.2f}'=='19.58'
qe=pd.read_csv(DATA/'ridge_correlated_training_evidence.csv')
assert [f'{v:.4f}' for v in qe.training_pearson_r]==['0.9646','0.9129','0.9865']
full=pd.read_csv(DATA/'ridge_correlated_full_polynomial_path.csv',index_col=0)
small=pd.read_csv(DATA/'ridge_correlated_small_polynomial_path.csv',index_col=0)
assert [f'{v:.4f}' for v in full.coefficient_l2.iloc[[0,-1]]]==['0.7977','0.0247']
assert f'{full.test_rmse.iloc[-1]:.6f}'=='0.204653'
assert f'{small.test_rmse.iloc[-1]:.6f}'=='0.256812'
assert q4.loc['full_polynomial','alpha_selected_on_validation']==1
assert f'{q4.loc["small_polynomial","alpha_selected_on_validation"]:.4f}'=='3.1623'
assert len(full)==len(small)==25
checks['regularization_all_reported_numbers']=True

# Rebuild the cleaned inputs and splitting from the submitted sources. This also
# verifies identity grouping and the first-principles calculations below.
n=nbformat.read(ROOT/'HW1_code_113062273.ipynb',as_version=4)
ns={'__name__':'__main__'}
setup=n.cells[2].source.replace("OUT = Path('HW1_results_113062273')",f'OUT = Path({str(HERE)!r})')
exec(setup,ns)
ns['display']=lambda *args,**kwargs:None
ns['table']=lambda name,frame,show=True:frame
for i in [3,5,6,18]: exec(n.cells[i].source,ns)
raw,clean=ns['raw'],ns['clean']
assert raw.shape==(114000,20) and len(clean)==88858
assert raw.track_id.value_counts().gt(1).sum()==16641 and raw.duplicated().sum()==450
assert len(ns['conflict_ids'])==720 and len(ns['valid_rows'])==111458
assert [len(raw),len(ns['dedup']),len(ns['dedup'].loc[~ns['invalid'].loc[ns['dedup'].index].any(axis=1)]),len(ns['valid_rows']),len(clean)]==[114000,113550,113386,111458,88858]
assert [raw.tempo.le(0).sum(),raw.time_signature.eq(0).sum(),raw.duration_ms.le(0).sum(),ns['invalid'].any(axis=1).sum()]==[157,163,1,164]
assert raw.track_genre.nunique()==114 and raw.groupby('track_genre').size().eq(1000).all()
splits=pd.read_csv(DATA/'split_track_ids.csv',index_col=0)
assert splits.track_id.is_unique and splits.groupby('recording_group').split.nunique().eq(1).all()
for name,idx in [('train',ns['train_idx']),('validation',ns['val_idx']),('test',ns['test_idx'])]:
    assert set(splits.loc[splits.split.eq(name),'track_id'])==set(clean.iloc[idx].track_id)
checks['raw_counts_cleaning_and_no_split_leakage']=True

# Independent NumPy least squares and explicit mean baseline, not sklearn models.
dev,test=ns['dev_idx'],ns['test_idx']
for target in ['energy','popularity']:
    numeric=ns['NUM']+(['energy'] if target=='popularity' else [])
    x=clean.iloc[dev][numeric].to_numpy(); xt=clean.iloc[test][numeric].to_numpy()
    mu=x.mean(axis=0); sd=x.std(axis=0); x=(x-mu)/sd; xt=(xt-mu)/sd
    for cat in ns['CAT']:
        levels=sorted(clean.iloc[dev][cat].unique())[1:]
        x=np.column_stack([x,*[clean.iloc[dev][cat].eq(level).to_numpy() for level in levels]])
        xt=np.column_stack([xt,*[clean.iloc[test][cat].eq(level).to_numpy() for level in levels]])
    x=np.column_stack([np.ones(len(dev)),x]); xt=np.column_stack([np.ones(len(test)),xt])
    y=clean.iloc[dev][target].to_numpy(); yt=clean.iloc[test][target].to_numpy()
    pred=xt@np.linalg.lstsq(x,y,rcond=None)[0]
    rmse=np.sqrt(np.mean((yt-pred)**2)); baseline=np.sqrt(np.mean((yt-y.mean())**2))
    np.testing.assert_allclose([rmse,baseline],reg.loc[target,['OLS_test_rmse','mean_baseline_test_rmse']].to_numpy(dtype=float),atol=1e-10,rtol=1e-10)
    assert f'{100*(1-rmse/baseline):.2f}'==('52.39' if target=='energy' else '1.46')
checks['independent_ols_and_training_mean_rmse']=True

# Independent closed-form SVD Ridge calculation, identical feature basis and rows.
columns=['loudness','acousticness','instrumentalness']
ids=pd.read_csv(DATA/'q4_final_small_training_ids.csv',index_col=0)
small_idx=clean.index[clean.track_id.isin(ids.track_id)].to_numpy()
assert len(small_idx)==80 and clean.iloc[small_idx].recording_group.nunique()==80
assert set(small_idx).issubset(set(ns['train_idx']))
for setting,idx in [('full_polynomial',dev),('small_polynomial',small_idx)]:
    poly=ns['PolynomialFeatures'](degree=3,include_bias=False)
    x=poly.fit_transform(clean.iloc[idx][columns]); xt=poly.transform(clean.iloc[test][columns])
    assert x.shape[1]==19
    mu=x.mean(axis=0); sd=x.std(axis=0); x=(x-mu)/sd; xt=(xt-mu)/sd
    y=clean.iloc[idx].energy.to_numpy(); yt=clean.iloc[test].energy.to_numpy()
    u,s,vt=np.linalg.svd(x,full_matrices=False)
    alpha=float(q4.loc[setting,'alpha_selected_on_validation'])
    coef=vt.T@((s/(s*s+alpha))*(u.T@(y-y.mean())))
    rmse=np.sqrt(np.mean((yt-(xt@coef+y.mean()))**2))
    np.testing.assert_allclose(rmse,q4.loc[setting,'selected_Ridge_test_rmse'],atol=1e-9,rtol=1e-9)
    coef0=np.linalg.lstsq(np.column_stack([np.ones(len(idx)),x]),y,rcond=None)[0]
    rmse0=np.sqrt(np.mean((yt-np.column_stack([np.ones(len(test)),xt])@coef0)**2))
    np.testing.assert_allclose(rmse0,q4.loc[setting,'OLS_test_rmse'],atol=1e-9,rtol=1e-9)
checks['independent_polynomial_ols_and_svd_ridge']=True

manifest=json.loads((DATA/'reproducibility.json').read_text(encoding='utf-8'))
assert manifest['chosen_k']==7 and manifest['clean_rows']==88858
checks['notebook_matches_report']=True
(HERE/'verification.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print(json.dumps(checks,indent=2),flush=True)
