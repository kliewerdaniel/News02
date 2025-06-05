import openai
import requests
import logging
from abc import ABC, abstractmethod
from typing import List, Dict
from functions.config_manager import ModelConfig

logger = logging.getLogger(__name__)

class LLMClient(ABC):
    @abstractmethod
    def chat_completion(self, messages: List[Dict], model_config: ModelConfig) -> str:
        pass

class OllamaClient(LLMClient):
    def chat_completion(self, messages: List[Dict], model_config: ModelConfig) -> str:
        try:
            import ollama
            
            # Configure Ollama client if endpoint is not default
            if model_config.api_endpoint != "http://localhost:11434":
                client = ollama.Client(host=model_config.api_endpoint)
            else:
                client = ollama
            
            response = client.chat(
                model=model_config.model,
                messages=messages,
                options={
                    'temperature': model_config.temperature,
                    'num_predict': model_config.max_tokens
                }
            )
            return response['message']['content']
            
        except Exception as e:
            logger.error(f"Ollama API error: {e}")
            raise

class OpenAICompatibleClient(LLMClient):
    def chat_completion(self, messages: List[Dict], model_config: ModelConfig) -> str:
        try:
            client = openai.OpenAI(
                base_url=model_config.api_endpoint,
                api_key=model_config.api_key
            )
            
            kwargs = {
                'model': model_config.model,
                'messages': messages,
                'temperature': model_config.temperature,
                'max_tokens': model_config.max_tokens
            }
            
            if model_config.top_p is not None:
                kwargs['top_p'] = model_config.top_p
            
            response = client.chat.completions.create(**kwargs)
            return response.choices[0].message.content
            
        except Exception as e:
            logger.error(f"OpenAI Compatible API error: {e}")
            raise

class GeminiClient(LLMClient):
    def __init__(self):
        self.last_request_time = 0
        self.request_count = 0
        self.reset_time = 0
        
    def chat_completion(self, messages: List[Dict], model_config: ModelConfig) -> str:
        import time
        
        # Implement rate limiting for Gemini free tier (10 requests per minute)
        current_time = time.time()
        
        # Reset counter every minute
        if current_time - self.reset_time >= 60:
            self.request_count = 0
            self.reset_time = current_time
            logger.info("🔄 Gemini rate limit counter reset")
        
        # If we're approaching the limit, add delay
        if self.request_count >= 8:  # Be conservative, start slowing at 8/10
            wait_time = 60 - (current_time - self.reset_time) + 5  # Wait until reset + buffer
            if wait_time > 0:
                logger.warning(f"🐌 Approaching Gemini rate limit. Waiting {wait_time:.1f}s to avoid 429 errors...")
                time.sleep(wait_time)
                # Reset after waiting
                self.request_count = 0
                self.reset_time = time.time()
        
        max_retries = 3
        for attempt in range(max_retries):
            try:
                # Use OpenAI-compatible endpoint for Gemini
                client = openai.OpenAI(
                    base_url=model_config.api_endpoint,
                    api_key=model_config.api_key
                )
                
                kwargs = {
                    'model': model_config.model,
                    'messages': messages,
                    'temperature': model_config.temperature,
                    'max_tokens': model_config.max_tokens
                }
                
                if model_config.top_p is not None:
                    kwargs['top_p'] = model_config.top_p
                
                response = client.chat.completions.create(**kwargs)
                self.request_count += 1
                self.last_request_time = time.time()
                
                logger.debug(f"✅ Gemini request successful ({self.request_count}/10 this minute)")
                return response.choices[0].message.content
                
            except Exception as e:
                error_str = str(e)
                
                # Check for rate limit error (429)
                if "429" in error_str or "rate limit" in error_str.lower() or "quota" in error_str.lower():
                    # Extract retry delay from error if available
                    retry_delay = 30  # Default to 30 seconds
                    
                    if "retryDelay" in error_str:
                        import re
                        delay_match = re.search(r'retryDelay.*?(\d+)s', error_str)
                        if delay_match:
                            retry_delay = int(delay_match.group(1)) + 5  # Add 5s buffer
                    
                    if attempt < max_retries - 1:
                        logger.warning(f"🚫 Gemini rate limit hit (429). Waiting {retry_delay}s before retry {attempt + 1}/{max_retries}")
                        logger.info("💡 Tip: Consider reducing MAX_ARTICLES_PER_FEED to avoid rate limits")
                        time.sleep(retry_delay)
                        
                        # Reset rate limiting counters after delay
                        self.request_count = 0
                        self.reset_time = time.time()
                        continue
                    else:
                        logger.error(f"❌ Gemini rate limit exceeded after {max_retries} attempts")
                        raise Exception(f"Gemini rate limit exceeded. Try again in a few minutes or reduce MAX_ARTICLES_PER_FEED setting.")
                
                # For other errors, log and retry with shorter delay
                elif attempt < max_retries - 1:
                    wait_time = 2 ** attempt  # Exponential backoff: 1s, 2s, 4s
                    logger.warning(f"🔄 Gemini API error (attempt {attempt + 1}/{max_retries}): {e}")
                    logger.info(f"Retrying in {wait_time}s...")
                    time.sleep(wait_time)
                else:
                    logger.error(f"❌ Gemini API error after {max_retries} attempts: {e}")
                    raise
        
        raise Exception("Max retries exceeded")

class LLMFactory:
    _gemini_client = None  # Singleton to maintain rate limiting state
    
    @staticmethod
    def create_client(provider: str) -> LLMClient:
        if provider == 'ollama':
            return OllamaClient()
        elif provider == 'openai_compatible':
            return OpenAICompatibleClient()
        elif provider == 'gemini':
            # Use singleton pattern to maintain rate limiting state across requests
            if LLMFactory._gemini_client is None:
                LLMFactory._gemini_client = GeminiClient()
                logger.info("🎯 Initialized Gemini client with intelligent rate limiting")
            return LLMFactory._gemini_client
        else:
            raise ValueError(f"Unsupported LLM provider: {provider}")

def retry_with_backoff(max_retries=3, backoff_factor=2):
    """Decorator for retry logic with exponential backoff"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries - 1:
                        logger.error(f"Failed after {max_retries} attempts: {e}")
                        raise e
                    wait_time = backoff_factor ** attempt
                    logger.warning(f"Attempt {attempt + 1} failed, retrying in {wait_time}s: {e}")
                    time.sleep(wait_time)
            return None
        return wrapper
    return decorator