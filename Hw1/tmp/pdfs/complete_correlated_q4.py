from pathlib import Path
import hashlib, json, sys
import nbformat

sys.stdout.reconfigure(encoding='utf-8')
root=Path(__file__).resolve().parents[2]
out=root/'tmp/pdfs/workspace_reread'
notebook_path=root/'HW1_code_113062273.ipynb'
backup=out/'HW1_code_113062273.before_q4.ipynb'
if not backup.exists(): backup.write_bytes(notebook_path.read_bytes())
for path in [root/'HW1_final_report_minimal_113062273.md', root/'output/pdf/minimal/HW1_final_report_113062273.pdf']:
    target=out/('before_rewrite_'+path.name)
    if not target.exists():target.write_bytes(path.read_bytes())
(out/'unchanged_inputs.json').write_text(json.dumps({str(p.relative_to(root)):hashlib.sha256(p.read_bytes()).hexdigest()
    for p in [root/'tracks.csv',root/'HW1_ai_use_113062273.md',root/'HW1_pre_report_113062273.pdf']},indent=2),encoding='utf-8')

source='''# Q4: correlated polynomial inputs on the full development dataset.
# Use only the three permitted audio columns. The basis is fixed before
# validation/test evaluation; alpha is selected by validation RMSE alone.
q4_features = ['loudness', 'acousticness', 'instrumentalness']
q4_alphas = np.logspace(-6, 6, 25)
q4_correlated_names = ['acousticness', 'acousticness^2', 'acousticness^3']

def q4_pipeline(alpha=None):
    return Pipeline([
        ('basis', PolynomialFeatures(degree=3, include_bias=False)),
        ('scale_basis', StandardScaler()),
        ('model', LinearRegression() if alpha is None else Ridge(alpha=alpha, solver='svd'))])

q4_basis = PolynomialFeatures(degree=3, include_bias=False)
q4_train_basis = q4_basis.fit_transform(clean.iloc[train_idx][q4_features])
q4_basis_names = q4_basis.get_feature_names_out(q4_features)
q4_train_corr = pd.DataFrame(q4_train_basis, columns=q4_basis_names).corr()
q4_correlations = []
for first, second in itertools.combinations(q4_correlated_names, 2):
    r = float(q4_train_corr.loc[first, second])
    q4_correlations.append([first, second, r, abs(r)])
q4_corr_evidence = pd.DataFrame(q4_correlations,
    columns=['feature_1', 'feature_2', 'training_pearson_r', 'absolute_r'])
assert q4_corr_evidence.absolute_r.gt(.90).all()
table('ridge_correlated_training_evidence', q4_corr_evidence)

# Preserve the original fixed 80 training observations for the smaller setting.
q4_small_idx = np.asarray(small_idx)
assert len(q4_small_idx) == 80
assert len(set(groups[q4_small_idx])) == 80
assert not set(groups[q4_small_idx]) & set(groups[val_idx])
assert not set(groups[q4_small_idx]) & set(groups[test_idx])
q4_small_basis = q4_basis.transform(clean.iloc[q4_small_idx][q4_features])
q4_small_corr = pd.DataFrame(q4_small_basis, columns=q4_basis_names).corr()
q4_small_evidence = pd.DataFrame([
    [a, b, float(q4_small_corr.loc[a,b]), abs(float(q4_small_corr.loc[a,b]))]
    for a,b in itertools.combinations(q4_correlated_names,2)],
    columns=['feature_1','feature_2','training_pearson_r','absolute_r'])
table('ridge_correlated_small_training_evidence', q4_small_evidence)

q4_summary_rows = []
for setting, fit_indices in [('full_polynomial', dev_idx), ('small_polynomial', q4_small_idx)]:
    selection_indices = train_idx if setting == 'full_polynomial' else q4_small_idx
    validation_errors = []
    for alpha in q4_alphas:
        model = q4_pipeline(float(alpha)).fit(clean.iloc[selection_indices][q4_features],
                                             clean.iloc[selection_indices].energy)
        validation_errors.append(root_mean_squared_error(clean.iloc[val_idx].energy,
            model.predict(clean.iloc[val_idx][q4_features])))
    selected_alpha = float(q4_alphas[int(np.argmin(validation_errors))])
    rows = []; coefficient_rows = {}
    for alpha, validation_error in zip(q4_alphas, validation_errors):
        model = q4_pipeline(float(alpha)).fit(clean.iloc[fit_indices][q4_features],
                                             clean.iloc[fit_indices].energy)
        prediction = model.predict(clean.iloc[test_idx][q4_features])
        coefficients = model.named_steps['model'].coef_
        assert np.isfinite(prediction).all()
        representative = [float(coefficients[list(q4_basis_names).index(name)])
                          for name in q4_correlated_names]
        rows.append([float(alpha), float(validation_error),
            root_mean_squared_error(clean.iloc[test_idx].energy,prediction),
            float(np.linalg.norm(coefficients)), *representative])
        coefficient_rows[float(alpha)] = coefficients
    path = pd.DataFrame(rows, columns=['alpha','validation_rmse','test_rmse',
        'coefficient_l2', *q4_correlated_names]).set_index('alpha')
    assert np.all(np.diff(path.coefficient_l2) <= 1e-8)
    table('ridge_correlated_'+setting+'_path', path)
    table('ridge_correlated_'+setting+'_coefficients',
        pd.DataFrame(coefficient_rows, index=q4_basis_names), show=False)
    ols = q4_pipeline().fit(clean.iloc[fit_indices][q4_features], clean.iloc[fit_indices].energy)
    ols_rmse = root_mean_squared_error(clean.iloc[test_idx].energy,
        ols.predict(clean.iloc[test_idx][q4_features]))
    chosen_rmse = float(path.loc[selected_alpha,'test_rmse'])
    q4_summary_rows.append([setting,len(fit_indices),len(q4_basis_names),selected_alpha,
        ols_rmse,chosen_rmse,ols_rmse-chosen_rmse])

q4_summary = pd.DataFrame(q4_summary_rows,columns=['setting','training_tracks','basis_features',
    'alpha_selected_on_validation','OLS_test_rmse','selected_Ridge_test_rmse',
    'test_rmse_improvement']).set_index('setting')
table('ridge_correlated_summary',q4_summary)
manifest['q4_correlated_basis'] = {
    'source_columns':q4_features,'polynomial_degree':3,
    'basis_count':len(q4_basis_names),'training_only_correlated_basis':q4_correlated_names,
    'full_selected_alpha':float(q4_summary.loc['full_polynomial','alpha_selected_on_validation']),
    'small_selected_alpha':float(q4_summary.loc['small_polynomial','alpha_selected_on_validation'])}
(OUT/'reproducibility.json').write_text(json.dumps(manifest,indent=2,ensure_ascii=False),encoding='utf-8')
print('Q4 correlated-input experiments completed; validation-only alpha selection.')
'''
notebook=nbformat.read(notebook_path,as_version=4)
marker='# Q4: correlated polynomial inputs on the full development dataset.'
if not any(marker in c.source for c in notebook.cells):
    notebook.cells.append(nbformat.v4.new_markdown_cell(
        '### Section 6 Q4: strongly correlated inputs in the full-data experiment\n'
        'The report uses this experiment. Degree-3 polynomial basis functions '
        'of loudness, acousticness and instrumentalness contain three mutually '
        'correlated acousticness powers on the full training split. All 19 basis '
        'columns are standardized using the fitting subset only. Full-data and '
        '80-track settings use the same basis, frozen original split and original '
        'small sample. Alpha is selected on validation, never on test.'))
    notebook.cells.append(nbformat.v4.new_code_cell(source))
    nbformat.validate(notebook)
    nbformat.write(notebook,notebook_path)
(out/'q4_source.py').write_text(source,encoding='utf-8')
print('Added reproducible Q4 experiment to notebook; original saved in audit directory.')
