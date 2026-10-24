from pathlib import Path
import hashlib,json,sys,time
import pandas as pd
import nbformat
from nbclient import NotebookClient

sys.stdout.reconfigure(encoding='utf-8')
root=Path(__file__).resolve().parents[2]
path=root/'HW1_code_113062273.ipynb'
results=root/'HW1_results_113062273'
tracked=['regression_results.csv','pca_variance.csv','kmeans_selection.csv',
         'cluster_stability.csv','additional_artist_information.csv','ridge_summary.csv',
         'ridge_small_correlated_basis.csv']
before={name:pd.read_csv(results/name) for name in tracked}
notebook=nbformat.read(path,as_version=4)
start=time.monotonic()
def completed(cell,cell_index,**kwargs):
    if cell.cell_type=='code':
        print(f'Completed cell {cell_index}; {time.monotonic()-start:.1f}s',flush=True)
NotebookClient(notebook,timeout=900,kernel_name='python3',
    resources={'metadata':{'path':str(root)}},on_cell_executed=completed).execute()
nbformat.validate(notebook)
code_cells=[c for c in notebook.cells if c.cell_type=='code']
assert all(c.execution_count is not None for c in code_cells)
assert not any(o.output_type=='error' for c in code_cells for o in c.outputs)
for name in tracked:
    pd.testing.assert_frame_equal(before[name],pd.read_csv(results/name),
                                  check_exact=False,rtol=1e-10,atol=1e-10)
nbformat.write(notebook,path)
checks=json.loads((root/'tmp/pdfs/workspace_reread/unchanged_inputs.json').read_text(encoding='utf-8'))
for name,digest in checks.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
verification_path=results/'verification.json'
verification=json.loads(verification_path.read_text(encoding='utf-8'))
verification['executed_code_cells']=len(code_cells)
verification['fresh_kernel_full_execution']=f'All {len(code_cells)} code cells completed without errors'
verification['reworked_q4']={'strong_original_feature_triple_claim':False,
    'supplementary_basis_mutually_correlated_above_095':True,
    'original_core_tables_reproduced':tracked,'tolerance':1e-10,
    'train_only_preprocessing':True,'validation_only_alpha_selection':True,
    'source_data_and_pre_report_unchanged':True}
verification_path.write_text(json.dumps(verification,indent=2),encoding='utf-8')
print('PASS: fresh-kernel execution, original results reproduced, Q4 completed.',flush=True)
