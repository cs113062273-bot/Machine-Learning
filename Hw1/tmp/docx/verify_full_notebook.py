from pathlib import Path
import json
import time
import nbformat
from nbclient import NotebookClient
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
path = ROOT / 'HW1_code_113062273.ipynb'
results = ROOT / 'HW1_results_113062273'
tracked = ['regression_results.csv', 'ridge_summary.csv',
           'additional_artist_information.csv', 'kmeans_selection.csv',
           'pca_variance.csv', 'cluster_stability.csv', 'ridge_small_correlated_basis.csv']
before = {name: pd.read_csv(results / name) for name in tracked}
notebook = nbformat.read(path, as_version=4)
start = time.monotonic()

def completed(cell, cell_index, **kwargs):
    if cell.cell_type == 'code':
        print(f'Executed code cell at position {cell_index}; elapsed {time.monotonic()-start:.1f}s', flush=True)

client = NotebookClient(notebook, timeout=900, kernel_name='python3',
    resources={'metadata': {'path': str(ROOT)}}, on_cell_executed=completed)
client.execute()
nbformat.validate(notebook)
code_cells = [c for c in notebook.cells if c.cell_type == 'code']
assert len(code_cells) == 16
assert all(c.execution_count is not None for c in code_cells)
assert not any(o.output_type == 'error' for c in code_cells for o in c.outputs)
for name in tracked:
    after = pd.read_csv(results / name)
    pd.testing.assert_frame_equal(before[name], after, check_exact=False, atol=1e-10, rtol=1e-10)

nbformat.write(notebook, path)
verification_path = results / 'verification.json'
verification = json.loads(verification_path.read_text(encoding='utf-8'))
verification['executed_code_cells'] = len(code_cells)
verification['fresh_kernel_full_execution'] = 'All 16 code cells completed without errors'
verification['reproduction_check'] = {'tables_compared': tracked, 'result': 'unchanged within 1e-10'}
verification_path.write_text(json.dumps(verification, indent=2), encoding='utf-8')
print('PASS: all 16 code cells, fresh kernel, no errors, all compared results reproduced.', flush=True)
