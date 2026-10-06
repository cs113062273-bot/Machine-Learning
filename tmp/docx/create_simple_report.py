from pathlib import Path
import re,sys
import pymupdf
from docx import Document
from docx.shared import Mm,Pt,RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH,WD_BREAK,WD_LINE_SPACING
from docx.enum.table import WD_TABLE_ALIGNMENT,WD_CELL_VERTICAL_ALIGNMENT
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.style import WD_STYLE_TYPE

sys.stdout.reconfigure(encoding='utf-8')
ROOT=Path(__file__).resolve().parents[2]
TMP=Path(__file__).resolve().parent
OUTPUT=ROOT/'HW1_final_report_simple_113062273.docx'

# Preset: compact_reference_guide. Existing report fidelity overrides:
# A4 15.17-mm margins; Microsoft JhengHei; explicit legacy heading/table tokens;
# body 10 pt with 14.5 pt leading; 5 pt after; images 155/170 mm.
# All resolved tokens are applied below; no lists or callouts are used.
# Named conversion overrides: Microsoft JhengHei; 15.17 mm margins;
# 9.35 pt body / 13.6 pt exact leading; native Word editable tables.
TOKENS={'page_width_mm':210,'page_height_mm':297,'margin_mm':15.17,
        'font':'Microsoft JhengHei','body_pt':10,'body_leading_pt':14.5,
        'heading_pt':15,'subheading_pt':10.8,'table_pt':8,'table_leading_pt':10.6,
        'caption_pt':7.7,'caption_leading_pt':10.3,
        'ink':'202A33','muted':'52606D','fill':'E9F0F4','alternate':'F7F9FB'}
source=(TMP/'report_simple.md').read_text(encoding='utf-8')
lines=source.splitlines()
lines=[line for line in lines if not ('OLS RMSE' in line and 'bootstrap' in line)]
text='\n'.join(lines)
text=re.sub(r'95% 區間由 test 錄音群組整組重抽 500 次計算，.*?預測沒有裁切',
            '預測沒有裁切',text)
assert 'bootstrap' not in text
assert text.count('<!-- pagebreak -->')==5

old=pymupdf.open(TMP/'original-ten-page-report.pdf')
names={4:'pca_comparison.png',6:'kmeans_k_selection.png',7:'track_clusters_pca_profiles.png',
       8:'regression_test_predictions.png',9:'artist_popularity.png',10:'ridge_regularization.png'}
for page,name in names.items():
    imgs=old[page-1].get_images()
    assert len(imgs)==1
    pymupdf.Pixmap(old,imgs[0][0]).save(TMP/name)
old.close()

doc=Document()
sec=doc.sections[0]
sec.page_width=Mm(210);sec.page_height=Mm(297)
sec.left_margin=sec.right_margin=sec.top_margin=sec.bottom_margin=Mm(TOKENS['margin_mm'])
sec.header_distance=Mm(7);sec.footer_distance=Mm(7)
grid=sec._sectPr.find(qn('w:docGrid'))
if grid is not None:sec._sectPr.remove(grid)
width_twips=int(round((210-2*TOKENS['margin_mm'])/25.4*1440))

def styled(name,size,leading,bold=False,before=0,after=0,color='202A33',keep=False):
    try:s=doc.styles[name]
    except KeyError:s=doc.styles.add_style(name,WD_STYLE_TYPE.PARAGRAPH)
    s.font.name=TOKENS['font'];s.font.size=Pt(size);s.font.bold=bold;s.font.color.rgb=RGBColor.from_string(color)
    rf=s.element.get_or_add_rPr().get_or_add_rFonts()
    for lang in ['ascii','hAnsi','eastAsia','cs']:rf.set(qn('w:'+lang),TOKENS['font'])
    pf=s.paragraph_format
    pf.space_before=Pt(before);pf.space_after=Pt(after)
    pf.line_spacing_rule=WD_LINE_SPACING.EXACTLY;pf.line_spacing=Pt(leading)
    pf.keep_with_next=keep;pf.widow_control=True
    ppr=s.element.get_or_add_pPr()
    snap=OxmlElement('w:snapToGrid');snap.set(qn('w:val'),'0');ppr.append(snap)
    return s

styled('Normal',10,14.5,after=5)
styled('Title',15,19,bold=True,after=10,keep=True)
styled('Heading 1',15,19,bold=True,after=10,keep=True)
styled('Heading 2',10.8,15,bold=True,before=5,after=5,keep=True)
styled('Caption',7.7,10.3,after=7,color='52606D')
styled('Report Source',7.7,10.3,after=7,color='52606D')
styled('Report Table',8,10.6)
styled('Report Table Header',8,10.6,bold=True)
styled('Report Table Gap',1,3,after=3)
styled('Report Image',1,1,keep=True)
doc.styles['Report Image'].paragraph_format.line_spacing=1.0
doc.styles['Report Image'].paragraph_format.line_spacing_rule=WD_LINE_SPACING.SINGLE
styled('Header',7.5,10,color='52606D')
styled('Footer',7.5,10,color='52606D')

header=sec.header.paragraphs[0];header.style=doc.styles['Header'];header.add_run('113062273 | HW1')
footer=sec.footer.paragraphs[0];footer.style=doc.styles['Footer'];footer.alignment=WD_ALIGN_PARAGRAPH.RIGHT
footer.add_run('頁 ')
for instr in ['PAGE','NUMPAGES']:
    if instr=='NUMPAGES':footer.add_run(' / ')
    r=footer.add_run();start=OxmlElement('w:fldChar');start.set(qn('w:fldCharType'),'begin');r._r.append(start)
    r=footer.add_run();field=OxmlElement('w:instrText');field.set(qn('xml:space'),'preserve');field.text=' '+instr+' ';r._r.append(field)
    r=footer.add_run();sep=OxmlElement('w:fldChar');sep.set(qn('w:fldCharType'),'separate');r._r.append(sep)
    footer.add_run('1' if instr=='PAGE' else '6')
    r=footer.add_run();end=OxmlElement('w:fldChar');end.set(qn('w:fldCharType'),'end');r._r.append(end)

def write_text(paragraph,s):
    # Current report has no prose lists; preserve all existing phrasing.
    parts=re.split(r'(\*\*.*?\*\*|`.*?`)',s)
    for piece in parts:
        if piece.startswith('**') and piece.endswith('**'):paragraph.add_run(piece[2:-2]).bold=True
        elif piece.startswith('`') and piece.endswith('`'):paragraph.add_run(piece[1:-1])
        else:paragraph.add_run(piece)

def table(block):
    rows=[[c.strip() for c in line.strip().strip('|').split('|')] for line in block]
    rows=[r for r in rows if not all(re.fullmatch(r'[:\- ]+',c) for c in r)]
    n=len(rows[0]);assert all(len(r)==n for r in rows)
    weights=[]
    for j in range(n):
        lengths=[sum(1 if ord(c)>255 else .52 for c in row[j]) for row in rows]
        weights.append(max(5,min(28,max(lengths))))
    if n==5 and '主要正向權重' in rows[0]:weights=[6,7,17,20,21]
    if n==5 and 'basis' in '|'.join(rows[0]):weights=[22,11,9,15,12]
    if n==4 and 'RMSE' in '|'.join(rows[0]):weights=[22,9,12,12]
    if n==5 and '曲風數' in '|'.join(rows[0]):weights=[5,24,9,12,13]
    widths=[round(width_twips*w/sum(weights)) for w in weights];widths[-1]+=width_twips-sum(widths)
    t=doc.add_table(rows=len(rows),cols=n);t.alignment=WD_TABLE_ALIGNMENT.LEFT;t.autofit=False
    pr=t._tbl.tblPr
    tw=pr.find(qn('w:tblW'));tw.set(qn('w:type'),'dxa');tw.set(qn('w:w'),str(width_twips))
    ind=OxmlElement('w:tblInd');ind.set(qn('w:w'),'100');ind.set(qn('w:type'),'dxa');pr.append(ind)
    margins=OxmlElement('w:tblCellMar')
    for side,val in [('top',60),('bottom',60),('start',100),('end',100)]:
        el=OxmlElement('w:'+side);el.set(qn('w:w'),str(val));el.set(qn('w:type'),'dxa');margins.append(el)
    pr.append(margins)
    borders=OxmlElement('w:tblBorders')
    for side in ['top','bottom','left','right','insideH','insideV']:
        el=OxmlElement('w:'+side);el.set(qn('w:val'),'single' if side in ['top','bottom','insideH'] else 'nil')
        el.set(qn('w:sz'),'4');el.set(qn('w:color'),'DAE1E7');borders.append(el)
    pr.append(borders)
    for gridcol,w in zip(t._tbl.tblGrid.gridCol_lst,widths):gridcol.set(qn('w:w'),str(w))
    for i,(row,values) in enumerate(zip(t.rows,rows)):
        trpr=row._tr.get_or_add_trPr();no_split=OxmlElement('w:cantSplit');trpr.append(no_split)
        if i==0:trpr.append(OxmlElement('w:tblHeader'))
        for j,(cell,value) in enumerate(zip(row.cells,values)):
            cell.width=Pt(widths[j]/20);cell.vertical_alignment=WD_CELL_VERTICAL_ALIGNMENT.CENTER
            tcw=cell._tc.get_or_add_tcPr().find(qn('w:tcW'));tcw.set(qn('w:type'),'dxa');tcw.set(qn('w:w'),str(widths[j]))
            p=cell.paragraphs[0];p.style=doc.styles['Report Table Header' if i==0 else 'Report Table'];write_text(p,value)
            fill=TOKENS['fill'] if i==0 else ('FFFFFF' if i%2 else TOKENS['alternate'])
            sh=OxmlElement('w:shd');sh.set(qn('w:fill'),fill);cell._tc.get_or_add_tcPr().append(sh)
    doc.add_paragraph(style='Report Table Gap')

lines=text.splitlines();i=0;page=1
while i<len(lines):
    line=lines[i].strip()
    if not line:i+=1;continue
    if line=='<!-- pagebreak -->':
        # Page break is attached to the next heading; avoid an extra blank paragraph.
        page+=1;i+=1
        while i<len(lines) and not lines[i].strip():i+=1
        assert lines[i].startswith('# ')
        p=doc.add_paragraph(style='Heading 1');p.paragraph_format.page_break_before=True
        write_text(p,lines[i][2:]);i+=1;continue
    if line.startswith('|'):
        block=[]
        while i<len(lines) and lines[i].strip().startswith('|'):block.append(lines[i]);i+=1
        table(block);continue
    if line.startswith('!['):
        m=re.fullmatch(r'!\[(.*?)\]\((.*?)\)',line)
        p=doc.add_paragraph(style='Report Image');p.alignment=WD_ALIGN_PARAGRAPH.CENTER
        shape=p.add_run().add_picture(str(TMP/Path(m.group(2)).name),width=Mm(155 if page==2 else 170))
        shape._inline.docPr.set('descr',m.group(1))
        doc.add_paragraph(m.group(1),style='Caption');i+=1;continue
    if line.startswith('# '):doc.add_paragraph(line[2:],style='Title' if page==1 else 'Heading 1');i+=1;continue
    if line.startswith('## '):doc.add_paragraph(line[3:],style='Heading 2');i+=1;continue
    paragraph=[line];i+=1
    while i<len(lines) and lines[i].strip() and not lines[i].strip().startswith(('#','|','![','<!--')):
        paragraph.append(lines[i].strip());i+=1
    s=' '.join(paragraph);p=doc.add_paragraph(style='Report Source' if s.startswith('資料：') else 'Normal');write_text(p,s)

props=doc.core_properties
props.title='HW1: Exploratory Analysis of a Music Catalog'
props.subject='113062273';props.author='113062273';props.last_modified_by='113062273'
props.keywords='';props.comments=''
doc.save(OUTPUT)
check=Document(OUTPUT)
alltext='\n'.join(p.text for p in check.paragraphs)+'\n'+'\n'.join(c.text for t in check.tables for r in t.rows for c in r.cells)
assert 'bootstrap' not in alltext
assert len(check.inline_shapes)==5
assert len(check.tables)==7
assert sum(bool(p.paragraph_format.page_break_before) for p in check.paragraphs)==5
print('Created editable DOCX:',OUTPUT)
print('Native tables:',len(check.tables),'Figures:',len(check.inline_shapes))
