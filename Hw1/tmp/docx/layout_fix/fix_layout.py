from pathlib import Path
from zipfile import ZipFile, ZIP_DEFLATED
from lxml import etree
import hashlib
import json
import re

ROOT = Path(__file__).resolve().parents[3]
SOURCE = ROOT / 'HW1_final_report_minimal_113062273.docx'
TARGET = ROOT / 'HW1_final_report_minimal_113062273_formatted.docx'
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W, 'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
      'a': 'http://schemas.openxmlformats.org/drawingml/2006/main'}
def tag(name): return '{' + W + '}' + name
def child(parent, name):
    e = parent.find(tag(name))
    if e is None: e = etree.SubElement(parent, tag(name))
    return e
def attrs(e, **values):
    e.attrib.clear()
    for k, v in values.items(): e.set(tag(k), str(v))
    return e
def value(p, name, val): attrs(child(p, name), val=val)
def ppr(p):
    e = p.find(tag('pPr'))
    if e is None:
        e = etree.Element(tag('pPr')); p.insert(0, e)
    return e
def txt(p): return ''.join(p.xpath('.//w:t/text()', namespaces=NS))

with ZipFile(SOURCE) as z:
    parts = {i.filename: z.read(i.filename) for i in z.infolist()}
document = etree.fromstring(parts['word/document.xml'])
styles = etree.fromstring(parts['word/styles.xml'])
body = document.find('w:body', NS)
before_text = document.xpath('//w:t/text()', namespaces=NS)
before_media = {k: hashlib.sha256(v).hexdigest() for k,v in parts.items() if k.startswith('word/media/')}
base = next(s.get(tag('styleId')) for s in styles.findall(tag('style'))
            if s.find(tag('name')) is not None and s.find(tag('name')).get(tag('val')).lower() == 'normal')

for sid, name, size, bold, before, after, keep in [
    ('HW1Answer', 'HW1 Answer', 24, False, 0, 60, False),
    ('HW1Section', 'HW1 Section', 28, True, 140, 100, True),
    ('HW1Question', 'HW1 Question', 24, True, 100, 80, True),
    ('HW1Subheading', 'HW1 Subheading', 24, True, 60, 60, True),
    ('HW1Figure', 'HW1 Figure', 24, False, 60, 40, True),
    ('HW1FigureCaption', 'HW1 Figure Caption', 22, False, 0, 80, False),
]:
    old = styles.find(f"w:style[@w:styleId='{sid}']", NS)
    if old is not None: styles.remove(old)
    s = etree.SubElement(styles, tag('style'))
    s.set(tag('type'), 'paragraph'); s.set(tag('styleId'), sid); s.set(tag('customStyle'), '1')
    value(s, 'name', name); value(s, 'basedOn', base); value(s, 'next', 'HW1Answer')
    pp = child(s, 'pPr')
    value(pp, 'keepNext', int(keep)); value(pp, 'keepLines', 0); value(pp, 'widowControl', 1)
    value(pp, 'pageBreakBefore', 0); value(pp, 'snapToGrid', 0)
    attrs(child(pp, 'spacing'), before=before, after=after, line=320, lineRule='exact')
    value(pp, 'outlineLvl', 0 if sid=='HW1Section' else 1 if sid=='HW1Question' else 9)
    rp = child(s, 'rPr')
    attrs(child(rp, 'rFonts'), ascii='標楷體', hAnsi='標楷體', eastAsia='標楷體', cs='標楷體')
    value(rp, 'sz', size); value(rp, 'szCs', size); value(rp, 'b', int(bold)); value(rp, 'bCs', int(bold))

# Keep Word's old title border from reappearing through inherited styles.
for s in styles.findall(tag('style')):
    n=s.find(tag('name'))
    if n is not None and n.get(tag('val'), '').lower()=='title':
        for b in s.findall('w:pPr/w:pBdr',NS): b.getparent().remove(b)

section = body.find('w:sectPr',NS)
page = section.find('w:pgSz',NS); margins = section.find('w:pgMar',NS)
usable = int(page.get(tag('w'))) - int(margins.get(tag('left'))) - int(margins.get(tag('right')))
indent = 240  # One 12-pt Chinese character, matching the user's 2.2 answer indentation.
content_width = usable - indent
removed=[]; roles=[]
for index, p in enumerate(list(body)):
    if p.tag != tag('p'): continue
    text=txt(p).strip()
    has_image=bool(p.findall('.//w:drawing',NS))
    if not text and not has_image and not p.xpath('.//w:br|.//w:fldChar|.//w:instrText|.//w:sectPr|.//w:object|.//w:pict',namespaces=NS):
        body.remove(p); removed.append(index); continue
    pp=ppr(p)
    if index==0:
        role='title'; left=0; keep=True; sid=None
    elif re.match(r'^\d+\s*\.?\s*Section\s+\d+:',text):
        role='section'; left=0; keep=True; sid='HW1Section'
    elif re.match(r'^\d+\.\d+\s',text):
        role='question'; left=0; keep=True; sid='HW1Question'
    elif has_image:
        role='image'; left=indent; keep=True; sid='HW1Figure'
    elif re.match(r'^圖\s*\d+\s*[：:]',text):
        role='caption'; left=indent; keep=False; sid='HW1FigureCaption'
    elif re.match(r'^[1-4]\.\s*(?!Section)',text) or re.match(r'^\([ab]\)\s+Two different',text) or text=='較合理的結果與證據':
        role='subheading'; left=indent; keep=True; sid='HW1Subheading'
    else:
        role='answer'; left=indent; keep=False; sid='HW1Answer'
    if sid is not None: value(pp,'pStyle',sid)
    value(pp,'keepNext',int(keep)); value(pp,'keepLines',int(has_image)); value(pp,'pageBreakBefore',0)
    value(pp,'widowControl',1); value(pp,'snapToGrid',0)
    attrs(child(pp,'ind'),left=left,right=0,firstLine=0)
    value(pp,'outlineLvl',0 if role=='section' else 1 if role=='question' else 9)
    # Explicit spacing overrides the pasted heading/image style properties.
    attrs(child(pp,'spacing'),before=140 if role=='section' else 100 if role=='question' else 60 if role in ('subheading','image') else 0,
          after=100 if role in ('section','title') else 40 if role=='image' else 60 if role=='answer' else 80,
          line=240 if has_image else 400 if role=='title' else 360 if role=='section' else 320,
          lineRule='auto' if has_image else 'exact')
    if role!='title': value(pp,'jc','left' if role in ('section','question','subheading','image','caption') else 'both')
    # Runs are preserved. Explicitly align text sizes where inherited/pasted formats differ.
    size=28 if role=='section' else 22 if role=='caption' else 24
    for r in p.findall('w:r',NS):
        if r.find('w:drawing',NS) is not None or role=='title': continue
        rp=child(r,'rPr')
        value(rp,'sz',size); value(rp,'szCs',size)
        if role in ('section','question','subheading'):
            value(rp,'b',1); value(rp,'bCs',1)
    # Proportionally fit inline drawings to the indented answer width.
    for drawing in p.findall('.//wp:inline',NS):
        e=drawing.find('wp:extent',NS)
        if e is None: continue
        max_cx=int(content_width*635)
        ratio=min(1,max_cx/int(e.get('cx')))
        if ratio<1:
            for ex in [e]+drawing.findall('.//a:xfrm/a:ext',NS):
                for dimension in ('cx','cy'):
                    ex.set(dimension,str(round(int(ex.get(dimension))*ratio)))
    roles.append({'index':index,'role':role,'indent_twips':left,'keep_next':keep})

for table_index, table in enumerate(body.findall('w:tbl',NS)):
    tp=child(table,'tblPr')
    attrs(child(tp,'tblW'),w=content_width,type='dxa')
    attrs(child(tp,'tblInd'),w=indent,type='dxa')
    attrs(child(tp,'tblLayout'),type='fixed')
    attrs(child(tp,'jc'),val='left')
    grid=table.find('w:tblGrid',NS)
    oldcols=[int(c.get(tag('w'))) for c in grid]
    widths=[round(content_width*c/sum(oldcols)) for c in oldcols]
    if table_index==1:
        widths=[round(content_width*0.45),round(content_width*0.275),round(content_width*0.275)]
    widths[-1]+=content_width-sum(widths)
    for c,width in zip(grid,widths): c.set(tag('w'),str(width))
    cell_margins=child(tp,'tblCellMar')
    for side in ('top','bottom'): attrs(child(cell_margins,side),w=40,type='dxa')
    row_count=len(table.findall('w:tr',NS))
    for rowindex,row in enumerate(table.findall('w:tr',NS)):
        trp=child(row,'trPr')
        value(trp,'cantSplit',1)
        for h in trp.findall(tag('trHeight')): trp.remove(h)
        if rowindex==0: value(trp,'tblHeader',1)
        col=0
        for cell in row.findall('w:tc',NS):
            cp=child(cell,'tcPr')
            span=cp.find(tag('gridSpan')); n=int(span.get(tag('val'))) if span is not None else 1
            attrs(child(cp,'tcW'),w=sum(widths[col:col+n]),type='dxa'); col+=n
            for p in cell.findall('w:p',NS):
                pp=ppr(p)
                attrs(child(pp,'ind'),left=0,right=0,firstLine=0)
                value(pp,'keepNext',int(rowindex==0 or (row_count<=5 and rowindex<row_count-1)))
                value(pp,'keepLines',0); value(pp,'pageBreakBefore',0)
                value(pp,'outlineLvl',9); value(pp,'snapToGrid',0)
                attrs(child(pp,'spacing'),before=0,after=0,line=300,lineRule='exact')

assert document.xpath('//w:t/text()',namespaces=NS)==before_text, 'Visible text changed'
parts['word/document.xml']=etree.tostring(document,xml_declaration=True,encoding='UTF-8',standalone=True)
parts['word/styles.xml']=etree.tostring(styles,xml_declaration=True,encoding='UTF-8',standalone=True)
with ZipFile(TARGET,'w',ZIP_DEFLATED) as z:
    for k,v in parts.items(): z.writestr(k,v)
with ZipFile(TARGET) as z:
    after=etree.fromstring(z.read('word/document.xml'))
    assert after.xpath('//w:t/text()',namespaces=NS)==before_text
    assert {k:hashlib.sha256(z.read(k)).hexdigest() for k in before_media}==before_media
audit={'source':str(SOURCE),'output':str(TARGET),'source_sha256':hashlib.sha256(SOURCE.read_bytes()).hexdigest(),
       'visible_text_preserved':True,'media_preserved':True,'removed_empty_paragraphs':removed,
       'answer_indent_twips':indent,'tables':len(after.findall('.//w:tbl',NS)),'images':len(after.findall('.//w:drawing',NS)),
       'paragraph_roles':roles}
Path(__file__).with_name('validation.json').write_text(json.dumps(audit,indent=2),encoding='utf-8')
print(json.dumps({k:v for k,v in audit.items() if k!='paragraph_roles'},ensure_ascii=True))
