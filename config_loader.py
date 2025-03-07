"""
Configuration Loader for Credit Assessment System

This module handles the loading and validation of configuration files
for the credit assessment system.
"""

import yaml
import json
import os
import logging
from pathlib import Path
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)

class ConfigLoader:
    """
    Handles loading and validating configuration files.
    
    Attributes:
        config_dir: Directory containing configuration files
    """
    
    def __init__(self, config_dir: str):
        """
        Initialize the configuration loader.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir)
        logger.info(f"Config loader initialized with directory: {self.config_dir}")
        
        # Create config directory if it doesn't exist
        self.config_dir.mkdir(exist_ok=True, parents=True)
    
    def load_config(self) -> Dict[str, Any]:
        """
        Load and merge all configuration files.
        
        Returns:
            Merged configuration dictionary
        """
        try:
            # Initialize with empty config
            config = {}
            
            # Load main config file
            main_config_path = self.config_dir / "config.yaml"
            if main_config_path.exists():
                with open(main_config_path, "r") as f:
                    config = yaml.safe_load(f)
                logger.info(f"Loaded main configuration from {main_config_path}")
            else:
                logger.warning(f"Main configuration file not found: {main_config_path}")
            
            # Load agent configurations
            agent_config_path = self.config_dir / "agents.yaml"
            if agent_config_path.exists():
                with open(agent_config_path, "r") as f:
                    agent_config = yaml.safe_load(f)
                # Add to main config
                config["agents"] = agent_config
                logger.info(f"Loaded agent configurations from {agent_config_path}")
            else:
                logger.warning(f"Agent configuration file not found: {agent_config_path}")
            
            # Load task configurations
            task_config_path = self.config_dir / "tasks.yaml"
            if task_config_path.exists():
                with open(task_config_path, "r") as f:
                    task_config = yaml.safe_load(f)
                # Add to main config
                config["tasks"] = task_config
                logger.info(f"Loaded task configurations from {task_config_path}")
            else:
                logger.warning(f"Task configuration file not found: {task_config_path}")
            
            # Validate the loaded configuration
            if self.validate_config(config):
                logger.info("Configuration validation successful")
            else:
                logger.warning("Configuration validation failed")
            
            return config
            
        except Exception as e:
            logger.error(f"Error loading configuration: {str(e)}")
            # Return minimal working configuration
            return {
                "output": {
                    "save_format": ["text", "json"],
                    "include_metadata": True
                }
            }
    
    def validate_config(self, config: Dict[str, Any]) -> bool:
        """
        Validate the configuration.
        
        Args:
            config: Configuration dictionary to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Check essential configuration elements
            if not isinstance(config, dict):
                logger.error("Configuration is not a dictionary")
                return False
            
            # Check output configuration
            if "output" not in config:
                logger.warning("Missing 'output' section in configuration")
                # Add default output configuration
                config["output"] = {
                    "save_format": ["text", "json"],
                    "include_metadata": True
                }
            
            # Check model access configuration
            if "portkey" not in config and "openai" not in config:
                logger.warning("Missing model access configuration (portkey or openai)")
                # Add default Portkey configuration
                config["portkey"] = {
                    "enabled": True,
                    "base_url": "https://api.portkey.ai/v1",
                    "api_key": "demo-key",
                    "virtual_key": "demo-virtual-key",
                    "model": "gpt-4o",
                    "max_tokens": 3000
                }
            
            # Validate agent configurations
            if "agents" not in config:
                logger.warning("Missing agent configurations")
            
            return True
            
        except Exception as e:
            logger.error(f"Error validating configuration: {str(e)}")
            return False
    
    def get_agent_config(self, agent_name: str) -> Dict[str, Any]:
        """
        Get the configuration for a specific agent.
        
        Args:
            agent_name: Name of the agent
            
        Returns:
            Agent configuration dictionary
        """
        try:
            # Load all configurations
            config = self.load_config()
            
            # Get agent-specific config
            if "agents" in config and agent_name in config["agents"]:
                agent_config = config["agents"][agent_name]
                
                # Merge with global Portkey/model configs if needed
                if "portkey" in config and "portkey" not in agent_config:
                    agent_config["portkey"] = config["portkey"]
                
                return agent_config
            
            # Fall back to global config
            logger.warning(f"No specific configuration found for {agent_name}, using global config")
            return config
            
        except Exception as e:
            logger.error(f"Error getting agent configuration: {str(e)}")
            # Return minimal working configuration
            return {
                "role": "AI Assistant",
                "model": "gpt-4o",
                "max_tokens": 3000
            }