"""
Generate a sample dataset for testing the EDA system.
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import os

# Set random seed for reproducibility
np.random.seed(42)

# Number of samples
n = 150

# Generate data
data = {
    # Numeric columns
    "age": np.random.randint(18, 70, n),
    "income": np.random.normal(50000, 20000, n).round(2),
    "credit_score": np.random.randint(300, 850, n),
    "purchase_amount": np.abs(np.random.exponential(100, n)).round(2),
    "years_customer": np.random.randint(0, 20, n),
    
    # Categorical columns
    "gender": np.random.choice(["Male", "Female", "Other"], n, p=[0.48, 0.48, 0.04]),
    "education": np.random.choice(
        ["High School", "Bachelor's", "Master's", "PhD", "Other"],
        n,
        p=[0.3, 0.35, 0.2, 0.1, 0.05]
    ),
    "region": np.random.choice(
        ["North", "South", "East", "West", "Central"],
        n,
        p=[0.2, 0.25, 0.2, 0.2, 0.15]
    ),
    "product_category": np.random.choice(
        ["Electronics", "Clothing", "Food", "Home", "Sports"],
        n
    ),
    
    # Binary column
    "is_member": np.random.choice([True, False], n, p=[0.6, 0.4]),
}

# Create DataFrame
df = pd.DataFrame(data)

# Add some missing values
df.loc[np.random.choice(n, 10, replace=False), "income"] = np.nan
df.loc[np.random.choice(n, 8, replace=False), "education"] = np.nan
df.loc[np.random.choice(n, 5, replace=False), "credit_score"] = np.nan

# Add some outliers
df.loc[0, "income"] = 500000  # Very high income
df.loc[1, "purchase_amount"] = 5000  # Large purchase
df.loc[2, "age"] = 95  # Old age

# Add a date column
start_date = datetime(2023, 1, 1)
dates = [start_date + timedelta(days=np.random.randint(0, 365)) for _ in range(n)]
df["signup_date"] = dates

# Add ID column
df["customer_id"] = [f"CUST_{i:04d}" for i in range(1, n + 1)]

# Reorder columns
df = df[["customer_id", "age", "gender", "education", "income", "credit_score", 
         "region", "product_category", "purchase_amount", "years_customer", 
         "is_member", "signup_date"]]

# Save to CSV
os.makedirs("sample_data", exist_ok=True)
df.to_csv("sample_data/test_customers.csv", index=False)

print(f"Generated dataset with {len(df)} rows and {len(df.columns)} columns")
print(f"Saved to: sample_data/test_customers.csv")
print("\nColumn summary:")
print(df.dtypes)
print(f"\nMissing values:\n{df.isnull().sum()}")
