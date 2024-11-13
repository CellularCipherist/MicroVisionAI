# Description: Configuration management system for FastAPI application.

from typing import Any, Dict, Optional
import os
import yaml
from pathlib import Path
import logging



class Config:
    """
    Configuration management system for the FastAPI application.

    This class provides a robust interface for loading and accessing configuration
    from YAML files with support for nested keys and default values. It implements
    basic validation and type checking while maintaining flexibility.

    Example:
        >>> config = Config()
        >>> debug_mode = config.get('app.debug', default=False)
        >>> api_key = config.get('api_keys.anthropic')
    """

    def __init__(self, config_file: Optional[str] = None) -> None:
        """
        Initialize configuration system.

        Args:
            config_file: Optional path to config file. If None, uses default path.
        """
        if config_file is None:
            config_file = str(Path(__file__).parent.parent / 'config.yaml')
        self.config_file: str = config_file
        self.config_data: Dict[str, Any] = self.load_config()

    def load_config(self) -> Dict[str, Any]:
        """
        Load and validate configuration from YAML file.

        Returns:
            Dict containing configuration data.

        Raises:
            FileNotFoundError: If config file is missing
            yaml.YAMLError: If YAML parsing fails
        """
        if not os.path.exists(self.config_file):
            raise FileNotFoundError(
                f"Configuration file not found: {self.config_file}"
            )

        with open(self.config_file, 'r') as file:
            try:
                return yaml.safe_load(file)
            except yaml.YAMLError as e:
                raise yaml.YAMLError(
                    f"Error parsing configuration file: {str(e)}"
                ) from e

    def get(self, key: str, default: Any = None) -> Any:
        """
        Retrieve configuration value using dot notation.

        Supports nested key access using dot notation and provides
        optional default values.

        Args:
            key: Dot-separated configuration key (e.g., 'app.debug')
            default: Optional default value if key not found

        Returns:
            Configuration value or default

        Raises:
            KeyError: If key not found and no default provided

        Example:
            >>> config.get('app.debug', default=False)
            >>> config.get('paths.imagej_dir')
        """
        keys = key.split('.')
        value = self.config_data

        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            if default is not None:
                return default
            raise KeyError(f"Configuration key not found: {key}")

    def validate_required_keys(self, required_keys: list) -> None:
        """
        Validate presence of required configuration keys.

        Args:
            required_keys: List of required dot-notation keys

        Raises:
            KeyError: If any required key is missing
        """
        missing_keys = []
        for key in required_keys:
            try:
                self.get(key)
            except KeyError:
                missing_keys.append(key)

        if missing_keys:
            raise KeyError(
                f"Missing required configuration keys: {', '.join(missing_keys)}"
            )


def load_config(config_file: Optional[str] = None) -> Config:
    """
    Factory function to load configuration.

    Args:
        config_file: Optional path to config file

    Returns:
        Initialized Config object
    """
    return Config(config_file)
