import os
import yaml
import logging
from dataclasses import dataclass
from typing import Optional, Dict, Any
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

@dataclass
class ModelConfig:
    api_endpoint: str
    api_key: str
    model: str
    temperature: float = 0.7
    max_tokens: int = 4096
    top_p: Optional[float] = None

class ConfigManager:
    def __init__(self):
        self.llm_provider = os.getenv('LLM_PROVIDER', 'ollama')
        self.models_config = self.load_model_configs()
        self.setup_logging()
        
    def setup_logging(self):
        """Setup logging configuration"""
        log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
        log_dir = os.getenv('LOG_DIR', 'logs')
        
        # Create logs directory if it doesn't exist
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=getattr(logging, log_level),
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f'{log_dir}/news_digest.log'),
                logging.StreamHandler()
            ]
        )
        
    def load_model_configs(self) -> Dict[str, ModelConfig]:
        """Load model configurations from YAML file"""
        config_path = os.getenv('AI_MODELS_CONFIG', 'settings/llm_settings/ai_models.yml')
        
        try:
            with open(config_path, 'r') as file:
                config_data = yaml.safe_load(file)
        except FileNotFoundError:
            logging.error(f"Model configuration file not found: {config_path}")
            raise
        except yaml.YAMLError as e:
            logging.error(f"Error parsing YAML configuration: {e}")
            raise
        
        configs = {}
        for name, config in config_data.items():
            try:
                configs[name] = ModelConfig(**config)
            except TypeError as e:
                logging.error(f"Invalid configuration for model '{name}': {e}")
                continue
        
        return configs
    
    def get_model_config(self, model_name: str) -> ModelConfig:
        """Get specific model configuration with environment variable overrides"""
        if model_name not in self.models_config:
            raise ValueError(f"Model configuration '{model_name}' not found")
        
        # Create a copy to avoid modifying the original
        config = ModelConfig(**self.models_config[model_name].__dict__)
        
        # Override with environment variables if provider-specific keys exist
        if self.llm_provider == 'ollama':
            config.api_endpoint = os.getenv('OLLAMA_BASE_URL', config.api_endpoint)
        elif self.llm_provider == 'openai_compatible':
            config.api_endpoint = os.getenv('OPENAI_API_BASE', config.api_endpoint)
            config.api_key = os.getenv('OPENAI_API_KEY', config.api_key)
        elif self.llm_provider == 'gemini':
            config.api_key = os.getenv('GEMINI_API_KEY', config.api_key)
        
        return config
    
    def get_database_config(self) -> Dict[str, Any]:
        """Get database configuration"""
        return {
            'enabled': os.getenv('DATABASE_ENABLED', 'true').lower() == 'true',
            'path': os.getenv('DATABASE_PATH', 'news.db')
        }
    
    def get_output_config(self) -> Dict[str, Any]:
        """Get output configuration"""
        return {
            'directory': os.getenv('OUTPUT_DIRECTORY', './output'),
            'max_articles_per_feed': int(os.getenv('MAX_ARTICLES_PER_FEED', '1'))
        }
    
    def get_tts_config(self) -> Dict[str, str]:
        """Get TTS configuration"""
        return {
            'voice': os.getenv('TTS_VOICE', 'en-US-GuyNeural')
        }
    
    def get_feeds_config_path(self) -> str:
        """Get feeds configuration file path"""
        return os.getenv('FEEDS_CONFIG_PATH', 'settings/feeds/feeds.yaml')

# Global configuration instance
config_manager = ConfigManager()