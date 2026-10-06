from pathlib import Path
import contextlib
import io
import json
import numpy as np
import pandas as pd
import nbformat
from sklearn.preprocessing import StandardScaler, PolynomialFeatures
from sklearn.pipeline import Pipeline
from sklearn.linear_model import LinearRegression
from sklearn.metrics import root_mean_squared_error

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / 'HW1_results_113062273'
path = ROOT / 'HW1_code_113062273.ipynb'
notebook = nbformat.read(path, as_version=4)
assert not any('ridge_small_correlated_basis' in c.source for c in notebook.cells)

source = '''# Training-only evidence for correlated polynomial basis features.
# These are powers of the already-standardized inputs, as in the Q4 pipeline.
small_basis = small_ols.named_steps['basis'].transform(
    small_ols.named_steps['scale_input'].transform(clean.iloc[small_idx][REG_FEATURES]))
small_basis_correlation = pd.DataFrame(small_basis, columns=basis_names).corr()
correlated_basis_names = ['loudness^2', 'loudness^3', 'loudness^2 instrumentalness']
correlated_basis_pairs = []
for feature1, feature2 in itertools.combinations(correlated_basis_names, 2):
    correlation = float(small_basis_correlation.loc[feature1, feature2])
    correlated_basis_pairs.append([feature1, feature2, correlation, abs(correlation)])
correlated_basis_evidence = pd.DataFrame(correlated_basis_pairs,
    columns=['basis_feature_1', 'basis_feature_2', 'training_pearson_r', 'absolute_r'])
table('ridge_small_correlated_basis', correlated_basis_evidence)
assert correlated_basis_evidence.absolute_r.gt(.95).all()
small_ols_training_rmse = root_mean_squared_error(clean.iloc[small_idx].energy,
    small_ols.predict(clean.iloc[small_idx][REG_FEATURES]))
print('Small-training OLS training RMSE:', small_ols_training_rmse)
print('Small-training Ridge training RMSE at validation-selected alpha:',
    small_path.loc[chosen_small, 'training_rmse'])
'''

# Recreate only the inputs and fitted OLS used by this added cell. Preserve the
# original saved 80 training IDs, all model parameters, and all existing results.
ids = pd.read_csv(OUT / 'ridge_small_training_ids.csv').track_id
raw = pd.read_csv(ROOT / 'tracks.csv').drop_duplicates('track_id').set_index('track_id')
clean = raw.loc[ids].reset_index()
features = ['loudness', 'acousticness', 'instrumentalness']
model = Pipeline([('scale_input', StandardScaler()),
                  ('basis', PolynomialFeatures(3, include_bias=False)),
                  ('scale_basis', StandardScaler()),
                  ('model', LinearRegression())]).fit(clean[features], clean.energy)
saved_path = pd.read_csv(OUT / 'ridge_small_polynomial_path.csv', index_col=0)

def table(name, frame, show=True):
    frame.to_csv(OUT / (name + '.csv'), encoding='utf-8-sig')
    if show:
        print(frame.round(6).to_string(index=False))
    return frame

import itertools
namespace = {'small_ols': model, 'clean': clean, 'small_idx': np.arange(len(clean)),
             'REG_FEATURES': features,
             'basis_names': model.named_steps['basis'].get_feature_names_out(features),
             'pd': pd, 'itertools': itertools, 'table': table,
             'root_mean_squared_error': root_mean_squared_error,
             'small_path': saved_path, 'chosen_small': float(saved_path.validation_rmse.idxmin())}
captured = io.StringIO()
with contextlib.redirect_stdout(captured):
    exec(compile(source, '<supplementary notebook cell>', 'exec'), namespace)

notebook.cells.append(nbformat.v4.new_markdown_cell(
    '### Q4: Training-only correlation evidence for the richer basis\n'
    'The permitted original continuous inputs have maximum absolute Pearson '
    'correlation 0.583187 in train. The existing polynomial setting contains '
    'three mutually correlated basis columns; this check uses only its 80 '
    'training observations and changes no fitted model or chosen alpha.'))
execution_count = max(c.get('execution_count') or 0 for c in notebook.cells) + 1
notebook.cells.append(nbformat.v4.new_code_cell(source, execution_count=execution_count,
    outputs=[nbformat.v4.new_output('stream', name='stdout', text=captured.getvalue())]))
nbformat.validate(notebook)
nbformat.write(notebook, path)

verification_path = OUT / 'verification.json'
verification = json.loads(verification_path.read_text(encoding='utf-8'))
verification['executed_code_cells'] = sum(c.cell_type == 'code' for c in notebook.cells)
verification['supplementary_basis_check'] = {
    'training_observations': 80,
    'source': 'Saved original small-training track IDs; training-only fitted preprocessing',
    'mutually_correlated_basis': namespace['correlated_basis_evidence'].to_dict(orient='records'),
    'OLS_training_rmse': namespace['small_ols_training_rmse'],
    'models_and_selected_alphas_changed': False,
}
verification_path.write_text(json.dumps(verification, indent=2), encoding='utf-8')
print(captured.getvalue())
print('Supplementary cell executed; notebook schema validation passed.')
