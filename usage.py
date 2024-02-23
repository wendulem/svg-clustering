import requests

def reconstruct_svg(json_data, visible_layers=None):
    svg_content = '<?xml version="1.0" encoding="UTF-8" standalone="no"?>\n'
    svg_content += '<svg xmlns="http://www.w3.org/2000/svg">\n'

    for layer in json_data['layers']:
        if visible_layers is None or layer['id'] in visible_layers:
            for path in layer['paths']:
                svg_content += '\t<path ' + ' '.join(f'{key}="{value}"' for key, value in path.items() if key != 'centroid') + ' />\n'

    svg_content += '</svg>'
    return svg_content

def serialize_svg(svg_content, filename='reconstructed_svg.svg'):
    with open(filename, 'w') as file:
        file.write(svg_content)
    print(f"Serialized SVG content written to '{filename}'.")

# Define the URL of your Flask API endpoint
url = 'http://127.0.0.1:5000/upload'

# Open the SVG file and read its content
with open('henley.svg', 'r') as file:
    svg_content = file.read()

# Create a dictionary containing the file content as form data
files = {'file': ('henley.svg', svg_content)}

# Send the POST request to the Flask API endpoint
response = requests.post(url, files=files)

# Check if request was successful (status code 200)
if response.status_code == 200:
    # Access the 'layers' key in the JSON response and get its length
    # layers_length = len(response.json().get('layers', []))
    # print("Number of layers:", layers_length)
    json_data = response.json()
    
    # Specify which layers are shown in the reconstructed SVG
    visible_layers = ['layer_0']  # Example: Specify layer IDs here

    reconstructed_svg = reconstruct_svg(json_data, visible_layers)

    # Serialize the reconstructed SVG
    serialize_svg(reconstructed_svg, 'reconstructed_svg_output.svg')
else:
    print("Request failed with status code:", response.status_code)
