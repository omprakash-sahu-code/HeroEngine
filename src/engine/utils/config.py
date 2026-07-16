import os
from typing import Dict, Any

def load_config(config_path: str) -> Dict[str, Any]:
    """Loads configuration data from a YAML file using a pure-Python parser

    to avoid third-party dependencies.

    Args:
        config_path: Absolute or relative file path to the config file.

    Returns:
        Dict[str, Any]: Configuration dictionary.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    with open(config_path, 'r', encoding='utf-8') as file:
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

