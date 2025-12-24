"""
Explainable AI (XAI) Tools for CrewAI Agents
Provides tools for SHAP and LIME explanations.
"""

import json
import os
from typing import Type

import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from crewai.tools import BaseTool
from pydantic import BaseModel, Field

from src.tools.data_tools import DataStore
from src.tools.ml_tools import ModelStore


class XAIConfig:
    """Configuration for XAI output."""
    output_dir: str = "output/charts"
    
    @classmethod
    def set_output_dir(cls, path: str):
        cls.output_dir = path
        os.makedirs(path, exist_ok=True)


# ============ SHAP Summary Tool ============

class GenerateSHAPSummaryInput(BaseModel):
    """Input for SHAP summary tool."""
    max_display: int = Field(default=10, description="Maximum features to display")


class GenerateSHAPSummaryTool(BaseTool):
    name: str = "generate_shap_summary"
    description: str = """
    Generate a SHAP summary plot showing global feature importance.
    Uses the trained model from ModelStore.
    Input: max_display (default 10)
    Returns: Path to the generated SHAP summary plot.
    """
    args_schema: Type[BaseModel] = GenerateSHAPSummaryInput
    
    def _run(self, max_display: int = 10) -> str:
        model = ModelStore.get_model()
        if model is None:
            return "Error: No trained model found. Run train_simple_model first."
        
        df = DataStore.get_dataframe()
        if df is None:
            return "Error: No dataset loaded"
        
        try:
            import shap
            
            metadata = ModelStore.get_metadata()
            target_column = metadata.get("target_column")
            feature_columns = metadata.get("feature_columns", [])
            encoders = ModelStore.get_label_encoders()
            
            # Prepare features
            X = df.drop(columns=[target_column])
            
            # Handle datetime columns - same as training
            datetime_cols = X.select_dtypes(include=['datetime64', 'datetime64[ns]']).columns.tolist()
            for col in datetime_cols:
                if col in X.columns:
                    X[f'{col}_year'] = X[col].dt.year
                    X[f'{col}_month'] = X[col].dt.month
                    X[f'{col}_day'] = X[col].dt.day
                    X[f'{col}_dayofweek'] = X[col].dt.dayofweek
                    X = X.drop(columns=[col])
            
            X_encoded = X.copy()
            
            for col in X_encoded.select_dtypes(include=['object', 'category']).columns:
                if col in encoders:
                    X_encoded[col] = encoders[col].transform(X_encoded[col].astype(str))
            
            # Ensure column order matches training
            X_encoded = X_encoded[feature_columns]
            
            # Calculate SHAP values
            explainer = shap.TreeExplainer(model)
            shap_values = explainer.shap_values(X_encoded)
            
            # Handle multi-class classification and different SHAP output formats
            # shap_values can be a list (binary/multiclass) or a numpy array (regression)
            if hasattr(shap_values, '__len__') and not isinstance(shap_values, np.ndarray):
                # It's a list - for classification, use positive class (index 1) or average
                if len(shap_values) == 2:
                    # Binary classification - use positive class
                    shap_values = shap_values[1]
                else:
                    # Multi-class - take mean absolute across classes
                    shap_values = np.abs(np.array(shap_values)).mean(axis=0)
            
            # Ensure shap_values is a numpy array
            shap_values = np.array(shap_values)
            
            # Create summary plot
            os.makedirs(XAIConfig.output_dir, exist_ok=True)
            
            fig, ax = plt.subplots(figsize=(10, 8))
            
            # Calculate mean absolute SHAP values
            mean_shap = np.abs(shap_values).mean(axis=0)
            
            # Ensure mean_shap is 1D (flatten if needed)
            mean_shap = np.asarray(mean_shap).flatten()
            
            # Create feature importance dict with safe scalar conversion
            feature_importance = {}
            for i, col in enumerate(feature_columns):
                if i < len(mean_shap):
                    # Extract scalar value safely
                    val = mean_shap[i]
                    feature_importance[col] = float(np.asarray(val).item()) if hasattr(val, '__len__') else float(val)
            
            # Sort by importance
            sorted_features = sorted(feature_importance.items(), key=lambda x: x[1], reverse=True)[:max_display]
            
            features = [f[0] for f in sorted_features][::-1]
            values = [f[1] for f in sorted_features][::-1]
            
            colors = plt.cm.Blues(np.linspace(0.4, 0.9, len(features)))
            ax.barh(features, values, color=colors)
            ax.set_xlabel('Mean |SHAP Value|', fontsize=12)
            ax.set_title('SHAP Feature Importance (Global)', fontsize=14, fontweight='bold')
            
            # Add value labels
            for i, (feat, val) in enumerate(zip(features, values)):
                ax.text(val + 0.01, i, f'{val:.4f}', va='center', fontsize=10)
            
            plt.tight_layout()
            
            filepath = os.path.join(XAIConfig.output_dir, "shap_summary.png")
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            # Store SHAP values in DataStore
            DataStore.set_metadata("shap_values", {
                "mean_importance": {k: float(v) for k, v in sorted_features},
                "plot_path": filepath
            })
            
            return json.dumps({
                "status": "success",
                "filepath": filepath,
                "top_features": {k: round(float(v), 4) for k, v in sorted_features[:5]},
                "interpretation": "Higher SHAP values indicate greater feature impact on predictions"
            }, indent=2)
            
        except ImportError:
            return "Error: SHAP library not installed. Run: pip install shap"
        except Exception as e:
            return f"Error generating SHAP summary: {str(e)}"


# ============ LIME Explanation Tool ============

class GenerateLIMEExplanationInput(BaseModel):
    """Input for LIME explanation tool."""
    row_index: int = Field(default=0, description="Index of the row to explain")


class GenerateLIMEExplanationTool(BaseTool):
    name: str = "generate_lime_explanation"
    description: str = """
    Generate a LIME explanation for a specific prediction.
    Shows which features influenced a particular instance's prediction.
    Input: row_index (default 0)
    Returns: Feature contributions for the selected instance.
    """
    args_schema: Type[BaseModel] = GenerateLIMEExplanationInput
    
    def _run(self, row_index: int = 0) -> str:
        model = ModelStore.get_model()
        if model is None:
            return "Error: No trained model found. Run train_simple_model first."
        
        df = DataStore.get_dataframe()
        if df is None:
            return "Error: No dataset loaded"
        
        if row_index < 0 or row_index >= len(df):
            return f"Error: row_index must be between 0 and {len(df)-1}"
        
        try:
            from lime.lime_tabular import LimeTabularExplainer
            
            metadata = ModelStore.get_metadata()
            target_column = metadata.get("target_column")
            feature_columns = metadata.get("feature_columns", [])
            problem_type = metadata.get("metadata", {}).get("problem_type", "classification")
            encoders = ModelStore.get_label_encoders()
            
            # Prepare features
            X = df.drop(columns=[target_column])
            
            # Handle datetime columns - same as training
            datetime_cols = X.select_dtypes(include=['datetime64', 'datetime64[ns]']).columns.tolist()
            for col in datetime_cols:
                if col in X.columns:
                    X[f'{col}_year'] = X[col].dt.year
                    X[f'{col}_month'] = X[col].dt.month
                    X[f'{col}_day'] = X[col].dt.day
                    X[f'{col}_dayofweek'] = X[col].dt.dayofweek
                    X = X.drop(columns=[col])
            
            X_encoded = X.copy()
            
            for col in X_encoded.select_dtypes(include=['object', 'category']).columns:
                if col in encoders:
                    X_encoded[col] = encoders[col].transform(X_encoded[col].astype(str))
            
            X_encoded = X_encoded[feature_columns]
            
            # Create LIME explainer
            mode = "classification" if problem_type == "classification" else "regression"
            explainer = LimeTabularExplainer(
                training_data=X_encoded.values,
                feature_names=feature_columns,
                mode=mode,
                random_state=42
            )
            
            # Get explanation for the instance
            instance = X_encoded.iloc[row_index].values
            
            if mode == "classification":
                explanation = explainer.explain_instance(
                    instance, 
                    model.predict_proba,
                    num_features=10
                )
            else:
                explanation = explainer.explain_instance(
                    instance, 
                    model.predict,
                    num_features=10
                )
            
            # Extract feature contributions
            feature_contributions = explanation.as_list()
            
            # Create visualization
            os.makedirs(XAIConfig.output_dir, exist_ok=True)
            
            fig, ax = plt.subplots(figsize=(10, 6))
            
            features = [f[0] for f in feature_contributions][::-1]
            weights = [f[1] for f in feature_contributions][::-1]
            colors = ['#28a745' if w > 0 else '#dc3545' for w in weights]
            
            ax.barh(features, weights, color=colors, alpha=0.8)
            ax.axvline(x=0, color='black', linewidth=0.5)
            ax.set_xlabel('Feature Contribution', fontsize=12)
            ax.set_title(f'LIME Explanation (Row #{row_index})', fontsize=14, fontweight='bold')
            
            plt.tight_layout()
            
            filepath = os.path.join(XAIConfig.output_dir, f"lime_explanation_row_{row_index}.png")
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            # Get prediction
            prediction = model.predict([instance])[0]
            if '__target__' in encoders:
                prediction = encoders['__target__'].inverse_transform([int(prediction)])[0]
            
            return json.dumps({
                "status": "success",
                "row_index": row_index,
                "prediction": str(prediction),
                "filepath": filepath,
                "feature_contributions": {f[0]: round(float(f[1]), 4) for f in feature_contributions},
                "interpretation": "Green bars push prediction higher, red bars push it lower"
            }, indent=2)
            
        except ImportError:
            return "Error: LIME library not installed. Run: pip install lime"
        except Exception as e:
            return f"Error generating LIME explanation: {str(e)}"


# ============ Feature Importance Comparison Tool ============

class CompareFeatureImportanceInput(BaseModel):
    """Input - no input needed."""
    pass


class CompareFeatureImportanceTool(BaseTool):
    name: str = "compare_feature_importance"
    description: str = """
    Compare feature importance from model vs SHAP values.
    Creates a side-by-side comparison chart.
    No input required.
    Returns: Path to comparison chart.
    """
    args_schema: Type[BaseModel] = CompareFeatureImportanceInput
    
    def _run(self) -> str:
        model = ModelStore.get_model()
        if model is None:
            return "Error: No trained model found"
        
        metadata = ModelStore.get_metadata()
        feature_columns = metadata.get("feature_columns", [])
        
        try:
            # Get model's native feature importance
            model_importance = dict(zip(feature_columns, model.feature_importances_))
            
            # Get SHAP importance if available
            shap_data = DataStore.get_metadata("shap_values")
            
            if shap_data is None:
                return "Error: Run generate_shap_summary first"
            
            shap_importance = shap_data.get("mean_importance", {})
            
            # Create comparison chart
            os.makedirs(XAIConfig.output_dir, exist_ok=True)
            
            fig, axes = plt.subplots(1, 2, figsize=(14, 6))
            
            # Model importance
            sorted_model = sorted(model_importance.items(), key=lambda x: x[1], reverse=True)[:10]
            features_model = [f[0] for f in sorted_model][::-1]
            values_model = [f[1] for f in sorted_model][::-1]
            
            axes[0].barh(features_model, values_model, color='steelblue', alpha=0.8)
            axes[0].set_xlabel('Importance')
            axes[0].set_title('Model Feature Importance\n(Gini/Mean Decrease)', fontsize=12, fontweight='bold')
            
            # SHAP importance
            sorted_shap = sorted(shap_importance.items(), key=lambda x: x[1], reverse=True)[:10]
            features_shap = [f[0] for f in sorted_shap][::-1]
            values_shap = [f[1] for f in sorted_shap][::-1]
            
            axes[1].barh(features_shap, values_shap, color='coral', alpha=0.8)
            axes[1].set_xlabel('Mean |SHAP Value|')
            axes[1].set_title('SHAP Feature Importance\n(Global Contribution)', fontsize=12, fontweight='bold')
            
            plt.tight_layout()
            
            filepath = os.path.join(XAIConfig.output_dir, "feature_importance_comparison.png")
            plt.savefig(filepath, dpi=150, bbox_inches='tight')
            plt.close(fig)
            
            return json.dumps({
                "status": "success",
                "filepath": filepath,
                "model_top_3": {k: round(float(v), 4) for k, v in sorted_model[:3]},
                "shap_top_3": {k: round(float(v), 4) for k, v in sorted_shap[:3]},
                "interpretation": "Comparing native model importance vs SHAP-based importance"
            }, indent=2)
            
        except Exception as e:
            return f"Error comparing importance: {str(e)}"
