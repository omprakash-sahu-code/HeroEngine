import os
from typing import Dict, Any

from src.engine.utils.paths import resource_path

def load_config(config_path: str) -> Dict[str, Any]:
    """Loads configuration data from a YAML file using a pure-Python parser.

    Args:
        config_path: File path to the config file.

    Returns:
        Dict[str, Any]: Configuration dictionary.
    """
    resolved_path = resource_path(config_path) if not os.path.isabs(config_path) else config_path
    if not os.path.exists(resolved_path):
        resolved_path = resource_path(config_path)
    if not os.path.exists(resolved_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path} (resolved: {resolved_path})")

    with open(resolved_path, 'r', encoding='utf-8') as file:
        content = file.read()

    result = {}
    stack = [(-1, result)]  # List of (indent_level, dict_ref)
    
    for line_num, line in enumerate(content.splitlines(), 1):
        # Remove comments (keep inline strings safe by basic checks if needed)
        if '#' in line:
            line = line.split('#')[0]
            
        stripped = line.strip()
        if not stripped:
            continue
            
        # Count leading spaces
        indent = len(line) - len(line.lstrip())
        
        if ':' in stripped:
            key, val = stripped.split(':', 1)
            key = key.strip()
            val = val.strip()
            
            # Parse value
            parsed_val = None
            if val:
                # Remove quotes
                if (val.startswith('"') and val.endswith('"')) or (val.startswith("'") and val.endswith("'")):
                    parsed_val = val[1:-1]
                elif val.startswith('[') and val.endswith(']'):
                    # Parse lists/arrays
                    raw_elements = [el.strip() for el in val[1:-1].split(',')]
                    parsed_val = []
                    for el in raw_elements:
                        if not el:
                            continue
                        # Strip nested quotes
                        if (el.startswith('"') and el.endswith('"')) or (el.startswith("'") and el.endswith("'")):
                            parsed_val.append(el[1:-1])
                        elif el.lower() == 'true':
                            parsed_val.append(True)
                        elif el.lower() == 'false':
                            parsed_val.append(False)
                        elif el.lower() == 'null' or el == '~':
                            parsed_val.append(None)
                        else:
                            try:
                                if '.' in el:
                                    parsed_val.append(float(el))
                                else:
                                    parsed_val.append(int(el))
                            except ValueError:
                                parsed_val.append(el)
                elif val.lower() == 'true':
                    parsed_val = True
                elif val.lower() == 'false':
                    parsed_val = False
                elif val.lower() == 'null' or val == '~':
                    parsed_val = None
                else:
                    try:
                        if '.' in val:
                            parsed_val = float(val)
                        else:
                            parsed_val = int(val)
                    except ValueError:
                        parsed_val = val
            else:
                # Nested dict
                parsed_val = {}
                
            # Align stack matching indentation level
            while stack and stack[-1][0] >= indent:
                stack.pop()
                
            if not stack:
                raise ValueError(f"Invalid indentation on line {line_num}: {line}")
                
            current_dict = stack[-1][1]
            current_dict[key] = parsed_val
            
            # If value is empty, it means we are opening a nested block
            if val == '':
                stack.append((indent, parsed_val))
                
    return result

