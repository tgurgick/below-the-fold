import os
import yaml
from typing import Dict, Any

class ConfigLoader:
    def __init__(self, config_dir: str = None):
        if config_dir is None:
            config_dir = os.path.join(os.path.dirname(__file__))
        self.config_dir = config_dir
        self._configs: Dict[str, Any] = {}

    def load_config(self, filename: str) -> Dict[str, Any]:
        """
        Load a YAML configuration file.
        
        Args:
            filename (str): Name of the YAML file to load
            
        Returns:
            Dict[str, Any]: Configuration data
        """
        if filename not in self._configs:
            file_path = os.path.join(self.config_dir, filename)
            with open(file_path, 'r') as f:
                self._configs[filename] = yaml.safe_load(f)
        return self._configs[filename]

    def get_prompt(self, config_name: str, prompt_key: str) -> str:
        """
        Get a specific prompt template from the configuration.
        
        Args:
            config_name (str): Name of the configuration file
            prompt_key (str): Key of the prompt in the configuration
            
        Returns:
            str: Prompt template
        """
        config = self.load_config(config_name)
        return config[prompt_key]['template']

    def get_config_value(self, config_name: str, key: str, default: Any = None) -> Any:
        """
        Get a specific configuration value.
        
        Args:
            config_name (str): Name of the configuration file
            key (str): Key to get from the configuration
            default (Any): Default value if key is not found
            
        Returns:
            Any: Configuration value
        """
        config = self.load_config(config_name)
        return config.get(key, default) 