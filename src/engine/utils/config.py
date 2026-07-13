import yaml
import os
from typing import Dict, Any

def load_config(config_path: str) -> Dict[str, Any]:
    """Loads configuration data from a YAML file.

    Args:
        config_path: Absolute or relative file path to the config file.

    Returns:
        Dict[str, Any]: Configuration dictionary.
    """
    if not os.path.exists(config_path):
        raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
    with open(config_path, 'r') as file:
        try:
            config = yaml.safe_load(file)
            return config if config else {}
        except yaml.YAMLError as exc:
            raise ValueError(f"Error parsing YAML config: {exc}")
