"""
Model Client for Portkey-OpenAI Integration
"""

import yaml
import json
import requests
import logging
from typing import Dict, Any, Optional, List
from enum import Enum
from portkey_ai import Portkey  # Import Portkey

logger = logging.getLogger(__name__)

class ModelAccessMethod(Enum):
    """Enumeration of supported model access methods."""
    PORTKEY = "portkey"  # Only Portkey is supported
    OPENAI_API = "openai_api"  # Fallback to OpenAI if needed

class ModelClient:
    """Unified client for accessing LLM models via Portkey or OpenAI."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None, config_path: Optional[str] = None):
        """
        Initialize the model client.
        
        Args:
            config: Configuration dictionary (optional)
            config_path: Path to configuration file (optional)
        """
        logger.info("Initializing ModelClient")
        
        try:
            if config:
                self.config = config
                logger.info("Using provided configuration dictionary")
            elif config_path:
                with open(config_path, "r") as f:
                    self.config = yaml.safe_load(f)
                logger.info(f"Loaded configuration from {config_path}")
            else:
                self.config = {}
                logger.warning("No configuration provided, using empty config")
            
            self.portkey_client = None  # Initialize Portkey client
            self.model_errors = []
            self._init_clients()
            
        except Exception as e:
            logger.error(f"Error initializing ModelClient: {str(e)}")
            self.model_errors.append(f"Initialization error: {str(e)}")
            raise
    
    def _init_clients(self):
        """Initialize necessary clients based on configuration."""
        logger.info("Initializing model clients...")
        
        # Initialize Portkey if enabled
        # if self.config.get('portkey', {}).get('enabled', False):
        try:
            self.portkey_client = Portkey(
                base_url="YOUR_PORTKEY_BASE_URL",
                api_key="YOUR_API_KEY_HERE",
                virtual_key="open-"
            )
            logger.info("Portkey client initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize Portkey client: {e}")
            self.model_errors.append(f"Portkey initialization error: {str(e)}")
            self.portkey_client = None
        # else:
        #     logger.info("Portkey is not enabled in configuration")

    def invoke_model(self, agent_name: str, messages: list) -> Dict[str, Any]:
        """Invoke the LLM model with detailed logging."""
        try:
            # Try Portkey first if enabled
            if self.portkey_client and self.config.get('portkey', {}).get('enabled', False):
                response = self._invoke_portkey(messages)
                response["model_used"] = "portkey"
                return response
                
            # Fallback to OpenAI
            response = self._invoke_openai(messages)
            response["model_used"] = "openai"
            return response
            
        except Exception as e:
            logger.error(f"Error in model invocation: {str(e)}")
            return {
                "content": [{"text": str(e)}],
                "error": str(e),
                "model_used": "error"
            }
    
    def _invoke_portkey(self, messages: list) -> Dict[str, Any]:
        """Invoke model through Portkey."""
        try:
            response = self.portkey_client.chat.completions.create(
                messages=messages,
                model="gpt-4o",
                max_tokens=3000,
                temperature=0
            )
            
            return {
                "content": [{"text": response.choices[0].message.content}],
                "model_used": "portkey"
            }
            
        except Exception as e:
            logger.error(f"Portkey invocation failed: {str(e)}")
            raise
    
    def invoke_model(self, agent_name: str, messages: List[Dict[str, str]]) -> Dict[str, Any]:
        """
        Invoke the model using Portkey.
        
        Args:
            agent_name: Name of the agent (for logging purposes)
            messages: List of messages to send to the model
            
        Returns:
            Dictionary containing the model's response
        """
        try:
            response = self.portkey_client.chat.completions.create(
                messages=messages,
                model="gpt-4o",
                max_tokens=3000,
                temperature=0
            )
            
            return {
                "content": [{"text": response.choices[0].message.content}],
                "model_used": "portkey"
            }
            
        except Exception as e:
            logger.error(f"Portkey invocation failed: {str(e)}")
            return {
                "content": [{"text": str(e)}],
                "error": str(e),
                "model_used": "error"
            }
    
    def _format_messages_for_openai(self, messages: list) -> list:
        """Format messages to match OpenAI's expected structure."""
        return [{
            "role": msg.get("role", "user"),
            "content": msg.get("content", "")
        } for msg in messages]
    
    def get_errors(self) -> list:
        """Get list of errors encountered."""
        return self.model_errors        