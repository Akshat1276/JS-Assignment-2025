import os
import json
import httpx
import logging
from typing import AsyncGenerator, Dict, Any, List
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class OpenRouterModel:
    """OpenRouter API integration for multiple free models"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Free models available on OpenRouter
        self.free_models = {
            "llama-3.1-8b": {
                "id": "meta-llama/llama-3.1-8b-instruct:free",
                "name": "Llama 3.1 8B",
                "description": "Meta's latest Llama model, great for general chat",
                "max_tokens": 8192
            },
            "gemma-7b": {
                "id": "google/gemma-7b-it:free", 
                "name": "Gemma 7B",
                "description": "Google's open model, excellent for conversations",
                "max_tokens": 8192
            },
            "mistral-7b": {
                "id": "mistralai/mistral-7b-instruct:free",
                "name": "Mistral 7B", 
                "description": "Fast and efficient French AI model",
                "max_tokens": 32768
            },
            "openchat": {
                "id": "openchat/openchat-7b:free",
                "name": "OpenChat 7B",
                "description": "Open-source conversational AI model",
                "max_tokens": 8192
            },
            "zephyr-7b": {
                "id": "huggingfaceh4/zephyr-7b-beta:free",
                "name": "Zephyr 7B Beta",
                "description": "HuggingFace's instruction-tuned model",
                "max_tokens": 4096
            }
        }
        
        if not self.api_key:
            logger.warning("OpenRouter API key not found in environment variables")
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format messages for OpenRouter API (OpenAI-compatible format)"""
        formatted_messages = []
        
        for message in messages:
            role = message['role']
            content = message['content']
            
            # Ensure role is valid (user, assistant, system)
            if role not in ['user', 'assistant', 'system']:
                role = 'user'
            
            formatted_messages.append({
                "role": role,
                "content": content
            })
        
        return formatted_messages
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str = "llama-3.1-8b",
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        """
        Generate response from OpenRouter model
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: Model key to use from free_models
            stream: Whether to stream the response
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Yields:
            String chunks of the response
        """
        if not self.api_key:
            yield "Error: OpenRouter API key not configured"
            return
        
        # Get model info
        if model not in self.free_models:
            yield f"Error: Model '{model}' not available. Available models: {list(self.free_models.keys())}"
            return
        
        model_info = self.free_models[model]
        model_id = model_info["id"]
        
        try:
            # Format messages
            formatted_messages = self._format_messages(messages)
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",  # Your site URL
                "X-Title": "LLM Chat App"  # Your app name
            }
            
            # Ensure max_tokens doesn't exceed model limit
            model_max_tokens = model_info.get("max_tokens", 4096)
            max_tokens = min(max_tokens, model_max_tokens)
            
            payload = {
                "model": model_id,
                "messages": formatted_messages,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "top_p": 0.9,
                "frequency_penalty": 0,
                "presence_penalty": 0,
                "stream": stream
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                if stream:
                    async with client.stream(
                        'POST',
                        self.base_url,
                        headers=headers,
                        json=payload
                    ) as response:
                        if response.status_code != 200:
                            error_text = await response.aread()
                            logger.error(f"OpenRouter API error: {response.status_code} - {error_text}")
                            yield f"Error: OpenRouter API returned status {response.status_code}"
                            return
                        
                        async for line in response.aiter_lines():
                            if line.strip():
                                # Handle Server-Sent Events format
                                if line.startswith("data: "):
                                    data_str = line[6:]  # Remove "data: " prefix
                                    
                                    if data_str.strip() == "[DONE]":
                                        break
                                    
                                    try:
                                        data = json.loads(data_str)
                                        
                                        if 'choices' in data and len(data['choices']) > 0:
                                            choice = data['choices'][0]
                                            if 'delta' in choice and 'content' in choice['delta']:
                                                content = choice['delta']['content']
                                                if content:
                                                    yield content
                                    
                                    except json.JSONDecodeError:
                                        continue
                                    except Exception as e:
                                        logger.error(f"Error parsing streaming response: {e}")
                                        continue
                else:
                    # Non-streaming response
                    response = await client.post(
                        self.base_url,
                        headers=headers,
                        json=payload
                    )
                    
                    if response.status_code != 200:
                        error_text = response.text
                        logger.error(f"OpenRouter API error: {response.status_code} - {error_text}")
                        yield f"Error: OpenRouter API returned status {response.status_code}"
                        return
                    
                    data = response.json()
                    
                    if 'choices' in data and len(data['choices']) > 0:
                        choice = data['choices'][0]
                        if 'message' in choice and 'content' in choice['message']:
                            yield choice['message']['content']
                        else:
                            yield "No response generated"
                    else:
                        yield "No response generated"
        
        except httpx.TimeoutException:
            logger.error("OpenRouter API request timed out")
            yield "Error: Request timed out"
        except Exception as e:
            logger.error(f"Error calling OpenRouter API: {e}")
            yield f"Error: {str(e)}"
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available free models"""
        return [
            {
                "id": model_key,
                "name": model_info["name"],
                "description": model_info["description"],
                "openrouter_id": model_info["id"],
                "max_tokens": model_info["max_tokens"]
            }
            for model_key, model_info in self.free_models.items()
        ]
    
    async def get_model_info(self, model: str = "llama-3.1-8b") -> Dict[str, Any]:
        """Get information about a specific model"""
        if model not in self.free_models:
            model = "llama-3.1-8b"  # Default fallback
        
        model_info = self.free_models[model]
        return {
            "name": model_info["name"],
            "provider": "OpenRouter",
            "model_id": model,
            "openrouter_id": model_info["id"],
            "max_tokens": model_info["max_tokens"],
            "supports_streaming": True,
            "supports_system_message": True,
            "description": model_info["description"]
        }

# Global OpenRouter model instance
openrouter_model = OpenRouterModel()

async def generate_openrouter_response(
    messages: List[Dict[str, str]],
    model: str = "llama-3.1-8b",
    stream: bool = True,
    **kwargs
) -> AsyncGenerator[str, None]:
    """
    Convenience function to generate OpenRouter response
    
    Args:
        messages: List of message dictionaries
        model: Model key to use
        stream: Whether to stream the response
        **kwargs: Additional parameters for generation
        
    Yields:
        String chunks of the response
    """
    async for chunk in openrouter_model.generate_response(
        messages, model=model, stream=stream, **kwargs
    ):
        yield chunk

async def get_openrouter_models() -> List[Dict[str, Any]]:
    """Get available OpenRouter models"""
    return await openrouter_model.get_available_models()

if __name__ == "__main__":
    import asyncio
    
    async def test_openrouter():
        """Test OpenRouter models"""
        print("🔗 Testing OpenRouter integration...")
        
        # Test getting available models
        models = await get_openrouter_models()
        print(f"\n📋 Available models ({len(models)}):")
        for model in models:
            print(f"  • {model['name']} ({model['id']}): {model['description']}")
        
        # Test a simple conversation
        messages = [
            {"role": "user", "content": "Hello! Can you tell me about yourself?"}
        ]
        
        print(f"\n💬 Testing conversation with {models[0]['name']}...")
        response_text = ""
        async for chunk in generate_openrouter_response(
            messages, 
            model=models[0]['id'], 
            stream=False
        ):
            response_text += chunk
        
        print(f"Response: {response_text}")
        
        # Test model info
        print(f"\n📊 Model info:")
        info = await openrouter_model.get_model_info(models[0]['id'])
        for key, value in info.items():
            print(f"  {key}: {value}")
    
    # Run test
    asyncio.run(test_openrouter())
