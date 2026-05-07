import pandas as pd
import numpy as np
import csv

# File paths
unemployment_file = '/Users/prabhatshastri/Downloads/data submission/Unemployment_rate_by_city__province___age_group_20260115002928.csv'
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

# Function to convert quarterly period to monthly periods
def quarter_to_months(quarter_str):
    """
    Convert quarterly period like '2020.1/4' to list of monthly periods
    2020.1/4 -> [2020.01, 2020.02, 2020.03]
    2020.2/4 -> [2020.04, 2020.05, 2020.06]
    2020.3/4 -> [2020.07, 2020.08, 2020.09]
    2020.4/4 -> [2020.10, 2020.11, 2020.12]
    """
    quarter_str = str(quarter_str).replace('"', '').strip()
    if '/' in quarter_str:
        year_quarter = quarter_str.split('/')[0]  # e.g., "2020.1"
        if '.' in year_quarter:
            year, quarter = year_quarter.split('.')
            quarter = int(quarter)
            
            # Calculate months for each quarter
            if quarter == 1:
                months = [1, 2, 3]
            elif quarter == 2:
                months = [4, 5, 6]
            elif quarter == 3:
                months = [7, 8, 9]
            elif quarter == 4:
                months = [10, 11, 12]
            else:
                return []
            
            # Return list of normalized monthly periods
            return [f"{year}.{str(m).zfill(2)}" for m in months]
    return []

print("Reading unemployment file...")
# Read unemployment file - use csv reader to preserve period format in column names
with open(unemployment_file, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    rows = list(reader)
    
    # First row is header
    header = rows[0]
    
    # Extract province, age group, and quarterly period columns
    province_col_idx = 0
    age_group_col_idx = 1
    quarter_cols = header[2:]  # All columns after province and age group
    
    # Create mapping from quarterly column names to their indices
    quarter_col_map = {}
    for i, col in enumerate(quarter_cols, start=2):
        quarter_col_map[col] = i
    
    # Read data rows
    data_rows = rows[1:]

# Now read with pandas for easier manipulation
unemp_df = pd.read_csv(unemployment_file)

# Filter out "Total" province rows (we want individual provinces)
unemp_df = unemp_df[unemp_df['By province'] != 'Total'].copy()

# Filter out "Total" age group rows (we want specific age groups)
unemp_df = unemp_df[unemp_df['By age group'] != 'Total'].copy()

# Standardize province names
unemp_df['By province'] = unemp_df['By province'].str.replace('"', '').str.strip()
unemp_df['By province'] = unemp_df['By province'].str.replace('Sejong_si', 'Sejong')
unemp_df['By province'] = unemp_df['By province'].str.replace('sejong', 'Sejong', case=False)

# Standardize age group names
unemp_df['By age group'] = unemp_df['By age group'].str.replace('"', '').str.strip()

# Map age groups to standardized names
age_group_mapping = {
    '15-29 Years old': '15_29',
    '30-59 Years old': '30_59',
    '60 Years old and over': '60_Plus'
}
unemp_df['Age_Group'] = unemp_df['By age group'].map(age_group_mapping)

# Get quarterly column names (excluding province and age group)
quarter_cols = [col for col in unemp_df.columns if col not in ['By province', 'By age group', 'Age_Group']]

# Melt the quarterly columns to long format
unemp_melted = unemp_df.melt(
    id_vars=['By province', 'Age_Group'],
    value_vars=quarter_cols,
    var_name='Quarter_Period',
    value_name='Unemployment_Rate'
)

# Convert quarterly periods to monthly periods
print("Converting quarterly data to monthly...")
monthly_rows = []
for _, row in unemp_melted.iterrows():
    quarter_period = str(row['Quarter_Period']).replace('"', '').strip()
    monthly_periods = quarter_to_months(quarter_period)
    
    for month_period in monthly_periods:
        monthly_rows.append({
            'City_Province': row['By province'],
            'Age_Group': row['Age_Group'],
            'Period': month_period,
            'Unemployment_Rate': row['Unemployment_Rate']
        })

unemp_monthly = pd.DataFrame(monthly_rows)

# Pivot age groups to columns (wide format)
unemp_pivoted = unemp_monthly.pivot_table(
    index=['Period', 'City_Province'],
    columns='Age_Group',
    values='Unemployment_Rate',
    aggfunc='first'  # Should be same value for all months in quarter
).reset_index()

# Rename columns
unemp_pivoted = unemp_pivoted.rename(columns={
    '15_29': 'Unemployment_Rate_15_29',
    '30_59': 'Unemployment_Rate_30_59',
    '60_Plus': 'Unemployment_Rate_60_Plus'
})

# Ensure Period is string
unemp_pivoted['Period'] = unemp_pivoted['Period'].astype(str)

print(f"Unemployment data shape: {unemp_pivoted.shape}")
print(f"Sample unemployment data:")
print(unemp_pivoted.head(10))

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

# Merge unemployment data
print("\nMerging unemployment data...")
final_df = pd.merge(
    merged_df,
    unemp_pivoted,
    on=['Period', 'City_Province'],
    how='left'
)

# Remove any duplicate columns
final_df = final_df.loc[:, ~final_df.columns.duplicated()]

# Remove columns with _x or _y suffixes if any
cols_to_drop = [col for col in final_df.columns if col.endswith('_x') or col.endswith('_y')]
if cols_to_drop:
    final_df = final_df.drop(columns=cols_to_drop)

# Ensure Period is string
final_df['Period'] = final_df['Period'].astype(str)

# Sort by Period and City_Province
final_df = final_df.sort_values(['Period', 'City_Province']).reset_index(drop=True)

# Verify 2020.10 is preserved
oct_check = final_df[final_df['Period'] == '2020.10']
print(f"\n2020.10 rows in final data: {len(oct_check)}")
if len(oct_check) > 0:
    print("Sample 2020.10 rows:")
    print(oct_check[['Period', 'City_Province', 'Unemployment_Rate_15_29', 'Unemployment_Rate_30_59']].head(3))

# Check for missing unemployment data
missing = final_df[final_df['Unemployment_Rate_15_29'].isna()]
print(f"\nRows with missing unemployment data: {len(missing)}")
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
