from pathlib import Path
import hashlib
import json
import re
import sys

from docx import Document
from docx.enum.style import WD_STYLE_TYPE
from docx.enum.table import WD_TABLE_ALIGNMENT, WD_CELL_VERTICAL_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_LINE_SPACING
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Mm, Pt, RGBColor

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[2]
SOURCE = ROOT / 'HW1_final_report_minimal_113062273.md'
OUTPUT = ROOT / 'HW1_final_report_minimal_113062273.docx'
QA = ROOT / 'tmp/docx/minimal_preview'
QA.mkdir(parents=True, exist_ok=True)

# Conversion fidelity: preserve the report's plain A4 visual system.
# Named overrides to compact_reference_guide: A4; 18 mm side margins;
# Microsoft JhengHei; black headings; existing source/question styles;
# no added cover, running header, callout or prose.
TOKENS = {'width_mm': 210, 'height_mm': 297, 'left_mm': 18, 'right_mm': 18,
          'top_mm': 16, 'bottom_mm': 17, 'font': 'Microsoft JhengHei',
          'body_pt': 10.5, 'body_leading_pt': 15, 'body_after_pt': 7,
          'title_pt': 15, 'section_pt': 12, 'question_heading_pt': 10.5,
          'question_pt': 9.5, 'source_pt': 8, 'table_pt': 9,
          'table_padding_dxa': 100, 'color': '000000'}
source = SOURCE.read_text(encoding='utf-8')
source_hash = hashlib.sha256(SOURCE.read_bytes()).hexdigest()
doc = Document()
sec = doc.sections[0]
sec.page_width, sec.page_height = Mm(210), Mm(297)
sec.left_margin = sec.right_margin = Mm(18)
sec.top_margin, sec.bottom_margin = Mm(16), Mm(17)
sec.header_distance, sec.footer_distance = Mm(8), Mm(8)
grid = sec._sectPr.find(qn('w:docGrid'))
if grid is not None:
    sec._sectPr.remove(grid)
width_dxa = round(174 / 25.4 * 1440)


def style(name, size, leading, *, bold=False, before=0, after=7, keep=False, ascii_font=None):
    s = doc.styles[name] if name in doc.styles else doc.styles.add_style(name, WD_STYLE_TYPE.PARAGRAPH)
    s.font.name, s.font.size = ascii_font or TOKENS['font'], Pt(size)
    s.font.bold = bold
    s.font.color.rgb = RGBColor.from_string('000000')
    fonts = s.element.get_or_add_rPr().get_or_add_rFonts()
    for language in ['ascii', 'hAnsi', 'cs']:
        fonts.set(qn('w:' + language), ascii_font or TOKENS['font'])
    fonts.set(qn('w:eastAsia'), TOKENS['font'])
    pf = s.paragraph_format
    pf.space_before, pf.space_after = Pt(before), Pt(after)
    pf.line_spacing_rule, pf.line_spacing = WD_LINE_SPACING.EXACTLY, Pt(leading)
    pf.keep_with_next, pf.widow_control = keep, True
    pf.left_indent = pf.right_indent = Pt(0)
    ppr = s.element.get_or_add_pPr()
    snap = OxmlElement('w:snapToGrid')
    snap.set(qn('w:val'), '0')
    ppr.append(snap)
    return s


style('Normal', 10.5, 15)
style('Title', 15, 22, bold=True, after=8, keep=True)
style('Heading 1', 12, 18, bold=True, before=5, after=5, keep=True)
style('Heading 2', 10.5, 16, bold=True, before=3, after=4, keep=True)
style('Report Source', 8, 12, after=6, keep=True)
style('Report Question', 9.5, 13, keep=True, ascii_font='Arial')
style('Report Table', 9, 13, after=0)
style('Report Table Header', 9, 13, bold=True, after=0)
style('Report Gap', 1, 2, after=5)
style('Caption', 9, 13, after=7)
image_style = style('Report Image', 1, 1, after=3, keep=True)
image_style.paragraph_format.line_spacing_rule = WD_LINE_SPACING.SINGLE
image_style.paragraph_format.line_spacing = 1
style('Footer', 8, 11, after=0)


def write(paragraph, text):
    for piece in re.split(r'(\*\*.*?\*\*)', text):
        run = paragraph.add_run(piece[2:-2] if piece.startswith('**') and piece.endswith('**') else piece)
        if piece.startswith('**') and piece.endswith('**'):
            run.bold = True


expected_text = []


def paragraph(text, name='Normal'):
    p = doc.add_paragraph(style=name)
    write(p, text)
    expected_text.append(p.text)
    return p


def table(rows):
    head = rows[0]
    ratios = ([.31, .69] if len(head) == 2 else
              [.10, .14, .76] if head[0] == 'PC' else
              [.36, .32, .32] if head[0] == '特徵平均' else
              [.43, .13, .22, .22] if len(head) == 4 else
              [1 / len(head)] * len(head))
    widths = [round(width_dxa * r) for r in ratios]
    widths[-1] += width_dxa - sum(widths)
    t = doc.add_table(rows=len(rows), cols=len(head))
    t.alignment, t.autofit = WD_TABLE_ALIGNMENT.LEFT, False
    pr = t._tbl.tblPr
    tw = pr.find(qn('w:tblW'))
    tw.set(qn('w:type'), 'dxa')
    tw.set(qn('w:w'), str(width_dxa))
    indent = OxmlElement('w:tblInd')
    indent.set(qn('w:w'), '100')
    indent.set(qn('w:type'), 'dxa')
    pr.append(indent)
    margins = OxmlElement('w:tblCellMar')
    for side, value in [('top', 60), ('bottom', 60), ('start', 100), ('end', 100)]:
        element = OxmlElement('w:' + side)
        element.set(qn('w:w'), str(value))
        element.set(qn('w:type'), 'dxa')
        margins.append(element)
    pr.append(margins)
    borders = OxmlElement('w:tblBorders')
    for side in ['top', 'bottom', 'left', 'right', 'insideH', 'insideV']:
        element = OxmlElement('w:' + side)
        element.set(qn('w:val'), 'single' if side in ['top', 'bottom', 'insideH'] else 'nil')
        element.set(qn('w:sz'), '3' if side == 'insideH' else '6')
        element.set(qn('w:color'), '909090' if side == 'insideH' else '000000')
        borders.append(element)
    pr.append(borders)
    for col, width in zip(t._tbl.tblGrid.gridCol_lst, widths):
        col.set(qn('w:w'), str(width))
    for i, (row, values) in enumerate(zip(t.rows, rows)):
        trpr = row._tr.get_or_add_trPr()
        trpr.append(OxmlElement('w:cantSplit'))
        if i == 0:
            trpr.append(OxmlElement('w:tblHeader'))
        for cell, value, width in zip(row.cells, values, widths):
            cell.width = Pt(width / 20)
            cell.vertical_alignment = WD_CELL_VERTICAL_ALIGNMENT.TOP
            tcw = cell._tc.get_or_add_tcPr().find(qn('w:tcW'))
            tcw.set(qn('w:type'), 'dxa')
            tcw.set(qn('w:w'), str(width))
            p = cell.paragraphs[0]
            p.style = doc.styles['Report Table Header' if i == 0 else 'Report Table']
            p.paragraph_format.keep_with_next = i < len(rows) - 1
            write(p, value)
    paragraph('', 'Report Gap')


lines = source.splitlines()
i = 0
tables_expected, images_expected = [], []
while i < len(lines):
    line = lines[i].strip()
    if not line:
        i += 1
        continue
    if line.startswith('|'):
        rows = []
        while i < len(lines) and lines[i].strip().startswith('|'):
            values = [v.strip() for v in lines[i].strip().strip('|').split('|')]
            if not all(re.fullmatch(r':?-+:?', value) for value in values):
                rows.append(values)
            i += 1
        table(rows)
        tables_expected.append(rows)
        continue
    image = re.fullmatch(r'!\[([^\]]*)\]\(([^)]+)\)', line)
    if image:
        p = paragraph('', 'Report Image')
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        shape = p.add_run().add_picture(str(ROOT / image.group(2)), width=Mm(174))
        shape._inline.docPr.set('descr', image.group(1))
        images_expected.append(image.group(2))
    elif line.startswith('### '):
        paragraph(line[4:], 'Heading 2')
    elif line.startswith('## '):
        paragraph(line[3:], 'Heading 1')
    elif line.startswith('# '):
        paragraph(line[2:], 'Title')
    elif line.startswith('要求依據：'):
        paragraph(line, 'Report Source')
    elif line.startswith('> '):
        paragraph(line[2:], 'Report Question')
    elif re.match(r'^圖 \d+：', line):
        paragraph(line, 'Caption')
    else:
        paragraph(line)
    i += 1

footer = sec.footer.paragraphs[0]
footer.style, footer.alignment = doc.styles['Footer'], WD_ALIGN_PARAGRAPH.RIGHT
footer.add_run('第 ')
field = OxmlElement('w:fldSimple')
field.set(qn('w:instr'), 'PAGE')
run = OxmlElement('w:r')
text = OxmlElement('w:t')
text.text = '1'
run.append(text)
field.append(run)
footer._p.append(field)
footer.add_run(' 頁')
doc.core_properties.title = 'HW1：音樂資料分析'
doc.core_properties.author = '113062273'
doc.core_properties.last_modified_by = '113062273'
doc.core_properties.comments = ''
doc.core_properties.keywords = ''
doc.save(OUTPUT)

check = Document(OUTPUT)
assert [p.text for p in check.paragraphs] == expected_text
assert len(check.tables) == len(tables_expected) == 6
for t, rows in zip(check.tables, tables_expected):
    assert [[c.text for c in row.cells] for row in t.rows] == rows
assert len(check.inline_shapes) == 3
assert sum(p.style.name == 'Heading 2' for p in check.paragraphs) == 13
assert hashlib.sha256(SOURCE.read_bytes()).hexdigest() == source_hash
(QA / 'structure_validation.json').write_text(json.dumps({
    'paragraph_text_preserved': True, 'native_editable_tables': 6,
    'embedded_figures': 3, 'question_headings': 13,
    'source_markdown_unchanged': True, 'conversion_tokens': TOKENS}, ensure_ascii=False, indent=2), encoding='utf-8')
print('Created editable DOCX:', OUTPUT)
