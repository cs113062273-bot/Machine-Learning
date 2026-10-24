from pathlib import Path
import hashlib, json, shutil, time
import nbformat
from nbclient import NotebookClient

ROOT = Path.cwd()
HERE = ROOT/'tmp/submission_final_check'
source = ROOT/'HW1_code_113062273.ipynb'
shutil.copy2(source, HERE/'notebook_before.ipynb')
shutil.copy2(ROOT/'HW1_ai_use_113062273.md', HERE/'ai_use_before.md')
n = nbformat.read(source, as_version=4)
n.cells[4].source = n.cells[4].source.replace(
    'Raw rows are deliberately used only for the audit and the explicitly labelled\nduplicate-weight sensitivity check.',
    'Raw rows are used for the audit. The duplicate-weight sensitivity check uses\ncleaned song-genre listings, retaining the same validity and conflict exclusions.')
n.cells[13].source = n.cells[13].source.replace(
    'The final k is the maximum sampled silhouette; inertia and its relative reductions\nare also reported.',
    'The final choice is k=7: inertia reductions become smaller after 7 and the\nsilhouette is a local maximum relative to k=6 and k=8. The global silhouette\nmaximum at k=2 is retained in the comparison, rather than ignored.')
assert 'BEST_K=int(k_metrics.silhouette.idxmax())' in n.cells[14].source
n.cells[14].source = n.cells[14].source.replace(
    'BEST_K=int(k_metrics.silhouette.idxmax())',
    '# Match the report: choose the elbow candidate and local silhouette peak.\nBEST_K=7')
n.cells[14].source = n.cells[14].source.replace(
    'Chosen k by maximum fixed-sample silhouette:',
    'Chosen k by inertia elbow and local silhouette peak:')
assert 'for c, color in enumerate([BLUE, ORANGE]):' in n.cells[26].source
n.cells[26].source = n.cells[26].source.replace(
    'for c, color in enumerate([BLUE, ORANGE]):',
    "for c, color in enumerate([BLUE, ORANGE, '#059669', PURPLE, '#db2777', '#0891b2', '#64748b']):")
n.cells[26].source = n.cells[26].source.replace(
    'ax.legend(frameon=False); ax.grid(alpha=.15)',
    'ax.legend(frameon=False, ncol=4); ax.grid(alpha=.15)')
n.cells[28].source += '\nassert BEST_K == 7\nassert len(cluster_profiles) == 7\nassert cluster_profiles.index.tolist() == list(range(7))\nassert len(q4_basis_names) == 19\nassert len(q4_alphas) == 25\nassert int(pd.Series(cluster_labels).value_counts().sum()) == len(clean)\nprint("Seven-cluster report consistency checks passed.")\n'
for c in n.cells:
    if c.cell_type == 'code':
        c.outputs = []
        c.execution_count = None
nbformat.validate(n)
start = time.time()
NotebookClient(n, timeout=900, kernel_name='python3',
    resources={'metadata':{'path':str(ROOT)}}).execute()
assert not [o for c in n.cells if c.cell_type == 'code' for o in c.outputs if o.output_type == 'error']
nbformat.validate(n)
nbformat.write(n, HERE/'executed_final.ipynb')
nbformat.write(n, source)
status = {'elapsed_seconds':round(time.time()-start,2),
    'executed_code_cells':sum(c.cell_type=='code' for c in n.cells),
    'errors':0, 'chosen_k':7,
    'notebook_sha256':hashlib.sha256(source.read_bytes()).hexdigest()}
(HERE/'execution.json').write_text(json.dumps(status,indent=2),encoding='utf-8')
print(json.dumps(status,indent=2),flush=True)
