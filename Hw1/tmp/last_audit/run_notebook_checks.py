from pathlib import Path
import hashlib
import json
import time
import nbformat
import pandas as pd
from nbclient import NotebookClient

ROOT = Path.cwd()
HERE = ROOT / 'tmp/last_audit'
source = ROOT / 'HW1_code_113062273.ipynb'
protected_names = ['HW1_code_113062273.ipynb', 'HW1_final_113062273.pdf',
    'HW1_ai_use_113062273.md', 'HW1_Spec (1).pdf', 'tracks.csv']
protected = {name: hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in protected_names}
(HERE/'protected_sha256.json').write_text(json.dumps(protected, indent=2), encoding='utf-8')
checks = {}
for mode in ['submitted', 'k7_candidate']:
    n = nbformat.read(source, as_version=4)
    out = HERE/mode/'results'
    out.mkdir(parents=True, exist_ok=True)
    n.cells[2].source = n.cells[2].source.replace("OUT = Path('HW1_results_113062273')", f'OUT = Path({str(out)!r})')
    if mode == 'k7_candidate':
        n.cells[14].source = n.cells[14].source.replace('BEST_K=int(k_metrics.silhouette.idxmax())',
            '# Choose k=7 using the inertia elbow and the local silhouette peak.\nBEST_K=7')
        n.cells[14].source = n.cells[14].source.replace('Chosen k by maximum fixed-sample silhouette:',
            'Chosen k by elbow and local silhouette peak:')
        n.cells[26].source = n.cells[26].source.replace('for c, color in enumerate([BLUE, ORANGE]):',
            "for c, color in enumerate([BLUE, ORANGE, '#059669', PURPLE, '#db2777', '#0891b2', '#64748b']):")
        n.cells[26].source = n.cells[26].source.replace("ax.legend(frameon=False); ax.grid(alpha=.15)",
            "ax.legend(frameon=False, ncol=4); ax.grid(alpha=.15)")
    start = time.time()
    NotebookClient(n, timeout=900, kernel_name='python3', resources={'metadata': {'path': str(ROOT)}}).execute()
    nbformat.write(n, HERE/mode/'executed.ipynb')
    errors = [o for c in n.cells if c.cell_type=='code' for o in c.outputs if o.output_type=='error']
    assert not errors
    manifest = json.loads((out/'reproducibility.json').read_text(encoding='utf-8'))
    checks[mode] = {'elapsed_seconds': round(time.time()-start, 2),
        'code_cells': sum(c.cell_type=='code' for c in n.cells), 'errors': len(errors),
        'chosen_k': manifest['chosen_k'], 'clean_rows': manifest['clean_rows']}
    print(json.dumps({mode: checks[mode]}), flush=True)
    print(pd.read_csv(out/'ridge_correlated_summary.csv').to_string(index=False), flush=True)

for name in ['pca_variance', 'kmeans_selection', 'regression_results', 'additional_artist_information',
             'ridge_correlated_summary', 'ridge_correlated_training_evidence', 'q4_final_small_training_ids']:
    a = pd.read_csv(HERE/'submitted/results'/f'{name}.csv', index_col=0)
    b = pd.read_csv(HERE/'k7_candidate/results'/f'{name}.csv', index_col=0)
    pd.testing.assert_frame_equal(a, b, check_exact=False, atol=1e-10, rtol=1e-10)
for name, digest in protected.items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest, name
checks['unrelated_results_same_after_k7'] = True
checks['original_files_unchanged'] = True
(HERE/'execution_checks.json').write_text(json.dumps(checks, indent=2), encoding='utf-8')
print(json.dumps(checks, indent=2), flush=True)
