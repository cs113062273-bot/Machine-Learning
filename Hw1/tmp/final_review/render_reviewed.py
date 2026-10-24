"""Run the skill renderer with Windows URI and available-rasterizer adapters."""
from pathlib import Path
import importlib.util
import os
import sys
import subprocess
import fitz

ROOT=Path(__file__).resolve().parents[2]
SKILL=Path('C:/Users/chinh/.codex/plugins/cache/openai-primary-runtime/documents/26.805.11740/skills/documents/render_docx.py')
spec=importlib.util.spec_from_file_location('skill_renderer',SKILL)
renderer=importlib.util.module_from_spec(spec)
spec.loader.exec_module(renderer)
LO=Path('C:/Users/chinh/.codex/tools/libreoffice-26.2.6')
executables=list(LO.rglob('soffice.com'))
if not executables: raise RuntimeError('Extracted LibreOffice console executable not found')
SOFFICE=executables[0]

def windows_run(cmd, env, verbose):
    cmd=list(cmd)
    if cmd[0]=='soffice': cmd[0]=str(SOFFICE)
    for i,s in enumerate(cmd):
        if s.startswith('-env:UserInstallation=file://'):
            raw=s.split('file://',1)[1]
            cmd[i]='-env:UserInstallation='+Path(raw).as_uri()
    proc=subprocess.run(cmd,env=env,capture_output=True,text=True,encoding='utf-8',errors='replace',timeout=75)
    if verbose:
        print(proc.stdout);print(proc.stderr)
    return proc

def fitz_rasterize(pdf_path,dpi,fmt,thread_count,output_folder,paths_only,output_file):
    paths=[]
    with fitz.open(pdf_path) as pdf:
        for i,page in enumerate(pdf,1):
            path=Path(output_folder)/f'page0001-{i:02d}.png'
            page.get_pixmap(dpi=dpi,alpha=False).save(str(path))
            paths.append(str(path))
    return paths

renderer._run_cmd=windows_run
renderer._build_lo_env=lambda user_profile:dict(os.environ)
renderer.convert_from_path=fitz_rasterize
sys.argv=[str(SKILL),str(ROOT/'HW1_final_report_reviewed_113062273.docx'),
          '--output_dir',str(Path(__file__).with_name('rendered')),'--emit_pdf','--dpi','130','--verbose']
renderer.main()
