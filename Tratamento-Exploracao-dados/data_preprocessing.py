import pandas as pd
import numpy as np
import zipfile
import os
from sklearn.experimental import enable_iterative_imputer
from sklearn.impute import IterativeImputer
from sklearn.preprocessing import LabelEncoder, OneHotEncoder # Although used before, good practice to have imported

def preprocess_application_data(csv_path):
    """
    Performs preprocessing steps on the application_{train|test}.csv data.

    Args:
        csv_path (str): The full path to the application_{train|test}.csv file.

    Returns:
        pd.DataFrame: The processed DataFrame.
    """
    # Load the data
    df = pd.read_csv('/content/home-credit-default-risk/application_train.csv')

    # --- Handle Anomalies ---
    # Create a new feature for the anomaly in DAYS_EMPLOYED
    df['DAYS_EMPLOYED_ANOM'] = df['DAYS_EMPLOYED'] == 365243
    # Replace the anomalous value with NaN in the original DAYS_EMPLOYED column
    df['DAYS_EMPLOYED'].replace({365243: np.nan}, inplace=True)
    # Create YEARS_EMPLOYED for interpretability (optional for modeling, but good for EDA)
    df['YEARS_EMPLOYED'] = df['DAYS_EMPLOYED'] / -365

    # --- Handle Missing Values ---
    # Simple imputation for OWN_CAR_AGE based on FLAG_OWN_CAR
    df['OWN_CAR_AGE'].fillna(0, inplace=True) # Assuming 0 age for those without cars

    # Identify columns with remaining NaNs
    missing_values = df.isnull().sum()
    missing_percentage = (missing_values / len(df)) * 100
    missing_df = pd.DataFrame({
        'Missing Count': missing_values,
        'Missing Percentage (%)': missing_percentage
    })
    missing_df = missing_df[missing_df['Missing Count'] > 0]

        
    # Separate columns with NaNs into numerical and categorical based on current dtypes
    numeric_cols_with_na = df[missing_df.index].select_dtypes(include=np.number).columns.tolist()
    categorical_cols_with_na = df[missing_df.index].select_dtypes(include='object').columns.tolist()

    # Impute categorical columns with 'Missing'
    for col in categorical_cols_with_na:
        df[col].fillna('Missing', inplace=True)

# --- One-Hot Encoding ---
    # Identify categorical columns (including those imputed with 'Missing')
    categorical_cols = df.select_dtypes(include='object').columns.tolist()
    df = pd.get_dummies(df, columns=categorical_cols, dummy_na=False)
    print(f"Shape do DataFrame após One-Hot Encoding: {df.shape}")

    # Check for remaining categorical columns
    # Re-identify numerical columns with NaNs after categorical imputation
    # Some columns might have been imputed with 'Missing' and are no longer numerical
    # Filter missing_df to get columns that are still numeric and have NaNs
    numeric_cols_with_na_after_cat_imputation = df[missing_df.index].select_dtypes(include=np.number).columns.tolist()

    # Separate columns for Median and MICE imputation (using a 30% threshold)
    cols_for_mice = []
    cols_for_median = []
    current_missing_percentage = (df[numeric_cols_with_na_after_cat_imputation].isnull().sum() / len(df)) * 100


    for col in numeric_cols_with_na_after_cat_imputation:
        if current_missing_percentage[col] > 30:
            cols_for_mice.append(col)
        else:
            cols_for_median.append(col)

    # Imputation by Median for columns with less NA
    for col in cols_for_median:
        median_val = df[col].median()
        df[col].fillna(median_val, inplace=True)

    # Imputation with MICE for columns with more NA
    if cols_for_mice:
        imputer = IterativeImputer(max_iter=10, random_state=0)
        df_mice_subset = df[cols_for_mice]
        imputed_data = imputer.fit_transform(df_mice_subset)
        df[cols_for_mice] = imputed_data

    
    return df

# Example usage (optional - can be removed or commented out when importing)
if __name__ == '__main__':
    # Define the path to the raw data file
    # Assuming the raw data is in '/content/home-credit-default-risk/'
    raw_csv_path = '/content/home-credit-default-risk/application_train.csv'

    # Check if the raw file exists
    if os.path.exists(raw_csv_path):
        print(f"Starting preprocessing for: {raw_csv_path}")
        processed_df = preprocess_application_data(raw_csv_path)
        print("Preprocessing complete.")
        print("Processed DataFrame shape:", processed_df.shape)
        print("Checking for remaining NaNs:", processed_df.isnull().sum().sum())

        # Optionally save the processed DataFrame
        output_path = '/content/home-credit-default-risk/application_train_processed_script.csv'
        processed_df.to_csv(output_path, index=False)
        print(f"Processed data saved to: {output_path}")
    else:
        print(f"Raw CSV file not found at: {raw_csv_path}")
        print("Please ensure 'application_train.csv' is in the correct directory.")
