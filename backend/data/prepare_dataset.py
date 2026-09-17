import os
import numpy as np
import pandas as pd

def generate_synthetic_dataset(n_samples: int = 10000, fraud_ratio: float = 0.03, random_state: int = 42) -> pd.DataFrame:
    """
    Generates a reproducible dataset combining PCA-like credit card features (V1-V10) 
    with domain-specific synthetic behavioral features for FraudShield AI training.
    """
    np.random.seed(random_state)
    n_fraud = int(n_samples * fraud_ratio)
    n_legit = n_samples - n_fraud

    # 1. Generate legitimate transactions
    legit_amount = np.random.exponential(scale=2500, size=n_legit) + 100
    legit_cust_avg = legit_amount * np.random.normal(1.0, 0.15, size=n_legit)
    legit_cust_std = legit_cust_avg * 0.2 + 50
    legit_amount_ratio = legit_amount / (legit_cust_avg + 1e-5)
    legit_z_score = (legit_amount - legit_cust_avg) / (legit_cust_std + 1e-5)
    
    legit_new_device = np.random.binomial(1, p=0.05, size=n_legit)
    legit_tx_10m = np.random.poisson(lam=0.2, size=n_legit)
    legit_tx_1h = legit_tx_10m + np.random.poisson(lam=0.5, size=n_legit)
    legit_tx_24h = legit_tx_1h + np.random.poisson(lam=2.0, size=n_legit)
    
    legit_p = np.array([
        0.01, 0.01, 0.005, 0.005, 0.005, 0.01, 0.02, 0.04, 0.07, 0.08, 0.08, 0.08,
        0.08, 0.08, 0.07, 0.07, 0.07, 0.06, 0.05, 0.04, 0.03, 0.02, 0.015, 0.01
    ])
    legit_p = legit_p / legit_p.sum()
    legit_hour = np.random.choice(range(24), size=n_legit, p=legit_p)
    legit_unusual_time = np.where((legit_hour < 6) | (legit_hour >= 23), 1, 0)
    legit_loc_anomaly = np.random.binomial(1, p=0.03, size=n_legit)
    legit_dist_loc = np.where(legit_loc_anomaly == 1, np.random.uniform(50, 800, size=n_legit), 0.0)
    legit_day_of_week = np.random.choice(range(7), size=n_legit)
    legit_tx_count = np.random.randint(5, 100, size=n_legit)

    # 2. Generate fraud transactions
    fraud_amount = np.random.exponential(scale=35000, size=n_fraud) + 15000
    fraud_cust_avg = np.random.uniform(1500, 3500, size=n_fraud)
    fraud_cust_std = fraud_cust_avg * 0.2 + 50
    fraud_amount_ratio = fraud_amount / (fraud_cust_avg + 1e-5)
    fraud_z_score = (fraud_amount - fraud_cust_avg) / (fraud_cust_std + 1e-5)
    
    fraud_new_device = np.random.binomial(1, p=0.75, size=n_fraud)
    fraud_tx_10m = np.random.poisson(lam=4.5, size=n_fraud) + 1
    fraud_tx_1h = fraud_tx_10m + np.random.poisson(lam=3.0, size=n_fraud)
    fraud_tx_24h = fraud_tx_1h + np.random.poisson(lam=5.0, size=n_fraud)
    
    fraud_p = np.array([
        0.10, 0.12, 0.12, 0.12, 0.10, 0.08, 0.04, 0.02, 0.02, 0.02, 0.02, 0.02,
        0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.02, 0.03, 0.04, 0.05, 0.06
    ])
    fraud_p = fraud_p / fraud_p.sum()
    fraud_hour = np.random.choice(range(24), size=n_fraud, p=fraud_p)

    fraud_unusual_time = np.where((fraud_hour < 6) | (fraud_hour >= 23), 1, 0)
    fraud_loc_anomaly = np.random.binomial(1, p=0.80, size=n_fraud)
    fraud_dist_loc = np.where(fraud_loc_anomaly == 1, np.random.uniform(200, 1500, size=n_fraud), 0.0)
    fraud_day_of_week = np.random.choice(range(7), size=n_fraud)
    fraud_tx_count = np.random.randint(1, 50, size=n_fraud)

    # 3. Create PCA features (V1-V10)
    legit_v = np.random.normal(loc=0.0, scale=1.0, size=(n_legit, 10))
    fraud_v = np.random.normal(loc=1.8, scale=1.5, size=(n_fraud, 10))

    # Combine into dataframes
    df_legit = pd.DataFrame(legit_v, columns=[f"V{i}" for i in range(1, 11)])
    df_legit["amount"] = legit_amount
    df_legit["customer_avg_amount"] = legit_cust_avg
    df_legit["amount_ratio"] = legit_amount_ratio
    df_legit["amount_z_score"] = legit_z_score
    df_legit["is_new_device"] = legit_new_device
    df_legit["transactions_last_10min"] = legit_tx_10m
    df_legit["transactions_last_1hour"] = legit_tx_1h
    df_legit["transactions_last_24hours"] = legit_tx_24h
    df_legit["unusual_time"] = legit_unusual_time
    df_legit["location_anomaly"] = legit_loc_anomaly
    df_legit["distance_from_usual_location"] = legit_dist_loc
    df_legit["customer_transaction_count"] = legit_tx_count
    df_legit["hour"] = legit_hour
    df_legit["day_of_week"] = legit_day_of_week
    df_legit["is_fraud"] = 0

    df_fraud = pd.DataFrame(fraud_v, columns=[f"V{i}" for i in range(1, 11)])
    df_fraud["amount"] = fraud_amount
    df_fraud["customer_avg_amount"] = fraud_cust_avg
    df_fraud["amount_ratio"] = fraud_amount_ratio
    df_fraud["amount_z_score"] = fraud_z_score
    df_fraud["is_new_device"] = fraud_new_device
    df_fraud["transactions_last_10min"] = fraud_tx_10m
    df_fraud["transactions_last_1hour"] = fraud_tx_1h
    df_fraud["transactions_last_24hours"] = fraud_tx_24h
    df_fraud["unusual_time"] = fraud_unusual_time
    df_fraud["location_anomaly"] = fraud_loc_anomaly
    df_fraud["distance_from_usual_location"] = fraud_dist_loc
    df_fraud["customer_transaction_count"] = fraud_tx_count
    df_fraud["hour"] = fraud_hour
    df_fraud["day_of_week"] = fraud_day_of_week
    df_fraud["is_fraud"] = 1

    df = pd.concat([df_legit, df_fraud], ignore_index=True)
    df = df.sample(frac=1.0, random_state=random_state).reset_index(drop=True)
    return df

if __name__ == "__main__":
    out_dir = os.path.join(os.path.dirname(__file__))
    os.makedirs(out_dir, exist_ok=True)
    csv_path = os.path.join(out_dir, "fraud_dataset.csv")
    df = generate_synthetic_dataset(n_samples=10000, fraud_ratio=0.03)
    df.to_csv(csv_path, index=False)
    print(f"Dataset generated with {len(df)} rows ({df['is_fraud'].sum()} fraud) saved to {csv_path}")
