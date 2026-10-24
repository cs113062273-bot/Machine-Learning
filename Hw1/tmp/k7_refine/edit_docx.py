from copy import deepcopy
from datetime import datetime
from pathlib import Path
from zipfile import ZipFile
import hashlib
import json
from lxml import etree as E
import pandas as pd
from PIL import Image

ROOT = Path.cwd()
TARGET = ROOT / 'HW1_final_report_reviewed_113062273.docx'
WORK = ROOT / 'tmp/k7_refine'
BACKUP = WORK / 'report_before_k7.docx'
if not BACKUP.exists():
    BACKUP.write_bytes(TARGET.read_bytes())
with ZipFile(BACKUP) as z:
    parts = {i.filename: z.read(i.filename) for i in z.infolist()}
    infos = z.infolist()
W = 'http://schemas.openxmlformats.org/wordprocessingml/2006/main'
NS = {'w': W, 'a': 'http://schemas.openxmlformats.org/drawingml/2006/main',
      'wp': 'http://schemas.openxmlformats.org/drawingml/2006/wordprocessingDrawing',
      'r': 'http://schemas.openxmlformats.org/officeDocument/2006/relationships'}
def tag(local):
    return '{' + W + '}' + local
def text(el):
    return ''.join(el.xpath('.//w:t/text()', namespaces=NS))
def find_range(body):
    nodes = list(body)
    start = next(i for i, el in enumerate(nodes) if text(el).startswith('3.2 Clustering individual tracks.'))
    end = next(i for i, el in enumerate(nodes) if text(el).startswith('4. Section 6:'))
    return nodes, start, end
doc = E.fromstring(parts['word/document.xml'])
body = doc.find(tag('body'))
nodes, start, end = find_range(body)
old = nodes[start:end]
outside_before = [E.tostring(el) for el in nodes[:start] + nodes[end:]]
paragraphs = [el for el in old if el.tag == tag('p')]
answer = next(el for el in paragraphs if text(el).startswith('對清理後'))
caption = next(el for el in paragraphs if text(el).startswith('圖1'))
question2 = old[0]
question3 = next(el for el in paragraphs if text(el).startswith('3.3'))
image_nodes = [el for el in paragraphs if el.xpath('.//w:drawing', namespaces=NS)]
old_table = next(el for el in old if el.tag == tag('tbl'))
profiles = pd.read_csv(WORK / 'k7_cluster_profiles.csv', index_col=0)
stability = pd.read_csv(WORK / 'cluster_stability.csv', index_col=0)
assert profiles.tracks.sum() == 88858
def paragraph(value, template=answer, keep_next=False, font_size=None):
    p = E.Element(tag('p'))
    prop = deepcopy(template.find(tag('pPr')))
    if prop is None:
        prop = E.Element(tag('pPr'))
    # Restrict paragraph changes to the requested sections.
    for name in ['pageBreakBefore', 'keepNext']:
        for el in list(prop.findall(tag(name))):
            prop.remove(el)
    if keep_next:
        E.SubElement(prop, tag('keepNext'))
    p.append(prop)
    r = E.SubElement(p, tag('r'))
    rp = E.SubElement(r, tag('rPr'))
    E.SubElement(rp, tag('b')).set(tag('val'), '0')
    if font_size:
        E.SubElement(rp, tag('sz')).set(tag('val'), str(font_size))
    E.SubElement(rp, tag('lang')).set(tag('eastAsia'), 'zh-TW')
    t = E.SubElement(r, tag('t'))
    t.text = value
    return p
def picture(index, filename):
    p = deepcopy(image_nodes[index])
    rid = p.xpath('.//a:blip/@r:embed', namespaces=NS)[0]
    rels = E.fromstring(parts['word/_rels/document.xml.rels'])
    rel = next(el for el in rels if el.get('Id') == rid)
    media = 'word/' + rel.get('Target')
    # Ensure changing this image cannot affect other sections.
    assert len(doc.xpath('.//a:blip[@r:embed="' + rid + '"]', namespaces=NS)) == 1
    parts[media] = (WORK / filename).read_bytes()
    with Image.open(WORK / filename) as im:
        height = round(6112800 * im.height / im.width)
    for el in p.xpath('.//wp:extent | .//a:xfrm/a:ext', namespaces=NS):
        el.set('cx', '6112800'); el.set('cy', str(height))
    prop = p.find(tag('pPr'))
    if prop.find(tag('keepNext')) is None:
        E.SubElement(prop, tag('keepNext'))
    return p
def feature_table():
    tbl = E.Element(tag('tbl'))
    pr = deepcopy(old_table.find(tag('tblPr')))
    pr.find(tag('tblW')).set(tag('w'), '9600')
    layout = pr.find(tag('tblLayout'))
    if layout is None:
        layout = E.SubElement(pr, tag('tblLayout'))
    layout.set(tag('type'), 'fixed')
    margins = pr.find(tag('tblCellMar'))
    if margins is None:
        margins = E.SubElement(pr, tag('tblCellMar'))
    for name in ['top','bottom','left','right']:
        item = margins.find(tag(name))
        if item is None:
            item = E.SubElement(margins, tag(name))
        item.set(tag('w'), '40'); item.set(tag('type'), 'dxa')
    tbl.append(pr)
    widths = [2040] + [1080] * 7
    grid = E.SubElement(tbl, tag('tblGrid'))
    for width in widths:
        E.SubElement(grid, tag('gridCol')).set(tag('w'), str(width))
    values = [['特徵平均'] + [f'群 {i}\n{int(profiles.loc[i,"tracks"]):,} 首' for i in range(7)]]
    for feature in profiles.columns.drop('tracks'):
        values.append([feature] + [f'{profiles.loc[i,feature]:.4f}' for i in range(7)])
    for index, row in enumerate(values):
        tr = E.SubElement(tbl, tag('tr'))
        trpr = E.SubElement(tr, tag('trPr'))
        E.SubElement(trpr, tag('cantSplit'))
        if index == 0:
            E.SubElement(trpr, tag('tblHeader'))
        for col, value in enumerate(row):
            tc = E.SubElement(tr, tag('tc'))
            tcp = E.SubElement(tc, tag('tcPr'))
            w = E.SubElement(tcp, tag('tcW'))
            w.set(tag('w'), str(widths[col])); w.set(tag('type'), 'dxa')
            E.SubElement(tcp, tag('vAlign')).set(tag('val'), 'center')
            p = paragraph('', font_size=19)
            pp = p.find(tag('pPr'))
            ind = pp.find(tag('ind'))
            if ind is not None:
                pp.remove(ind)
            space = pp.find(tag('spacing'))
            if space is None:
                space = E.SubElement(pp, tag('spacing'))
            space.set(tag('after'), '20'); space.set(tag('line'), '240'); space.set(tag('lineRule'), 'auto')
            E.SubElement(pp, tag('jc')).set(tag('val'), 'left' if col == 0 else 'center')
            rp = p.find(tag('r')).find(tag('rPr'))
            rp.find(tag('b')).set(tag('val'), '1' if index == 0 else '0')
            # Keep the compact numeric table intact without affecting other tables.
            if index < len(values)-1:
                E.SubElement(pp, tag('keepNext'))
            r = p.find(tag('r'))
            r.remove(r.find(tag('t')))
            for j, line in enumerate(value.split('\n')):
                if j:
                    E.SubElement(r, tag('br'))
                E.SubElement(r, tag('t')).text = line
            tc.append(p)
    return tbl

s1 = stability.loc['uniform_subsample_1']
s2 = stability.loc['uniform_subsample_2']
new = [deepcopy(question2),
    paragraph('對清理後全部 88,858 首歌曲的標準化九項音訊特徵做 K-means，檢查 k = 2–10，使用 seed = 113062273、n_init = 10。inertia 使用全部歌曲；silhouette 使用固定 seed 隨機抽出的同一批 2,000 首，降低兩兩距離的計算成本。'),
    picture(0, 'k7_selection.png'),
    paragraph('圖 1：不同 k 的 inertia 與 silhouette；虛線標示選擇的 k = 7。', caption),
    paragraph('與 k = 2 相比，k = 7 的 inertia 從 627,300.1 降至 373,493.2，降低 40.46%；silhouette 從 0.2633 降至 0.2061，降低 21.73%。雖然 k = 2 的 silhouette 最高，但 inertia 在 k = 7 後降幅縮小，而且 k = 7 的 silhouette 比鄰近的 k = 6、8 高，因此選擇 k = 7。'),
    paragraph('各群歌曲數和九項特徵的平均值如下；數值以原始單位呈現。', keep_next=True),
    feature_table(),
    paragraph('Cluster 0 能量較低、原聲程度較高；Cluster 1 能量較高、器樂程度高；Cluster 2 音量和能量最高，速度最快。'),
    paragraph('Cluster 3 音量和能量最低，原聲與器樂程度都高；Cluster 4 口語成分最高，現場感也高；Cluster 5 可舞性和正向情緒分數最高；Cluster 6 現場感最高，能量也較高。'),
    deepcopy(question3),
    paragraph('證據一：PCA 投影。圖 2 中，低能量、原聲程度高的 Cluster 3 偏向 PC1 的低分側，高能量的 Cluster 2、5 偏向高分側，符合第 2.2 題對 PC1 的解讀。可舞性和正向情緒較高的 Cluster 5，也偏向 PC2 的高分側。部分群仍重疊，前兩個 PC 沒有把七群完全分開。'),
    picture(1, 'k7_pca.png'),
    paragraph('圖 2：同一批 2,000 首歌曲的 PC1–PC2 投影；七種顏色代表九項音訊特徵分出的七群。', caption),
    paragraph(f'證據二：抽樣穩定性。用固定 seed = 113062273 另外隨機抽兩批各 20,000 首，分別重新標準化並做七群 K-means，再對全部歌曲分群。與全資料結果相比，對齊群號後只有 {s1.matched_changed_fraction*100:.2f}%、{s2.matched_changed_fraction*100:.2f}% 的歌曲改群，ARI 分別為 {s1.ARI:.4f}、{s2.ARI:.4f}，表示結果不太受這兩次抽樣影響。'),
    paragraph('兩項證據支持分群反映音訊差異，而且結果相對穩定。分群沒有使用曲風標籤，但不能因此說歌曲一定有七個天然類別。')]
for el in old:
    body.remove(el)
for i, el in enumerate(new):
    body.insert(start+i, el)
nodes_after, new_start, new_end = find_range(body)
assert [E.tostring(el) for el in nodes_after[:new_start] + nodes_after[new_end:]] == outside_before
parts['word/document.xml'] = E.tostring(doc, xml_declaration=True, encoding='UTF-8', standalone=True)
candidate = WORK / TARGET.name
with ZipFile(candidate, 'w') as z:
    for info in infos:
        z.writestr(info, parts[info.filename])
with ZipFile(BACKUP) as a, ZipFile(candidate) as b:
    changed = [name for name in a.namelist() if a.read(name) != b.read(name)]
assert set(changed) == {'word/document.xml', 'word/media/image1.png', 'word/media/image2.png'}, changed
audit = {'changed_package_parts': changed, 'outside_3_2_3_3_xml_identical': True,
    'original_sha256': hashlib.sha256(BACKUP.read_bytes()).hexdigest(),
    'candidate_sha256': hashlib.sha256(candidate.read_bytes()).hexdigest(),
    'cluster_count': 7, 'track_count': int(profiles.tracks.sum()),
    'stability': [s1.to_dict(), s2.to_dict()]}
(WORK / 'docx_scope_audit.json').write_text(json.dumps(audit, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(audit, ensure_ascii=False, indent=2))
