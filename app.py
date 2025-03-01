from flask import Flask, render_template, request, jsonify
import pandas as pd
import re

app = Flask(__name__)

# Load the cleaned dataset
try:
    data = pd.read_csv('cleaned_training_data.csv', dtype={'Ratio (Gly:Starch:Carbon)': str})
    data.columns = data.columns.str.strip()  # Ensure column names are clean
except Exception as e:
    print(f"Error loading dataset: {e}")
    data = None

# Function to clean 'Heat (°C)' column
def clean_heat_column(value):
    match = re.findall(r'\d+', str(value))
    if len(match) == 2:
        return (int(match[0]) + int(match[1])) / 2  # Average of range
    elif len(match) == 1:
        return int(match[0])
    else:
        return None

# Apply cleaning to 'Heat (°C)' if dataset is loaded
if data is not None and 'Heat (°C)' in data.columns:
    data['Heat (°C)'] = data['Heat (°C)'].apply(clean_heat_column)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/get_ratio', methods=['POST'])
def get_ratio():
    try:
        if data is None:
            return jsonify({"error": "Dataset failed to load"}), 500

        tensile_strength = request.json.get('tensile_strength')
        elongation = request.json.get('elongation')

        if tensile_strength is None or elongation is None:
            return jsonify({"error": "Missing input values"}), 400

        # Convert inputs to float
        tensile_strength = float(tensile_strength)
        elongation = float(elongation)

        # Check if required columns exist
        required_columns = ['Tensile Strength (MPa)', 'Elongation at Break (%)', 'Ratio (Gly:Starch:Carbon)']
        if not all(col in data.columns for col in required_columns):
            return jsonify({"error": "Dataset missing required columns"}), 500

        # Find the closest matching row
        closest_row = data.iloc[((data['Tensile Strength (MPa)'] - tensile_strength).abs() + 
                                 (data['Elongation at Break (%)'] - elongation).abs()).idxmin()]
        
        ratio = closest_row['Ratio (Gly:Starch:Carbon)']

        return jsonify({"ratio": ratio})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)
