import pandas as pd
import io

# please don't be weird and make sure you export with normal units:
# time in seconds, distance in meters or feet or inches, area in cm² or m² or in²

# Required Columns
REQUIRED_COLUMNS = {
    'time': 'Time',
    'altitude': 'Altitude',
    'velocity': 'Total velocity',
    'referenceArea':'Reference area',
    'normalForceCoefficient':'Normal force coefficient',
    'cgLocation':'CG location',
    'cpLocation':'CP location',
}

# Unit Conversion Factors
UNIT_CONVERSIONS = {
    ('in', 'm'): 0.0254,
    ('ft', 'm'): 0.3048,
    ('ft/s', 'm/s'): 0.3048,
    ('cm²','m²'): 0.0001,
    ('in²','m²'): 0.00064516,
    ('lb·ft²', 'kg·m²'): 0.0421401,
    ('', ''): 1.0
}

# Load CSV File
def load_csv(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        return lines

# Extract Unit from Column Name
def extract_unit(column_name):
    """Extracts the unit from a column name if present inside parentheses."""
    if '(' in column_name and ')' in column_name:
        return column_name.split('(')[-1].split(')')[0]
    return None

# Convert Units
def convert_units(df, column_units):
    for key, expected_unit in REQUIRED_COLUMNS.values():
        actual_unit = column_units.get(key)

        if actual_unit and actual_unit != expected_unit:
            conversion_factor = UNIT_CONVERSIONS.get((actual_unit, expected_unit))

            if conversion_factor:
                df[key] *= conversion_factor
                print(f"Converted {key} from {actual_unit} to {expected_unit}.")
            else:
                print(f"Warning: No conversion available for {key} from {actual_unit} to {expected_unit}.")
    return df

# Get required columns
def get_required_columns(lines):
    # Find the first non-metadata line (header row)
    header_line = 0
    for i, line in enumerate(lines):
        if line.startswith('# Event'):
            header_line = i - 1 # The previous line contains column names
            break

    # Clean the header line by removing the leading '#'
    header = lines[header_line].lstrip('#').strip()

    # Reconstruct CSV data, starting from the actual data rows
    csv_data = '\n'.join([header] + lines[header_line + 1:])

    # Read CSV from in-memory string
    df = pd.read_csv(io.StringIO(csv_data))

    # Strip whitespace and normalize column names
    df.columns = df.columns.str.strip().str.replace('\u200b', '')  # Remove invisible Unicode characters

    # Match required columns using partial names
    selected_columns = {}
    column_units = {}
    for key, col_substring in REQUIRED_COLUMNS.items():
        for col in df.columns:
            if col_substring.lower() in col.lower():  # Case-insensitive substring search
                selected_columns[key] = col
                column_units[key] = extract_unit(col)
                break  # Stop searching once the first match is found
    if not selected_columns:
        print("Warning: No matching columns found in CSV. Check column names.")
        return df

    # Ensure all selected columns exist in the DataFrame before selecting
    valid_columns = []
    for col in selected_columns.values():
        if col in df.columns:
            valid_columns.append(col)

    df = df[valid_columns]
    df.rename(columns=selected_columns, inplace=True)  # Standardize column names

    # Convert units using separate function
    #df = convert_units(df, column_units)
    print("columnunits: ")
    print(column_units)

    print(df.head(50).to_string(index=False))  # Display first few rows to confirm successful import
    return df

# --- Main Execution ---
file_path = r'C:\Users\naomi\PycharmProjects\pitchfreq\Aurora_Cycle0_14-11-2024 - Copy.csv'  # Replace with actual file path
lines = load_csv(file_path)
df = get_required_columns(lines)
