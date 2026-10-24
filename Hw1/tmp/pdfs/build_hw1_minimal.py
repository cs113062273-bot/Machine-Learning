from pathlib import Path
import argparse
import html
import re
import sys

import pymupdf
from reportlab.lib import colors
from reportlab.lib.enums import TA_LEFT
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, Image,
)

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[2]
parser = argparse.ArgumentParser()
parser.add_argument('--source', default=str(ROOT / 'HW1_final_report_minimal_113062273.md'))
parser.add_argument('--output', default=str(ROOT / 'output/pdf/minimal/HW1_final_report_113062273.pdf'))
parser.add_argument('--preview', default=str(ROOT / 'tmp/pdfs/hw1_minimal_preview'))
args = parser.parse_args()
SOURCE = Path(args.source).resolve()
OUTPUT = Path(args.output).resolve()
PREVIEW = Path(args.preview).resolve()
OUTPUT.parent.mkdir(parents=True, exist_ok=True)
PREVIEW.mkdir(parents=True, exist_ok=True)

pdfmetrics.registerFont(TTFont('JH', 'C:/Windows/Fonts/msjh.ttc', subfontIndex=0))
pdfmetrics.registerFont(TTFont('JHB', 'C:/Windows/Fonts/msjhbd.ttc', subfontIndex=0))
pdfmetrics.registerFontFamily('JH', normal='JH', bold='JHB', italic='JH', boldItalic='JHB')

body = ParagraphStyle('body', fontName='JH', fontSize=10.2, leading=15,
                      wordWrap='CJK', spaceAfter=7, alignment=TA_LEFT)
title = ParagraphStyle('title', parent=body, fontName='JHB', fontSize=15,
                       leading=22, spaceAfter=8, keepWithNext=True)
section = ParagraphStyle('section', parent=body, fontName='JHB', fontSize=12,
                         leading=18, spaceBefore=5, spaceAfter=5, keepWithNext=True)
subsection = ParagraphStyle('subsection', parent=body, fontName='JHB', fontSize=10.6,
                            leading=16, spaceBefore=3, spaceAfter=4, keepWithNext=True)
note = ParagraphStyle('note', parent=body, fontSize=8.2, leading=12,
                      spaceAfter=6, keepWithNext=True)
question = ParagraphStyle('question', fontName='Helvetica', fontSize=9.3,
                          leading=12.8, spaceAfter=7, alignment=TA_LEFT,
                          keepWithNext=True)
cell = ParagraphStyle('cell', parent=body, fontSize=9.2, leading=13, spaceAfter=0)
header = ParagraphStyle('header', parent=cell, fontName='JHB')

def formatted(text):
    value = html.escape(text)
    return re.sub(r'\*\*(.+?)\*\*', r'<b>\1</b>', value)

def widths(rows, available):
    h = rows[0]
    if len(h) == 2:
        return [available * .31, available * .69]
    if h[0] == 'PC':
        return [available * .10, available * .14, available * .76]
    if h[0] == 'k':
        return [available * .16, available * .42, available * .42]
    if h[0] == '特徵平均':
        return [available * .36, available * .32, available * .32]
    if len(h) == 4:
        return [available * .43, available * .13, available * .22, available * .22]
    if h[0] == 'Alpha' and 'loudness' in h[1]:
        return [available * .12, available * .21, available * .23,
                available * .25, available * .19]
    if len(h) == 5:
        return [available * .12, available * .22, available * .22,
                available * .23, available * .21]
    if len(h) == 6:
        return [available * .12, available * .17, available * .17,
                available * .17, available * .19, available * .18]
    return [available / len(h)] * len(h)

def table(rows, available):
    content = [[Paragraph(formatted(c), header if ri == 0 else cell)
                for c in row] for ri, row in enumerate(rows)]
    result = Table(content, colWidths=widths(rows, available), repeatRows=1,
                   hAlign='LEFT', spaceBefore=2, spaceAfter=8)
    result.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LINEABOVE', (0, 0), (-1, 0), .6, colors.black),
        ('LINEBELOW', (0, 0), (-1, 0), .5, colors.black),
        ('LINEBELOW', (0, 1), (-1, -1), .25, colors.Color(.55, .55, .55)),
    ]))
    return result

doc = SimpleDocTemplate(str(OUTPUT), pagesize=A4,
                        leftMargin=18 * mm, rightMargin=18 * mm,
                        topMargin=16 * mm, bottomMargin=17 * mm,
                        title=SOURCE.read_text(encoding='utf-8').splitlines()[0].removeprefix('# '), author='113062273')
lines = SOURCE.read_text(encoding='utf-8').splitlines()
story = []
i = 0
while i < len(lines):
    line = lines[i].strip()
    if not line:
        i += 1
        continue
    if line == '<!-- pagebreak -->':
        story.append(PageBreak())
    elif re.fullmatch(r'!\[[^\]]*\]\([^)]+\)', line):
        image_path = re.fullmatch(r'!\[[^\]]*\]\(([^)]+)\)', line).group(1)
        figure = Image(str((SOURCE.parent / image_path).resolve()))
        factor = min(doc.width / figure.imageWidth, 1)
        figure.drawWidth = figure.imageWidth * factor
        figure.drawHeight = figure.imageHeight * factor
        figure.hAlign = 'CENTER'
        figure.spaceAfter = 4
        next_line = i + 1
        while next_line < len(lines) and not lines[next_line].strip():
            next_line += 1
        if next_line < len(lines) and re.match(r'^圖 \d+：', lines[next_line].strip()):
            caption = Paragraph(formatted(lines[next_line].strip()), body)
            story.append(KeepTogether([figure, caption]))
            i = next_line
        else:
            story.append(figure)
    elif line.startswith('|'):
        rows = []
        while i < len(lines) and lines[i].strip().startswith('|'):
            columns = [c.strip() for c in lines[i].strip().strip('|').split('|')]
            if not all(re.fullmatch(r':?-+:?', c) for c in columns):
                rows.append(columns)
            i += 1
        story.append(KeepTogether([table(rows, doc.width)]))
        continue
    elif line.startswith('# '):
        story.append(Paragraph(formatted(line[2:]), title))
    elif line.startswith('## '):
        story.append(Paragraph(formatted(line[3:]), section))
    elif line.startswith('### '):
        story.append(Paragraph(formatted(line[4:]), subsection))
    elif line.startswith('要求依據：'):
        story.append(Paragraph(formatted(line), note))
    elif line.startswith('> '):
        story.append(Paragraph(formatted(line[2:]), question))
    else:
        story.append(Paragraph(formatted(line), body))
    i += 1

def footer(canvas, doc):
    canvas.saveState()
    canvas.setFont('JH', 8)
    canvas.drawRightString(A4[0] - 18 * mm, 9 * mm, f'第 {doc.page} 頁')
    canvas.restoreState()

doc.build(story, onFirstPage=footer, onLaterPages=footer)
pdf = pymupdf.open(OUTPUT)
assert len(pdf) <= 10, len(pdf)
for i, page in enumerate(pdf):
    page.get_pixmap(matrix=pymupdf.Matrix(1.5, 1.5)).save(PREVIEW / f'page-{i+1:02}.png')
    text = page.get_text(sort=True)
    print(f'PAGE {i+1}: {len(text)} characters; first: {text[:80]!r}')
(PREVIEW / 'extracted.txt').write_text('\n\n'.join(
    f'=== PAGE {i+1} ===\n{page.get_text(sort=True)}' for i, page in enumerate(pdf)), encoding='utf-8')
print(f'PDF created: {OUTPUT}; pages={len(pdf)}')
