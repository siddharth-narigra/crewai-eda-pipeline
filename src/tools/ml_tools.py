"""
Machine Learning Tools for CrewAI Agents
Provides tools for model recommendation and simple model training.
"""

import json
import os
import pickle
import time
from datetime import datetime
from typing import Any, Type

import numpy as np
import pandas as pd
from crewai.tools import BaseTool
from pydantic import BaseModel, Field
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier, RandomForestRegressor
from sklearn.preprocessing import LabelEncoder
from sklearn.metrics import (
    precision_score, recall_score, f1_score, confusion_matrix, mean_absolute_error
)

from src.tools.data_tools import DataStore


class ModelStore:
    """Singleton to store the trained model and metadata."""
    _instance = None
    _model = None
    _model_type: str = None
    _target_column: str = None
    _feature_columns: list = []
    _label_encoders: dict = {}
    _model_metadata: dict = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @classmethod
    def set_model(cls, model, model_type: str, target: str, features: list, encoders: dict, metadata: dict):
        cls._model = model
        cls._model_type = model_type
        cls._target_column = target
        cls._feature_columns = features
        cls._label_encoders = encoders
        cls._model_metadata = metadata
    
    @classmethod
    def get_model(cls):
        return cls._model
    
    @classmethod
    def get_metadata(cls) -> dict:
        return {
            "model_type": cls._model_type,
            "target_column": cls._target_column,
            "feature_columns": cls._feature_columns,
            "metadata": cls._model_metadata
        }
    
    @classmethod
    def get_label_encoders(cls) -> dict:
        return cls._label_encoders


# ============ Suggest Models Tool ============

class SuggestModelsInput(BaseModel):
    """Input for model suggestion tool."""
    target_column: str = Field(description="Name of the target variable to predict")


class SuggestModelsBasedOnDataTool(BaseTool):
    name: str = "suggest_models"
    description: str = """
    Analyze dataset characteristics and suggest suitable ML models.
    Input: target_column - the column to predict
    Returns: List of recommended algorithms with justifications.
    """
    args_schema: Type[BaseModel] = SuggestModelsInput
    
    def _run(self, target_column: str) -> str:
        df = DataStore.get_dataframe()
        if df is None:
            return "Error: No dataset loaded"
        
        if target_column not in df.columns:
            return f"Error: Target column '{target_column}' not found"
        
        # Analyze target variable
        target = df[target_column]
        n_unique = target.nunique()
        n_samples = len(df)
        n_features = len(df.columns) - 1
        
        recommendations = {
            "target_analysis": {},
            "data_characteristics": {},
            "recommended_models": [],
            "reasoning": []
        }
        
        # Determine problem type
        if pd.api.types.is_numeric_dtype(target) and n_unique > 10:
            problem_type = "regression"
            recommendations["target_analysis"] = {
                "type": "continuous",
                "problem": "regression",
                "unique_values": int(n_unique),
                "mean": float(target.mean()),
                "std": float(target.std())
            }
        else:
            problem_type = "classification"
            class_distribution = target.value_counts().to_dict()
            recommendations["target_analysis"] = {
                "type": "categorical" if target.dtype == 'object' else "discrete",
                "problem": "classification",
                "n_classes": int(n_unique),
                "class_distribution": {str(k): int(v) for k, v in class_distribution.items()},
                "is_balanced": max(class_distribution.values()) / min(class_distribution.values()) < 3
            }
        
        # Analyze data characteristics
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
        categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
        
        recommendations["data_characteristics"] = {
            "n_samples": n_samples,
            "n_features": n_features,
            "numeric_features": len(numeric_cols) - 1,  # Exclude target if numeric
            "categorical_features": len(categorical_cols),
            "missing_values": int(df.isnull().sum().sum()),
            "sample_to_feature_ratio": round(n_samples / max(n_features, 1), 2)
        }
        
        # Make recommendations
        if problem_type == "classification":
            recommendations["recommended_models"] = [
                {
                    "model": "Random Forest Classifier",
                    "priority": 1,
                    "reason": "Robust, handles mixed data types, interpretable feature importance"
                },
                {
                    "model": "XGBoost Classifier",
                    "priority": 2,
                    "reason": "High performance, handles imbalanced data well"
                },
                {
                    "model": "Logistic Regression",
                    "priority": 3,
                    "reason": "Simple baseline, highly interpretable coefficients"
                }
            ]
            if n_unique == 2:
                recommendations["reasoning"].append("Binary classification detected - all suggested models work well")
            else:
                recommendations["reasoning"].append(f"Multi-class classification ({n_unique} classes) - ensemble methods recommended")
        else:
            recommendations["recommended_models"] = [
                {
                    "model": "Random Forest Regressor",
                    "priority": 1,
                    "reason": "Robust, minimal tuning needed, feature importance available"
                },
                {
                    "model": "XGBoost Regressor",
                    "priority": 2,
                    "reason": "High performance, handles non-linear relationships"
                },
                {
                    "model": "Linear Regression",
                    "priority": 3,
                    "reason": "Simple baseline, interpretable coefficients"
                }
            ]
            recommendations["reasoning"].append("Continuous target detected - tree-based ensembles recommended for robustness")
        
        # Add general recommendations
        if n_samples < 1000:
            recommendations["reasoning"].append("Small dataset - avoid deep learning, prefer simpler models")
        if recommendations["data_characteristics"]["sample_to_feature_ratio"] < 10:
            recommendations["reasoning"].append("Low sample-to-feature ratio - regularization recommended")
        
        # Store for later use
        DataStore.set_metadata("model_recommendations", recommendations)
        DataStore.set_metadata("target_column", target_column)
        DataStore.set_metadata("problem_type", problem_type)
        
        return json.dumps(recommendations, indent=2)


# ============ Train Simple Model Tool ============

class TrainModelInput(BaseModel):
    """Input for model training tool."""
    target_column: str = Field(description="Name of the target variable")
    test_size: float = Field(default=0.2, description="Fraction of data for testing (0.1-0.4)")


class TrainSimpleModelTool(BaseTool):
    name: str = "train_simple_model"
    description: str = """
    Train a Random Forest model on the cleaned dataset.
    Input: target_column, test_size (default 0.2)
    Returns: Model performance metrics and confirmation.
    """
    args_schema: Type[BaseModel] = TrainModelInput
    
    def _run(self, target_column: str, test_size: float = 0.2) -> str:
        df = DataStore.get_dataframe()
        if df is None:
            return "Error: No dataset loaded"
        
        if target_column not in df.columns:
            return f"Error: Target column '{target_column}' not found"
        
        try:
            # Prepare data
            X = df.drop(columns=[target_column])
            y = df[target_column]
            
            # Handle datetime columns - convert to numeric features
            datetime_cols = X.select_dtypes(include=['datetime64', 'datetime64[ns]']).columns.tolist()
            for col in datetime_cols:
                if col in X.columns:
                    # Extract useful features from datetime
                    X[f'{col}_year'] = X[col].dt.year
                    X[f'{col}_month'] = X[col].dt.month
                    X[f'{col}_day'] = X[col].dt.day
                    X[f'{col}_dayofweek'] = X[col].dt.dayofweek
                    # Drop the original datetime column
                    X = X.drop(columns=[col])
            
            # Encode categorical features
            label_encoders = {}
            X_encoded = X.copy()
            
            for col in X_encoded.select_dtypes(include=['object', 'category']).columns:
                le = LabelEncoder()
                X_encoded[col] = le.fit_transform(X_encoded[col].astype(str))
                label_encoders[col] = le
            
            # Encode target if categorical
            target_encoder = None
            if y.dtype == 'object' or y.dtype.name == 'category':
                target_encoder = LabelEncoder()
                y_encoded = target_encoder.fit_transform(y.astype(str))
                label_encoders['__target__'] = target_encoder
                problem_type = "classification"
            else:
                y_encoded = y.values
                # Determine problem type based on unique values
                problem_type = "classification" if y.nunique() <= 10 else "regression"
            
            # Split data
            X_train, X_test, y_train, y_test = train_test_split(
                X_encoded, y_encoded, test_size=test_size, random_state=42
            )
            
            # Training start time
            start_time = time.time()
            
            # Train model
            if problem_type == "classification":
                model = RandomForestClassifier(n_estimators=100, random_state=42, n_jobs=-1)
                model.fit(X_train, y_train)
                
                # Training duration
                training_duration = round(time.time() - start_time, 2)
                
                train_score = model.score(X_train, y_train)
                test_score = model.score(X_test, y_test)
                
                # Predictions for additional metrics
                y_pred = model.predict(X_test)
                
                # Classification metrics
                avg_method = 'weighted' if len(np.unique(y_encoded)) > 2 else 'binary'
                precision = precision_score(y_test, y_pred, average=avg_method, zero_division=0)
                recall = recall_score(y_test, y_pred, average=avg_method, zero_division=0)
                f1 = f1_score(y_test, y_pred, average=avg_method, zero_division=0)
                
                # Confusion matrix
                cm = confusion_matrix(y_test, y_pred)
                
                metrics = {
                    "model_type": "RandomForestClassifier",
                    "problem_type": "classification",
                    "train_accuracy": round(float(train_score), 4),
                    "test_accuracy": round(float(test_score), 4),
                    "precision": round(float(precision), 4),
                    "recall": round(float(recall), 4),
                    "f1_score": round(float(f1), 4),
                    "n_classes": int(len(np.unique(y_encoded))),
                    "confusion_matrix": cm.tolist(),
                }
            else:
                model = RandomForestRegressor(n_estimators=100, random_state=42, n_jobs=-1)
                model.fit(X_train, y_train)
                
                # Training duration
                training_duration = round(time.time() - start_time, 2)
                
                train_score = model.score(X_train, y_train)
                test_score = model.score(X_test, y_test)
                
                # Calculate additional metrics
                y_pred = model.predict(X_test)
                mse = float(np.mean((y_test - y_pred) ** 2))
                rmse = float(np.sqrt(mse))
                mae = float(mean_absolute_error(y_test, y_pred))
                
                metrics = {
                    "model_type": "RandomForestRegressor",
                    "problem_type": "regression",
                    "train_r2": round(float(train_score), 4),
                    "test_r2": round(float(test_score), 4),
                    "rmse": round(rmse, 4),
                    "mae": round(mae, 4),
                }
            
            # Common training metadata
            metrics["trained_at"] = datetime.now().isoformat()
            metrics["training_duration_seconds"] = training_duration
            metrics["random_state"] = 42
            metrics["test_size"] = test_size
            metrics["train_samples"] = len(X_train)
            metrics["test_samples"] = len(X_test)
            metrics["total_samples"] = len(X_encoded)
            metrics["feature_count"] = len(X_encoded.columns)
            
            # Hyperparameters
            metrics["hyperparameters"] = {
                "n_estimators": 100,
                "random_state": 42,
                "n_jobs": -1,
                "criterion": "gini" if problem_type == "classification" else "squared_error",
                "max_depth": None,
                "min_samples_split": 2,
                "min_samples_leaf": 1,
            }
            
            # Feature importance
            feature_importance = dict(zip(X_encoded.columns, model.feature_importances_))
            sorted_importance = dict(sorted(feature_importance.items(), key=lambda x: x[1], reverse=True))
            metrics["top_features"] = {k: round(float(v), 4) for k, v in list(sorted_importance.items())[:10]}
            
            # Store model
            ModelStore.set_model(
                model=model,
                model_type=metrics["model_type"],
                target=target_column,
                features=list(X_encoded.columns),
                encoders=label_encoders,
                metadata=metrics
            )
            
            # Save model to disk
            os.makedirs("output/models", exist_ok=True)
            with open("output/models/trained_model.pkl", "wb") as f:
                pickle.dump({
                    "model": model,
                    "encoders": label_encoders,
                    "features": list(X_encoded.columns),
                    "target": target_column,
                    "metrics": metrics
                }, f)
            
            metrics["model_saved"] = "output/models/trained_model.pkl"
            metrics["status"] = "success"
            
            # Append Model Training Summary to report
            self._append_model_summary_to_report(metrics, problem_type)
            
            return json.dumps(metrics, indent=2)
            
        except Exception as e:
            return f"Error training model: {str(e)}"
    
    def _append_model_summary_to_report(self, metrics: dict, problem_type: str):
        """Append Model Training Summary section to report.md and report.html"""
        try:
            report_path = "output/report.md"
            html_path = "output/report.html"
            
            if not os.path.exists(report_path):
                return  # Report doesn't exist yet
            
            # Generate markdown section
            md_section = self._generate_model_summary_markdown(metrics, problem_type)
            
            # Append to markdown report
            with open(report_path, "a", encoding="utf-8") as f:
                f.write("\n\n" + md_section)
            
            # Append to HTML report if it exists
            if os.path.exists(html_path):
                html_section = self._markdown_to_html(md_section)
                with open(html_path, "r", encoding="utf-8") as f:
                    html_content = f.read()
                
                # Insert before closing body tag
                if "</body>" in html_content:
                    html_content = html_content.replace("</body>", html_section + "\n</body>")
                else:
                    html_content += html_section
                
                with open(html_path, "w", encoding="utf-8") as f:
                    f.write(html_content)
                    
        except Exception as e:
            print(f"Warning: Could not append model summary to report: {e}")
    
    def _generate_model_summary_markdown(self, metrics: dict, problem_type: str) -> str:
        """Generate markdown content for Model Training Summary section"""
        train_pct = round(metrics.get("train_samples", 0) / max(metrics.get("total_samples", 1), 1) * 100, 1)
        test_pct = round(metrics.get("test_samples", 0) / max(metrics.get("total_samples", 1), 1) * 100, 1)
        
        md = f"""## 9. Model Training Summary

### Training Configuration
- **Model Type**: {metrics.get("model_type", "N/A")}
- **Trained At**: {metrics.get("trained_at", "N/A")}
- **Training Duration**: {metrics.get("training_duration_seconds", "N/A")} seconds
- **Test Size**: {int(metrics.get("test_size", 0.2) * 100)}%
- **Random State**: {metrics.get("random_state", 42)}

### Data Split
| Set | Samples | Percentage |
|-----|---------|------------|
| Training | {metrics.get("train_samples", "N/A"):,} | {train_pct}% |
| Testing | {metrics.get("test_samples", "N/A"):,} | {test_pct}% |
| **Total** | **{metrics.get("total_samples", "N/A"):,}** | **100%** |

### Performance Metrics
"""
        
        if problem_type == "classification":
            md += f"""- **Test Accuracy**: {metrics.get("test_accuracy", 0) * 100:.2f}%
- **Train Accuracy**: {metrics.get("train_accuracy", 0) * 100:.2f}%
- **Precision**: {metrics.get("precision", 0) * 100:.2f}%
- **Recall**: {metrics.get("recall", 0) * 100:.2f}%
- **F1-Score**: {metrics.get("f1_score", 0) * 100:.2f}%
- **Number of Classes**: {metrics.get("n_classes", "N/A")}
"""
            # Add confusion matrix if available
            cm = metrics.get("confusion_matrix")
            if cm and len(cm) == 2:
                md += f"""
### Confusion Matrix
|  | Predicted 0 | Predicted 1 |
|--|-------------|-------------|
| **Actual 0** | {cm[0][0]} | {cm[0][1]} |
| **Actual 1** | {cm[1][0]} | {cm[1][1]} |
"""
        else:
            md += f"""- **Test R²**: {metrics.get("test_r2", 0):.4f}
- **Train R²**: {metrics.get("train_r2", 0):.4f}
- **RMSE**: {metrics.get("rmse", 0):.4f}
- **MAE**: {metrics.get("mae", 0):.4f}
"""
        
        # Add hyperparameters
        hyperparams = metrics.get("hyperparameters", {})
        if hyperparams:
            md += "\n### Hyperparameters\n| Parameter | Value |\n|-----------|-------|\n"
            for key, value in hyperparams.items():
                md += f"| {key} | {value} |\n"
        
        # Add top features
        top_features = metrics.get("top_features", {})
        if top_features:
            md += "\n### Top 5 Features\n"
            for i, (feature, importance) in enumerate(list(top_features.items())[:5], 1):
                md += f"{i}. **{feature}**: {importance * 100:.2f}%\n"
        
        return md
    
    def _markdown_to_html(self, md_content: str) -> str:
        """Simple markdown to HTML conversion for the model summary section"""
        import re
        
        html = md_content
        
        # Convert headers
        html = re.sub(r'^### (.+)$', r'<h3>\1</h3>', html, flags=re.MULTILINE)
        html = re.sub(r'^## (.+)$', r'<h2>\1</h2>', html, flags=re.MULTILINE)
        
        # Convert bold
        html = re.sub(r'\*\*(.+?)\*\*', r'<strong>\1</strong>', html)
        
        # Convert lists
        html = re.sub(r'^- (.+)$', r'<li>\1</li>', html, flags=re.MULTILINE)
        html = re.sub(r'^(\d+)\. (.+)$', r'<li>\2</li>', html, flags=re.MULTILINE)
        
        # Wrap consecutive li elements in ul
        html = re.sub(r'(<li>.*?</li>\n)+', lambda m: f'<ul>{m.group(0)}</ul>', html, flags=re.DOTALL)
        
        # Convert tables (simplified)
        lines = html.split('\n')
        in_table = False
        result = []
        for line in lines:
            if '|' in line and not line.strip().startswith('|--'):
                if not in_table:
                    result.append('<table class="model-summary-table" style="border-collapse: collapse; margin: 1rem 0;">')
                    in_table = True
                cells = [c.strip() for c in line.split('|')[1:-1]]
                row = '<tr>' + ''.join(f'<td style="border: 1px solid #000; padding: 0.5rem;">{c}</td>' for c in cells) + '</tr>'
                result.append(row)
            elif in_table and '|--' not in line:
                result.append('</table>')
                in_table = False
                result.append(line)
            elif '|--' not in line:
                result.append(line)
        
        if in_table:
            result.append('</table>')
        
        html = '\n'.join(result)
        html = f'<div class="model-summary-section" style="margin-top: 2rem; padding: 1rem; border: 3px solid #000;">\n{html}\n</div>'
        
        return html
