# HW1：音樂資料分析

學號：113062273

## 2. 事前預期與結果

要求依據：HW1_Spec (1).pdf 第 4-5 頁；HW1_Intro.pdf 第 11 頁。

事前預期 energy 與 loudness 正相關、與 acousticness 負相關；接近零或方向相反就不支持預期。清理後的 Pearson r 分別為 0.7594、-0.7353，支持這項預期。

另一項預期是不同曲風有音訊差異，相近曲風的特徵較接近；分布接近或高度混合就不支持預期。acousticness、energy 的曲風間變異占比分別為 0.4883、0.4542，但曲風分群仍有包含 94 種曲風的大群。因此只有部分支持，不能說曲風能清楚分開。

## 3. 資料品質

要求依據：HW1_Spec (1).pdf 第 5-6 頁；HW1_Intro.pdf 第 12 頁。

只使用提供的 tracks.csv，共 114,000 列、20 欄。以下依對後續分析的影響排序。

| 優先序與問題 | 原始資料的證據 |
| --- | --- |
| 1. 重複歌曲 | 16,641 個 track_id 出現多次；450 列完全重複。 |
| 2. 同一 ID 的 popularity 不一致 | 720 個 ID 的 popularity 有衝突；檢查的音訊欄位沒有衝突。 |
| 3. 零 tempo、零拍號與不合法長度 | tempo <= 0 有 157 列、time_signature = 0 有 163 列、duration_ms <= 0 有 1 列；聯集共 164 列。 |
| 4. 曲風筆數規整與多重標籤 | 114 種曲風各有 1,000 列；同一 track_id 可出現在多種曲風。 |

**1. 重複歌曲。**同曲跨 train/test 可能低估誤差，重複列也會改變 PCA 與分群權重。先刪完全重複列，每個 ID 留一筆，曲風標籤另存。回歸將相同歌手／歌名或完整音訊與音樂屬性相同的歌曲放在同一錄音群組。取捨是改以歌曲而非配對列加權，群組規則也可能合併不同演奏版本。

**2. popularity 衝突。**任取一列會依賴檔案順序，取平均會改變目標定義。因此排除全部衝突 ID，共移除 1,928 筆當時仍有效的配對列。取捨是失去歌曲及可能真實的時間變化，也可能造成選擇偏差。

**3. 節奏與長度問題。**這些值無法直接當成正常節奏或長度，會影響特徵距離與模型。因此刪除，不任意補平均值。取捨是可能刪除非節拍音樂或偵測困難的歌曲。

**4. 曲風與多標籤。**曲風列數不能代表平台的自然曲風比例，多標籤也會重複加權歌曲。保留曲風做特徵比較，同曲在每種曲風只算一次；跨曲風統計讓每首歌的標籤權重合計為 1。缺少抽樣機率，無法修正母體比例，因此曲風比例及曲風間變異占比只作描述。

重複排在衝突之前，因為影響 16,641 首歌，且同時影響 PCA、分群與回歸評估；衝突影響 720 個 ID，主要影響目標可信度。

清理流程為 114,000 → 113,550 → 113,386 → 111,458 筆配對列，最後得到 88,858 個唯一 track_id。清理程式在 notebook。Sections 4-6 使用這 88,858 首歌曲，不使用原始重複列。

<!-- pagebreak -->

## 4. PCA

要求依據：HW1_Spec (1).pdf 第 6-7 頁；HW1_Intro.pdf 第 13-14 頁。

使用 danceability、energy、loudness、speechiness、acousticness、instrumentalness、liveness、valence、tempo 九項連續音訊特徵。key、mode、time_signature 是類別代碼，不直接當成距離座標。

### 4.1 有效維度

以累積解釋至少 90% 變異為標準。標準化 PCA 需要 7 個 PC，累積 94.86%；6 個只有 89.77%。

### 4.2 前幾個主成分

| PC | 解釋變異 | 主要權重與解讀 |
| --- | --- | --- |
| PC1 | 31.94% | loudness 0.516、energy 0.508、acousticness -0.438：高能量／較大聲與較原聲的差異。 |
| PC2 | 15.99% | danceability 0.566、valence 0.526、instrumentalness -0.314、tempo -0.280：可舞性及正向分數，與器樂、節奏分數的共同變動。 |
| PC3 | 13.93% | liveness 0.674、speechiness 0.643：現場感與口語相關分數的變動。 |

### 4.3 標準化的影響

未標準化時，PC1 解釋 97.13%，只需 1 個 PC 就達 90%；其 tempo 權重為 0.9992。

PCA 在 w 為單位向量時，最大化投影變異 w^T S w，S 是共變異矩陣。原尺度 tempo 的變異數為 882.4921，占總變異 96.99%，loudness 為 26.9388，因此 tempo 主導未標準化的結果。標準化後，各欄變異約為 1，主成分改由欄位間的關係決定。本次採標準化結果，避免單位大小主導分析。

## 5.1 曲風分群

要求依據：HW1_Spec (1).pdf 第 7 頁；HW1_Intro.pdf 第 15-16 頁。

每種曲風以九項音訊特徵平均作 profile，同曲在同曲風只算一次。用歌曲層級的平均、標準差轉換尺度，再做階層分群。比較 Euclidean、city-block 距離與 average、complete linkage；都切成 8 群以便比較。

| 距離／linkage | 共用 Euclidean 距離計算的 silhouette |
| --- | --- |
| Euclidean／average | 0.2634 |
| Euclidean／complete | 0.2079 |
| City-block／average | 0.2387 |
| City-block／complete | 0.2032 |

選 Euclidean／average，因為共用距離下的 silhouette 最高。black-metal、death-metal、grindcore 同群，平均 energy 0.910、acousticness 0.014；classical、ambient、opera 等另一群為 0.276、0.801，呈現可解釋的音訊差異。

改成 city-block／average，opera 移到 honky-tonk 等所在群；改成 Euclidean／complete，原本大群中的 metal、heavy-metal 與 pop、dance、house 等被分開。主要設定仍有包含 94 種曲風的大群，因此只作粗略分組。

<!-- pagebreak -->

## 5.2 歌曲分群

要求依據：HW1_Spec (1).pdf 第 7 頁；HW1_Intro.pdf 第 16 頁。

對全部 88,858 首歌曲的標準化九項音訊特徵做 k-means，使用 n_init = 10、seed = 113062273。inertia 使用全部資料；silhouette 使用同一批固定 seed 均勻抽出的 2,000 首，減少兩兩距離的計算成本。

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

## 5.3 分群是否有意義

要求依據：HW1_Spec (1).pdf 第 8 頁；HW1_Intro.pdf 第 16 頁。

**證據一：不同抽樣的穩定性。**另外均勻抽兩批各 20,000 首，分別重估標準化及 k-means，再對全部歌曲預測。與全資料分群相比，對齊群號後的分群改變比例為 0.27%、0.34%，ARI 為 0.9887、0.9855。這降低單次抽樣造成分群的疑慮。

**證據二：未使用曲風輸入，仍有可解釋的關聯。**每首歌的多曲風權重合計為 1。new-age、sleep 的加權標籤分別有 90.73%、96.16% 在低能量 Cluster 0；heavy-metal、drum-and-bass 分別有 98.11%、99.58% 在高能量 Cluster 1。各群最大單一曲風占比只有 3.79%、1.46%，並非只複製單一曲風。

兩項證據支持穩定且可解釋的音訊粗分，但連續梯度也可能被 k-means 切成群，不能據此證明有兩個天然音樂類別。

<!-- pagebreak -->

## 6. 回歸

要求依據：HW1_Spec (1).pdf 第 8-9 頁；HW1_Intro.pdf 第 17-18 頁。

相同錄音群組不跨集合。Train、validation、test 分別有 56,931、14,158、17,769 首。OLS 使用 Train 與 validation 合併的 development，共 71,089 首；baseline 也使用 development 的目標平均值。標準化及編碼只 fit 擬合模型用的訓練資料。

Q1、Q2 使用 danceability、speechiness、acousticness、instrumentalness、liveness、valence、loudness、tempo，以及 one-hot 的 key、mode、time_signature；預測 popularity 再加入 energy。target 本身不作輸入。

### 6.1 事前預測、實際結果與 baseline

要求依據：HW1_Spec (1).pdf 第 9 頁 Q1；HW1_Intro.pdf 第 18 頁。

| 項目 | Energy | Popularity |
| --- | --- | --- |
| 事前預測 RMSE | 0.1200 | 18.0000 |
| OLS test RMSE | 0.1223 | 20.2001 |
| 訓練平均值 baseline test RMSE | 0.2569 | 20.4984 |

energy 比事前預估高 0.0023，接近預期；popularity 高 2.2001，比預期難預測。誤差單位分別為 energy 的 0-1 分數、popularity 的 0-100 分數。

### 6.2 兩項任務的差異

要求依據：HW1_Spec (1).pdf 第 9 頁 Q2；HW1_Intro.pdf 第 18 頁。

相對各自 baseline，energy 的 RMSE 降低 52.39%，popularity 只降低 1.46%，所以 energy 較容易由這些音訊特徵線性預測。

development 中，energy 與 loudness、acousticness 的 Pearson r 為 0.7591、-0.7336；popularity 與兩者為 0.0756、-0.0393，與 energy 為 0.0145。這支持音訊對 energy 較有線性資訊。此結果只針對本次線性模型，不能推論所有模型都無法預測 popularity。

### 6.3 額外的預測資訊

要求依據：HW1_Spec (1).pdf 第 9 頁 Q3；HW1_Intro.pdf 第 18 頁。

選 artists。使用原始藝人字串 one-hot，少於 5 筆的類別合併；前處理只 fit development。兩個模型都使用 alpha = 10 的 Ridge，並在相同 test 比較。

| Test 子集合 | 歌曲數 | 僅音訊 RMSE | 加 artists RMSE |
| --- | --- | --- | --- |
| 全部 | 17,769 | 20.2002 | 17.8755 |
| development 見過相同藝人字串 | 12,668 | 19.9217 | 16.5363 |
| development 未見過相同藝人字串 | 5,101 | 20.8758 | 20.8323 |

整體 RMSE 降低 11.51%，支持 artists 包含額外資訊；改善主要來自已見過的藝人字串，不能推廣成對陌生藝人也有相同效果。

<!-- pagebreak -->

### 6.4 正則化

要求依據：HW1_Spec (1).pdf 第 9 頁 Q4；HW1_Intro.pdf 第 18 頁。

target 是 energy。完整資料設定使用 loudness、acousticness、instrumentalness。Train 中三組 Pearson r 為 -0.5832、-0.4347、0.0945，原始三欄不是彼此高度相關；允許的八個連續輸入中，最高 |r| 為 0.5832。

三欄標準化後 fit Ridge，alpha 從 10^-6 到 10^6，共 25 組。用 Train 擬合、validation RMSE 選 alpha，再用 development 重訓；test 不用來選 alpha。下表列出代表性的強度，係數對應標準化輸入。

| Alpha | loudness 係數 | acousticness 係數 | instrumentalness 係數 | Test RMSE |
| --- | --- | --- | --- | --- |
| 10^-6 | 0.143925 | -0.106258 | 0.027031 | 0.136381 |
| 1 | 0.143923 | -0.106258 | 0.027030 | 0.136381 |
| 100 | 0.143664 | -0.106247 | 0.026879 | 0.136380 |
| 10^4 | 0.123805 | -0.102507 | 0.015744 | 0.137908 |
| 10^6 | 0.012350 | -0.011959 | -0.002579 | 0.238385 |

同輸入 OLS 的 test RMSE 為 0.136381；validation 選出的 alpha = 100 為 0.136380，只改善約 0.00000093，沒有實質提升。正則化增強使整體係數收縮，但過強會提高誤差。

**高度相關與效果較清楚的設定。**從 Train 均勻抽 80 個不同錄音群組，各取一首，減少訓練樣本數。先標準化三欄，展開三次多項式得到 19 個基底，再標準化基底後 fit OLS／Ridge。validation、test 不加入這 80 首的訓練。

以 L、I 表示在這 80 首上標準化的 loudness、instrumentalness。僅用這 80 首計算，基底 L² 與 L³ 的 r 為 -0.9719、L² 與 L²I 為 0.9671、L³ 與 L²I 為 -0.9755，三者彼此高度相關，且包含在上述 19 個輸入中。下表係數為基底再次標準化後的係數。

| Alpha | L² 係數 | L³ 係數 | L²I 係數 | Test RMSE |
| --- | --- | --- | --- | --- |
| 10^-6 | 0.022413 | -0.448325 | -0.423591 | 0.181219 |
| 1 | 0.188368 | 0.016435 | -0.019882 | 0.161706 |
| 10 | 0.064717 | 0.001537 | 0.005048 | 0.143941 |
| 10^3 | -0.001374 | 0.002206 | -0.002262 | 0.218099 |
| 10^6 | -0.000006 | 0.000006 | -0.000007 | 0.256840 |

validation 選 alpha = 10。同設定 OLS test RMSE 為 0.181219，Ridge 為 0.143941，降低 20.57%。係數 L2 長度從 alpha = 10^-6 的 1.534435 降到 alpha = 10^6 的 0.000042；個別係數不一定單調。小樣本與較多基底下，適度收縮降低過擬合，過強又會失去訊號。## 結果對資料使用的意義

要求依據：HW1_Spec (1).pdf 第 1 頁。

清理後資料可用於音訊差異探索、歌曲粗分與 energy 線性預測。音訊對 popularity 的線性預測力弱，artists 的改善主要適用於已見藝人。重複、目標衝突與曲風配額限制資料可靠性及母體外推；資料也沒有 popularity 的計算公式與評分時間，無法判定跨時間預測的適用性。
