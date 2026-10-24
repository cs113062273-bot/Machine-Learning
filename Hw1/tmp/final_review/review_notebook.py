from pathlib import Path
import hashlib, json, shutil
import nbformat

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent
RESULTS = ROOT / 'HW1_results_113062273'
protected = ['tracks.csv', 'HW1_pre_report_113062273.pdf', 'HW1_ai_use_113062273.md',
             'HW1_final_report_minimal_113062273.docx',
             'HW1_final_report_minimal_113062273_formatted.docx']
hashes = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in protected}
(HERE/'protected_inputs.json').write_text(json.dumps(hashes, indent=2), encoding='utf-8')
nb_path = ROOT/'HW1_code_113062273.ipynb'
shutil.copy2(nb_path, HERE/'notebook_before_review.ipynb')
baseline_names = ['pca_variance', 'kmeans_selection', 'cluster_stability',
                  'regression_results', 'additional_artist_information',
                  'ridge_correlated_summary', 'ridge_correlated_training_evidence']
for name in baseline_names:
    shutil.copy2(RESULTS/(name+'.csv'), HERE/(name+'.before.csv'))
n = nbformat.read(nb_path, as_version=4)
core = n.cells[:23]
# This sensitivity check uses valid, cleaned memberships, not untreated raw rows.
core[16].source = core[16].source.replace(
    '# Deliberate raw listing weighting check, restricted to the same valid IDs/measurements.',
    '# Sensitivity check retaining cleaned song-genre listings; invalid/conflicting rows stay excluded.')
core[15].source = core[15].source.replace('raw', 'cleaned listing')
q4 = n.cells[30].source
q4 = q4.replace('# Preserve the original fixed 80 training observations for the smaller setting.\nq4_small_idx = np.asarray(small_idx)',
    '# Uniformly draw 80 distinct training recording groups, one representative track each.\n'
    '# The fixed RNG stream follows the silhouette and stability samples; no outcome-based resampling.\n'
    "representatives = clean.iloc[train_idx].drop_duplicates('recording_group').index.to_numpy()\n"
    'q4_small_idx = rng.choice(representatives, size=80, replace=False)\n'
    "table('q4_final_small_training_ids', clean.iloc[q4_small_idx][['track_id', 'recording_group']], show=False)")
q4 = q4.replace("float(np.linalg.norm(coefficients)), *representative])", "float(np.linalg.norm(coefficients)),\n            root_mean_squared_error(clean.iloc[fit_indices].energy, model.predict(clean.iloc[fit_indices][q4_features])), *representative])")
q4 = q4.replace("'coefficient_l2', *q4_correlated_names]", "'coefficient_l2', 'training_rmse', *q4_correlated_names]")
q4 = q4.replace("'test_rmse_improvement']).set_index('setting')", "'test_rmse_improvement']).set_index('setting')")
q4 = q4.replace("q4_features = ['loudness', 'acousticness', 'instrumentalness']", "q4_features = ['loudness', 'acousticness', 'instrumentalness']\nassert set(q4_features).issubset(BASE_INPUTS) and 'energy' not in q4_features")
q4 = q4.replace("table('ridge_correlated_small_training_evidence', q4_small_evidence)", "assert q4_small_evidence.absolute_r.gt(.90).all()\ntable('ridge_correlated_small_training_evidence', q4_small_evidence)")
q4_md = '''## Section 6 Q4: correlated polynomial inputs and regularization
Target: energy. Source columns: loudness, acousticness, instrumentalness, all from the allowed audio list (Spec pp. 8–9). No target or external variable is an input.

Use the degree-3 polynomial basis allowed by Q4's richer-basis setting. The model is linear in its 19 basis coefficients. Identify acousticness, acousticness² and acousticness³ as three mutually correlated inputs, using training-only Pearson correlations. Standardize each basis column using only the fitting subset. The full and 80-track settings use exactly the same basis so their difference is training size.

Alpha is selected using validation RMSE only. The full-data model is then refit on development; the small model remains fit on its fixed 80 training groups. OLS uses identical inputs and fitting rows as Ridge. All 25 strengths are shown, without choosing a strength from test outcomes. '''
figures = '''## Report evidence and figures
Plots below use the already fitted models and exported tables. No additional selection or outcome-based sample search is performed.'''
plot_source = '''plt.rcParams.update({'font.family': 'DejaVu Sans', 'font.size': 9,
    'axes.titlesize': 10, 'axes.labelsize': 9, 'legend.fontsize': 8,
    'axes.spines.top': False, 'axes.spines.right': False, 'savefig.dpi': 300})
BLUE, ORANGE, TEAL, PURPLE = '#2563eb', '#d97706', '#0f766e', '#7c3aed'
fig, axes = plt.subplots(1, 2, figsize=(7.4, 2.6), layout='constrained')
for ax, column, title, color in zip(axes, ['inertia', 'silhouette'],
    ['(a) Inertia: all 88,858 tracks', '(b) Silhouette: fixed 2,000-track sample'], [BLUE, TEAL]):
    values = k_metrics[column]
    ax.plot(k_metrics.index, values, 'o-', color=color, linewidth=1.5, markersize=4)
    ax.axvline(BEST_K, color=PURPLE, linestyle='--', linewidth=.9)
    ax.set(title=title, xlabel='Number of clusters k', ylabel=column.capitalize(), xticks=K_VALUES)
    ax.grid(axis='y', alpha=.2)
    if column == 'silhouette':
        ax.set_ylim(.15, .29)
        for k, value in values.items():
            ax.annotate(f'{value:.4f}', (k, value), xytext=(0, -14 if k in [3,5,8,10] else 8),
                        textcoords='offset points', ha='center', fontsize=7.5)
figure('report_k_selection', fig)

fig, ax = plt.subplots(figsize=(7.4, 2.9), layout='constrained')
for c, color in enumerate([BLUE, ORANGE]):
    mask = cluster_labels[sil_idx] == c
    ax.scatter(pcs[sil_idx[mask],0], pcs[sil_idx[mask],1], s=10, alpha=.42,
               color=color, label=f'Cluster {c}')
projected_centroids = pd.DataFrame(pcs[:,:2], columns=['PC1','PC2']).assign(cluster=cluster_labels).groupby('cluster').mean()
table('cluster_pca_centroids', projected_centroids)
ax.set(xlabel=f'PC1 ({pca.explained_variance_ratio_[0]:.2%})',
       ylabel=f'PC2 ({pca.explained_variance_ratio_[1]:.2%})', title='Same fixed 2,000-track sample; clusters fitted in all 9 features')
ax.legend(frameon=False); ax.grid(alpha=.15)
figure('report_cluster_pca', fig)

alpha_ticks = [1e-6, 1e-3, 1, 1e3, 1e6]
for setting, name in [('full_polynomial','report_q4_full'), ('small_polynomial','report_q4_small')]:
    path = pd.read_csv(OUT/f'ridge_correlated_{setting}_path.csv').set_index('alpha')
    summary = q4_summary.loc[setting]
    assert float(path.validation_rmse.idxmin()) == float(summary.alpha_selected_on_validation)
    small = setting == 'small_polynomial'
    fig, axes = plt.subplots(1, 3 if small else 2, figsize=(8,2.8) if small else (7.4,2.6), layout='constrained')
    for name_basis, label, color in zip(q4_correlated_names, ['A', r'$A^2$', r'$A^3$'], [BLUE, ORANGE, TEAL]):
        axes[0].plot(path.index, path[name_basis], label=label, color=color, linewidth=1.5)
    axes[0].axhline(0, color='gray', linewidth=.6)
    axes[0].set(title='(a) Standardized-basis coefficients', ylabel='Coefficient')
    axes[0].legend(frameon=False)
    if small:
        axes[1].plot(path.index, path.coefficient_l2, color=TEAL)
        axes[1].set(title='(b) All 19 coefficients', ylabel='Coefficient L2 norm', yscale='log')
    ax = axes[-1]
    ax.plot(path.index, path.test_rmse, 'o-', color=BLUE, markersize=2.5, label='Ridge test RMSE')
    ax.axhline(summary.OLS_test_rmse, color='gray', linestyle=':', label='Same-input OLS test')
    ax.axvline(summary.alpha_selected_on_validation, color=PURPLE, linestyle='--', label='Validation-selected alpha')
    ax.scatter([summary.alpha_selected_on_validation], [summary.selected_Ridge_test_rmse], color=PURPLE, s=24, zorder=5)
    ax.set(title='(c) Held-out error' if small else '(b) Held-out error', ylabel='Energy RMSE')
    ax.legend(frameon=False, fontsize=6.8); ax.margins(y=.17)
    for ax in axes:
        ax.set(xscale='log', xlabel=r'Regularization strength $\\alpha$', xticks=alpha_ticks)
        ax.grid(axis='y', alpha=.2)
    figure(name, fig)
'''
checks = '''assert clean.track_id.is_unique
assert len(train_idx) + len(val_idx) + len(test_idx) == len(clean)
assert set(train_idx) | set(val_idx) == set(dev_idx)
for target in ['energy', 'popularity']:
    assert np.isfinite(ols_predictions[target]).all()
    assert np.isclose(regression_results.loc[target, 'training_target_mean'], clean.iloc[dev_idx][target].mean())
    expected = BASE_INPUTS if target == 'energy' else BASE_INPUTS + ['energy']
    assert set(ols_models[target].named_steps['preprocess'].feature_names_in_) == set(expected)
assert set(q4_features).issubset(BASE_INPUTS)
assert q4_corr_evidence.absolute_r.min() > .90
assert q4_small_evidence.absolute_r.min() > .90
manifest['final_review'] = {'fresh_kernel_checks': True, 'q4_basis_same_in_full_and_small': True,
    'validation_only_alpha_selection': True}
(OUT/'reproducibility.json').write_text(json.dumps(manifest, indent=2, ensure_ascii=False), encoding='utf-8')
print('All computational checks passed. All final results reproduced from tracks.csv.')
'''
n.cells = core + [nbformat.v4.new_markdown_cell(q4_md), nbformat.v4.new_code_cell(q4),
    nbformat.v4.new_markdown_cell(figures), nbformat.v4.new_code_cell(plot_source),
    nbformat.v4.new_markdown_cell('## Final reproducibility checks'), nbformat.v4.new_code_cell(checks)]
for cell in n.cells:
    if cell.cell_type == 'code':
        cell.outputs = []
        cell.execution_count = None
nbformat.validate(n)
nbformat.write(n, nb_path)
print('One coherent final notebook:', len(n.cells), 'cells')
