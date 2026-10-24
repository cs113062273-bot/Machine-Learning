from pathlib import Path
import json, hashlib, time
import nbformat, pandas as pd, numpy as np
from nbclient import NotebookClient
ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent
path = ROOT/'HW1_code_113062273.ipynb'
start = time.time()
n = nbformat.read(path, as_version=4)
NotebookClient(n, timeout=900, kernel_name='python3', resources={'metadata': {'path': str(ROOT)}}).execute()
nbformat.write(n, path)
errors = [o for c in n.cells if c.cell_type == 'code' for o in c.outputs if o.output_type == 'error']
assert not errors
for name in ['pca_variance', 'kmeans_selection', 'cluster_stability', 'regression_results',
             'additional_artist_information', 'ridge_correlated_summary', 'ridge_correlated_training_evidence']:
    a = pd.read_csv(HERE/(name+'.before.csv'), index_col=0)
    b = pd.read_csv(ROOT/'HW1_results_113062273'/(name+'.csv'), index_col=0)
    pd.testing.assert_frame_equal(a,b,check_exact=False,atol=1e-10,rtol=1e-10)
protected = json.loads((HERE/'protected_inputs.json').read_text(encoding='utf-8'))
for name, expected in protected.items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest() == expected, name
audit = {'fresh_kernel_run': True, 'executed_code_cells': sum(c.cell_type=='code' for c in n.cells),
    'elapsed_seconds': round(time.time()-start,2), 'baseline_numeric_tables_matched': True,
    'protected_files_unchanged': True, 'no_execution_errors': True}
(HERE/'notebook_verification.json').write_text(json.dumps(audit,indent=2), encoding='utf-8')
print(json.dumps(audit))
print(pd.read_csv(ROOT/'HW1_results_113062273/ridge_correlated_summary.csv').to_string(index=False))
