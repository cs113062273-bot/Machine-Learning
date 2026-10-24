# HW1 作答架構（待自行撰寫）

學號：113062273

## 1. Auditing the Dataset

### 1.1 Identify and prioritize at least four data-quality findings, ordered from most to least important based on how strongly you believe each one could affect the analyses or models in this assignment.

要求依據：HW1_Spec (1).pdf 第 5-6 頁，Section 3 Q1。

> For each finding, include: a. Evidence: one number, table, or figure showing that the issue is present. b. Why it matters: explain how the issue could affect a later analysis or model. c. Your decision: state what you will do about it. d. Trade-off: explain what information, data, or reliability you may lose because of that decision.

你的答案：

________________________________________

________________________________________

### 1.2 Justify your ranking.

要求依據：HW1_Spec (1).pdf 第 6 頁，Section 3 Q2。

> Explain why you ranked your first finding as more important than your second.

你的答案：

________________________________________

________________________________________

### 1.3 Apply your cleaning decisions.

要求依據：HW1_Spec (1).pdf 第 6 頁，Section 3 Q3。

> In your submitted notebook, include the code that transforms the raw dataset into the cleaned dataset used in your analysis. The code should be reproducible from the original tracks.csv dataset.

你的答案：

________________________________________

________________________________________

## 2. The Geometry of the Feature Space

### 2.1 Effective dimensionality.

要求依據：HW1_Spec (1).pdf 第 6 頁，Section 4 Q1。

> Use PCA to estimate how many principal components are needed to represent most of the variation in the audio features. Clearly state the criterion or metrics you use to decide how many components are sufficient.

你的答案：

________________________________________

________________________________________

### 2.2 Interpret the leading principal components.

要求依據：HW1_Spec (1).pdf 第 7 頁，Section 4 Q2。

> For the first few principal components, explain in plain language what kind of variation each component appears to capture.

你的答案：

________________________________________

________________________________________

### 2.3 Effect of standardization.

要求依據：HW1_Spec (1).pdf 第 7 頁，Section 4 Q3。

> Repeat the PCA without standardizing the features first. Compare the result with the standardized PCA and explain why they differ. Your explanation should refer to the quantity that PCA maximizes. Support your explanation with either: a. A short mathematical derivation. b. A variance calculation using your own data.

你的答案：

________________________________________

________________________________________

## 3. Structure in the Data

### 3.1 Clustering genres.

要求依據：HW1_Spec (1).pdf 第 7 頁，Section 5 Q1。

> Create one representative audio-feature profile for each genre, and use hierarchical clustering to group similar genres together. Show how the resulting genre groupings differ, and explain which result you find more reasonable based on evidence from the data. Compare: a. Two different measures of dissimilarity. b. Two different linkage methods.

你的答案：

________________________________________

________________________________________

### 3.2 Clustering individual tracks.

要求依據：HW1_Spec (1).pdf 第 7 頁，Section 5 Q2。

> Using the standardized audio features, cluster the individual tracks (e.g. with k-means). To choose the number of clusters k, compute at least two quantitative criteria (e.g. the elbow of the inertia curve and the silhouette score) over a range of k, show them, and explain your final choice. Then describe what each resulting cluster represents in terms of its audio characteristics (e.g. by reporting the mean of each feature per cluster). Some clustering methods or criteria may be expensive to run on all 114,000 rows. If you use a subset of the data for clustering or evaluation, clearly state how the subset was selected and why.

你的答案：

________________________________________

________________________________________

### 3.3 Are the clusters meaningful?

要求依據：HW1_Spec (1).pdf 第 8 頁，Section 5 Q3。

> A clustering algorithm always returns k clusters, even on data with no real structure. Provide evidence that the clusters you found in Question 2 reflect real differences between tracks, rather than being an artifact of the algorithm, the sampling, or the way genres were assigned. Provide at least two evidence. For example: a. Plot the clusters in the space of the first two principal components and explain whether the cluster boundaries align with the directions of variation you interpreted there. b. Stability. Re-run the clustering with a different random seed, a different subsample, or after applying your cleaning decisions from Section 3, and report how much the cluster assignments change.

你的答案：

________________________________________

________________________________________

## 4. Two Regression Targets

### 4.1 Compare your predictions with the actual results.

要求依據：HW1_Spec (1).pdf 第 9 頁，Section 6 Q1。

> Restate the RMSE values you predicted in Section 2. Then fit a linear regression model for each target and report its held-out RMSE. For each target, also report the RMSE of a simple baseline model that ignores the input features and always predicts the mean target value from the training set.

你的答案：

________________________________________

________________________________________

### 4.2 Explain the difference in predictive performance.

要求依據：HW1_Spec (1).pdf 第 9 頁，Section 6 Q2。

> Compare the two regression tasks and explain why one target is easier or harder to predict from the available features. Support your explanation with evidence from this dataset, such as relationships between the target and the input features, rather than only making a general statement such as “the data are noisy.”

你的答案：

________________________________________

________________________________________

### 4.3 Look for additional predictive information.

要求依據：HW1_Spec (1).pdf 第 9 頁，Section 6 Q3。

> If one target is difficult to predict from the audio features, look for one other variable in the dataset that may contain useful information about that target. For example, pick one non-audio column in tracks.csv that you think carries information about the target. Support your choice with an appropriate measurement or plot.

你的答案：

________________________________________

________________________________________

### 4.4 Study the effect of regularization.

要求依據：HW1_Spec (1).pdf 第 9 頁，Section 6 Q4。

> Use energy as the target for this question. Identify several input features that are strongly correlated with one another. Standardize these features, then fit a regularized linear regression model using these features, and vary the regularization strength over several orders of magnitude. Report how the coefficients and held-out RMSE change as regularization becomes stronger. If regularization does not improve held-out performance on the full dataset, say so. Then create a setting in which regularization has a clearer effect, for example by using a smaller training set, a richer set of basis functions (such as polynomial features), or both.

你的答案：

________________________________________

________________________________________

事前預期與發現的比較，放入相關分析的答案；要求見 Spec 第 5 頁。整體資料應用的優點與限制，放入最後的結論；要求見 Spec 第 1 頁。
