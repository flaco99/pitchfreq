import pandas as pd
import io

# please don't be weird and make sure you export with normal units:
# time in seconds, distance in meters or feet or inches, area in cm² or m²

# Required Columns
REQUIRED_COLUMNS = {
    'time': 'Time (s)',
    'altitude': 'Altitude (ft)',
    'velocity': 'Total velocity (ft/s)',
    'referenceArea':'Reference area',
    'normalForceCoefficient':'Normal force coefficient',
    'cgLocation':'CG location (in)',
    'cpLocation':'CP location (in)',
}

# Unit Conversion Factors
UNIT_CONVERSIONS = {
    ('ft', 'm'): 0.3048,
    ('ft/s', 'm/s'): 0.3048,
    ('lb·ft²', 'kg·m²'): 0.0421401,
}

# Load CSV File
def load_csv(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        return lines

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
    for key, col_substring in REQUIRED_COLUMNS.items():
        for col in df.columns:
            if col_substring.lower() in col.lower():  # Case-insensitive substring search
                selected_columns[key] = col
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

    print(df.head(50).to_string(index=False))  # Display first few rows to confirm successful import
    return df

# --- Main Execution ---
file_path = r'C:\Users\naomi\PycharmProjects\pitchfreq\Aurora_Cycle0_14-11-2024 - Copy.csv'  # Replace with actual file path
lines = load_csv(file_path)
df = get_required_columns(lines)
