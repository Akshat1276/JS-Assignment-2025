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

class HuggingFaceModel:
    """HuggingFace Transformers model integration"""
    
    def __init__(self):
        self.api_key = os.getenv('HUGGINGFACE_API_KEY')
        self.base_url = "https://api-inference.huggingface.co/models"
        self.available_models = {
            "dialogpt": "microsoft/DialoGPT-large",
            "blenderbot": "facebook/blenderbot-400M-distill", 
            "codet5": "Salesforce/codet5-base"
        }
        
        if not self.api_key:
            logger.warning("HuggingFace API key not found in environment variables")
    
    def _format_messages_for_hf(self, messages: List[Dict[str, str]]) -> str:
        """Format messages for HuggingFace models"""
        # Convert conversation to a single prompt
        conversation = ""
        for message in messages:
            role = message['role']
            content = message['content']
            
            if role == 'user':
                conversation += f"Human: {content}\n"
            elif role == 'assistant':
                conversation += f"Assistant: {content}\n"
            elif role == 'system':
                conversation = f"System: {content}\n" + conversation
        
        # Add final prompt for assistant response
        conversation += "Assistant:"
        return conversation
    
    async def generate_response(
        self,
        messages: List[Dict[str, str]],
        model: str = None,
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 512
    ) -> AsyncGenerator[str, None]:
        """
        Generate response from HuggingFace model
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            model: HuggingFace model name (optional)
            stream: Whether to stream the response
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            
        Yields:
            String chunks of the response
        """
        if not self.api_key:
            yield "Error: HuggingFace API key not configured"
            return
        
        try:
            # Use provided model or default to dialogpt
            if model and model in self.available_models:
                model_name = self.available_models[model]
            else:
                model_name = self.available_models["dialogpt"]
            
            url = f"{self.base_url}/{model_name}"
            
            # Format input for the model
            prompt = self._format_messages_for_hf(messages)
            
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            
            payload = {
                "inputs": prompt,
                "parameters": {
                    "max_new_tokens": max_tokens,
                    "temperature": temperature,
                    "do_sample": True,
                    "top_p": 0.9,
                    "return_full_text": False
                },
                "options": {
                    "wait_for_model": True,
                    "use_cache": False
                }
            }
            
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(url, headers=headers, json=payload)
                
                if response.status_code != 200:
                    error_text = response.text
                    logger.error(f"HuggingFace API error: {response.status_code} - {error_text}")
                    
                    # Handle common errors
                    if response.status_code == 503:
                        yield "Error: Model is loading, please try again in a few moments"
                    elif response.status_code == 401:
                        yield "Error: Invalid API key"
                    else:
                        yield f"Error: HuggingFace API returned status {response.status_code}"
                    return
                
                try:
                    data = response.json()
                    
                    if isinstance(data, list) and len(data) > 0:
                        # Standard response format
                        generated_text = data[0].get('generated_text', '')
                        
                        if stream:
                            # Simulate streaming by yielding chunks
                            words = generated_text.split()
                            for i, word in enumerate(words):
                                if i == 0:
                                    yield word
                                else:
                                    yield f" {word}"
                        else:
                            yield generated_text
                    
                    elif isinstance(data, dict):
                        # Handle different response formats
                        if 'generated_text' in data:
                            yield data['generated_text']
                        elif 'error' in data:
                            yield f"Error: {data['error']}"
                        else:
                            yield "No response generated"
                    
                    else:
                        yield "Unexpected response format"
                
                except json.JSONDecodeError as e:
                    logger.error(f"Failed to parse HuggingFace response: {e}")
                    yield "Error: Invalid response format"
        
        except httpx.TimeoutException:
            logger.error("HuggingFace API request timed out")
            yield "Error: Request timed out"
        except Exception as e:
            logger.error(f"Error calling HuggingFace API: {e}")
            yield f"Error: {str(e)}"
    
    async def get_available_models(self) -> List[Dict[str, Any]]:
        """Get list of available HuggingFace models"""
        return [
            {
                "name": "DialoGPT Large",
                "model_id": "dialogpt",
                "description": "Conversational AI model by Microsoft",
                "hf_model": "microsoft/DialoGPT-large"
            },
            {
                "name": "BlenderBot",
                "model_id": "blenderbot",
                "description": "Open-domain chatbot by Facebook",
                "hf_model": "facebook/blenderbot-400M-distill"
            },
            {
                "name": "CodeT5",
                "model_id": "codet5",
                "description": "Code generation and understanding model",
                "hf_model": "Salesforce/codet5-base"
            }
        ]
    
    async def get_model_info(self, model: str = None) -> Dict[str, Any]:
        """Get information about a specific model"""
        model_key = model or "dialogpt"
        if model_key in self.available_models:
            model_name = self.available_models[model_key]
        else:
            model_name = self.available_models["dialogpt"]
            
        return {
            "name": f"HuggingFace {model_name}",
            "provider": "HuggingFace",
            "model_id": model_key,
            "hf_model": model_name,
            "max_tokens": 512,
            "supports_streaming": True,
            "supports_system_message": False
        }

# Global HuggingFace model instance
huggingface_model = HuggingFaceModel()

async def generate_huggingface_response(
    messages: List[Dict[str, str]],
    model: str = None,
    stream: bool = True,
    **kwargs
) -> AsyncGenerator[str, None]:
    """
    Convenience function to generate HuggingFace response
    
    Args:
        messages: List of message dictionaries
        model: Model name to use
        stream: Whether to stream the response
        **kwargs: Additional parameters for generation
        
    Yields:
        String chunks of the response
    """
    async for chunk in huggingface_model.generate_response(
        messages, model=model, stream=stream, **kwargs
    ):
        yield chunk

async def get_huggingface_models() -> List[Dict[str, Any]]:
    """Get available HuggingFace models"""
    return await huggingface_model.get_available_models()

if __name__ == "__main__":
    import asyncio
    
    async def test_huggingface():
        """Test HuggingFace model"""
        messages = [
            {"role": "user", "content": "Hello! How are you today?"}
        ]
        
        print("Testing HuggingFace model...")
        response_text = ""
        async for chunk in generate_huggingface_response(messages, stream=False):
            response_text += chunk
        
        print(f"Response: {response_text}")
        
        print("\nAvailable models:")
        models = await get_huggingface_models()
        for model in models:
            print(f"- {model['name']}: {model['model_id']}")
    
    # Run test
    asyncio.run(test_huggingface())
