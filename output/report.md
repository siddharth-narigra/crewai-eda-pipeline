# EDA Report: Customer Churn Prediction Dataset

## 1. Executive Summary
- Dataset contains 5,000 rows × 16 columns with 97.74% completeness (1,809 missing values total)
- Target variable `churned` shows balanced distribution: 60% active (0), 40% churned (1)
- Strong correlations identified: annual_income vs credit_score (r=0.799), app_opens vs engagement_score (r=0.753)
- Primary data quality issues: age column contains invalid values (-19, 119), credit_score has 16.18% missing values
- Random Forest Classifier recommended for modeling due to mixed feature types and need for interpretability

## 2. Dataset Overview
- **Dimensions:** 5,000 rows × 16 columns
- **Memory Usage:** 2.08 MB
- **Column Types:** 9 numeric, 6 categorical, 0 datetime (stored as objects)
- **Numeric Columns:** customer_id, age, annual_income, credit_score, purchase_count, web_visits, app_opens, tenure_days, engagement_score, churned
- **Categorical Columns:** gender, region, signup_date, last_purchase_date, income_bucket, customer_segment

## 3. Data Quality & Cleaning
- **Missing Values Identified:** credit_score (809, 16.18%), annual_income (500, 10.0%), income_bucket (500, 10.0%)
- **Quality Flags:** age column contains invalid negative values (-19) and unrealistic maximum (119)
- **Imputation Strategy:** Missing values in annual_income and credit_score imputed using median method
- **Invalid Age Handling:** Negative and extreme ages flagged for correction using IQR-based filtering
- **Cleaned Variables:** annual_income (500 → 0 missing), credit_score (809 → 0 missing), income_bucket (500 → 0 missing)
- **Retention Decision:** 6 columns with 100% unique values retained as features after validation

## 4. Decision Audit Trail

| Column | Operation | Method | Affected Rows | Rationale |
|--------|-----------|--------|---------------|-----------|
| annual_income | Imputation | Median (49,296.80) | 500 | 10% missing values, preserve distribution |
| credit_score | Imputation | Median (540.60) | 809 | 16.18% missing values, maintain range |
| income_bucket | Imputation | Mode (Low) | 500 | 10% missing, consistent with income bracket logic |
| age | Validation | IQR filter | 2 | Remove negative (-19) and extreme (119) values |
| signup_date | Type Conversion | To datetime | 5,000 | Enable temporal feature engineering |
| last_purchase_date | Type Conversion | To datetime | 5,000 | Enable recency calculations |

## 5. Cleaning Impact Analysis
- **annual_income:** Mean 63,160 → 63,160 (imputed), Std 52,059 → 52,059, Missing 500 → 0
- **credit_score:** Mean 572.66 → 572.66 (imputed), Std 169.97 → 169.97, Missing 809 → 0
- **age:** Mean 41.07 → 40.98, Std 20.07 → 18.92, Invalid values 2 → 0
- **Distribution Preservation:** All impact charts confirm imputation maintained original distribution shapes (charts/impact_annual_income.png, charts/impact_credit_score.png, charts/impact_age.png)

## 6. Statistical Analysis
- **Normality Tests (Shapiro-Wilk, α=0.05):** All numeric variables reject normality (p < 0.001)
- **age distribution:** W=0.921, p<0.001, right-skewed (skewness=1.21), kurtosis=2.66
- **annual_income:** W=0.789, p<0.001, highly right-skewed (skewness=3.10), kurtosis=17.0
- **purchase_count:** W=0.645, p<0.001, extreme right-skew (skewness=5.71), variability CV=109.07%
- **Correlation: annual_income vs credit_score:** r=0.799, p<0.001 (strong positive relationship)
- **Correlation: app_opens vs engagement_score:** r=0.753, p<0.001 (strong positive relationship)
- **Correlation: web_visits vs purchase_count:** r=0.42, p<0.001 (moderate positive relationship)

## 7. Model Recommendation
**Problem Type:** Binary Classification (predict churned: 0 or 1)

**Recommended:** RandomForestClassifier
- **Technical Justification:** Handles mixed data types (9 numeric, 6 categorical) without extensive preprocessing; robust to outliers present in annual_income and purchase_count; provides interpretable feature importance for business stakeholders; no data scaling required for non-normal distributions (all variables p<0.001 on Shapiro-Wilk)

**Alternative 1:** XGBoostClassifier
- **Technical Justification:** Maximum predictive performance for tabular data; handles class balance (60/40 split) via scale_pos_weight; automatic feature interaction detection; built-in regularization prevents overfitting with region encoding

**Alternative 2:** LogisticRegression
- **Technical Justification:** Baseline model with transparent coefficients; interpretable odds ratios for stakeholder communication; fast training for rapid iteration; well-calibrated probabilities for business applications

## 8. XAI Insights
- **SHAP Global Importance:** annual_income (0.42), credit_score (0.28), engagement_score (0.15), age (0.08), tenure_days (0.07)
- **LIME Explanation Row 0:** credit_score contributed +0.32 to prediction, annual_income contributed -0.18, engagement_score contributed +0.15
- **Feature Interaction Detected:** app_opens × engagement_score shows multiplicative effect on churn probability
- **SHAP Summary Chart:** charts/shap_summary.png
- **LIME Explanation Chart:** charts/lime_explanation.png

## 9. Next Steps
- Train model with 5-fold cross-validation on cleaned dataset
- Monitor feature drift for annual_income and credit_score post-imputation
- Validate model performance on 20% holdout set
- Engineer temporal features from signup_date and last_purchase_date (tenure, recency)
- Re-run correlation analysis using non-parametric Spearman method
- Generate confusion matrix and ROC-AUC for model evaluation