# HW1 AI-use log

- 學號：113062273
- 工具：OpenAI Codex（本次對話中的程式代理）
- 使用日期：2026-10-02（Asia/Taipei）
- 編碼：UTF-8

## AI 使用範圍與實際驗證

本紀錄由 Codex 依本次實際操作整理。以下的程式執行、數值核對與圖表檢查均由 Codex 完成；尚未收到學生自行檢查程式或完成 demo 練習的紀錄。

| 使用範圍 | AI 協助內容 | 本次已完成的驗證 |
| --- | --- | --- |
| 作業要求與既有 pre-report | 讀取 Intro、Spec 與原始 pre-report，建立 notebook 的實作範圍；保留 energy RMSE 0.12、popularity RMSE 18 的原始預測。 | 檢查 PDF 原頁面，避免中文抽取亂碼影響理解；核對允許的回歸輸入、繳交檔名、報告頁數與 AI 規則。沒有改寫 pre-report。 |
| 載入與資料稽核 | 使用 starter 指定的 tracks.csv 下載網址；檢查缺值、值域、完整重複列、重複 ID、衝突的 popularity、tempo／拍號為 0、曲風筆數和音樂類別碼。 | 確認原資料為 114,000 列、20 欄；計算 SHA-256；保存各項證據表、清理流程筆數及衝突範例。原始 CSV 保持不變。 |
| 清理與切分 | 移除完全重複列、不合法／未偵測的 tempo 或拍號及音訊／目標衝突 ID；每個 track_id 留一筆並另保留所有 genre memberships。使用歌手／歌名和完整音訊屬性相同的紀錄建立錄音群組。 | 清理後共有 88,858 個唯一 track_id。程式斷言唯一性、數值完整及曲風 membership 一致；另從原始資料獨立核對，確認相同正規化歌手／歌名和相同完整音訊向量都未跨越 train、validation、test。 |
| PCA | 對九項連續音訊特徵分別執行標準化與未標準化 PCA；輸出累積解釋變異、loadings、各特徵變異和投影變異。 | 直接使用經驗共變異矩陣的 eigenvalues 獨立重算兩組 explained variance ratios，與 PCA 結果比對；核對第一主成分投影變異與最大 eigenvalue 相等。 |
| 曲風與歌曲分群 | 建立曲風平均音訊 profile；比較 Euclidean／city-block 和 average／complete 的四種組合。對 k=2 至 10 擬合 k-means，計算 inertia 和固定 2,000 筆樣本的 silhouette；檢查重抽樣及 listing 權重的敏感度。 | 所有隨機程序使用學號 seed 或由該 seed 初始化的亂數產生器。保存 ARI、配對後變動比例、cluster 特徵平均與 PCA 投影圖；逐一檢查圖表文字與標籤。 |
| Energy／popularity 回歸 | 只使用規格允許的音訊特徵，目標自身不作輸入；key、mode、time_signature 使用 one-hot encoding。比較 OLS 與訓練平均值 baseline；另外僅在 Q3 加入 artists 欄位。 | 所有 scaler／encoder 只在對應訓練資料上 fit。另以 NumPy least squares 與直接平均值公式獨立重算 test RMSE，與 notebook 在 1e-10 容許誤差內一致；分開檢查 seen／unseen artist 結果。 |
| 正則化 | 對 energy 使用 loudness、acousticness、instrumentalness，比較 alpha=1e-6 至 1e6 的係數與 RMSE；建立 80 個訓練錄音群組、三次多項式的額外設定，補查基底之間的相關。 | 先檢查 training-only 相關矩陣；alpha 由 validation RMSE 選擇，test 曲線只用於描述。核對係數 L2 norm 隨 alpha 增加而下降；小樣本三次多項式共有 19 項 basis features，OLS 與 Ridge 使用相同的 80 筆訓練資料。額外以原本保存的 80 個訓練 ID 重建標準化及多項式基底，確認三個基底的配對相關絕對值皆大於 0.95，並核對 OLS／Ridge 的訓練誤差；模型、樣本與選定 alpha 均未改動。 |
| Notebook 與結果輸出 | 寫入可獨立執行的 notebook、圖表、CSV 證據及重現資訊。 | 最終 16 個 code cells 已在全新 kernel 由頭執行到底，全部完成且無 error outputs；以 nbformat 驗證格式。將 OLS、artists、Ridge、PCA、k 選擇、分群穩定性及基底相關的七份關鍵 CSV 與重跑前比較，在 1e-10 容許誤差內一致。原有 7 張圖皆經視覺檢查。 |

## 開發過程的修正

- PDF 中文文字抽取出現亂碼，改以原頁面渲染確認 pre-report；文字檔使用 UTF-8。
- 錄音群組程式將 filtered DataFrame 的 GroupBy positions 對應回原始 row indices，避免誤配不同歌曲。
- 初版小樣本試驗使用六次多項式，產生 83 個 basis features，超過 80 筆訓練資料且 OLS 外推極不穩定。- 回歸 hexbin 色條改為「Count (log scale)」，符合實際採用的對數色階。

## 檢查結果與可重現性

- 原始資料 SHA-256：`db8cd3670209db33285dbfa7ad08dc05446219e9c430e7750abfd17e99297c42`。
- 最終 OLS test RMSE：energy `0.1222879145`；popularity `20.2001495316`。
- 同一 test set 的訓練平均值 baseline RMSE：energy `0.2568802252`；popularity `20.4984277200`。
- Notebook 包含固定 seed、套件版本、原始資料下載程式、清理程式及全部分析程式。CSV／PNG 可重新產生。
- `reproducibility.json` 保存資料雜湊、版本、切分大小及參數；`verification.json` 保存獨立數值核對的結果。

## 學生仍需自行完成

- 親自閱讀、執行並理解 notebook，能說明清理取捨、分群限制、群組切分及正則化；demo 需要能解釋或修改程式。
- 確認 pre-report 的實際提交時間與 eeclass 的繳交紀錄；本次沒有操作 eeclass。
- 若之後另外使用 AI 或完成自己的人工驗證，依實際情況更新本紀錄，勿將代理的自動檢查記作已完成的人工檢查。
