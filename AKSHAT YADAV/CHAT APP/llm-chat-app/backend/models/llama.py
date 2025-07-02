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

class LlamaModel:
    """LLaMA model integration via OpenRouter"""
    
    def __init__(self):
        self.api_key = os.getenv('OPENROUTER_API_KEY') or os.getenv('LLAMA_API_KEY')
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.default_model = "meta-llama/llama-2-7b-chat"
        
        if not self.api_key:
            logger.warning("OpenRouter/LLaMA API key not found in environment variables")
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, str]]:
        """Format messages for LLaMA via OpenRouter (OpenAI-compatible format)"""
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
        model: str = None,
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 1024
    ) -> AsyncGenerator[str, None]:
        """
        Generate response from LLaMA model via OpenRouter
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: LLaMA model variant to use
            stream: Whether to stream the response
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Yields:
            String chunks of the response
        """
        if not self.api_key:
            yield "Error: OpenRouter API key not configured"
            return
        
        try:
            # Use provided model or default
            model_name = model or self.default_model
            
            # Format messages
            formatted_messages = self._format_messages(messages)
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "http://localhost:8000",  # Your site URL
                "X-Title": "LLM Chat App"  # Your app name
            }
            
            payload = {
                "model": model_name,
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
        """Get list of available LLaMA models via OpenRouter"""
        return [
            {
                "name": "LLaMA 2 7B Chat",
                "model_id": "meta-llama/llama-2-7b-chat",
                "description": "Meta's LLaMA 2 7B parameter chat model"
            },
            {
                "name": "LLaMA 2 13B Chat",
                "model_id": "meta-llama/llama-2-13b-chat",
                "description": "Meta's LLaMA 2 13B parameter chat model"
            },
            {
                "name": "LLaMA 2 70B Chat",
                "model_id": "meta-llama/llama-2-70b-chat",
                "description": "Meta's LLaMA 2 70B parameter chat model"
            },
            {
                "name": "Code Llama 7B Instruct",
                "model_id": "meta-llama/codellama-7b-instruct",
                "description": "Meta's Code Llama 7B parameter instruct model"
            },
            {
                "name": "Code Llama 13B Instruct",
                "model_id": "meta-llama/codellama-13b-instruct",
                "description": "Meta's Code Llama 13B parameter instruct model"
            }
        ]
    
    async def get_model_info(self, model: str = None) -> Dict[str, Any]:
        """Get information about a specific LLaMA model"""
        model_name = model or self.default_model
        return {
            "name": f"LLaMA {model_name}",
            "provider": "Meta (via OpenRouter)",
            "model_id": model_name,
            "max_tokens": 1024,
            "supports_streaming": True,
            "supports_system_message": True
        }

# Global LLaMA model instance
llama_model = LlamaModel()

async def generate_llama_response(
    messages: List[Dict[str, str]],
    model: str = None,
    stream: bool = True,
    **kwargs
) -> AsyncGenerator[str, None]:
    """
    Convenience function to generate LLaMA response
    
    Args:
        messages: List of message dictionaries
        model: Model variant to use
        stream: Whether to stream the response
        **kwargs: Additional parameters for generation
        
    Yields:
        String chunks of the response
    """
    async for chunk in llama_model.generate_response(
        messages, model=model, stream=stream, **kwargs
    ):
        yield chunk

async def get_llama_models() -> List[Dict[str, Any]]:
    """Get available LLaMA models"""
    return await llama_model.get_available_models()

if __name__ == "__main__":
    import asyncio
    
    async def test_llama():
        """Test LLaMA model"""
        messages = [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Hello! Can you help me with a coding question?"}
        ]
        
        print("Testing LLaMA model...")
        response_text = ""
        async for chunk in generate_llama_response(messages, stream=False):
            response_text += chunk
        
        print(f"Response: {response_text}")
        
        print("\nAvailable LLaMA models:")
        models = await get_llama_models()
        for model in models:
            print(f"- {model['name']}: {model['model_id']}")
    
    # Run test
    asyncio.run(test_llama())
