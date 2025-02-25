from flask import Flask, render_template, request, jsonify
import pandas as pd
import re

app = Flask(__name__)

# Load the cleaned dataset
data = pd.read_csv('cleaned_training_data.csv', dtype={'Ratio (Gly:Starch:Carbon)': str})
data.columns = data.columns.str.strip()

# Function to clean 'Heat (°C)' column
def clean_heat_column(value):
    match = re.findall(r'\d+', str(value))
    if len(match) == 2:
        return (int(match[0]) + int(match[1])) / 2  # Average of range
    elif len(match) == 1:
        return int(match[0])
    else:
        return None

# Apply cleaning to 'Heat (°C)'
data['Heat (°C)'] = data['Heat (°C)'].apply(clean_heat_column)

@app.route('/', methods=['GET', 'POST'])
def index():
    try:
        flexibility_levels = data['Flexibility'].unique().tolist()
    except KeyError:
        return render_template('index.html', error="Error: 'Flexibility' column not found in the dataset.")

    return render_template('index.html', flexibility_levels=flexibility_levels)

@app.route('/get_data', methods=['POST'])
def get_data():
    selected_flexibility = request.json.get('flexibility')
    
    if not selected_flexibility:
        return jsonify({"error": "No flexibility selected"}), 400

    try:
        # Filter data based on selected flexibility
        filtered_data = data[data['Flexibility'] == selected_flexibility]

        if filtered_data.empty:
            return jsonify({"error": "No data found for the selected flexibility"}), 404

        # Aggregate data for each Real Use Case
        aggregated_data = filtered_data.groupby('Real Use Case').agg({
            'Heat (°C)': 'mean',
            'Tensile Strength (MPa)': 'mean',
            'Elongation at Break (%)': 'mean',
            'Ratio (Gly:Starch:Carbon)': lambda x: x.mode().iloc[0] if not x.empty else x.iloc[0]
        }).reset_index()

        return jsonify(aggregated_data.to_dict(orient='records'))
    except KeyError as e:
        return jsonify({"error": f"Missing column: {str(e)}"}), 500

if __name__ == '__main__':
    app.run(debug=True)

