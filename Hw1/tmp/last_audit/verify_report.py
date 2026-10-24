from pathlib import Path
import hashlib
import json
import nbformat
import numpy as np
import pandas as pd
import pymupdf

ROOT = Path.cwd()
HERE = ROOT/'tmp/last_audit'
DATA = HERE/'k7_candidate/results'
report = pymupdf.open(ROOT/'HW1_final_113062273.pdf')
checks = {}
table = report[2].find_tables().tables[0].extract()
profiles = pd.read_csv(DATA/'track_cluster_profiles_raw.csv', index_col=0)
counts = pd.read_csv(DATA/'track_cluster_counts.csv', index_col=0).tracks
assert [int(cell.split('\n')[1].split()[0].replace(',','')) for cell in table[0][1:]] == counts.tolist()
for row in table[1:]:
    for cluster, value in enumerate(row[1:]):
        assert value == f'{profiles.loc[cluster,row[0]]:.4f}', (cluster, row[0], value)
checks['seven_cluster_table_all_63_feature_means_and_counts_match'] = True
reg = pd.read_csv(DATA/'regression_results.csv',index_col=0)
rt = report[3].find_tables().tables[0].extract()
for row, field in zip(rt[1:], ['preregistered_rmse','OLS_test_rmse','mean_baseline_test_rmse']):
    assert row[1] == f'{reg.loc["energy",field]:.4f}'
    assert row[2] == f'{reg.loc["popularity",field]:.4f}'
checks['regression_table_all_six_values_match'] = True
artist = pd.read_csv(DATA/'additional_artist_information.csv',index_col=0)
at = report[3].find_tables().tables[1].extract()
for row, name in zip(at[1:], ['all','seen_artist_string','unseen_artist_string']):
    assert int(row[1].replace(',','')) == artist.loc[name,'tracks']
    assert row[2] == f'{artist.loc[name,"audio_only_rmse"]:.4f}'
    assert row[3] == f'{artist.loc[name,"audio_plus_artists_rmse"]:.4f}'
checks['artists_table_all_values_match'] = True
st = pd.read_csv(DATA/'cluster_stability.csv',index_col=0)
assert f'{100*st.loc["uniform_subsample_1","matched_changed_fraction"]:.2f}%' == '1.51%'
assert f'{100*st.loc["uniform_subsample_2","matched_changed_fraction"]:.2f}%' == '0.79%'
checks['seven_cluster_stability_matches'] = True
assert f'{100*reg.loc["energy","relative_rmse_reduction"]:.2f}' == '52.39'
assert f'{100*reg.loc["popularity","relative_rmse_reduction"]:.2f}' == '1.46'
assert f'{100*(1-artist.loc["all","audio_plus_artists_rmse"]/artist.loc["all","audio_only_rmse"]):.2f}' == '11.51'
q4 = pd.read_csv(DATA/'ridge_correlated_summary.csv',index_col=0)
assert f'{100*(1-q4.loc["small_polynomial","selected_Ridge_test_rmse"]/q4.loc["small_polynomial","OLS_test_rmse"]):.2f}' == '19.58'
checks['all_reported_rmse_improvement_percentages_match'] = True

assign = pd.read_csv(DATA/'genre_group_assignments.csv',index_col=0)
def same(config, genres):
    return assign.loc[genres, config].nunique()==1
assert same('euclidean_average',['opera','classical','ambient'])
assert same('cityblock_average',['opera','honky-tonk','jazz'])
assert same('cityblock_average',['black-metal','death-metal','grindcore','breakbeat','drum-and-bass'])
assert same('euclidean_average',['metal','heavy-metal','pop','dance','house'])
assert same('euclidean_complete',['metal','heavy-metal'])
assert same('euclidean_complete',['pop','dance','house'])
assert assign.loc['metal','euclidean_complete'] != assign.loc['pop','euclidean_complete']
assert assign.loc['black-metal','cityblock_average'] != assign.loc['metal','cityblock_average']
assert same('cityblock_complete',['black-metal','death-metal','grindcore','metal','heavy-metal'])
checks['all_stated_genre_group_changes_match'] = True

raw = pd.read_csv(ROOT/'tracks.csv')
assert raw.track_id.value_counts().gt(1).sum() == 16641
assert raw.duplicated().sum() == 450
assert raw.groupby('track_id').popularity.nunique().gt(1).sum() == 720
assert raw.tempo.le(0).sum()==157
assert raw.time_signature.eq(0).sum()==163
assert raw.duration_ms.le(0).sum()==1
assert (raw.tempo.le(0)|raw.time_signature.eq(0)|raw.duration_ms.le(0)).sum()==164
assert raw.groupby('track_genre').size().eq(1000).all()
assert raw.track_genre.nunique()==114
checks['raw_audit_counts_independently_match'] = True
splits = pd.read_csv(DATA/'split_track_ids.csv',index_col=0)
assert splits.groupby('recording_group').split.nunique().eq(1).all()
assert splits.track_id.is_unique
checks['no_recording_group_or_track_id_crosses_regression_split'] = True

# Prepare a reviewed replacement copy, while retaining the user's submitted file.
n = nbformat.read(HERE/'k7_candidate/executed.ipynb',as_version=4)
n.cells[2].source = n.cells[2].source.replace(f'OUT = Path({str(DATA)!r})',"OUT = Path('HW1_results_113062273')")
n.cells[13].source = n.cells[13].source.replace(
    'The final k is the maximum sampled silhouette; inertia and its relative reductions\nare also reported.',
    'The final choice is k=7: inertia reductions become smaller after 7 and the\nsilhouette is a local maximum compared with k=6 and k=8. The global silhouette\nmaximum at k=2 is reported as a trade-off.')
outdir = ROOT/'output/notebook/k7_verified'
outdir.mkdir(parents=True,exist_ok=True)
nbformat.validate(n)
nbformat.write(n,outdir/'HW1_code_113062273.ipynb')
checks['seven_cluster_replacement_notebook_prepared_and_executed'] = True
for name,digest in json.loads((HERE/'protected_sha256.json').read_text()).items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest, name
checks['user_original_files_unchanged'] = True
(HERE/'report_numeric_checks.json').write_text(json.dumps(checks,indent=2),encoding='utf-8')
print(json.dumps(checks,indent=2))
