# Q4: audit original predictors first; polynomial features only in the smaller setting.
# No original-feature group is labelled strongly correlated without numerical evidence.
q4_raw_candidates = list(NUM)
q4_raw_training_corr = clean.iloc[train_idx][q4_raw_candidates].corr()
table('q4_original_feature_correlations_training', q4_raw_training_corr)
q4_all_allowed_corr = clean.iloc[train_idx][BASE_INPUTS].corr()
table('q4_all_allowed_numeric_code_correlations_training', q4_all_allowed_corr)
# Integer-code correlations above are diagnostic only; key/metre are not ordered musical distances.
q4_raw_pairs = pd.DataFrame([
    [a,b,float(q4_raw_training_corr.loc[a,b]),abs(float(q4_raw_training_corr.loc[a,b]))]
    for a,b in itertools.combinations(q4_raw_candidates,2)],
    columns=['feature_1','feature_2','training_pearson_r','absolute_r']).sort_values('absolute_r',ascending=False)
table('q4_original_feature_pairs_training', q4_raw_pairs, show=False)
q4_raw_triples = []
for triple in itertools.combinations(q4_raw_candidates,3):
    weakest = min(abs(float(q4_raw_training_corr.loc[a,b])) for a,b in itertools.combinations(triple,2))
    q4_raw_triples.append([*triple,weakest])
q4_raw_triples = pd.DataFrame(q4_raw_triples,
    columns=['feature_1','feature_2','feature_3','minimum_pairwise_absolute_r']).sort_values(
        'minimum_pairwise_absolute_r',ascending=False)
table('q4_original_feature_triples_training',q4_raw_triples,show=False)
q4_original_features = list(q4_raw_triples.iloc[0][['feature_1','feature_2','feature_3']])
assert set(q4_original_features).issubset(BASE_INPUTS) and 'energy' not in q4_original_features
table('q4_selected_original_correlations_training',q4_raw_training_corr.loc[q4_original_features,q4_original_features])
print('Selected original columns by the largest minimum pairwise |Pearson r|:',q4_original_features)
print('Weakest selected pair:',float(q4_raw_triples.iloc[0].minimum_pairwise_absolute_r))
print('No claim that this original-feature triple is strongly correlated.')

q4_strengths = np.logspace(-6,6,25)
q4_final_basis_names = {}

def q4_original_then_small_pipeline(alpha=None,polynomial=False):
    steps=[('scale_original',StandardScaler())]
    if polynomial:
        steps += [('basis',PolynomialFeatures(degree=3,include_bias=False)),('scale_basis',StandardScaler())]
    steps += [('model',LinearRegression() if alpha is None else Ridge(alpha=float(alpha),solver='svd'))]
    return Pipeline(steps)

q4_final_summary = []
q4_final_paths = {}
q4_final_models = {}
q4_small_basis_correlations = None
for setting,indices,polynomial in [('full_original',dev_idx,False),('small_polynomial',small_idx,True)]:
    selection_indices = train_idx if setting=='full_original' else indices
    assert not set(groups[indices]) & set(groups[test_idx])
    if setting=='small_polynomial':
        assert len(indices)==80 and len(set(groups[indices]))==80
        assert not set(groups[indices]) & set(groups[val_idx])
    validation_errors=[]
    for alpha in q4_strengths:
        fitted=q4_original_then_small_pipeline(alpha,polynomial).fit(
            clean.iloc[selection_indices][q4_original_features],clean.iloc[selection_indices].energy)
        validation_errors.append(root_mean_squared_error(clean.iloc[val_idx].energy,
            fitted.predict(clean.iloc[val_idx][q4_original_features])))
    selected_alpha=float(q4_strengths[int(np.argmin(validation_errors))])
    ols=q4_original_then_small_pipeline(None,polynomial).fit(
        clean.iloc[indices][q4_original_features],clean.iloc[indices].energy)
    names=(ols.named_steps['basis'].get_feature_names_out(q4_original_features)
           if polynomial else np.asarray(q4_original_features))
    q4_final_basis_names[setting]=list(names)
    if polynomial:
        representative=['loudness^2','loudness^3','instrumentalness loudness^2']
        basis_values=ols.named_steps['basis'].transform(
            ols.named_steps['scale_original'].transform(clean.iloc[indices][q4_original_features]))
        basis_corr=pd.DataFrame(basis_values,columns=names).corr()
        q4_small_basis_correlations=pd.DataFrame([
            [a,b,float(basis_corr.loc[a,b]),abs(float(basis_corr.loc[a,b]))]
            for a,b in itertools.combinations(representative,2)],
            columns=['basis_feature_1','basis_feature_2','training_pearson_r','absolute_r'])
        assert q4_small_basis_correlations.absolute_r.gt(.95).all()
        table('q4_small_polynomial_correlated_basis',q4_small_basis_correlations)
    else:
        representative=q4_original_features
    rows=[];coefficients={}
    for alpha,validation_error in zip(q4_strengths,validation_errors):
        fitted=q4_original_then_small_pipeline(alpha,polynomial).fit(
            clean.iloc[indices][q4_original_features],clean.iloc[indices].energy)
        coef=fitted.named_steps['model'].coef_
        rows.append([float(alpha),float(validation_error),
            root_mean_squared_error(clean.iloc[test_idx].energy,fitted.predict(clean.iloc[test_idx][q4_original_features])),
            root_mean_squared_error(clean.iloc[indices].energy,fitted.predict(clean.iloc[indices][q4_original_features])),
            float(np.linalg.norm(coef)),*[float(coef[list(names).index(n)]) for n in representative]])
        coefficients[float(alpha)]=coef
        if float(alpha)==selected_alpha:
            q4_final_models[setting]=fitted
    path=pd.DataFrame(rows,columns=['alpha','validation_rmse','test_rmse','training_rmse','coefficient_l2',*representative]).set_index('alpha')
    assert np.diff(path.coefficient_l2).max() <= 1e-7
    q4_final_paths[setting]=path
    table('q4_'+setting+'_path',path)
    table('q4_'+setting+'_coefficients',pd.DataFrame(coefficients,index=names),show=False)
    ols_test_rmse=root_mean_squared_error(clean.iloc[test_idx].energy,ols.predict(clean.iloc[test_idx][q4_original_features]))
    selected_test_rmse=float(path.loc[selected_alpha,'test_rmse'])
    q4_final_summary.append([setting,len(indices),len(names),selected_alpha,
        root_mean_squared_error(clean.iloc[indices].energy,ols.predict(clean.iloc[indices][q4_original_features])),
        ols_test_rmse,selected_test_rmse,ols_test_rmse-selected_test_rmse])

q4_final_summary=pd.DataFrame(q4_final_summary,columns=['setting','training_tracks','input_columns',
    'alpha_selected_on_validation','OLS_training_rmse','OLS_test_rmse','Ridge_test_rmse','test_rmse_improvement']).set_index('setting')
table('q4_summary',q4_final_summary)
fig,axes=plt.subplots(2,2,figsize=(12,8))
for setting,row in [('full_original',0),('small_polynomial',1)]:
    path=q4_final_paths[setting]
    representatives=[c for c in path.columns if c not in ['validation_rmse','test_rmse','training_rmse','coefficient_l2']]
    for column in representatives:
        axes[row,0].semilogx(path.index,path[column],label=column)
    axes[row,0].set(xlabel='Ridge alpha',ylabel='Coefficient',title=setting+': standardized inputs')
    axes[row,0].legend(fontsize=8)
    axes[row,1].semilogx(path.index,path.validation_rmse,label='Validation: selection fit')
    axes[row,1].semilogx(path.index,path.test_rmse,label='Test: final fit')
    axes[row,1].axhline(q4_final_summary.loc[setting,'OLS_test_rmse'],color='gray',linestyle=':',label='Same-input OLS test')
    axes[row,1].axvline(q4_final_summary.loc[setting,'alpha_selected_on_validation'],color='gray',linestyle='--')
    axes[row,1].set(xlabel='Ridge alpha',ylabel='Energy RMSE',title=setting+': error')
    axes[row,1].legend(fontsize=8)
fig.tight_layout();figure('q4_original_then_small',fig)
manifest['q4_original_first']={
    'target':'energy','original_columns':q4_original_features,
    'selection_rule':'maximize minimum absolute pairwise Pearson r over 3 original continuous columns; training inputs only',
    'maximum_original_pairwise_absolute_r':float(q4_raw_pairs.absolute_r.max()),
    'selected_minimum_pairwise_absolute_r':float(q4_raw_triples.iloc[0].minimum_pairwise_absolute_r),
    'strong_original_correlation_claim':False,
    'polynomial_basis_only_in_smaller_setting':True,'small_training_tracks':80,
    'full_alpha_selected_on_validation':float(q4_final_summary.loc['full_original','alpha_selected_on_validation']),
    'small_alpha_selected_on_validation':float(q4_final_summary.loc['small_polynomial','alpha_selected_on_validation'])}
(OUT/'reproducibility.json').write_text(json.dumps(manifest,indent=2),encoding='utf-8')
print('Original-input Q4 audit and separate smaller polynomial setting completed.')
