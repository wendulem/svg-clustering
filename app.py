from flask import Flask, request, jsonify, render_template
from flask_cors import CORS
import numpy as np
from weasyprint import HTML
# Import your helper functions
from parse_svg import parse_svg_and_preprocess, cluster_paths, map_clusters_to_paths

app = Flask(__name__)
CORS(app)  # Enable CORS for cross-origin requests

@app.route('/upload', methods=['POST'])
def upload_file():
    if 'file' not in request.files:
        return 'No file part', 400
    file = request.files['file']
    if file.filename == '' or not file.filename.endswith('.svg'):
        return 'No selected file or invalid format', 400
    
    svg_content = file.read().decode('utf-8')

    # # UNCOMMENT DURING LOCAL TESTING - POP INTO ITS OWN TEST CASE
    # def load_svg_as_string(file_path):
    #     with open(file_path, 'r') as file:
    #         svg_string = file.read()
    #     return svg_string
    # # Example usage
    # file_path = 'henley.svg'
    # svg_content = load_svg_as_string(file_path)

    # Process the SVG content using the helper functions
    paths_data = parse_svg_and_preprocess(svg_content)

    # Extract centroids for clustering. Ensure points are valid (not None)
    points = np.array([path['centroid'] for path in paths_data if path['centroid'] is not None])

    if len(points) > 0:
        cluster_labels, points = cluster_paths(paths_data, points)
        layers_json = map_clusters_to_paths(paths_data, cluster_labels, points)
        # print(layers_json)
    else:
        layers_json = {"layers": []}

    # You can return layers_json as a JSON response
    return jsonify(layers_json), 200

if __name__ == '__main__':
    app.run(debug=True)
