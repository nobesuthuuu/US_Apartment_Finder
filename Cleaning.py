import pandas as pd
import numpy as np

# Loading the data
df = pd.read_csv("City_MedianRentalPrice_1Bedroom.csv")

# Drop the unnamed index column if it exists
if df.columns[0] == 'Unnamed: 0':
    df = df.drop(df.columns[0], axis=1)

# Keep only essential columns
essential_columns = ['RegionName', 'State', 'Metro', 'CountyName']
# Add all date columns (they start with numbers)
date_columns = [col for col in df.columns if col[0].isdigit()]
columns_to_keep = essential_columns + date_columns

# Keep only the selected columns
df = df[columns_to_keep]

# Print initial dataset information
print("\nInitial dataset shape:", df.shape)
print("\nInitial missing values in each column:")
print(df.isnull().sum())

# Calculate missing value percentage for each row
missing_percentage = df[date_columns].isnull().sum(axis=1) / len(date_columns) * 100

# Remove rows with more than 80% missing values
rows_before = len(df)
df = df[missing_percentage <= 80]
rows_removed = rows_before - len(df)
print(f"\nRows removed due to >80% missing values: {rows_removed}")

# Handle missing values using interpolation
print("\nApplying interpolation to remaining missing values...")
df[date_columns] = df[date_columns].interpolate(method='linear', axis=1)

# Forward fill and backward fill for any remaining missing values at the edges
df[date_columns] = df[date_columns].fillna(method='ffill', axis=1).fillna(method='bfill', axis=1)

# Handle any remaining missing values in location data
df = df.dropna(subset=['RegionName', 'State'])

# Print final statistics
print("\nFinal dataset shape:", df.shape)
print("\nMissing values after cleaning:")
print(df.isnull().sum())

# Save the cleaned dataset
df.to_csv("cleaned_rental_data.csv", index=False)
print("\nCleaned dataset saved as 'cleaned_rental_data.csv'")
