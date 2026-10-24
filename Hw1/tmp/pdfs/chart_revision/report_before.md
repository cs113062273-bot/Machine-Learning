# HW1：音樂資料分析

學號：113062273

## 1. Auditing the Dataset

### 1.1 Identify and prioritize at least four data-quality findings, ordered from most to least important based on how strongly you believe each one could affect the analyses or models in this assignment.

要求依據：HW1_Spec (1).pdf 第 5-6 頁，Section 3 Q1。

> For each finding, include: a. Evidence: one number, table, or figure showing that the issue is present. b. Why it matters: explain how the issue could affect a later analysis or model. c. Your decision: state what you will do about it. d. Trade-off: explain what information, data, or reliability you may lose because of that decision.

以下依對後續分析的影響排序。

| 優先序與問題| 原始資料的證據 |
| --- | --- |
| 1. 重複歌曲 | 16,641 個 track_id 出現多次；450 列完全重複。 |
| 2. 同一 ID 的 popularity 不一致 | 720 個 ID 的 popularity 有衝突；檢查的音訊欄位沒有衝突。 |
| 3. 零 tempo、零拍號與不合法長度 | tempo <= 0 有 157 列、time_signature = 0 有 163 列、duration_ms <= 0 有 1 列；聯集共 164 列。 |
| 4. 曲風筆數規整與多重標籤 | 114 種曲風各有 1,000 列；同一 track_id 可出現在多種曲風。 |

**1. 重複歌曲。**同曲跨 train/test 可能低估誤差，重複列也會改變 PCA 與分群權重。先刪完全重複列，每個 ID 留一筆，曲風標籤另存。回歸將相同歌手／歌名或完整音訊與音樂屬性相同的歌曲放在同一錄音群組。取捨是改以歌曲而非配對列加權，群組規則也可能合併不同演奏版本。

**2. popularity 衝突。**任取一列會依賴檔案順序，取平均會改變目標定義。因此排除全部衝突 ID，共移除 1,928 筆當時仍有效的配對列。取捨是失去歌曲及可能真實的時間變化，也可能造成選擇偏差。

**3. 節奏與長度問題。**這些值無法直接當成正常節奏或長度，會影響特徵距離與模型。因此刪除，不任意補平均值。取捨是可能刪除非節拍音樂或偵測困難的歌曲。

**4. 曲風與多標籤。**曲風列數不能代表平台的自然曲風比例，多標籤也會重複加權歌曲。保留曲風做特徵比較，同曲在每種曲風只算一次；第 3.3 節曲風與分群的交叉統計，讓每首歌的標籤權重合計為 1。缺少抽樣機率，無法修正母體比例，因此曲風比例及曲風間變異占比只作描述。

### 1.2 Justify your ranking.

要求依據：HW1_Spec (1).pdf 第 6 頁，Section 3 Q2。

> Explain why you ranked your first finding as more important than your second.

重複排在衝突之前，因為影響 16,641 首歌，且同時影響 PCA、分群與回歸評估；衝突影響 720 個 ID，主要影響目標可信度。

### 1.3 Apply your cleaning decisions.

要求依據：HW1_Spec (1).pdf 第 6 頁，Section 3 Q3。

> In your submitted notebook, include the code that transforms the raw dataset into the cleaned dataset used in your analysis. The code should be reproducible from the original tracks.csv dataset.

清理流程為 114,000 → 113,550 → 113,386 → 111,458 筆配對列，最後得到 88,858 個唯一 track_id。程式已實作於 HW1_code_113062273.ipynb，可由原始 tracks.csv 重現。本報告 PCA、分群與回歸的結果均使用清理後的唯一歌曲；曲風分析另外保留歌曲與曲風的對應。

## 2. The Geometry of the Feature Space

要求依據：HW1_Spec (1).pdf 第 6-7 頁，Section 4。

使用 danceability、energy、loudness、speechiness、acousticness、instrumentalness、liveness、valence、tempo 九項連續音訊特徵。key、mode、time_signature 是類別代碼，不直接當成距離座標。

### 2.1 Effective dimensionality.

要求依據：HW1_Spec (1).pdf 第 6 頁，Section 4 Q1。

> Use PCA to estimate how many principal components are needed to represent most of the variation in the audio features. Clearly state the criterion or metrics you use to decide how many components are sufficient.

以累積解釋至少 90% 變異為標準。標準化 PCA 需要 7 個 PC，累積 94.86%；6 個只有 89.77%。

### 2.2 Interpret the leading principal components.

要求依據：HW1_Spec (1).pdf 第 7 頁，Section 4 Q2。

> For the first few principal components, explain in plain language what kind of variation each component appears to capture.

| PC| 解釋變異 | 主要權重與解讀 |
| --- | --- | --- |
| PC1 | 31.94% | loudness 0.516、energy 0.508、acousticness -0.438：高能量／較大聲與較原聲的差異。 |
| PC2 | 15.99% | danceability 0.566、valence 0.526、instrumentalness -0.314、tempo -0.280：可舞性及正向分數，與器樂、節奏分數的共同變動。 |
| PC3 | 13.93% | liveness 0.674、speechiness 0.643：現場感與口語相關分數的變動。 |

### 2.3 Effect of standardization.

要求依據：HW1_Spec (1).pdf 第 7 頁，Section 4 Q3。

> Repeat the PCA without standardizing the features first. Compare the result with the standardized PCA and explain why they differ. Your explanation should refer to the quantity that PCA maximizes. Support your explanation with either: a. A short mathematical derivation. b. A variance calculation using your own data.

未標準化時，PC1 解釋 97.13%，只需 1 個 PC 就達 90%；其 tempo 權重為 0.9992。

PCA 在 w 為單位向量時，最大化投影變異 w^T S w，S 是共變異矩陣。原尺度 tempo 的變異數為 882.4921，占總變異 96.99%，loudness 為 26.9388，因此 tempo 主導未標準化的結果。標準化後，各欄變異約為 1，主成分改由欄位間的關係決定。本次採標準化結果，避免單位大小主導分析。

## 3. Structure in the Data

### 3.1 Clustering genres.

要求依據：HW1_Spec (1).pdf 第 7 頁，Section 5 Q1。

> Create one representative audio-feature profile for each genre, and use hierarchical clustering to group similar genres together. Show how the resulting genre groupings differ, and explain which result you find more reasonable based on evidence from the data. Compare: a. Two different measures of dissimilarity. b. Two different linkage methods.

每種曲風以九項音訊特徵平均作 profile，同曲在同曲風只算一次。用歌曲層級的平均、標準差轉換尺度，再做階層分群。比較 Euclidean、city-block 距離與 average、complete linkage；都切成 8 群以便比較。

| 距離／linkage | 共用 Euclidean 距離計算的 silhouette |
| --- | --- |
| Euclidean／average | 0.2634 |
| Euclidean／complete | 0.2079 |
| City-block／average | 0.2387 |
| City-block／complete | 0.2032 |

選 Euclidean／average，因為共用距離下的 silhouette 最高。black-metal、death-metal、grindcore 同群，平均 energy 0.910、acousticness 0.014；classical、ambient、opera 等另一群為 0.276、0.801，呈現可解釋的音訊差異。

改成 city-block／average，opera 移到 honky-tonk 等所在群；改成 Euclidean／complete，原本大群中的 metal、heavy-metal 與 pop、dance、house 等被分開。主要設定仍有包含 94 種曲風的大群，因此只作粗略分組。事前預期不同曲風有音訊差異、相近曲風的特徵較接近；上述特徵差異支持前者，但大群仍高度混合，只能部分支持整體預期。（事前預期比較依據：HW1_Spec (1).pdf 第 5 頁。）

### 3.2 Clustering individual tracks.

要求依據：HW1_Spec (1).pdf 第 7 頁，Section 5 Q2。

> Using the standardized audio features, cluster the individual tracks (e.g. with k-means). To choose the number of clusters k, compute at least two quantitative criteria (e.g. the elbow of the inertia curve and the silhouette score) over a range of k, show them, and explain your final choice. Then describe what each resulting cluster represents in terms of its audio characteristics (e.g. by reporting the mean of each feature per cluster). Some clustering methods or criteria may be expensive to run on all 114,000 rows. If you use a subset of the data for clustering or evaluation, clearly state how the subset was selected and why.

對全部 88,858首歌曲的標準化九項音訊特徵做 k-means，使用 n_init = 10、seed = 113062273。inertia 使用全部資料；silhouette 使用同一批固定 seed 均勻抽出的 2,000 首，減少兩兩距離的計算成本。

| k | Inertia | Silhouette |
| --- | --- | --- |
| 2 | 627,300.1 | 0.2633 |
| 3 | 556,338.6 | 0.1697 |
| 4 | 501,470.8 | 0.1782 |
| 5 | 451,775.5 | 0.1814 |
| 6 | 410,514.9 | 0.1974 |
| 7 | 373,493.2 | 0.2061 |
| 8 | 352,584.2 | 0.1847 |
| 9 | 334,358.6 | 0.1854 |
| 10 | 320,584.2 | 0.1743 |

inertia 持續下降，沒有唯一明顯轉折；k = 7 後降幅縮小，但 silhouette 在 k = 2 最高。因此選 k = 2，作為較容易解釋的粗分。

| 特徵平均 | Cluster 0：22,301 首 | Cluster 1：66,557 首 |
| --- | --- | --- |
| danceability | 0.4635 | 0.5961 |
| energy | 0.2988 | 0.7476 |
| loudness | -14.4880 | -6.4712 |
| speechiness | 0.0594 | 0.0972 |
| acousticness | 0.7500 | 0.1874 |
| instrumentalness | 0.3251 | 0.1222 |
| liveness | 0.1795 | 0.2288 |
| valence | 0.3093 | 0.5238 |
| tempo | 110.2413 | 126.2822 |

Cluster 0 平均較安靜、低能量，原聲及器樂分數較高；Cluster 1 的能量、音量、可舞性、valence 與 tempo 較高。這是群平均，不表示每首歌曲都符合描述。

### 3.3 Are the clusters meaningful?

要求依據：HW1_Spec (1).pdf 第 8 頁，Section 5 Q3。

> A clustering algorithm always returns k clusters, even on data with no real structure. Provide evidence that the clusters you found in Question 2 reflect real differences between tracks, rather than being an artifact of the algorithm, the sampling, or the way genres were assigned. Provide at least two evidence. For example: a. Plot the clusters in the space of the first two principal components and explain whether the cluster boundaries align with the directions of variation you interpreted there. b. Stability. Re-run the clustering with a different random seed, a different subsample, or after applying your cleaning decisions from Section 3, and report how much the cluster assignments change.

**證據一：不同抽樣的穩定性。**另外均勻抽兩批各 20,000 首，分別重估標準化及 k-means，再對全部歌曲預測。與全資料分群相比，對齊群號後的分群改變比例為 0.27%、0.34%，ARI 為 0.9887、0.9855。這降低單次抽樣造成分群的疑慮。

**證據二：未使用曲風輸入，仍有可解釋的關聯。**每首歌的多曲風權重合計為 1。new-age、sleep 的加權標籤分別有 90.73%、96.16% 在低能量 Cluster 0；heavy-metal、drum-and-bass 分別有 98.11%、99.58% 在高能量 Cluster 1。各群最大單一曲風占比只有 3.79%、1.46%，並非只複製單一曲風。

兩項證據支持穩定且可解釋的音訊粗分，但連續梯度也可能被 k-means 切成群，不能據此證明有兩個天然音樂類別。

## 4. Two Regression Targets

要求依據：HW1_Spec (1).pdf 第 8 頁，Section 6。

相同錄音群組不跨集合。Train、validation、test 分別有 56,931、14,158、17,769 首。OLS 使用 Train 與 validation 合併的 development，共 71,089 首；baseline 也使用 development 的目標平均值。標準化及編碼只 fit 擬合模型用的訓練資料。

Q1、Q2 使用 danceability、speechiness、acousticness、instrumentalness、liveness、valence、loudness、tempo，以及 one-hot 的 key、mode、time_signature；預測 popularity 再加入 energy。target 本身不作輸入。

### 4.1 Compare your predictions with the actual results.

要求依據：HW1_Spec (1).pdf 第 9 頁，Section 6 Q1。

> Restate the RMSE values you predicted in Section 2. Then fit a linear regression model for each target and report its held-out RMSE. For each target, also report the RMSE of a simple baseline model that ignores the input features and always predicts the mean target value from the training set.

事前 RMSE 數值取自已完成的 HW1_pre_report_113062273.pdf 第 1 頁。

| 項目 | Energy| Popularity |
| --- | --- | --- |
| 事前預測 RMSE | 0.1200 | 18.0000 |
| OLS test RMSE | 0.1223 | 20.2001 |
| 訓練平均值 baseline test RMSE | 0.2569 | 20.4984 |

energy 比事前預估高 0.0023，接近預期；popularity 高 2.2001，比預期難預測。誤差單位分別為 energy 的 0-1 分數、popularity 的 0-100 分數。

### 4.2 Explain the difference in predictive performance.

要求依據：HW1_Spec (1).pdf 第 9 頁，Section 6 Q2。

> Compare the two regression tasks and explain why one target is easier or harder to predict from the available features. Support your explanation with evidence from this dataset, such as relationships between the target and the input features, rather than only making a general statement such as “the data are noisy.”

相對各自 baseline，energy 的 RMSE 降低 52.39%，popularity 只降低 1.46%，所以 energy 較容易由這些音訊特徵線性預測。

development 中，energy 與 loudness、acousticness 的 Pearson r 為 0.7591、-0.7336；popularity 與兩者為 0.0756、-0.0393，與 energy 為 0.0145。這支持音訊對 energy 較有線性資訊。此結果只針對本次線性模型，不能推論所有模型都無法預測 popularity。

energy 與 loudness 正相關、與 acousticness 負相關的方向，支持 pre-report 的第一項預期。（事前預期比較依據：HW1_Spec (1).pdf 第 5 頁。）

### 4.3 Look for additional predictive information.

要求依據：HW1_Spec (1).pdf 第 9 頁，Section 6 Q3。

> If one target is difficult to predict from the audio features, look for one other variable in the dataset that may contain useful information about that target. For example, pick one non-audio column in tracks.csv that you think carries information about the target. Support your choice with an appropriate measurement or plot.

選 artists。使用原始藝人字串 one-hot，少於 5 筆的類別合併；前處理只 fit development。兩個模型都使用 alpha = 10 的 Ridge，並在相同 test 比較。

| Test 子集合 | 歌曲數 | 僅音訊 RMSE | 加 artists RMSE |
| --- | --- | --- | --- |
| 全部 | 17,769 | 20.2002 | 17.8755 |
| development 見過相同藝人字串 | 12,668 | 19.9217 | 16.5363 |
| development 未見過相同藝人字串 | 5,101 | 20.8758 | 20.8323 |

整體 RMSE 降低 11.51%，支持 artists 包含額外資訊；改善主要來自已見過的藝人字串，不能推廣成對陌生藝人也有相同效果。

### 4.4 Study the effect of regularization.

要求依據：HW1_Spec (1).pdf 第 9 頁，Section 6 Q4。

> Use energy as the target for this question. Identify several input features that are strongly correlated with one another. Standardize these features, then fit a regularized linear regression model using these features, and vary the regularization strength over several orders of magnitude. Report how the coefficients and held-out RMSE change as regularization becomes stronger. If regularization does not improve held-out performance on the full dataset, say so. Then create a setting in which regularization has a clearer effect, for example by using a smaller training set, a richer set of basis functions (such as polynomial features), or both.

target 是 energy，不包含在輸入。**原始欄位稽核與完整資料實驗。**只用 Train 檢查八個允許的連續輸入，最高 |Pearson r| 為 0.5832（acousticness 與 loudness）。列舉全部 56 組三欄組合，選擇「三組 |r| 中最小值」最大的組合，得到 instrumentalness、valence、loudness；三組 r 分別為 -0.3290、-0.4347、0.2837。這個原始子集的相關仍有限，不能稱為彼此高度相關。完整資料先使用此子集觀察正則化，補充設定再使用高度相關基底；兩種輸入分開報告。

三欄標準化後 fit OLS／Ridge，前處理只 fit 訓練資料。alpha 為 10^-6 至 10^6，共 25 組；先用 Train 擬合，依 validation RMSE 選 alpha，再用 development 重訓。下表係數對應標準化原始輸入，test 不用來選 alpha。

| Alpha | instrumentalness 係數 | valence 係數 | loudness 係數 | Test RMSE |
| --- | --- | --- | --- | --- |
| 10^-6 | 0.053301 | 0.021675 | 0.211199 | 0.159787 |
| 100 | 0.053051 | 0.021676 | 0.210794 | 0.159784 |
| 10^4 | 0.034047 | 0.021644 | 0.177846 | 0.162445 |
| 10^6 | -0.002557 | 0.003905 | 0.012740 | 0.245810 |

完整資料 validation 選 alpha = 10^-6。相同三欄的 OLS 與 Ridge test RMSE 均為 0.159787，差約 3.3e-14，沒有實質改善。alpha 增強時，整體係數長度縮小，但個別係數不一定單調，instrumentalness 也會變號；過強的正則化使 test RMSE 上升。

**高度相關基底與小樣本實驗。**依本題第二段的小樣本、多項式設定，從 Train 以固定 seed 均勻抽 80 個不同錄音群組，各取一首。使用同樣三個原始欄位，先標準化，展開三次多項式為 19 個基底，再逐基底標準化。每次前處理與模型都只 fit 這 80 首；validation、test 不加入訓練，alpha 依 validation 選擇。

令 L、I 為這 80 首上標準化的 loudness、instrumentalness。基底 L²、L³、L²I 的三組 Pearson r 為 -0.9719、0.9671、-0.9755，彼此高度相關，且都包含在模型輸入中。下表係數對應再次標準化的基底；L2 長度計算全部 19 個係數。

| Alpha | L² 係數 | L³ 係數 | L²I 係數 | 係數 L2 長度 | Test RMSE |
| --- | --- | --- | --- | --- | --- |
| 10^-6 | 0.032489 | 0.269261 | -0.026660 | 1.242279 | 0.224119 |
| 3.16228 | 0.047479 | 0.020729 | -0.043697 | 0.360136 | 0.174244 |
| 10^3 | -0.002536 | 0.003223 | -0.003521 | 0.015745 | 0.240868 |
| 10^6 | -0.000006 | 0.000006 | -0.000007 | 0.000026 | 0.256886 |

小樣本 validation 選 alpha = 3.162278。相同 80 首與基底的 OLS test RMSE 為 0.224119，Ridge 為 0.174244，降低 22.25%；訓練 RMSE 從 0.135556 升至 0.152454。這符合適度收縮抑制過擬合的現象，但過強會失去訊號。此設定只有一批小樣本；高度相關的結論適用於基底，不適用於原始三欄。

清理後資料可用於音訊探索、歌曲粗分與 energy 線性預測。音訊對 popularity 的線性預測力弱，artists 的改善主要限於已見藝人。重複、目標衝突、曲風配額及未知評分公式與時間，限制資料可靠性、母體及跨時間外推。（HW1_Spec (1).pdf 第 1 頁。）
