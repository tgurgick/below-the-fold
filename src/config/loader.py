import os
import yaml
import logging
from typing import Dict, Any

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

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
            logger.debug(f"Loading config from {file_path}")
            try:
                with open(file_path, 'r') as f:
                    content = f.read()
                    logger.debug(f"Raw YAML content:\n{content}")
                    try:
                        self._configs[filename] = yaml.load(content, Loader=yaml.FullLoader)
                    except yaml.YAMLError as e:
                        logger.error(f"Error parsing YAML: {str(e)}")
                        raise
                    logger.debug(f"Parsed YAML content: {self._configs[filename]}")
            except Exception as e:
                logger.error(f"Error loading config file: {str(e)}")
                raise
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
        try:
            config = self.load_config(config_name)
            logger.debug(f"Getting prompt for key '{prompt_key}' from config: {config}")
            if prompt_key not in config:
                raise KeyError(f"Prompt key '{prompt_key}' not found in config")
            if not isinstance(config[prompt_key], dict) or 'template' not in config[prompt_key]:
                raise ValueError(f"Invalid prompt format for key '{prompt_key}'")
            return config[prompt_key]['template']
        except Exception as e:
            logger.error(f"Error getting prompt: {str(e)}")
            raise

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