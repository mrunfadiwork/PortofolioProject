import pandas as pd
import numpy as np
import csv

# File paths
households_file = '/Users/prabhatshastri/Downloads/data submission/Resident Households by City, County, and District.csv'
merged_file = '/Users/prabhatshastri/Downloads/data submission/merged_retail_population_data.csv'
output_file = '/Users/prabhatshastri/Downloads/data submission/merged_retail_population_data.csv'

# Normalize period format function
def normalize_period(period):
    period_str = str(period).replace('"', '').strip()
    if period_str.endswith(' p)'):
        period_str = period_str[:-3].strip()
    if '.' in period_str:
        parts = period_str.split('.')
        year = parts[0]
        month_part = parts[1].split()[0]
        month = month_part.zfill(2)
        return f"{year}.{month}"
    return period_str

print("Reading households file...")
# Read households file
households_df = pd.read_csv(households_file)

# Filter for "Household[Household]" item only
households_df = households_df[households_df['Item'] == 'Household[Household]'].copy()

# Get province-level data only (filter out city/district level data)
# The provinces we want are: Seoul, Busan, Daegu, Incheon, Gwangju, Daejeon, Ulsan, Sejong,
# Gyeonggi-do, Gangwon-do, Chungcheongbuk-do, Chungcheongnam-do, Jeollabuk-do, Jeollanam-do,
# Gyeongsangbuk-do, Gyeongsangnam-do, Jeju-do

provinces = [
    'Seoul', 'Busan', 'Daegu', 'Incheon', 'Gwangju', 'Daejeon', 'Ulsan', 'Sejong', 'Sejong-si',
    'Gyeonggi-do', 'Gangwon-do', 'Chungcheongbuk-do', 'Chungcheongnam-do',
    'Jeollabuk-do', 'Jeollanam-do', 'Gyeongsangbuk-do', 'Gyeongsangnam-do', 'Jeju-do', 'Jeju'
]

# Standardize province names first
households_df['By Administrative District'] = households_df['By Administrative District'].str.replace('"', '').str.strip()
households_df['By Administrative District'] = households_df['By Administrative District'].str.replace('Sejong-si', 'Sejong')
households_df['By Administrative District'] = households_df['By Administrative District'].str.replace('Sejong_si', 'Sejong')
households_df['By Administrative District'] = households_df['By Administrative District'].str.replace('sejong', 'Sejong', case=False)
households_df['By Administrative District'] = households_df['By Administrative District'].str.replace('Jeju$', 'Jeju-do', regex=True)

# Filter for province-level data (after standardization)
standardized_provinces = [
    'Seoul', 'Busan', 'Daegu', 'Incheon', 'Gwangju', 'Daejeon', 'Ulsan', 'Sejong',
    'Gyeonggi-do', 'Gangwon-do', 'Chungcheongbuk-do', 'Chungcheongnam-do',
    'Jeollabuk-do', 'Jeollanam-do', 'Gyeongsangbuk-do', 'Gyeongsangnam-do', 'Jeju-do'
]
households_df = households_df[households_df['By Administrative District'].isin(standardized_provinces)].copy()

# Get monthly column names (columns with "Month" in them)
month_cols = [col for col in households_df.columns if 'Month' in col]

# Create mapping from column names to normalized periods
col_to_period = {}
for col in month_cols:
    # Extract period from column name like "2020.01 Month" or '"2020.10 Month"'
    period_raw = col.replace(' Month', '').strip().replace('"', '').replace("'", '')
    period_normalized = normalize_period(period_raw)
    col_to_period[col] = period_normalized

# Melt the monthly columns to long format
households_melted = households_df.melt(
    id_vars=['By Administrative District'],
    value_vars=month_cols,
    var_name='Period_Raw',
    value_name='Number_of_Households'
)

# Map column names to normalized periods
households_melted['Period'] = households_melted['Period_Raw'].map(col_to_period)

# Rename column
households_melted = households_melted.rename(columns={'By Administrative District': 'City_Province'})

# Select only needed columns
households_final = households_melted[['Period', 'City_Province', 'Number_of_Households']].copy()

# Ensure Period is string
households_final['Period'] = households_final['Period'].astype(str)

# Remove any duplicates
households_final = households_final.drop_duplicates(subset=['Period', 'City_Province'], keep='first')

print(f"Households data shape: {households_final.shape}")
print(f"Sample households data:")
print(households_final.head(10))

# Read the existing merged file - read Period as string to preserve format
print("\nReading existing merged file...")
merged_df = pd.read_csv(merged_file, dtype={'Period': str})

# Ensure Period is normalized and string
merged_df['Period'] = merged_df['Period'].apply(normalize_period)
merged_df['Period'] = merged_df['Period'].astype(str)

# Check for actual duplicates
print(f"Checking for duplicates (before: {len(merged_df)} rows)...")
duplicates = merged_df[merged_df.duplicated(subset=['Period', 'City_Province'], keep=False)]
print(f"Actual duplicate rows: {len(duplicates)}")
if len(duplicates) > 0:
    merged_df = merged_df.drop_duplicates(subset=['Period', 'City_Province'], keep='first')
    print(f"After removing duplicates: {len(merged_df)} rows")

# Remove existing household-related columns if they exist (we'll recreate them)
cols_to_remove = ['Number_of_Households', 'Household_Size', 'Retail_Sales_Per_Household']
for col in cols_to_remove:
    if col in merged_df.columns:
        merged_df = merged_df.drop(columns=[col])
        print(f"Removed existing column: {col}")

# Merge households data
print("\nMerging households data...")
print(f"households_final columns: {households_final.columns.tolist()}")
print(f"households_final shape: {households_final.shape}")
print(f"Sample households_final:")
print(households_final.head(5))

# Check if Number_of_Households already exists in merged_df
if 'Number_of_Households' in merged_df.columns:
    print("WARNING: Number_of_Households already exists in merged_df, will be replaced")

final_df = pd.merge(
    merged_df,
    households_final,
    on=['Period', 'City_Province'],
    how='left',
    suffixes=('', '_household')  # Add suffix only if there's a conflict
)

# Handle any columns with _household suffix (rename them back)
for col in final_df.columns:
    if col.endswith('_household'):
        base_col = col.replace('_household', '')
        final_df[base_col] = final_df[col]
        final_df = final_df.drop(columns=[col])

# Remove any remaining duplicate columns (keep first)
final_df = final_df.loc[:, ~final_df.columns.duplicated()]

# Debug: Check columns after merge
print(f"\nColumns after merge: {final_df.columns.tolist()}")
print(f"Number_of_Households in columns: {'Number_of_Households' in final_df.columns}")

# Create derived features
print("\nCreating derived features...")
# Check if Number_of_Households exists before creating derived features
if 'Number_of_Households' in final_df.columns:
    # Household_Size = Population / Number_of_Households
    final_df['Household_Size'] = final_df['Population'] / final_df['Number_of_Households']

    # Retail_Sales_Per_Household = Retail_Sales / Number_of_Households
    final_df['Retail_Sales_Per_Household'] = final_df['Retail_Sales'] / final_df['Number_of_Households']
else:
    print("ERROR: Number_of_Households column not found after merge!")
    print("Available columns:", final_df.columns.tolist())
    raise KeyError("Number_of_Households column missing after merge")

# Ensure Period is string
final_df['Period'] = final_df['Period'].astype(str)

# Sort by Period and City_Province
final_df = final_df.sort_values(['Period', 'City_Province']).reset_index(drop=True)

# Verify 2020.10 is preserved
oct_check = final_df[final_df['Period'] == '2020.10']
print(f"\n2020.10 rows in final data: {len(oct_check)}")
if len(oct_check) > 0:
    print("Sample 2020.10 rows with household data:")
    print(oct_check[['Period', 'City_Province', 'Number_of_Households', 'Household_Size', 'Retail_Sales_Per_Household']].head(3))

# Check for missing household data
missing = final_df[final_df['Number_of_Households'].isna()]
print(f"\nRows with missing household data: {len(missing)}")
if len(missing) > 0:
    print("Sample missing rows:")
    print(missing[['Period', 'City_Province']].head(10))

# Save the updated merged dataframe - use QUOTE_ALL to preserve strings
print(f"\nSaving to {output_file}...")
final_df.to_csv(output_file, index=False, quoting=csv.QUOTE_ALL)

print(f"\nMerge complete!")
print(f"Shape of final data: {final_df.shape}")
print(f"\nColumn names: {final_df.columns.tolist()}")
print(f"\nFirst few rows:")
print(final_df.head(5))
print(f"\nSample derived features for Busan 2020.01:")
sample = final_df[(final_df['Period'] == '2020.01') & (final_df['City_Province'] == 'Busan')]
if len(sample) > 0:
    print(sample[['Period', 'City_Province', 'Number_of_Households', 'Household_Size', 'Retail_Sales_Per_Household']])
