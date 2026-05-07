import pandas as pd
import numpy as np
import csv

# Read the retail sales file with multi-level headers
retail_file = '/Users/prabhatshastri/Downloads/data submission/Large_retail_nonspecialized_stores_sales_by_city_and_province_20260102204454.csv'
population_file = '/Users/prabhatshastri/Downloads/data submission/Resident_Population_by_City__County__and_District_20260104192233.csv'

# Normalize period format function
def normalize_period(period):
    # Convert to string and clean up
    period_str = str(period).replace('"', '').strip()
    
    # Remove trailing "p)" for provisional data
    if period_str.endswith(' p)'):
        period_str = period_str[:-3].strip()
    
    # Parse the period
    if '.' in period_str:
        parts = period_str.split('.')
        year = parts[0]
        month_part = parts[1].split()[0]  # Remove any remaining trailing text
        
        # Pad month to 2 digits (e.g., "1" -> "01", "10" -> "10")
        # This ensures "2020.1" becomes "2020.01" and "2020.10" stays "2020.10"
        month = month_part.zfill(2)
        return f"{year}.{month}"
    return period_str

# Read retail sales - first read as text to preserve Period format
with open(retail_file, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    lines = list(reader)
    # Extract Period values from data rows (skip header rows 0 and 1)
    period_values = []
    for row in lines[2:]:  # Start from row 2 (0-indexed)
        # Get first column value (CSV reader handles quotes correctly)
        if len(row) > 0:
            period_val = row[0].strip().replace('"', '')
            period_values.append(period_val)

# Now read with proper headers
retail_df = pd.read_csv(retail_file, skiprows=0, header=[0, 1])

# Flatten the multi-level columns
new_cols = []
for col in retail_df.columns:
    if col[0] == 'Period' or col[1] == 'Period':
        new_cols.append('Period')
    else:
        new_cols.append(col[0])  # Use city/province name from first level

retail_df.columns = new_cols

# Replace Period column with the preserved string values
retail_df['Period'] = period_values

# Clean up and normalize the Period column
retail_df['Period'] = retail_df['Period'].apply(normalize_period)

# Melt the retail data to long format
retail_melted = retail_df.melt(
    id_vars=['Period'],
    var_name='City_Province',
    value_name='Retail_Sales'
)

# Read population file - first read as text to preserve Period format
with open(population_file, 'r', encoding='utf-8') as f:
    reader = csv.reader(f)
    lines = list(reader)
    # Extract Period values from data rows (skip row 0 title, rows 1-2 are headers)
    pop_period_values = []
    for row in lines[3:]:  # Start from row 3 (0-indexed)
        # Get first column value (CSV reader handles quotes correctly)
        if len(row) > 0:
            period_val = row[0].strip().replace('"', '')
            pop_period_values.append(period_val)

# Now read with proper headers (skip first row which is title)
pop_df = pd.read_csv(population_file, skiprows=1, header=[0, 1])

# Flatten the multi-level columns for population
new_pop_cols = []
for col in pop_df.columns:
    if col[0] == 'Period' or col[1] == 'Period':
        new_pop_cols.append('Period')
    else:
        # Keep the full column name to extract city name later
        new_pop_cols.append(f"{col[0]}_{col[1]}")

pop_df.columns = new_pop_cols

# Replace Period column with the preserved string values
pop_df['Period'] = pop_period_values

# Clean up and normalize the Period column
pop_df['Period'] = pop_df['Period'].apply(normalize_period)

# Extract Total, Male, and Female population columns separately
total_pop_cols = [col for col in pop_df.columns if 'Koreans (Total) (Person)' in col or col == 'Period']
male_pop_cols = [col for col in pop_df.columns if 'Koreans (Male) (Person)' in col or col == 'Period']
female_pop_cols = [col for col in pop_df.columns if 'Koreans (Female) (Person)' in col or col == 'Period']

pop_total = pop_df[total_pop_cols].copy()
pop_male = pop_df[male_pop_cols].copy()
pop_female = pop_df[female_pop_cols].copy()

# Function to rename columns and extract city/province names
def rename_pop_columns(df, pop_type):
    city_mapping = {}
    for col in df.columns:
        if col == 'Period':
            city_mapping[col] = 'Period'
        else:
            # Extract city name (everything before the first underscore after the city name)
            city_name = col.split('_Koreans')[0]
            city_mapping[col] = city_name
    return df.rename(columns=city_mapping)

pop_total = rename_pop_columns(pop_total, 'Total')
pop_male = rename_pop_columns(pop_male, 'Male')
pop_female = rename_pop_columns(pop_female, 'Female')

# Melt each population dataset to long format
pop_total_melted = pop_total.melt(
    id_vars=['Period'],
    var_name='City_Province',
    value_name='Population_Total'
)

pop_male_melted = pop_male.melt(
    id_vars=['Period'],
    var_name='City_Province',
    value_name='Population_Male'
)

pop_female_melted = pop_female.melt(
    id_vars=['Period'],
    var_name='City_Province',
    value_name='Population_Female'
)

# Remove "Whole country" entries as they're not in retail data
pop_total_melted = pop_total_melted[pop_total_melted['City_Province'] != 'Whole country'].copy()
pop_male_melted = pop_male_melted[pop_male_melted['City_Province'] != 'Whole country'].copy()
pop_female_melted = pop_female_melted[pop_female_melted['City_Province'] != 'Whole country'].copy()

# Standardize city/province names for merging
# Retail data uses: Sejong, but population uses: Sejong_si
# Standardize all to 'Sejong' for consistency
pop_total_melted['City_Province'] = pop_total_melted['City_Province'].str.replace('Sejong_si', 'Sejong')
pop_male_melted['City_Province'] = pop_male_melted['City_Province'].str.replace('Sejong_si', 'Sejong')
pop_female_melted['City_Province'] = pop_female_melted['City_Province'].str.replace('Sejong_si', 'Sejong')

# Aggregate population data by Period and City_Province (take mean if multiple values exist)
pop_total_melted = pop_total_melted.groupby(['Period', 'City_Province'])['Population_Total'].mean().reset_index()
pop_male_melted = pop_male_melted.groupby(['Period', 'City_Province'])['Population_Male'].mean().reset_index()
pop_female_melted = pop_female_melted.groupby(['Period', 'City_Province'])['Population_Female'].mean().reset_index()

# Merge all population data together
pop_melted = pd.merge(
    pop_total_melted,
    pop_male_melted,
    on=['Period', 'City_Province'],
    how='outer'
)
pop_melted = pd.merge(
    pop_melted,
    pop_female_melted,
    on=['Period', 'City_Province'],
    how='outer'
)

# Rename Population_Total to Population for consistency
pop_melted = pop_melted.rename(columns={'Population_Total': 'Population'})

# Merge the two dataframes (inner join to keep only records with both datasets)
merged_df = pd.merge(
    retail_melted,
    pop_melted,
    on=['Period', 'City_Province'],
    how='inner'
)

# Period values should already be normalized, but ensure consistency
merged_df['Period'] = merged_df['Period'].apply(normalize_period)

# Ensure Period is explicitly a string (not float)
merged_df['Period'] = merged_df['Period'].astype(str)

# Sort by Period and City_Province
merged_df = merged_df.sort_values(['Period', 'City_Province']).reset_index(drop=True)

# Verify we have all months including .10
print(f"\nChecking for 2020.10 in merged data:")
oct_rows = merged_df[merged_df['Period'] == '2020.10']
print(f"Rows with 2020.10: {len(oct_rows)}")
if len(oct_rows) > 0:
    print(oct_rows[['Period', 'City_Province']].head(5))

# Save the merged dataframe - ensure Period is quoted to preserve as string
output_file = '/Users/prabhatshastri/Downloads/data submission/merged_retail_population_data.csv'
merged_df.to_csv(output_file, index=False, quoting=csv.QUOTE_ALL)  # QUOTE_ALL to preserve strings

print(f"Merged data saved to: {output_file}")
print(f"\nShape of merged data: {merged_df.shape}")
print(f"\nFirst few rows:")
print(merged_df.head(20))
print(f"\nColumn names: {merged_df.columns.tolist()}")
print(f"\nUnique cities/provinces: {merged_df['City_Province'].nunique()}")
print(f"\nDate range: {merged_df['Period'].min()} to {merged_df['Period'].max()}")
