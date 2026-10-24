# Q4 已驗證的數值與實驗設定

題目來源：HW1_Spec (1).pdf 第 8 頁（輸入限制）、第 9 頁 Section 6 Q4（實驗要求）。

target：energy。資料：原始 tracks.csv 經 notebook 清理後的唯一歌曲。沒有加入外部資料。

原始連續候選：danceability、speechiness、acousticness、instrumentalness、liveness、valence、loudness、tempo。key、mode、time_signature 的數值相關也已核對，僅作代碼診斷，沒有當成等距音樂座標。

特徵選法：僅用 Train 的輸入，列舉所有三欄組合，選取「三組 |Pearson r| 中最小值」最大的組合。結果為 instrumentalness、valence、loudness。沒有使用 validation/test 或 target 來選欄位。

| 原始欄位配對 | Train Pearson r |
| --- | --- |
| instrumentalness / valence | -0.329037 |
| instrumentalness / loudness | -0.434697 |
| valence / loudness | 0.283738 |

全部允許原始欄位的最高 |Pearson r|：0.583187（acousticness / loudness）。最佳三欄組合的最小 |r|：0.283738。這些數字不支持把原始三欄稱為彼此高度相關。

完整資料設定：3 個原始輸入，先標準化，再 fit OLS / Ridge。選參數時 Train = 56,931；validation = 14,158。最後以 development = 71,089 重訓；test = 17,769。同錄音群組不跨集合。

補充設定：使用原先固定抽樣的 80 首，來自 80 個不同 Train 錄音群組。三欄先標準化，展開三次多項式為 19 個基底，再標準化基底。所有 fit 僅用這 80 首。validation/test 不加入訓練。

兩種設定皆使用 alpha = 10^-6 至 10^6，共 25 組；alpha 僅依 validation RMSE 選擇。

| 設定 | 輸入數 | 選定 alpha | OLS test RMSE | Ridge test RMSE |
| --- | --- | --- | --- | --- |
| 完整資料／原始輸入 | 3 | 1e-06 | 0.159787277 | 0.159787277 |
| 80 首／多項式 | 19 | 3.16228 | 0.224119115 | 0.174244242 |

完整資料 RMSE 差：3.31e-14。小樣本 RMSE 相對降幅：22.25%。

## 完整資料原始輸入：代表強度的係數與 held-out RMSE

| Alpha | instrumentalness | valence | loudness | 係數 L2 長度 | Test RMSE |
| --- | --- | --- | --- | --- | --- |
| 1e-06 | 0.053301 | 0.021675 | 0.211199 | 0.218897 | 0.159787 |
| 10000 | 0.034047 | 0.021644 | 0.177846 | 0.182365 | 0.162445 |
| 1e+06 | -0.002557 | 0.003905 | 0.012740 | 0.013569 | 0.245810 |

## 80 首多項式：代表強度的係數與 held-out RMSE

| Alpha | loudness^2 | loudness^3 | instrumentalness loudness^2 | 係數 L2 長度 | Test RMSE |
| --- | --- | --- | --- | --- | --- |
| 1e-06 | 0.032489 | 0.269261 | -0.026660 | 1.242279 | 0.224119 |
| 3.16228 | 0.047479 | 0.020729 | -0.043697 | 0.360136 | 0.174244 |
| 10000 | -0.000512 | 0.000575 | -0.000619 | 0.002439 | 0.254161 |
| 1e+06 | -0.000006 | 0.000006 | -0.000007 | 0.000026 | 0.256886 |

## 補充設定中相關基底的數據

| 基底一 | 基底二 | 80 首 Train Pearson r |
| --- | --- | --- |
| loudness^2 | loudness^3 | -0.971933 |
| loudness^2 | instrumentalness loudness^2 | 0.967090 |
| loudness^3 | instrumentalness loudness^2 | -0.975495 |

這三組相關屬於補充設定的多項式基底，不是原始資料欄位。程式：HW1_code_113062273.ipynb 最後一節。完整 25 組係數與誤差：q4_full_original_path.csv、q4_small_polynomial_path.csv；全部基底係數另見同名 coefficients.csv；摘要見 q4_summary.csv。
