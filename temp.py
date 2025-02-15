import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import ticker
import io

# please don't be weird and make sure you export with normal units:
# time in seconds, distance in meters or feet or inches, area in cm² or m² or in²

################################# INPUT HERE #################################
INERTIA_FULL_TANK = 235050.8943 # lb-in^2
INERTIA_DRY = 192890.4115 # lb-in^2
##############################################################################

# Required Columns
REQUIRED_COLUMNS = [
    'Time',
    'Altitude',
    'Total velocity',
    'Reference area',
    'Normal force coefficient',
    'CG location',
    'CP location',
]

# Unit Conversion Factors
UNIT_CONVERSIONS = {
    ('in', 'm'): 0.0254,
    ('ft', 'm'): 0.3048,
    ('ft/s', 'm/s'): 0.3048,
    ('cm²','m²'): 0.0001,
    ('in²','m²'): 0.00064516,
    ('lb·ft²', 'kg·m²'): 0.0421401,
}

# Required Units and Columns
REQUIRED_UNITS = {'Time': 's', 'Altitude': 'm', 'Total velocity': 'm/s', 'Reference area': 'm²',
                  'Normal force coefficient': '', 'CG location': 'm', 'CP location': 'm'}
REQUIRED_COLUMN_NAMES = ['Time (s)', 'Altitude (m)', 'Total velocity (m/s)', 'Reference area (m²)',
                   'Normal force coefficient ()', 'CG location (m)', 'CP location (m)']

# Constants
BURNOUT_TIME = 0 # placeholder
INERTIA_FULL_TANK *= 0.0002926397  # converted to kg-m^2
INERTIA_DRY *= 0.0002926397  # converted to kg-m^2

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
def convert_units(df, column_units, selected_columns):
    for key, required_unit in REQUIRED_UNITS.items():
        keyNameWithOriginalUnit = selected_columns[key]
        actual_unit = column_units.get(key)
        if actual_unit and actual_unit != required_unit:
            conversion_factor = UNIT_CONVERSIONS.get((actual_unit, required_unit))
            if conversion_factor:
                df[keyNameWithOriginalUnit] = pd.to_numeric(df[keyNameWithOriginalUnit], errors='coerce')  # Ensure numeric data
                df[keyNameWithOriginalUnit] *= conversion_factor
                # Update the column name to reflect the new unit
                new_column_name = f"{key} ({required_unit})"
                df.rename(columns={keyNameWithOriginalUnit: new_column_name}, inplace=True)
            else:
                print(f"Warning: No conversion available for {keyNameWithOriginalUnit} from {actual_unit} to {required_unit}.")
    return df

def get_events(df):
    # Extract event markers and associate them with the latest timestamp
    events = []
    latest_timestamp = 0.0  # Track the most recent valid timestamp

    for index, row in df.iterrows():
        time_value = row['Time (s)']

        # Check if the value is a numeric timestamp
        if isinstance(time_value, (int, float)) or (
                isinstance(time_value, str) and time_value.replace('.', '', 1).isdigit()):
            latest_timestamp = float(time_value)  # Update the latest valid timestamp

        # If the value starts with '# Event', treat it as an event description
        elif isinstance(time_value, str) and time_value.startswith('# Event'):
            events.append((latest_timestamp, time_value.strip()))
            if 'BURNOUT' in time_value.strip():
                global BURNOUT_TIME
                BURNOUT_TIME = latest_timestamp
    return events

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
    for col_substring in REQUIRED_COLUMNS:
        for col in df.columns:
            if col_substring.lower() in col.lower():  # Case-insensitive substring search
                selected_columns[col_substring] = col
                column_units[col_substring] = extract_unit(col)
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
    df = convert_units(df, column_units, selected_columns)

    e = get_events(df)
    print('events:')
    print(e)

    # Remove rows where critical columns contain NaN
    df = df.dropna(subset=REQUIRED_COLUMN_NAMES)

    return df

def get_air_density(altitude):
    # todo: make more accurate
    # Returns air density (kg/m³) for a given altitude (m)
    # Data from the table (Altitude in meters and corresponding Air Density in kg/m³)
    ALTITUDES = np.array([0, 1000, 2000, 3000, 4000, 5000, 6000, 7000, 8000, 9000, 10000,
                          15000, 20000, 25000, 30000, 40000, 50000, 60000, 70000, 80000])
    DENSITIES = np.array([1.225, 1.112, 1.007, 0.9093, 0.8194, 0.7364, 0.6601, 0.5900,
                          0.5258, 0.4671, 0.4135, 0.1948, 0.08891, 0.04008, 0.01841,
                          0.003996, 0.001027, 0.0003097, 0.00008283, 0.00001846])

    if altitude > ALTITUDES[-1]:
        return 0.00001
    return np.interp(altitude, ALTITUDES, DENSITIES)

def get_inertia(time):
    # Returns longitudinal moment of inertia (kg/m²) for a given time (s)
    global INERTIA_FULL_TANK, INERTIA_DRY
    if float(time) < BURNOUT_TIME:
        return INERTIA_FULL_TANK
    if float(time) >= BURNOUT_TIME:
        return INERTIA_DRY

def add_air_and_inertia(df):
    # add air density column
    if 'Altitude (m)' not in df.columns:
        raise KeyError("The DataFrame must contain an 'Altitude (m)' column.")
    altitude_values = df['Altitude (m)']
    air_density_values = altitude_values.apply(get_air_density)
    df['Air Density (kg/m³)'] = air_density_values

    # add inertia column
    if 'Time (s)' not in df.columns:
        raise KeyError("The DataFrame must contain an 'Time (s)' column.")
    time_values = df['Time (s)']
    inertia_values = time_values.apply(get_inertia)
    df['Longitudinal moment of inertia (kg·m²)'] = inertia_values

    return df

def add_pitch_freq(df):
    # Add a column for natural pitch frequency in rad/sec
    df['Pitch Frequency (rad/sec)'] = np.sqrt(
        ((df['Air Density (kg/m³)'] / 2) * (df['Total velocity (m/s)'] ** 2) *
         df['Reference area (m²)'] * df['Normal force coefficient ()'] *
         (df['CP location (m)'] - df['CG location (m)'])) /
        df['Longitudinal moment of inertia (kg·m²)']
    )

    # Add a column for pitch frequency in deg/sec
    df['Pitch Frequency (deg/sec)'] = df['Pitch Frequency (rad/sec)'] * 57.2958

    # Add a column for pitch frequency in Hz
    df['Pitch Frequency (Hz)'] = df['Pitch Frequency (deg/sec)'] / 360.0

    return df

def plot_pitch_frequency(df):
    # Generate a plot of Pitch Frequency (Hz) vs Time (s)
    plt.figure(figsize=(10, 5))
    plt.plot(df['Time (s)'], df['Pitch Frequency (Hz)'], marker='o', linestyle='-', color='b', label='Pitch Frequency (Hz)')

    plt.xlabel('Time (s)')
    plt.ylabel('Pitch Frequency (Hz)')
    plt.title('Pitch Frequency vs Time')

    # Format the x-axis to use nice round numbers
    ax = plt.gca()
    ax.xaxis.set_major_locator(ticker.MaxNLocator(nbins=10, integer=True))  # Automatically choose best tick spacing

    plt.legend()
    plt.grid()
    plt.show()

# Main Execution
test_file_path = r'C:\Users\naomi\PycharmProjects\pitchfreq\test.csv'
file_path = r'C:\Users\naomi\PycharmProjects\pitchfreq\Aurora_Cycle0_14-11-2024 - Copy.csv'
lines = load_csv(file_path)
df = get_required_columns(lines)
df = add_air_and_inertia(df)
add_pitch_freq(df)
plot_pitch_frequency(df)
print(df.head(10).to_string(index=False))  # Display first few rows
