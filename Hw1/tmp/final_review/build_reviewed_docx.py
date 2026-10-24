from pathlib import Path
import copy, json, re
import pandas as pd
from docx import Document
from docx.shared import Pt, Mm, Twips
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.enum.text import WD_ALIGN_PARAGRAPH
from docx.enum.style import WD_STYLE_TYPE

ROOT = Path(__file__).resolve().parents[2]
HERE = Path(__file__).parent
R = ROOT/'HW1_results_113062273'
d = Document(ROOT/'HW1_final_report_minimal_113062273_formatted.docx')
original = list(d.paragraphs)

def set_text(p, text):
    p.clear(); p.add_run(text)
    return p

def after(p, text='', style='HW1 Answer'):
    np = d.add_paragraph(text, style)
    p._p.addnext(np._p)
    return np

def remove(p):
    p._p.getparent().remove(p._p)

set_text(original[0], 'HW1: Exploratory Analysis of a Music Catalog')
set_text(original[1], '1. Section 3: Auditing the Dataset')
set_text(original[23], '1.2 Justify your ranking.')
set_text(original[26], '清理程式位於 HW1_code_113062273.ipynb 的 Section 3，可從原始 tracks.csv 重現：114,000 列依序去除完全重複列、無效值與衝突 ID，再整理為 88,858 首唯一歌曲，曲風標籤另存。後續 PCA、分群與回歸均使用清理後資料。')
remove(original[28])  # Replace the older section-wide source note with precise per-question notes.
set_text(original[53], '對清理後全部 88,858 首歌曲的標準化九項音訊特徵做 k-means，檢查 k = 2–10。固定隨機種子，n_init = 10。inertia 使用全部歌曲；silhouette 使用同一批均勻無放回抽出的 2,000 首，減少兩兩距離的計算成本。')
original[54].clear()
original[54].add_run().add_picture(str(R/'report_k_selection.png'), width=Mm(169.8))
after(original[51], '上述特徵差異符合 pre-report「不同曲風有音訊差異」的預期；black-metal、death-metal、grindcore 同群，也與「相近曲風的特徵較接近」一致。這只支持所列例子，不能概括所有曲風。（事前預期比較：HW1_Spec (1).pdf 第 5 頁。）')

# Two direct evidence types from Q3: PCA projection plus rerun stability.
set_text(original[59], '證據一：PCA 投影。圖 2 的兩群主要沿 PC1 區分，與第 2.2 題解讀的「高能量、較大聲、原聲程度較低」方向一致。這表示分群對應可解釋的音訊差異；但投影中仍有重疊，沒有明顯空隙。')
p = after(original[59], style='HW1 Figure')
p.add_run().add_picture(str(R/'report_cluster_pca.png'), width=Mm(169.8))
after(p, '圖 2：固定 2,000 首歌曲的 PC1–PC2 投影；顏色為九項音訊特徵分群的結果，未使用曲風標籤。', 'HW1 Figure Caption')
set_text(original[60], '證據二：不同抽樣的穩定性。另外均勻無放回抽兩批各 20,000 首，分別重新擬合標準化及 k-means，再對全部歌曲預測。與全資料分群相比，對齊群號後的分群改變比例為 0.27%、0.34%，ARI 為 0.9887、0.9855。這降低結果只由單次抽樣造成的疑慮。')
set_text(original[61], '兩項證據支持穩定且可解釋的音訊粗分；分群未使用曲風標籤，因此不是依曲風標籤直接分組。連續梯度也可能被 k-means 切成群，不能據此證明有兩個天然音樂類別。')
set_text(original[64], '回歸使用清理後唯一歌曲，依錄音群組切分，避免同一錄音跨集合。Development 共 71,089 首，test 共 17,769 首；OLS 與 baseline 均用 development 擬合，baseline 固定預測其目標平均值。輸入為 Spec 指定的 11 項音訊特徵；預測 popularity 時額外加入 energy，均排除目標本身。連續輸入標準化，key、mode、time_signature 使用 one-hot；前處理只擬合 development。事前預測值取自已提交的 pre-report。')

# Replace the whole mixed old Q4 experiment, preserving the user's plain answer style.
for p in original[74:83]: remove(p)
s = pd.read_csv(R/'ridge_correlated_summary.csv', index_col=0)
full, small = s.loc['full_polynomial'], s.loc['small_polynomial']
c = pd.read_csv(R/'ridge_correlated_training_evidence.csv', index_col=0)
sc = pd.read_csv(R/'ridge_correlated_small_training_evidence.csv', index_col=0)
full_path = pd.read_csv(R/'ridge_correlated_full_polynomial_path.csv', index_col=0)
small_path = pd.read_csv(R/'ridge_correlated_small_polynomial_path.csv', index_col=0)
improvement = 100*(1-small.selected_Ridge_test_rmse/small.OLS_test_rmse)
texts = [
    '以 energy 為目標，使用允許的 loudness、acousticness、instrumentalness 三欄，展開為 19 項三次多項式基底；模型對基底係數保持線性。令 A 為原尺度 acousticness，Train 中 A、A²、A³ 的三組 Pearson r 分別為 ' + '、'.join(f'{v:.4f}' for v in c.training_pearson_r) + '，皆超過 0.90，呈現彼此高度相關。以下相關性及係數均以模型實際使用的基底為單位，energy 不作為輸入。',
    '每項基底分別標準化，前處理只擬合當次訓練資料。Ridge 的 α 從 10⁻⁶ 到 10⁶，共 25 組；完整資料先用 Train 56,931 首擬合、validation 14,158 首選 α，再用 development 71,089 首重訓。Test 17,769 首只用於呈現 held-out RMSE，不用來選 α。OLS 使用相同基底及訓練資料。',
    f'完整資料選 α = {full.alpha_selected_on_validation:g}。OLS test RMSE 為 {full.OLS_test_rmse:.6f}，Ridge 為 {full.selected_Ridge_test_rmse:.6f}，差約 {full.test_rmse_improvement:.2g}，沒有實質改善。α 增強時，全部 19 個係數的 L2 長度由 {full_path.iloc[0].coefficient_l2:.4f} 降至 {full_path.iloc[-1].coefficient_l2:.4f}；圖 3 顯示個別係數會調整或變號，並非各自單調縮小。過強的正則化使 test RMSE 升至 {full_path.iloc[-1].test_rmse:.6f}。',
    '為呈現較明顯的效果，固定隨機種子，從 Train 均勻無放回抽取 80 個不同錄音群組，各取一首，使用完全相同的 19 項基底。這 80 首中 A、A²、A³ 的三組 r 為 ' + '、'.join(f'{v:.4f}' for v in sc.training_pearson_r) + '，仍皆超過 0.90。前處理與模型只擬合這 80 首，α 由相同 validation 選擇，不將 validation 或 test 加入訓練。',
    f'小樣本選 α = {small.alpha_selected_on_validation:.4f}。OLS test RMSE 為 {small.OLS_test_rmse:.6f}，Ridge 為 {small.selected_Ridge_test_rmse:.6f}，降低 {improvement:.2f}%。係數整體收縮，適度正則化改善此設定的預測表現；α 過強時，test RMSE 上升至 {small_path.iloc[-1].test_rmse:.6f}。這支持正則化可減少小樣本、相關基底下的過擬合。',
]
texts[0] = texts[0].replace('呈现', '呈現')
anchor = original[73]
anchor = after(anchor, texts[0])
anchor = after(anchor, texts[1])
pic = after(anchor, style='HW1 Figure')
pic.add_run().add_picture(str(R/'report_q4_full.png'), width=Mm(169.8))
anchor = after(pic, '圖 3：完整資料中 A、A²、A³ 的標準化基底係數與 test RMSE；虛線標示 validation 選出的 α。', 'HW1 Figure Caption')
anchor = after(anchor, texts[2])
anchor = after(anchor, texts[3])
pic = after(anchor, style='HW1 Figure')
pic.add_run().add_picture(str(R/'report_q4_small.png'), width=Mm(169.8))
anchor = after(pic, '圖 4：80 首設定的代表基底係數、全部 19 個係數的 L2 長度與 test RMSE。', 'HW1 Figure Caption')
after(anchor, texts[4])
set_text(original[83], '整體而言，清理後資料可支援音訊探索、歌曲粗分與 energy 線性預測；popularity 的音訊線性預測力較弱，artists 的改善主要限於已見藝人。重複歌曲、目標衝突、曲風配額及缺少評分時間資訊，限制資料可靠性與母體、跨時間外推。')
original[83].paragraph_format.space_before = Pt(8)

# The evidence table satisfies Intro p.12 while the (a)-(d) answers remain intact.
tab = d.add_table(rows=1, cols=2)
tab.rows[0].cells[0].text = '優先序與品質問題'
tab.rows[0].cells[1].text = '原始資料的證據'
for label, evidence in [
    ('1. 重複歌曲', '16,641 個重複 ID；450 列完全重複'),
    ('2. popularity 不一致', '720 個 ID 的 popularity 有衝突'),
    ('3. 無效節奏、拍號或長度', 'tempo ≤ 0：157 列；拍號 0：163 列；長度 ≤ 0：1 列；聯集 164 列'),
    ('4. 曲風配額及多重標籤', '114 種曲風各 1,000 列；同一 ID 可有多種曲風'),
]:
    row=tab.add_row(); row.cells[0].text=label; row.cells[1].text=evidence
original[2]._p.addnext(tab._tbl)

note = d.styles.add_style('HW1 Source', WD_STYLE_TYPE.PARAGRAPH)
note.base_style = d.styles['HW1 Answer']
note.font.size = Pt(9)
note.paragraph_format.line_spacing = Pt(12)
note.paragraph_format.space_after = Pt(3)
note.paragraph_format.keep_with_next = True
pages = {'1.1':('5–6','12'),'1.2':('6','12'),'1.3':('6','12'),
         '2.1':('6','13–14'),'2.2':('7','14'),'2.3':('7','14'),
         '3.1':('7','15–16'),'3.2':('7','16'),'3.3':('8','16'),
         '4.1':('8–9','17–18'),'4.2':('9','18'),'4.3':('9','18'),'4.4':('8–9','18')}
for p in list(d.paragraphs):
    match = re.match(r'^(\d\.\d)\s', p.text)
    if match:
        spec, intro = pages[match.group(1)]
        after(p, f'要求依據：HW1_Spec (1).pdf 第 {spec} 頁；HW1_Intro.pdf 第 {intro} 頁。', 'HW1 Source')

# Explicitly normalize answer indentation and spacing; no empty spacer paragraphs.
for p in list(d.paragraphs):
    if not p.text and not p._p.xpath('.//w:drawing'):
        remove(p); continue
    if p.style.name.startswith('HW1'):
        pf = p.paragraph_format
        pf.left_indent = Twips(0 if p.style.name in ['HW1 Section','HW1 Question'] else 240)
        pf.first_line_indent = Pt(0); pf.right_indent=Pt(0)
        pf.page_break_before=False; pf.widow_control=True
        if p.style.name in ['HW1 Answer', 'HW1 Figure Caption']:
            pf.keep_with_next=False; pf.keep_together=False
        elif p.style.name in ['HW1 Section','HW1 Question','HW1 Subheading','HW1 Source','HW1 Figure']:
            pf.keep_with_next=True
        if p.style.name=='HW1 Figure':
            # Inline images need automatic line height; an exact 16-pt line crops the chart.
            pf.line_spacing=1.0
            pf.keep_together=True
        if p.style.name=='HW1 Answer':
            pf.space_before=Pt(0); pf.space_after=Pt(2); pf.line_spacing=Pt(15)
            p.alignment=WD_ALIGN_PARAGRAPH.LEFT
        for run in p.runs:
            if not run._r.xpath('.//w:drawing'):
                run.font.name='標楷體'; run._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'標楷體')
                run.font.size=Pt(9 if p.style.name=='HW1 Source' else 11 if p.style.name=='HW1 Figure Caption' else 14 if p.style.name=='HW1 Section' else 12)

content_width=9626
def element(parent, name, **attrs):
    el=parent.find(qn('w:'+name))
    if el is None: el=OxmlElement('w:'+name); parent.append(el)
    for k,v in attrs.items(): el.set(qn('w:'+k),str(v))
    return el
for i,t in enumerate(d.tables):
    t.autofit=False
    widths=([.30,.70] if i==0 else [.36,.32,.32] if i==1 else [.45,.275,.275] if i==2 else [.43,.13,.22,.22])
    twips=[round(content_width*x) for x in widths];twips[-1]+=content_width-sum(twips)
    tp=t._tbl.tblPr
    element(tp,'tblW',w=content_width,type='dxa');element(tp,'tblInd',w=240,type='dxa')
    element(tp,'tblLayout',type='fixed')
    mar=element(tp,'tblCellMar')
    for side in ['top','bottom']: element(mar,side,w=40,type='dxa')
    for side in ['left','right']: element(mar,side,w=80,type='dxa')
    borders=element(tp,'tblBorders')
    for edge in ['top','bottom','insideH']: element(borders,edge,val='single',sz=4,color='808080')
    for edge in ['left','right','insideV']: element(borders,edge,val='nil')
    for gc,width in zip(t._tbl.tblGrid.gridCol_lst,twips): gc.set(qn('w:w'),str(width))
    for row_idx,row in enumerate(t.rows):
        trp=row._tr.get_or_add_trPr();element(trp,'cantSplit',val=1)
        if row_idx==0: element(trp,'tblHeader',val=1)
        for cell,width in zip(row.cells,twips):
            element(cell._tc.get_or_add_tcPr(),'tcW',w=width,type='dxa')
            for p in cell.paragraphs:
                pf=p.paragraph_format
                pf.left_indent=Pt(0);pf.first_line_indent=Pt(0)
                pf.line_spacing=Pt(15);pf.space_before=Pt(0);pf.space_after=Pt(0)
                pf.keep_with_next=(row_idx<len(t.rows)-1)
                pf.keep_together=False
                for r in p.runs:
                    r.font.size=Pt(11);r.font.name='標楷體';r.bold=row_idx==0
                    r._element.get_or_add_rPr().get_or_add_rFonts().set(qn('w:eastAsia'),'標楷體')

# Keep each short quality finding's (a)-(d) answer together, avoiding a lone (d).
for start,end in [(3,7),(8,12),(13,17),(18,22)]:
    for p in original[start:end]: p.paragraph_format.keep_with_next=True

target=ROOT/'HW1_final_report_reviewed_113062273.docx'
# Do not retain unused relationships to the superseded charts in the final package.
used=set(d.part._element.xpath('//@r:embed'))
for rid,rel in list(d.part.rels.items()):
    if rel.reltype.endswith('/image') and rid not in used: d.part.drop_rel(rid)
d.save(target)
questions=[p.text for p in d.paragraphs if re.match(r'^\d\.\d\s',p.text)]
assert len(questions)==13
assert len(d.inline_shapes)==4
assert len(d.tables)==4
assert '0.174244' not in '\n'.join(p.text for p in d.paragraphs)
assert '0.159787' not in '\n'.join(p.text for p in d.paragraphs)
(HERE/'docx_structure.json').write_text(json.dumps({'questions':questions,'tables':len(d.tables),
    'figures':len(d.inline_shapes),'per_question_pdf_pages':pages},ensure_ascii=False,indent=2),encoding='utf-8')
print('Saved reviewed DOCX; 13 questions, 4 tables, 4 figures.')
