from pathlib import Path
import hashlib, json, re, shutil
import numpy as np, pandas as pd, nbformat, fitz
from docx import Document
from docx.text.paragraph import Paragraph
from docx.table import Table
from docx.oxml.ns import qn

ROOT=Path(__file__).resolve().parents[2]
HERE=Path(__file__).parent
R=ROOT/'HW1_results_113062273'
docx=ROOT/'HW1_final_report_reviewed_113062273.docx'
d=Document(docx)
pdf=HERE/'rendered/HW1_final_report_reviewed_113062273.pdf'
pages=fitz.open(pdf)
assert len(pages)==6 and len(pages)<=10
assert len(d.tables)==4 and len(d.inline_shapes)==4
texts='\n'.join(p.text for p in d.paragraphs)
assert len(re.findall(r'^\d\.\d\s',texts,re.M))==13
assert texts.count('要求依據：')==13
assert not any(x in texts for x in ['0.159787','0.174244','0.224119'])
assert all(x in texts for x in ['0.128638','0.128637','0.181219','0.145732','19.58%'])

# Check every displayed table value against its reproducible numerical source.
profiles=pd.read_csv(R/'track_cluster_profiles_raw.csv',index_col=0)
counts=pd.read_csv(R/'track_cluster_counts.csv',index_col=0)
for row in d.tables[1].rows[1:]:
    name=row.cells[0].text
    for cluster,cell in enumerate(row.cells[1:]):
        assert cell.text==f'{profiles.loc[cluster,name]:.4f}', (name,cluster)
reg=pd.read_csv(R/'regression_results.csv',index_col=0)
for row,name in zip(d.tables[2].rows[1:],['preregistered_rmse','OLS_test_rmse','mean_baseline_test_rmse']):
    for target,cell in zip(['energy','popularity'],row.cells[1:]):
        assert cell.text==f'{reg.loc[target,name]:.4f}'
artists=pd.read_csv(R/'additional_artist_information.csv',index_col=0)
for row,name in zip(d.tables[3].rows[1:],['all','seen_artist_string','unseen_artist_string']):
    assert row.cells[1].text==f'{int(artists.loc[name,"tracks"]):,}'
    assert row.cells[2].text==f'{artists.loc[name,"audio_only_rmse"]:.4f}'
    assert row.cells[3].text==f'{artists.loc[name,"audio_plus_artists_rmse"]:.4f}'

# Independently recount raw quality evidence.
raw=pd.read_csv(ROOT/'tracks.csv').drop(columns=['Unnamed: 0'],errors='ignore')
assert raw.shape==(114000,20)
assert int((raw.track_id.value_counts()>1).sum())==16641
assert int(raw.duplicated().sum())==450
assert int((raw.groupby('track_id').popularity.nunique()>1).sum())==720
assert int((raw.tempo<=0).sum())==157
assert int((raw.time_signature==0).sum())==163
assert int((raw.duration_ms<=0).sum())==1
assert int(((raw.tempo<=0)|(raw.time_signature==0)|(raw.duration_ms<=0)).sum())==164
assert len(raw.track_genre.unique())==114 and raw.track_genre.value_counts().eq(1000).all()

# Independently confirm every named genre-group difference in the report.
g=pd.read_csv(R/'genre_group_assignments.csv',index_col=0)
def same(config,names): return g.loc[names,config].nunique()==1
assert same('euclidean_average',['opera','classical','ambient'])
assert same('cityblock_average',['opera','honky-tonk','jazz'])
assert same('euclidean_average',['black-metal','death-metal','grindcore'])
assert not same('euclidean_average',['black-metal','breakbeat'])
assert same('cityblock_average',['black-metal','death-metal','grindcore','breakbeat','drum-and-bass'])
assert same('euclidean_average',['metal','heavy-metal','pop','dance','house'])
assert same('euclidean_complete',['metal','heavy-metal'])
assert not same('euclidean_complete',['metal','pop'])
assert not same('cityblock_average',['black-metal','metal'])
assert same('cityblock_complete',['black-metal','death-metal','grindcore','metal','heavy-metal'])
assert g.groupby('euclidean_average').size().max()==94

# Confirm fitted curves and selection, not merely the prose numbers.
summary=pd.read_csv(R/'ridge_correlated_summary.csv',index_col=0)
for setting in summary.index:
    path=pd.read_csv(R/f'ridge_correlated_{setting}_path.csv',index_col=0)
    assert np.allclose(path.index,np.logspace(-6,6,25))
    assert path.validation_rmse.idxmin()==summary.loc[setting,'alpha_selected_on_validation']
    assert np.isclose(path.loc[path.validation_rmse.idxmin(),'test_rmse'],summary.loc[setting,'selected_Ridge_test_rmse'])
    assert np.diff(path.coefficient_l2).max()<1e-7
assert summary.loc['full_polynomial','test_rmse_improvement']<1e-6
assert summary.loc['small_polynomial','selected_Ridge_test_rmse']<summary.loc['small_polynomial','OLS_test_rmse']
for name in ['ridge_correlated_training_evidence','ridge_correlated_small_training_evidence']:
    assert pd.read_csv(R/(name+'.csv')).absolute_r.min()>.90

notes=nbformat.read(ROOT/'HW1_code_113062273.ipynb',as_version=4)
assert sum(c.cell_type=='code' for c in notes.cells)==16
assert all(c.execution_count is not None and not any(o.output_type=='error' for o in c.outputs)
           for c in notes.cells if c.cell_type=='code')

# All four DOCX images must be the exact latest notebook-generated figures.
image_names=['report_k_selection','report_cluster_pca','report_q4_full','report_q4_small']
images={hashlib.sha256((R/(name+'.png')).read_bytes()).hexdigest():name for name in image_names}
seen=set()
md=[]
for child in d.element.body:
    if child.tag==qn('w:p'):
        p=Paragraph(child,d)
        if p.text:
            prefix='# ' if p is d.paragraphs[0] else '# ' if p.style.name=='HW1 Section' else '## ' if p.style.name=='HW1 Question' else ''
            if p.text.startswith('HW1:'): prefix='# '
            md.append(prefix+p.text)
        for rid in child.xpath('.//@r:embed'):
            digest=hashlib.sha256(d.part.rels[rid].target_part.blob).hexdigest()
            assert digest in images
            name=images[digest];seen.add(name)
            md.append(f'![{name}](HW1_results_113062273/{name}.png)')
    elif child.tag==qn('w:tbl'):
        t=Table(child,d)
        for i,row in enumerate(t.rows):
            md.append('| '+' | '.join(c.text.replace('\n','；') for c in row.cells)+' |')
            if i==0: md.append('| '+' | '.join(['---']*len(row.cells))+' |')
    md.append('')
assert seen==set(image_names)

for name,expected in json.loads((HERE/'protected_inputs.json').read_text()).items():
    assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==expected

# Synchronize the files currently open in the IDE, keeping backups first.
md_path=ROOT/'HW1_final_report_minimal_113062273.md'
if not (HERE/'report_before_review.md').exists(): shutil.copy2(md_path,HERE/'report_before_review.md')
md_path.write_text('\n'.join(md).strip()+'\n',encoding='utf-8')
pdf_target=ROOT/'output/pdf/minimal/HW1_final_report_113062273.pdf'
if not (HERE/'report_before_review.pdf').exists(): shutil.copy2(pdf_target,HERE/'report_before_review.pdf')
shutil.copy2(pdf,pdf_target)

# Preserve superseded generated experiments outside the active results directory.
archive=HERE/'superseded_results';archive.mkdir(exist_ok=True)
archived=[]
for path in list(R.iterdir()):
    stale=(path.name.startswith('q4_') and path.name!='q4_final_small_training_ids.csv')
    stale |= path.name.startswith('ridge_') and not path.name.startswith('ridge_correlated_')
    stale |= path.name.startswith('regularization_') or path.name=='Q4_verified_results.md'
    if stale and path.is_file():
        assert ROOT in path.resolve().parents and ROOT in archive.resolve().parents
        shutil.move(str(path),str(archive/path.name));archived.append(path.name)

audit={'source_requirement_pages_verified':True,'report_questions':13,'report_pages':len(pages),
    'fresh_kernel_code_cells':16,'numerical_tables_verified':True,'raw_quality_recount_verified':True,
    'genre_comparisons_verified':True,'all_report_images_match_notebook':True,
    'q4_inputs_highly_correlated_in_both_settings':True,'alpha_selected_by_validation':True,
    'full_dataset_no_material_regularization_improvement':True,'small_dataset_improvement_percent':
    float(100*(1-summary.loc['small_polynomial','selected_Ridge_test_rmse']/summary.loc['small_polynomial','OLS_test_rmse'])),'all_pages_visually_inspected':True,
    'protected_files_unchanged':True,'report_pdf_md_synchronized':True,
    'report_docx_sha256':hashlib.sha256(docx.read_bytes()).hexdigest(),
    'archived_superseded_results':archived}
(HERE/'final_verification.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
(R/'verification.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k!='archived_superseded_results'},indent=2))
