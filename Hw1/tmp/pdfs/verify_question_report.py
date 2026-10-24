from pathlib import Path
import hashlib
import json
import re
import sys

import nbformat
import pandas as pd
import pymupdf

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[2]
AUDIT = ROOT / 'tmp/pdfs/workspace_reread'
report = (ROOT / 'HW1_final_report_minimal_113062273.md').read_text(encoding='utf-8')
registry = json.loads((AUDIT / 'report_question_sources.json').read_text(encoding='utf-8'))
spec = pymupdf.open(ROOT / 'HW1_Spec (1).pdf')


def normalize(text):
    return re.sub(r'\s+', ' ', text.replace('\u200b', '')).strip()


lines = []
for line in report.splitlines():
    if line.startswith('要求依據：'):
        continue
    line = re.sub(r'^### \d+\.\d+ ', '', line)
    lines.append(line.removeprefix('> '))
content = normalize(' '.join(lines))
for question in registry:
    assert normalize(question['original_english']) in content, question['question']
    actual_pages = ' '.join(spec[i - 1].get_text() for i in question['spec_pages'])
    assert normalize(question['original_english']) in normalize(actual_pages), question['question']
for number in range(1, 5):
    block = report.split(f'### 4.{number} ', 1)[1].split('### ', 1)[0]
    assert '第 9 頁' in block
assert 'Compare your predictions' not in report.split('## 4.', 1)[0]
assert '## 1. Auditing the Dataset' in report
assert 'The Data' not in report and 'Pre-Registration' not in report
assert len(registry) == 13
assert re.findall(r'^### (\d+\.\d+) ', report, re.M) == [
    '1.1', '1.2', '1.3', '2.1', '2.2', '2.3',
    '3.1', '3.2', '3.3', '4.1', '4.2', '4.3', '4.4']

pdf = pymupdf.open(ROOT / 'output/pdf/minimal/HW1_final_report_113062273.pdf')
assert len(pdf) <= 10
extracted = '\n'.join(page.get_text() for page in pdf)
pdf_content = normalize(' '.join(
    re.sub(r'^\d+\.\d+ ', '', line)
    for line in extracted.splitlines()
    if not line.startswith('要求依據：')))
for question in registry:
    assert normalize(question['original_english']) in pdf_content, question['question']
assert '\ufffd' not in extracted
for value in ['0.1223', '20.2001', '0.2569', '20.4984', '0.5832', '-0.3290',
              '-0.4347', '0.2837', '-0.9719', '0.9671', '-0.9755',
              '0.159787', '0.224119', '0.174244', '22.25%']:
    assert value in extracted, value

original_hashes = json.loads((AUDIT / 'unchanged_inputs.json').read_text(encoding='utf-8'))
for name, original_hash in original_hashes.items():
    assert hashlib.sha256((ROOT / name).read_bytes()).hexdigest() == original_hash, name

notebook = nbformat.read(ROOT / 'HW1_code_113062273.ipynb', as_version=4)
nbformat.validate(notebook)
code = [cell for cell in notebook.cells if cell.cell_type == 'code']
assert len(code) == 19 and all(cell.execution_count is not None for cell in code)
assert not any(output.output_type == 'error' for cell in code for output in cell.outputs)

summary = pd.read_csv(ROOT / 'HW1_results_113062273/q4_summary.csv').set_index('setting')
small = summary.loc['small_polynomial']
assert abs(100 * (1 - small.Ridge_test_rmse / small.OLS_test_rmse) - 22.25) < .005
correlations = pd.read_csv(ROOT / 'HW1_results_113062273/q4_small_polynomial_correlated_basis.csv')
assert correlations.absolute_r.gt(.95).all()
assert '不能稱為彼此高度相關' in report
assert '補充設定再使用高度相關基底' in report
assert 'same original input' not in report

validation = {
    'source_verified_questions_and_instructions': len(registry),
    'report_pdf_pages': len(pdf),
    'regression_Q1_to_Q4_spec_page': 9,
    'notebook_executed_code_cells': len(code),
    'source_data_pre_report_and_AI_log_unchanged': True,
    'english_original_questions_and_report_numbers_verified': True,
    'no_data_description_or_pre_registration_chapter': True,
    'numeric_report_consistency': 'passed',
    'original_input_audit_before_full_model': 'passed',
    'small_setting_mutually_correlated_basis': 'passed',
    'original_input_correlation_limitation_disclosed': True,
}
(AUDIT / 'final_report_validation.json').write_text(json.dumps(validation, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps(validation, ensure_ascii=False, indent=2))
