import re
import numpy as np

def interpolate_bezier(control_points, is_cubic=True, t_values=np.linspace(0, 1, 10)):
    """Interpolate points for quadratic or cubic Bézier curves."""
    points = []
    for t in t_values:
        if is_cubic:
            p0, p1, p2, p3 = control_points
            point = (1-t)**3 * p0 + 3 * (1-t)**2 * t * p1 + 3 * (1-t) * t**2 * p2 + t**3 * p3
        else:  # Quadratic
            p0, p1, p2 = control_points
            point = (1-t)**2 * p0 + 2 * (1-t) * t * p1 + t**2 * p2
        points.append(point)
    return np.array(points)

def calculate_centroid(points):
    """Calculate the centroid of a set of points."""
    return np.mean(points, axis=0)

def update_current_pos(current_pos, param, command, is_relative):
    """Update current position based on the command type and relativity."""
    if is_relative and command.lower() == command:
        return current_pos + param
    return param

def custom_split_params(params):
    # Split the parameters based on a dash followed by a digit or a comma followed by a digit
    parsed_params = [float(p) for p in re.findall(r'-?\d*\.?\d+(?:[eE][-+]?\d+)?', params)]
    return np.array(parsed_params)

def parse_path_d_and_collect_points(d):
    command_re = re.compile(r'([MmLlHhVvCcSsQqTtAaZz])((?:-?\d*\.?\d+[,]?\s*)+)')
    current_pos = np.array([0.0, 0.0])
    previous_control_point = None  # For handling 's' command
    start_pos = np.array([0.0, 0.0])
    all_points = []

    for command, params in command_re.findall(d):
        params = custom_split_params(params)
        is_relative = command.islower()

        if command in 'Mm':
            for p in params.reshape(-1, 2):
                new_pos = update_current_pos(current_pos, p, command, is_relative)
                current_pos = new_pos
                if command == 'M':
                    start_pos = new_pos  # Only update start_pos for the 'M' command

        elif command in 'LlHhVv':
            # For 'L', 'H', 'V' commands, calculate new_pos and append to all_points
            for p in params.reshape(-1, 2) if command in 'Ll' else params:
                if command in 'Hh':
                    new_pos = np.array([p if command == 'H' else current_pos[0] + p, current_pos[1]])
                elif command in 'Vv':
                    new_pos = np.array([current_pos[0], p if command == 'V' else current_pos[1] + p])
                else:  # 'Ll'
                    new_pos = update_current_pos(current_pos, p, command, is_relative)
                all_points.append(new_pos)
                current_pos = new_pos

        elif command in 'CcQq':
            # For 'C', 'Q' commands, interpolate points and append them to all_points
            is_cubic = command in 'Cc'
            step = 6 if is_cubic else 4
            for i in range(0, len(params), step):
                control_points = [current_pos] + list(params[i:i+step].reshape(-1, 2))
                if is_relative:
                    control_points = [current_pos] + [update_current_pos(current_pos, p, command, is_relative) for p in params[i:i+step].reshape(-1, 2)]
                bezier_points = interpolate_bezier(control_points, is_cubic)
                all_points.extend(bezier_points)
                current_pos = control_points[-1]

        elif command in 'Ss':
            # Handle smooth curveto
            params = params.reshape(-1, 4)
            for x2, y2, x, y in params:
                if command == 's' and previous_control_point is not None:
                    # Reflect the previous control point relative to the current position
                    reflected = current_pos * 2 - previous_control_point
                else:
                    # If there's no previous control point, use current position as the first control point
                    reflected = current_pos
                if is_relative:
                    x2 += current_pos[0]
                    y2 += current_pos[1]
                    x += current_pos[0]
                    y += current_pos[1]

                new_pos = np.array([x, y])
                control_points = [reflected, np.array([x2, y2]), new_pos]
                bezier_points = interpolate_bezier(control_points, is_cubic=False)  # False for quadratic
                all_points.extend(bezier_points)
                current_pos = new_pos
                previous_control_point = np.array([x2, y2])  # Update for next potential 's' command

        elif command in 'Zz':
            # Closepath command
            all_points.append(start_pos)
            current_pos = start_pos  # Reset current_pos to start_pos

        elif command in 'Aa':
            # Placeholder for elliptical arc handling; actual implementation would be more complex
            print(f"Elliptical arc command '{command}' handling is simplified and may not accurately represent all points.")

        else:
            print(f"Command '{command}' is not specifically handled in this script.")

    # After processing all commands, calculate a single centroid for the collected points
    if all_points:
        overall_centroid = calculate_centroid(np.vstack(all_points))
        return overall_centroid
    return np.array([])  # Return an empty array if no points were processed
