from pathlib import Path
import json
import re
import sys

import pandas as pd
import pymupdf

sys.stdout.reconfigure(encoding='utf-8')
ROOT = Path(__file__).resolve().parents[2]
OLD = (ROOT / 'tmp/pdfs/workspace_reread/before_rewrite_HW1_final_report_minimal_113062273.md').read_text(encoding='utf-8')
RESULTS = ROOT / 'HW1_results_113062273'
SPEC = pymupdf.open(ROOT / 'HW1_Spec (1).pdf')


def normalized(text):
    return re.sub(r'\s+', ' ', text.replace('\u200b', '').replace('\ufeff', '')).strip()


registry = []


def question(number, pages, text):
    source = normalized(' '.join(SPEC[i - 1].get_text() for i in pages))
    assert normalized(text) in source, (number, text)
    source_section, source_question = map(int, number.split('.'))
    report_number = f'{source_section - 2}.{source_question}'
    registry.append({'question': number, 'report_question': report_number,
                     'spec_pages': pages, 'original_english': text})
    if '?' in text and text.index('?') < text.index('. '):
        title, rest = text.split('? ', 1)
        title += '?'
    else:
        title, rest = text.split('. ', 1)
        title += '.'
    return (f'### {report_number} {title}\n\n'
            f'要求依據：HW1_Spec (1).pdf 第 {"-".join(map(str, pages))} 頁，Section {source_section} Q{source_question}。\n\n'
            f'> {rest}\n\n')


def old_between(start, end):
    return OLD.split(start, 1)[1].split(end, 1)[0].strip().replace('<!-- pagebreak -->', '').strip()


pre_instruction = 'You will compare these expectations with your actual findings later in the assignment and discuss in the report.'
assert pre_instruction in normalized(SPEC[4].get_text())
parts = ['''# HW1：音樂資料分析

學號：113062273

## 1. Auditing the Dataset

''']
parts.append(question('3.1', [5, 6], 'Identify and prioritize at least four data-quality findings, ordered from most to least important based on how strongly you believe each one could affect the analyses or models in this assignment. For each finding, include: a. Evidence: one number, table, or figure showing that the issue is present. b. Why it matters: explain how the issue could affect a later analysis or model. c. Your decision: state what you will do about it. d. Trade-off: explain what information, data, or reliability you may lose because of that decision.'))
audit = old_between('| 優先序與問題', '重複排在衝突之前')
audit = audit.replace('跨曲風統計讓每首歌的標籤權重合計為 1。',
                      '第 3.3 節曲風與分群的交叉統計，讓每首歌的標籤權重合計為 1。')
parts.append('以下依對後續分析的影響排序。\n\n| 優先序與問題' + audit + '\n\n')
parts.append(question('3.2', [6], 'Justify your ranking. Explain why you ranked your first finding as more important than your second.'))
parts.append('重複排在衝突之前' + old_between('重複排在衝突之前', '清理流程為') + '\n\n')
parts.append(question('3.3', [6], 'Apply your cleaning decisions. In your submitted notebook, include the code that transforms the raw dataset into the cleaned dataset used in your analysis. The code should be reproducible from the original tracks.csv dataset.'))
parts.append('清理流程為 114,000 → 113,550 → 113,386 → 111,458 筆配對列，最後得到 88,858 個唯一 track_id。程式已實作於 HW1_code_113062273.ipynb，可由原始 tracks.csv 重現。本報告 PCA、分群與回歸的結果均使用清理後的唯一歌曲；曲風分析另外保留歌曲與曲風的對應。\n\n')
parts.append('## 2. The Geometry of the Feature Space\n\n')
parts.append('要求依據：HW1_Spec (1).pdf 第 6-7 頁，Section 4。\n\n')
parts.append(old_between('使用 danceability', '### 4.1 有效維度').join(['使用 danceability', '\n\n']))
parts.append(question('4.1', [6], 'Effective dimensionality. Use PCA to estimate how many principal components are needed to represent most of the variation in the audio features. Clearly state the criterion or metrics you use to decide how many components are sufficient.'))
parts.append(old_between('以累積解釋', '### 4.2 前幾個主成分').join(['以累積解釋', '\n\n']))
parts.append(question('4.2', [7], 'Interpret the leading principal components. For the first few principal components, explain in plain language what kind of variation each component appears to capture.'))
parts.append('| PC' + old_between('| PC', '### 4.3 標準化的影響') + '\n\n')
parts.append(question('4.3', [7], 'Effect of standardization. Repeat the PCA without standardizing the features first. Compare the result with the standardized PCA and explain why they differ. Your explanation should refer to the quantity that PCA maximizes. Support your explanation with either: a. A short mathematical derivation. b. A variance calculation using your own data.'))
parts.append('未標準化時' + old_between('未標準化時', '## 5.1 曲風分群') + '\n\n')
parts.append('## 3. Structure in the Data\n\n')
parts.append(question('5.1', [7], 'Clustering genres. Create one representative audio-feature profile for each genre, and use hierarchical clustering to group similar genres together. Show how the resulting genre groupings differ, and explain which result you find more reasonable based on evidence from the data. Compare: a. Two different measures of dissimilarity. b. Two different linkage methods.'))
genre_answer = '每種曲風以' + old_between('每種曲風以', '## 5.2 歌曲分群')
genre_answer = genre_answer.replace('主要設定仍有包含 94 種曲風的大群，因此只作粗略分組。',
    '主要設定仍有包含 94 種曲風的大群，因此只作粗略分組。事前預期不同曲風有音訊差異、相近曲風的特徵較接近；上述特徵差異支持前者，但大群仍高度混合，只能部分支持整體預期。（事前預期比較依據：HW1_Spec (1).pdf 第 5 頁。）')
parts.append(genre_answer + '\n\n')
parts.append(question('5.2', [7], 'Clustering individual tracks. Using the standardized audio features, cluster the individual tracks (e.g. with k-means). To choose the number of clusters k, compute at least two quantitative criteria (e.g. the elbow of the inertia curve and the silhouette score) over a range of k, show them, and explain your final choice. Then describe what each resulting cluster represents in terms of its audio characteristics (e.g. by reporting the mean of each feature per cluster). Some clustering methods or criteria may be expensive to run on all 114,000 rows. If you use a subset of the data for clustering or evaluation, clearly state how the subset was selected and why.'))
parts.append('對全部 88,858' + old_between('對全部 88,858', '## 5.3 分群是否有意義') + '\n\n')
parts.append(question('5.3', [8], 'Are the clusters meaningful? A clustering algorithm always returns k clusters, even on data with no real structure. Provide evidence that the clusters you found in Question 2 reflect real differences between tracks, rather than being an artifact of the algorithm, the sampling, or the way genres were assigned. Provide at least two evidence. For example: a. Plot the clusters in the space of the first two principal components and explain whether the cluster boundaries align with the directions of variation you interpreted there. b. Stability. Re-run the clustering with a different random seed, a different subsample, or after applying your cleaning decisions from Section 3, and report how much the cluster assignments change.'))
parts.append('**證據一：' + old_between('**證據一：', '## 6. 回歸') + '\n\n')
parts.append('## 4. Two Regression Targets\n\n要求依據：HW1_Spec (1).pdf 第 8 頁，Section 6。\n\n')
parts.append('相同錄音群組不跨集合。' + old_between('相同錄音群組不跨集合。', '### 6.1 事前預測、實際結果與 baseline') + '\n\n')
parts.append(question('6.1', [9], 'Compare your predictions with the actual results. Restate the RMSE values you predicted in Section 2. Then fit a linear regression model for each target and report its held-out RMSE. For each target, also report the RMSE of a simple baseline model that ignores the input features and always predicts the mean target value from the training set.'))
parts.append('事前 RMSE 數值取自已完成的 HW1_pre_report_113062273.pdf 第 1 頁。\n\n')
parts.append('| 項目 | Energy' + old_between('| 項目 | Energy', '### 6.2 兩項任務的差異') + '\n\n')
parts.append(question('6.2', [9], 'Explain the difference in predictive performance. Compare the two regression tasks and explain why one target is easier or harder to predict from the available features. Support your explanation with evidence from this dataset, such as relationships between the target and the input features, rather than only making a general statement such as “the data are noisy.”'))
performance_answer = '相對各自 baseline' + old_between('相對各自 baseline', '### 6.3 額外的預測資訊')
parts.append(performance_answer + '\n\n')
parts.append('energy 與 loudness 正相關、與 acousticness 負相關的方向，支持 pre-report 的第一項預期。（事前預期比較依據：HW1_Spec (1).pdf 第 5 頁。）\n\n')
parts.append(question('6.3', [9], 'Look for additional predictive information. If one target is difficult to predict from the audio features, look for one other variable in the dataset that may contain useful information about that target. For example, pick one non-audio column in tracks.csv that you think carries information about the target. Support your choice with an appropriate measurement or plot.'))
parts.append('選 artists。' + old_between('選 artists。', '### 6.4 正則化') + '\n\n')
parts.append(question('6.4', [9], 'Study the effect of regularization. Use energy as the target for this question. Identify several input features that are strongly correlated with one another. Standardize these features, then fit a regularized linear regression model using these features, and vary the regularization strength over several orders of magnitude. Report how the coefficients and held-out RMSE change as regularization becomes stronger. If regularization does not improve held-out performance on the full dataset, say so. Then create a setting in which regularization has a clearer effect, for example by using a smaller training set, a richer set of basis functions (such as polynomial features), or both.'))
parts.append('target 是 energy，不包含在輸入。**原始欄位稽核與完整資料實驗。**只用 Train 檢查八個允許的連續輸入，最高 |Pearson r| 為 0.5832（acousticness 與 loudness）。列舉全部 56 組三欄組合，選擇「三組 |r| 中最小值」最大的組合，得到 instrumentalness、valence、loudness；三組 r 分別為 -0.3290、-0.4347、0.2837。這個原始子集的相關仍有限，不能稱為彼此高度相關。完整資料先使用此子集觀察正則化，補充設定再使用高度相關基底；兩種輸入分開報告。\n\n')
parts.append('三欄標準化後 fit OLS／Ridge，前處理只 fit 訓練資料。alpha 為 10^-6 至 10^6，共 25 組；先用 Train 擬合，依 validation RMSE 選 alpha，再用 development 重訓。下表係數對應標準化原始輸入，test 不用來選 alpha。\n\n')


def ridge_table(setting, alphas, columns, labels, norm=False):
    path = pd.read_csv(RESULTS / f'q4_{setting}_path.csv').set_index('alpha')
    headers = ['Alpha'] + labels + (['係數 L2 長度'] if norm else []) + ['Test RMSE']
    text = '| ' + ' | '.join(headers) + ' |\n| ' + ' | '.join(['---']*len(headers)) + ' |\n'
    for alpha in alphas:
        row = path.iloc[(abs(path.index.to_numpy() - alpha)).argmin()]
        label = {1e-6: '10^-6', 1e4: '10^4', 1e6: '10^6', 1e3: '10^3'}.get(alpha, f'{alpha:g}')
        values = [row[c] for c in columns + (['coefficient_l2'] if norm else []) + ['test_rmse']]
        text += '| ' + ' | '.join([label] + [f'{v:.6f}' for v in values]) + ' |\n'
    return text + '\n'


parts.append(ridge_table('full_original', [1e-6, 100, 1e4, 1e6],
    ['instrumentalness','valence','loudness'],['instrumentalness 係數','valence 係數','loudness 係數']))
summary = pd.read_csv(RESULTS / 'q4_summary.csv').set_index('setting')
full, small = summary.loc['full_original'], summary.loc['small_polynomial']
parts.append(f'完整資料 validation 選 alpha = 10^-6。相同三欄的 OLS 與 Ridge test RMSE 均為 {full.OLS_test_rmse:.6f}，差約 {full.test_rmse_improvement:.1e}，沒有實質改善。alpha 增強時，整體係數長度縮小，但個別係數不一定單調，instrumentalness 也會變號；過強的正則化使 test RMSE 上升。\n\n')
parts.append('**高度相關基底與小樣本實驗。**依本題第二段的小樣本、多項式設定，從 Train 以固定 seed 均勻抽 80 個不同錄音群組，各取一首。使用同樣三個原始欄位，先標準化，展開三次多項式為 19 個基底，再逐基底標準化。每次前處理與模型都只 fit 這 80 首；validation、test 不加入訓練，alpha 依 validation 選擇。\n\n')
parts.append('令 L、I 為這 80 首上標準化的 loudness、instrumentalness。基底 L²、L³、L²I 的三組 Pearson r 為 -0.9719、0.9671、-0.9755，彼此高度相關，且都包含在模型輸入中。下表係數對應再次標準化的基底；L2 長度計算全部 19 個係數。\n\n')
parts.append(ridge_table('small_polynomial', [1e-6, float(small.alpha_selected_on_validation), 1e3, 1e6],
    ['loudness^2','loudness^3','instrumentalness loudness^2'],['L² 係數','L³ 係數','L²I 係數'],norm=True))
improvement = 100 * small.test_rmse_improvement / small.OLS_test_rmse
parts.append(f'小樣本 validation 選 alpha = {small.alpha_selected_on_validation:.6f}。相同 80 首與基底的 OLS test RMSE 為 {small.OLS_test_rmse:.6f}，Ridge 為 {small.Ridge_test_rmse:.6f}，降低 {improvement:.2f}%；訓練 RMSE 從 {small.OLS_training_rmse:.6f} 升至 0.152454。這符合適度收縮抑制過擬合的現象，但過強會失去訊號。此設定只有一批小樣本；高度相關的結論適用於基底，不適用於原始三欄。\n\n')
final_instruction = 'Finally, you will summarize what your results imply about the strengths and limitations of this dataset for machine-learning applications.'
assert final_instruction in normalized(SPEC[0].get_text())
parts.append('清理後資料可用於音訊探索、歌曲粗分與 energy 線性預測。音訊對 popularity 的線性預測力弱，artists 的改善主要限於已見藝人。重複、目標衝突、曲風配額及未知評分公式與時間，限制資料可靠性、母體及跨時間外推。（HW1_Spec (1).pdf 第 1 頁。）\n')

report = ''.join(parts)
assert '<!-- pagebreak -->' not in report
assert report.count('Compare your predictions with the actual results.') == 1
assert '## 1. Auditing the Dataset' in report
assert 'The Data' not in report
assert 'Pre-Registration' not in report
assert pre_instruction not in report
assert final_instruction not in report
assert len(registry) == 13
assert 'AI-use' not in report and 'AI 生成' not in report
(ROOT / 'HW1_final_report_minimal_113062273.md').write_text(report, encoding='utf-8')
(ROOT / 'tmp/pdfs/workspace_reread/report_question_sources.json').write_text(json.dumps(registry, ensure_ascii=False, indent=2), encoding='utf-8')
print(f'Rewrote report: {len(report)} characters; {len(registry)} source-verified English instructions/questions.')
