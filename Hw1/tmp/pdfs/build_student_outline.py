from pathlib import Path
import hashlib
import json
import sys

import nbformat
import pandas as pd
import pymupdf

sys.stdout.reconfigure(encoding='utf-8')
root=Path(__file__).resolve().parents[2]
out=root/'HW1_results_113062273'
audit=root/'tmp/pdfs/workspace_reread'
registry=json.loads((audit/'report_question_sources.json').read_text(encoding='utf-8'))
section_titles={1:'Auditing the Dataset',2:'The Geometry of the Feature Space',
                3:'Structure in the Data',4:'Two Regression Targets'}
outline=['# HW1 作答架構（待自行撰寫）\n\n學號：113062273\n\n']
section=None
for question in registry:
    report_section=int(question['report_question'].split('.')[0])
    source_section,source_question=question['question'].split('.')
    if report_section!=section:
        outline.append(f'## {report_section}. {section_titles[report_section]}\n\n')
        section=report_section
    english=question['original_english']
    if '?' in english and english.index('?')<english.index('. '):
        title,rest=english.split('? ',1);title+='?'
    else:
        title,rest=english.split('. ',1);title+='.'
    outline.append(f"### {question['report_question']} {title}\n\n")
    outline.append(f"要求依據：HW1_Spec (1).pdf 第 {'-'.join(map(str,question['spec_pages']))} 頁，Section {source_section} Q{source_question}。\n\n")
    outline.append('> '+rest+'\n\n你的答案：\n\n________________________________________\n\n________________________________________\n\n')
outline.append('事前預期與發現的比較，放入相關分析的答案；要求見 Spec 第 5 頁。整體資料應用的優點與限制，放入最後的結論；要求見 Spec 第 1 頁。\n')
(root/'HW1_report_outline_113062273.md').write_text(''.join(outline),encoding='utf-8')

summary=pd.read_csv(out/'q4_summary.csv').set_index('setting')
pairwise=pd.read_csv(out/'q4_selected_original_correlations_training.csv',index_col=0)
triples=pd.read_csv(out/'q4_original_feature_triples_training.csv',index_col=0)
derived=pd.read_csv(out/'q4_small_polynomial_correlated_basis.csv',index_col=0)
full,small=summary.loc['full_original'],summary.loc['small_polynomial']
facts=['# Q4 已驗證的數值與實驗設定\n\n',
       '题目來源：HW1_Spec (1).pdf 第 8 頁（輸入限制）、第 9 頁 Section 6 Q4（實驗要求）。\n\n',
       'target：energy。資料：原始 tracks.csv 經 notebook 清理後的唯一歌曲。沒有加入外部資料。\n\n',
       '原始連續候選：danceability、speechiness、acousticness、instrumentalness、liveness、valence、loudness、tempo。key、mode、time_signature 的數值相關也已核對，僅作代碼診斷，沒有當成等距音樂座標。\n\n',
       '特徵選法：僅用 Train 的輸入，列舉所有三欄組合，選取「三組 |Pearson r| 中最小值」最大的組合。結果為 instrumentalness、valence、loudness。沒有使用 validation/test 或 target 來選欄位。\n\n',
       '| 原始欄位配對 | Train Pearson r |\n| --- | --- |\n']
for a,b in [('instrumentalness','valence'),('instrumentalness','loudness'),('valence','loudness')]:
    facts.append(f'| {a} / {b} | {pairwise.loc[a,b]:.6f} |\n')
facts.append('\n全部允許原始欄位的最高 |Pearson r|：0.583187（acousticness / loudness）。最佳三欄組合的最小 |r|：'+f'{triples.iloc[0].minimum_pairwise_absolute_r:.6f}'+'。這些數字不支持把原始三欄稱為彼此高度相關。\n\n')
facts.append('完整資料設定：3 個原始輸入，先標準化，再 fit OLS / Ridge。選參數時 Train = 56,931；validation = 14,158。最後以 development = 71,089 重訓；test = 17,769。同錄音群組不跨集合。\n\n')
facts.append('補充設定：使用原先固定抽樣的 80 首，來自 80 個不同 Train 錄音群組。三欄先標準化，展開三次多項式為 19 个基底，再標準化基底。所有 fit 僅用這 80 首。validation/test 不加入訓練。\n\n')
facts.append('兩種設定皆使用 alpha = 10^-6 至 10^6，共 25 組；alpha 僅依 validation RMSE 選擇。\n\n')
facts.append('| 設定 | 輸入數 | 選定 alpha | OLS test RMSE | Ridge test RMSE |\n| --- | --- | --- | --- | --- |\n')
for name,label in [('full_original','完整資料／原始輸入'),('small_polynomial','80 首／多項式')]:
    row=summary.loc[name]
    facts.append(f'| {label} | {int(row.input_columns)} | {row.alpha_selected_on_validation:.6g} | {row.OLS_test_rmse:.9f} | {row.Ridge_test_rmse:.9f} |\n')
facts.append(f'\n完整資料 RMSE 差：{full.test_rmse_improvement:.3g}。小樣本 RMSE 相對降幅：{100*small.test_rmse_improvement/small.OLS_test_rmse:.2f}%。\n\n')
for name,label in [('full_original','完整資料原始輸入'),('small_polynomial','80 首多項式')]:
    path=pd.read_csv(out/f'q4_{name}_path.csv').set_index('alpha')
    coef_cols=[c for c in path.columns if c not in ['validation_rmse','test_rmse','training_rmse','coefficient_l2']]
    facts.append('## '+label+'：代表強度的係數與 held-out RMSE\n\n')
    facts.append('| Alpha | '+' | '.join(coef_cols)+' | 係數 L2 長度 | Test RMSE |\n')
    facts.append('| '+' | '.join(['---']*(len(coef_cols)+3))+' |\n')
    selected=float(summary.loc[name,'alpha_selected_on_validation'])
    values=sorted(set([1e-6,selected,1e4,1e6]))
    for alpha in values:
        row=path.iloc[abs(path.index.to_numpy()-alpha).argmin()]
        facts.append('| '+f'{alpha:.6g}'+' | '+' | '.join(f'{row[c]:.6f}' for c in coef_cols+['coefficient_l2','test_rmse'])+' |\n')
    facts.append('\n')
facts.append('## 補充設定中相關基底的數據\n\n| 基底一 | 基底二 | 80 首 Train Pearson r |\n| --- | --- | --- |\n')
for _,row in derived.iterrows():
    facts.append(f'| {row.basis_feature_1} | {row.basis_feature_2} | {row.training_pearson_r:.6f} |\n')
facts.append('\n這三組相關屬於補充設定的多項式基底，不是原始資料欄位。\n\n')
facts.append('程式：HW1_code_113062273.ipynb 最後一節。完整 25 組係數與誤差：q4_full_original_path.csv、q4_small_polynomial_path.csv；全部基底係數另見同名 coefficients.csv；摘要見 q4_summary.csv。\n')
(out/'Q4_verified_results.md').write_text(''.join(facts).replace('题目','題目').replace('19 个','19 個'),encoding='utf-8')

notebook=nbformat.read(root/'HW1_code_113062273.ipynb',as_version=4)
code=[c for c in notebook.cells if c.cell_type=='code']
assert len(code)==18 and all(c.execution_count is not None for c in code)
assert not any(o.output_type=='error' for c in code for o in c.outputs)
assert float(triples.iloc[0].minimum_pairwise_absolute_r)<.3
assert derived.absolute_r.gt(.95).all()
verification=json.loads((out/'verification.json').read_text(encoding='utf-8'))
verification['original_q4_audit']={
    'all_allowed_original_columns_examined':True,'selection_uses_training_inputs_only':True,
    'original_features':list(pairwise.index),
    'largest_minimum_correlation_across_original_triples':float(triples.iloc[0].minimum_pairwise_absolute_r),
    'strong_original_feature_triple_claim':False,
    'polynomial_features_only_in_new_small_setting':True,
    'validation_only_alpha_selection':True,
    'overall_assignment_compliance_certified':False,
    'remaining_items':['Student-written report prose','Clarification of strong original-input requirement']}
(out/'verification.json').write_text(json.dumps(verification,ensure_ascii=False,indent=2),encoding='utf-8')
hashes=json.loads((audit/'unchanged_inputs.json').read_text(encoding='utf-8'))
for name,digest in hashes.items():
    assert hashlib.sha256((root/name).read_bytes()).hexdigest()==digest,name
print('Created student-writing outline and numerical evidence; code verified, input files preserved.')
