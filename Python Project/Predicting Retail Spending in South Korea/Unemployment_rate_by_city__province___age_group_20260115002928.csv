import pandas as pd
import numpy as np
import csv

# File paths
age_group_file = '/Users/prabhatshastri/Downloads/data submission/Population by age group.csv'
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

# Read the age group file
print("Reading age group file...")
age_df = pd.read_csv(age_group_file)

# Filter for Population[Person] only (not Male/Female)
age_df = age_df[age_df['Item'] == 'Population[Person]'].copy()

# Get the administrative district and age group columns
age_df = age_df[['By Administrative District', 'By Age Group (Five-Year)'] + 
                 [col for col in age_df.columns if 'Month' in col]].copy()

# Rename columns for easier handling
age_df = age_df.rename(columns={'By Administrative District': 'City_Province', 
                                'By Age Group (Five-Year)': 'Age_Group'})

# Define age group mapping to buckets
age_mapping = {
    '0-4 Years old': 'below_15',
    '5-9 Years old': 'below_15',
    '10-14 Years old': 'below_15',
    '15-19 Years old': '15_29',
    '20-24 Years old': '15_29',
    '25-29 Years old': '15_29',
    '30-34 Years old': '30_59',
    '35-39 Years old': '30_59',
    '40-44 Years old': '30_59',
    '45-49 Years old': '30_59',
    '50-54 Years old': '30_59',
    '55-59 Years old': '30_59',
    '60-64 Years old': '60_Plus',
    '65-69 Years old': '60_Plus',
    '70-74 Years old': '60_Plus',
    '75-79 Years old': '60_Plus',
    '80-84 Years old': '60_Plus',
    '85-89 Years old': '60_Plus',
    '90-94 Years old': '60_Plus',
    '95-99 Years old': '60_Plus',
    '100 Years old & over': '60_Plus',
    'Total': None  # Skip Total rows
}

# Filter out Total rows and rows with unmapped age groups
age_df = age_df[age_df['Age_Group'].isin(age_mapping.keys())].copy()
age_df = age_df[age_df['Age_Group'] != 'Total'].copy()

# Map age groups to buckets
age_df['Age_Bucket'] = age_df['Age_Group'].map(age_mapping)

# Remove "Whole country" entries
age_df = age_df[age_df['City_Province'] != 'Whole country'].copy()

# Melt the monthly columns to long format
month_cols = [col for col in age_df.columns if 'Month' in col]

# Create a mapping from column names to normalized periods
# Read the raw column names to preserve period format
col_to_period = {}
for col in month_cols:
    # Extract period from column name like "2020.01 Month" or '"2020.10 Month"'
    period_raw = col.replace(' Month', '').strip().replace('"', '').replace("'", '')
    # Normalize the period
    period_normalized = normalize_period(period_raw)
    col_to_period[col] = period_normalized

age_melted = age_df.melt(
    id_vars=['City_Province', 'Age_Group', 'Age_Bucket'],
    value_vars=month_cols,
    var_name='Period_Raw',
    value_name='Population'
)

# Map column names to normalized periods using our mapping
age_melted['Period'] = age_melted['Period_Raw'].map(col_to_period)

# Aggregate by Period, City_Province, and Age_Bucket (ensure no duplicates)
age_aggregated = age_melted.groupby(['Period', 'City_Province', 'Age_Bucket'])['Population'].sum().reset_index()

# Pivot to wide format (one column per age bucket)
age_pivoted = age_aggregated.pivot_table(
    index=['Period', 'City_Province'],
    columns='Age_Bucket',
    values='Population',
    aggfunc='sum'
).reset_index()

# Remove any duplicate rows
age_pivoted = age_pivoted.drop_duplicates(subset=['Period', 'City_Province'])

# Rename columns to match desired format
age_pivoted = age_pivoted.rename(columns={
    'below_15': 'Population_below_15',
    '15_29': 'Population_15_29',
    '30_59': 'Population_30_59',
    '60_Plus': 'Population_60_Plus'
})

# Standardize city/province names
age_pivoted['City_Province'] = age_pivoted['City_Province'].str.replace('Sejong_si', 'Sejong')
age_pivoted['City_Province'] = age_pivoted['City_Province'].str.replace('"', '').str.strip()

# Handle case sensitivity and name variations
age_pivoted['City_Province'] = age_pivoted['City_Province'].str.replace('sejong', 'Sejong', case=False)
age_pivoted['City_Province'] = age_pivoted['City_Province'].str.replace('Jeju$', 'Jeju-do', regex=True)

# Read the existing merged file - read Period as string to preserve format
print("Reading existing merged file...")
merged_df = pd.read_csv(merged_file, dtype={'Period': str})

# Ensure Period is normalized in merged file (as string)
merged_df['Period'] = merged_df['Period'].apply(normalize_period)
merged_df['Period'] = merged_df['Period'].astype(str)

# Check for actual duplicates (same Period and City_Province as strings)
print(f"Checking for duplicates (before: {len(merged_df)} rows)...")
duplicates = merged_df[merged_df.duplicated(subset=['Period', 'City_Province'], keep=False)]
print(f"Actual duplicate rows: {len(duplicates)}")
if len(duplicates) > 0:
    print("Sample duplicates:")
    print(duplicates[['Period', 'City_Province']].head(10))
    # Remove only actual duplicates
    merged_df = merged_df.drop_duplicates(subset=['Period', 'City_Province'], keep='first')
    print(f"After removing duplicates: {len(merged_df)} rows")

# Check if merged_df already has age group columns and remove them if they exist
age_cols_to_remove = ['Population_15_29', 'Population_30_59', 'Population_60_Plus', 'Population_below_15']
for col in age_cols_to_remove:
    if col in merged_df.columns:
        merged_df = merged_df.drop(columns=[col])

# Merge the age group data with the existing merged dataset
print("Merging age group data...")
final_df = pd.merge(
    merged_df,
    age_pivoted,
    on=['Period', 'City_Province'],
    how='left'
)

# Remove any duplicate columns (keep first occurrence)
final_df = final_df.loc[:, ~final_df.columns.duplicated()]

# Remove columns with _x or _y suffixes (these are duplicates from merge)
cols_to_drop = [col for col in final_df.columns if col.endswith('_x') or col.endswith('_y')]
final_df = final_df.drop(columns=cols_to_drop)

# Ensure Period is string
final_df['Period'] = final_df['Period'].astype(str)

# Sort by Period and City_Province
final_df = final_df.sort_values(['Period', 'City_Province']).reset_index(drop=True)

# Verify 2020.10 is preserved
oct_check = final_df[final_df['Period'] == '2020.10']
print(f"\n2020.10 rows in final data: {len(oct_check)}")

# Save the updated merged dataframe - use QUOTE_ALL to preserve strings
print(f"Saving to {output_file}...")
final_df.to_csv(output_file, index=False, quoting=csv.QUOTE_ALL)  # QUOTE_ALL to preserve strings

print(f"\nMerge complete!")
print(f"Shape of final data: {final_df.shape}")
print(f"\nColumn names: {final_df.columns.tolist()}")
print(f"\nFirst few rows:")
print(final_df.head(10))
print(f"\nMissing age group data:")
if 'Population_below_15' in final_df.columns:
    missing = final_df[final_df['Population_below_15'].isna()]
    print(f"Rows with missing age data: {len(missing)}")
    if len(missing) > 0:
        print(missing[['Period', 'City_Province']].head(10))
else:
    print("Age group columns not found - check column names above")
