import pandas as pd
import io

# --- Required Columns ---
REQUIRED_COLUMNS = {
    'time': 'Time (s)',
    'altitude': 'Altitude (ft)',
    'velocity': 'Total velocity (ft/s)',
    'referenceArea':'Reference area (cm²)',
    'normalForceCoefficient':'Normal force coefficient (​)',
    'cgLocation':'CG location (in)',
    'cpLocation':'CP location (in)',
}

# --- Read CSV File ---
def load_csv(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    # Print all lines including comments
    for line in lines[:20]:  # Print first 20 lines to check structure
        print(line.strip())

    # Find the first non-metadata line (header row)
    header_line = 0
    for i, line in enumerate(lines):
        if line.startswith('# Event'):
            header_line = i - 1 # The previous line contains column names
            break

    # Clean the header line by removing the leading '#'
    header = lines[header_line].lstrip('#').strip()

    # Print the detected header row for debugging
    print(f"Detected header row: {header_line}")
    print(f"Header content: {lines[header_line]}")

    # Reconstruct CSV data, starting from the actual data rows
    csv_data = '\n'.join([header] + lines[header_line + 1:])

    # Read CSV from in-memory string
    df = pd.read_csv(io.StringIO(csv_data))

    # Strip whitespace and normalize column names
    df.columns = df.columns.str.strip().str.replace('\u200b', '')  # Remove invisible Unicode characters

    # Extract only relevant columns
    selected_columns = {key: col for key, col in REQUIRED_COLUMNS.items() if col in df.columns}

    if not selected_columns:
        print("Warning: No matching columns found in CSV. Check column names.")
        return df

    df = df[list(selected_columns.values())]
    df.rename(columns=selected_columns, inplace=True)  # Standardize column names

    print(df.head().to_string(index=False))  # Display first few rows to confirm successful import
    return df

# --- Main Execution ---
file_path = r'C:\Users\naomi\PycharmProjects\pitchfreq\Aurora_Cycle0_14-11-2024 - Copy.csv'  # Replace with actual file path
df = load_csv(file_path)
