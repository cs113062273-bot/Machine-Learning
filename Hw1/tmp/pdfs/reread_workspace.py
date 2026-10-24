from pathlib import Path
from collections import Counter
import hashlib, json, sys, zipfile
import xml.etree.ElementTree as ET
import pandas as pd
import pymupdf
from PIL import Image, ImageDraw, ImageFont

sys.stdout.reconfigure(encoding='utf-8')
root=Path(__file__).resolve().parents[2]
out=root/'tmp/pdfs/workspace_reread'
files=sorted(p for p in root.rglob('*') if p.is_file()
             and '.git' not in p.relative_to(root).parts
             and '__pycache__' not in p.relative_to(root).parts
             and out not in p.parents)
out.mkdir(parents=True,exist_ok=True)
manifest=[]; texts=[]; images=[]; known_images=set()
for path in files:
    rel=str(path.relative_to(root)); data=path.read_bytes()
    item={'path':rel,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()}
    suffix=path.suffix.lower()
    if suffix=='.pdf':
        doc=pymupdf.open(path)
        item['pages']=len(doc)
        text='\n\n'.join(f'=== PAGE {i+1} ===\n'+page.get_text(sort=True) for i,page in enumerate(doc))
        (out/(path.name+'.'+item['sha256'][:6]+'.txt')).write_text(text,encoding='utf-8')
        item['text_chars']=len(text)
        texts.append(f'\n=== FILE {rel} ===\n'+text)
    elif suffix=='.docx':
        with zipfile.ZipFile(path) as archive:
            xml=ET.fromstring(archive.read('word/document.xml'))
            ns={'w':'http://schemas.openxmlformats.org/wordprocessingml/2006/main'}
            text='\n'.join(''.join(p.itertext()) for p in xml.findall('.//w:p',ns))
            # Extract only visible text runs, including table cells.
            text='\n'.join(''.join(t.text or '' for t in p.findall('.//w:t',ns))
                           for p in xml.findall('.//w:p',ns))
            item['text_chars']=len(text)
            texts.append(f'\n=== FILE {rel} ===\n'+text)
            for name in archive.namelist():
                if name.startswith('word/media/') and name.lower().endswith('.png'):
                    imgdata=archive.read(name); digest=hashlib.sha256(imgdata).hexdigest()
                    if digest not in known_images:
                        target=out/(digest[:12]+'.png');target.write_bytes(imgdata)
                        images.append((str(target),rel+' / '+name));known_images.add(digest)
    elif suffix=='.csv':
        frame=pd.read_csv(path)
        item.update(rows=len(frame),columns=list(frame.columns),missing=frame.isna().sum().to_dict())
        if len(frame)<1000:
            texts.append(f'\n=== FILE {rel} ===\n'+frame.to_string(index=False))
        else:
            texts.append(f'\n=== FILE {rel} ===\n'+frame.describe(include='all').to_string()
                         +'\nMissing:\n'+frame.isna().sum().to_string())
        if path.name=='split_track_ids.csv':
            item['split_counts']=frame['split'].value_counts().to_dict()
            item['groups_crossing_splits']=int(frame.groupby('recording_group')['split'].nunique().gt(1).sum())
    elif suffix=='.ipynb':
        notebook=json.loads(data.decode('utf-8-sig'))
        item['cells']=len(notebook['cells'])
        parts=[]
        for i,c in enumerate(notebook['cells']):
            parts.append(f'CELL {i} ({c["cell_type"]})\n'+''.join(c['source']))
            for output in c.get('outputs',[]):
                if 'text' in output: parts.append(''.join(output['text']))
                elif 'text/plain' in output.get('data',{}):parts.append(''.join(output['data']['text/plain']))
        text='\n\n'.join(parts)
        (out/(path.name+'.txt')).write_text(text,encoding='utf-8')
        texts.append(f'\n=== FILE {rel} ===\n'+text)
    elif suffix in ['.md','.py','.ps1','.txt','.json'] or path.name=='AGENTS.md':
        text=data.decode('utf-8-sig',errors='replace')
        item['text_chars']=len(text)
        texts.append(f'\n=== FILE {rel} ===\n'+text)
    elif suffix=='.png':
        im=Image.open(path);im.load();item['size']=list(im.size)
        if item['sha256'] not in known_images:
            images.append((str(path),rel));known_images.add(item['sha256'])
    manifest.append(item)
(out/'manifest.json').write_text(json.dumps(manifest,ensure_ascii=False,indent=2,default=str),encoding='utf-8')
(out/'all_text.txt').write_text('\n'.join(texts),encoding='utf-8')
font=ImageFont.truetype('C:/Windows/Fonts/msjh.ttc',14)
for start in range(0,len(images),6):
    sheet=Image.new('RGB',(1500,1680),'white');draw=ImageDraw.Draw(sheet)
    for j,(path,label) in enumerate(images[start:start+6]):
        x=(j%2)*750;y=(j//2)*560
        img=Image.open(path).convert('RGB');img.thumbnail((720,515))
        sheet.paste(img,(x+(750-img.width)//2,y+30+(515-img.height)//2))
        draw.text((x+8,y+5),label[-90:],fill='black',font=font)
    sheet.save(out/f'images-{start//6+1:02}.jpg')
print('Files inspected:',len(manifest),'Extensions:',dict(Counter(Path(x['path']).suffix for x in manifest)))
print('Unique images:',len(images),'contact sheets:',(len(images)+5)//6)
print('PDFs:',[(x['path'],x['pages']) for x in manifest if 'pages' in x])
print('All text chars:',sum(len(t) for t in texts))
