# COMPREHENSIVE EDA REPORT - CHURN PREDICTION DATASET

## 1. EXECUTIVE SUMMARY
- **Dataset Dimensions**: 505 rows × 12 columns with 100% completeness after cleaning
- **Target Variable**: `churned` (binary classification) - 24.4% churn rate (382 retained, 123 churned)
- **Missing Values**: 144 values (2.38% of dataset) across 6 columns successfully imputed using auto-strategy
- **Key Correlation Identified**: annual_income vs credit_score (r=0.88, p<0.001)
- **Recommended Model**: RandomForest classifier due to mixed data types and interpretability requirements
- **Critical Data Quality Issues**: 10 invalid negative age values remain (-3.90 min), 5 duplicate rows detected

## 2. DATASET OVERVIEW

**Memory Usage**: 0.15 MB

**Column Type Distribution**:
- Numeric: 8 columns (customer_id, age, annual_income, credit_score, total_spent, avg_order_value, purchase_frequency, churned)
- Categorical: 3 columns (gender, region, membership_tier)
- Datetime: 1 column (signup_date - requires conversion)

**Structure**: 505 rows × 12 columns (0 rows dropped during cleaning)

**List of Columns**:
- customer_id (INT64)
- age (FLOAT64)
- gender (OBJECT)
- region (OBJECT)
- annual_income (FLOAT64)
- credit_score (FLOAT64)
- total_spent (FLOAT64)
- avg_order_value (FLOAT64)
- purchase_frequency (FLOAT64)
- membership_tier (OBJECT)
- churned (INT64 - Target)
- signup_date (OBJECT)

## 3. DATA QUALITY & CLEANING

**Quality Flags Detected**:
- HIGH_MISSING: 6 columns with 4.95% missing values each
- OUTLIERS_DETECTED: 6 numeric columns identified via IQR method
- INVALID_VALUES: Negative age values (-3.90) and age > 100

**Imputation Methods Applied**:
- **age**: 19 missing values imputed using mean (35.89)
- **annual_income**: 25 missing values imputed using mean (42,217.67)
- **credit_score**: 25 missing values imputed using mean (586.31)
- **total_spent**: 25 missing values imputed using mean (9,218.32)
- **avg_order_value**: 25 missing values imputed using mean (1,040.85)
- **membership_tier**: 25 missing values imputed using mode (Silver)

**Outlier Detection (IQR Method)**:
| Column | Outliers Detected | % of Dataset | Range Identified |
|--------|-------------------|--------------|------------------|
| age | 10 | 2.06% | -3.90 to 112.0 |
| annual_income | 19 | 3.96% | 93,076.86 to 208,551.00 |
| total_spent | 17 | 3.54% | 24,123.62 to 50,753.27 |
| avg_order_value | 51 | 10.62% | 2,366.06 to 16,984.41 |
| purchase_frequency | 18 | 3.56% | 15.06 to 26.99 |
| churned | 123 | 24.36% | Single value 1.0 |

## 4. DECISION AUDIT TRAIL

| Column | Operation | Method | Affected Rows | Rationale |
|--------|-----------|--------|---------------|-----------|
| age | Impute missing | Mean (35.89) | 19 | Auto-strategy for numeric, preserves central tendency |
| annual_income | Impute missing | Mean (42,217.67) | 25 | Auto-strategy for numeric, maintains distribution shape |
| credit_score | Impute missing | Mean (586.31) | 25 | Auto-strategy for numeric, preserves variance |
| total_spent | Impute missing | Mean (9,218.32) | 25 | Auto-strategy for numeric, maintains spending pattern |
| avg_order_value | Impute missing | Mean (1,040.85) | 25 | Auto-strategy for numeric, preserves order value distribution |
| membership_tier | Impute missing | Mode (Silver) | 25 | Auto-strategy for categorical, maintains dominant category |
| Multiple | Detect outliers | IQR method | 241 total | Identify values beyond 1.5×IQR for future treatment |

## 5. CLEANING IMPACT ANALYSIS

**Before Cleaning State**:
- Overall Completeness: 97.62%
- Total Missing Values: 144
- Rows: 505, Columns: 12

**After Cleaning State**:
- Overall Completeness: 100%
- Total Missing Values: 0
- Rows: 505, Columns: 12 (no data loss)

**Column-Specific Impact**:
- **age**: Mean 35.89→35.89 (preserved), Missing 19→0, Std 13.91→13.65 (slight reduction)
- **annual_income**: Mean 42,217.67→42,217.67 (preserved), Missing 25→0, Std 23,286.66→22,701.77 (slight reduction)
- **credit_score**: Mean 586.31→586.31 (preserved), Missing 25→0, Std 134.59→131.20 (slight reduction)
- **total_spent**: Mean 9,218.32→9,218.32 (preserved), Missing 25→0, Std 6,895.13→6,721.94 (slight reduction)
- **avg_order_value**: Mean 1,040.85→1,040.85 (preserved), Missing 25→0, Std 1,742.94→1,699.16 (slight reduction)
- **membership_tier**: Mode Silver preserved, Missing 25→0, Distribution balanced

**Validation**: All mean values preserved; variance reduced slightly due to imputation (expected behavior)

**Referenced Charts**: charts/impact_age.png, charts/impact_annual_income.png, charts/impact_credit_score.png

## 6. STATISTICAL ANALYSIS

**Normality Test Results (Shapiro-Wilk, α=0.05)**:
| Column | Statistic | p-value | Null Hypothesis |
|--------|-----------|---------|-----------------|
| customer_id | 0.9549 | <0.001 | Rejected |
| age | 0.9081 | <0.001 | Rejected |
| annual_income | 0.8610 | <0.001 | Rejected |
| credit_score | 0.9598 | <0.001 | Rejected |
| total_spent | 0.8456 | <0.001 | Rejected |
| avg_order_value | 0.4735 | <0.001 | Rejected |
| purchase_frequency | 0.8399 | <0.001 | Rejected |
| churned | 0.5329 | <0.001 | Rejected |

**Interpretation**: ALL numeric columns significantly deviate from normal distribution (p<0.001). avg_order_value shows strongest deviation (W=0.4735). Non-parametric methods or transformation required.

**Correlation Analysis (Pearson)**:
- **annual_income vs credit_score**: r=0.88, p<0.001 (strong positive correlation)
- **annual_income vs total_spent**: r=0.71, p<0.001 (moderate positive correlation)

**Categorical Analysis**:
- **Gender**: 47.7% Female, 47.5% Male, 4.8% Other (entropy: 1.23)
- **Region**: 20 regions, most common Region_3 (6.5%), highly distributed (entropy: 4.30)
- **Membership Tier**: Silver 52.1%, Gold 35.5%, Platinum 7.3%, Bronze 5.2% (entropy: 1.52)

**Duplicate Rows**: 5 duplicate rows (0.99%) detected - requires removal

## 7. MODEL RECOMMENDATION

**Problem Type**: Binary Classification (predict churn: 0 or 1)

**Primary Recommendation**: RandomForest Classifier

**Technical Justification**:
- **Mixed Data Handling**: Native support for numeric and categorical features without extensive preprocessing
- **Interpretability**: Built-in feature importance identifies purchase_frequency as top driver (84.2% importance)
- **Imbalanced Data**: class_weight='balanced' parameter addresses 24.4% churn rate
- **No Feature Scaling**: Tree-based models handle skewed features (income, order values) naturally
- **Small Dataset**: 505 samples × 45.9:1 feature ratio fits RandomForest efficiency
- **Non-Normality**: Doesn't assume normal distribution (validated by Shapiro-Wilk tests)

**Alternative Recommendation**: XGBoost Classifier
- **Use Case**: If higher accuracy needed and computational cost acceptable
- **Advantage**: Built-in regularization and scale_pos_weight for imbalance
- **Trade-off**: Less interpretable than RandomForest

**Baseline Model**: Logistic Regression
- **Use Case**: Regulatory transparency requirements
- **Advantage**: Coefficient-based interpretability, probabilistic output
- **Trade-off**: Assumes linear relationships; requires encoding and scaling

**Model State**: RandomForest baseline trained with 1.0 training accuracy (requires validation monitoring for overfitting)

## 8. XAI INSIGHTS

**SHAP Global Feature Importance**:
- purchase_frequency: 0.842 (84.2% importance - dominant predictor)
- age: 0.048 (4.8% importance)
- avg_order_value: 0.032 (3.2% importance)
- total_spent: 0.028 (2.8% importance)
- annual_income: 0.021 (2.1% importance)
- credit_score: 0.015 (1.5% importance)
- membership_tier: 0.011 (1.1% importance)
- Remaining features: <1% each

**Interpretation**: Customer engagement (purchase_frequency) overwhelmingly drives churn predictions, with demographic and financial factors playing minor supporting roles.

**LIME Explanation (Row 0)**:
- Row 0 Prediction: Churn = 0 (retained)
- **Feature Contributions**:
  - purchase_frequency: -0.45 (decreases churn probability)
  - age: +0.12 (slightly increases churn risk)
  - avg_order_value: -0.08 (decreases churn probability)
  - total_spent: -0.06 (decreases churn probability)
  - annual_income: +0.03 (slightly increases churn risk)

**Interpretation**: High purchase frequency strongly predicts retention for this customer. Age and income slightly increase churn risk, but engagement metrics dominate.

**Referenced Charts**: charts/shap_summary.png, charts/lime_explanation.png

## 9. NEXT STEPS

**Immediate Analytical Actions**:
1. Remove 5 duplicate rows (0.99% of dataset) to prevent training bias
2. Manually address 10 invalid negative age values (-3.90 min) through removal or imputation
3. Convert signup_date from object to datetime format, extract year/month features
4. Apply log transformation to highly skewed features: annual_income, total_spent, avg_order_value
5. Cap extreme outliers in avg_order_value (values > $2,366) using IQR bounds

**Model Training Actions**:
6. Train RandomForest with 5-fold stratified cross-validation due to 24.4% class imbalance
7. Use F1-score and AUC-ROC as primary metrics (focus beyond accuracy)
8. Monitor for overfitting given baseline training accuracy of 1.0
9. Validate on holdout set with 20% split
10. Compare against Logistic Regression baseline to justify model complexity

**Feature Engineering Actions**:
11. Create age groups (0-25, 26-40, 41-55, 56+) to capture non-linear age effects
12. Generate RFM segments from recency (signup_date), frequency (purchase_frequency), monetary (total_spent)
13. One-hot encode membership_tier and gender for logistic regression compatibility
14. Extract region tiering if urban/rural patterns emerge from geographic analysis
15. Monitor for feature drift in purchase_frequency (dominant predictor)

**Validation & Monitoring Actions**:
16. Compute confusion matrix to assess precision/recall trade-offs for churn detection
17. Calculate SHAP values on test set to verify purchase_frequency dominance
18. Establish baseline performance threshold (F1 > 0.75) for business viability
19. Track model calibration (probability reliability) using reliability diagrams
20. Plan quarterly retraining schedule to account for data drift in financial metrics

**Data Quality Actions**:
21. Re-run correlation analysis after duplicate removal to verify r=0.88 income-credit relationship
22. Validate Shapiro-Wilk tests remain significant after log transformation
23. Document data lineage: track imputation methods for regulatory compliance
24. Create monitoring dashboard for missing value rates (target: <1% post-production)
25. Archive cleaned dataset snapshot for reproducibility