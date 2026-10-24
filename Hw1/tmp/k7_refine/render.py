from pathlib import Path

original = Path('tmp/final_review/render_reviewed.py').read_text(encoding='utf-8')
original = original.replace("str(ROOT/'HW1_final_report_reviewed_113062273.docx')",
    "str(Path(__file__).with_name('HW1_final_report_reviewed_113062273.docx'))")
exec(compile(original, __file__, 'exec'))
