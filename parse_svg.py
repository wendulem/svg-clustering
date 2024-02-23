from sklearn.cluster import DBSCAN
import numpy as np
import xml.etree.ElementTree as ET
import re

from parse_path_d import parse_path_d_and_collect_points

def parse_svg_and_preprocess(svg_content):
    root = ET.fromstring(svg_content)
    
    # Try to find the style tag
    style_tag = root.find('.//{http://www.w3.org/2000/svg}style')
    if style_tag is None:
        print("Style tag not found. Skipping style parsing.")
        css_rules = {}
    else:
        style_text = style_tag.text
        css_rules = {}
        for rule in re.findall(r'\.(\w+)\s*\{(.*?)\}', style_text, re.DOTALL):
            class_name, styles = rule
            style_dict = {item.split(':')[0].strip(): item.split(':')[1].strip() for item in styles.split(';') if item}
            css_rules[class_name] = style_dict

    paths_data = []

    for index, path in enumerate(root.findall('.//{http://www.w3.org/2000/svg}path')):
        attributes = path.attrib
        d_attr = attributes.get('d', '')
        centroid = parse_path_d_and_collect_points(d_attr) if d_attr else None

        class_name = attributes.get('class')
        css_style = css_rules.get(class_name, {})

        path_data = {
            'id': attributes.get('id', f'path{index}'),
            'd': d_attr,
            'attributes': {**attributes, **css_style},
            'centroid': centroid.tolist() if centroid is not None else None
        }
        paths_data.append(path_data)

    return paths_data

from sklearn.cluster import DBSCAN

def cluster_paths(paths_data, points):
    if len(points) > 0:
        dbscan = DBSCAN(eps=10, min_samples=2)
        cluster_labels = dbscan.fit_predict(points)
        
        # Count the number of points labeled as noise (-1)
        noise_count = len(cluster_labels[cluster_labels == -1])
        print("Number of points labeled as noise:", noise_count)
        
        return cluster_labels, points
    return None, None

def map_clusters_to_paths(paths_data, cluster_labels, points):
    if cluster_labels is None:
        return {"layers": []}  # Handle case with no valid centroids or paths
    
    clustered_paths = {}
    point_index = 0  # Index to track the current point in points array
    for path in paths_data:
        if path['centroid'] is None:
            continue  # Skip paths without centroids
        label = cluster_labels[point_index]
        point_index += 1

        if label not in clustered_paths:
            clustered_paths[label] = []
        clustered_paths[label].append(path)

    layers_json = {
        'layers': [
            {
                'id': f'layer_{cluster_id}',
                'visible': True,
                'selectable': True,
                'paths': [{'type': 'path', **path['attributes'], 'd': path['d'], 'centroid': path['centroid']} for path in paths]
            } for cluster_id, paths in clustered_paths.items()
        ]
    }
    return layers_json