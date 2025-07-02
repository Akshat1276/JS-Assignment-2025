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

class GeminiModel:
    """Google Gemini AI model integration"""
    
    def __init__(self):
        self.api_key = os.getenv('GEMINI_API_KEY')
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.model_name = "gemini-1.5-flash"  # Using Flash for faster responses
        
        if not self.api_key:
            logger.warning("Gemini API key not found in environment variables")
    
    def _format_messages(self, messages: List[Dict[str, str]]) -> List[Dict[str, Any]]:
        """Format messages for Gemini API"""
        formatted_messages = []
        
        for message in messages:
            role = message['role']
            content = message['content']
            
            # Gemini uses 'user' and 'model' roles
            if role == 'assistant':
                role = 'model'
            
            formatted_messages.append({
                "role": role,
                "parts": [{"text": content}]
            })
        
        return formatted_messages
    
    async def generate_response(
        self, 
        messages: List[Dict[str, str]], 
        stream: bool = True,
        temperature: float = 0.7,
        max_tokens: int = 2048
    ) -> AsyncGenerator[str, None]:
        """
        Generate response from Gemini model
        
        Args:
            messages: List of message dictionaries with 'role' and 'content'
            stream: Whether to stream the response
            temperature: Sampling temperature (0.0 to 1.0)
            max_tokens: Maximum tokens to generate
            
        Yields:
            String chunks of the response
        """
        if not self.api_key:
            yield "Error: Gemini API key not configured"
            return
        
        try:
            # Format messages for Gemini
            formatted_messages = self._format_messages(messages)
            
            # Prepare request payload
            payload = {
                "contents": formatted_messages,
                "generationConfig": {
                    "temperature": temperature,
                    "maxOutputTokens": max_tokens,
                    "topP": 0.8,
                    "topK": 10
                }
            }
            
            # Choose endpoint based on streaming
            if stream:
                endpoint = f"{self.base_url}/models/{self.model_name}:streamGenerateContent"
            else:
                endpoint = f"{self.base_url}/models/{self.model_name}:generateContent"
            
            headers = {
                "Content-Type": "application/json",
            }
            
            # Add API key to URL
            url = f"{endpoint}?key={self.api_key}"
            
            async with httpx.AsyncClient(timeout=30.0) as client:
                if stream:
                    async with client.stream(
                        'POST',
                        url,
                        headers=headers,
                        json=payload
                    ) as response:
                        if response.status_code != 200:
                            error_text = await response.aread()
                            logger.error(f"Gemini API error: {response.status_code} - {error_text}")
                            yield f"Error: Gemini API returned status {response.status_code}"
                            return
                        
                        async for chunk in response.aiter_lines():
                            if chunk.strip():
                                try:
                                    # Parse JSON chunk
                                    data = json.loads(chunk)
                                    
                                    # Extract text from candidates
                                    if 'candidates' in data and len(data['candidates']) > 0:
                                        candidate = data['candidates'][0]
                                        if 'content' in candidate and 'parts' in candidate['content']:
                                            for part in candidate['content']['parts']:
                                                if 'text' in part:
                                                    yield part['text']
                                
                                except json.JSONDecodeError:
                                    continue
                                except Exception as e:
                                    logger.error(f"Error parsing Gemini response chunk: {e}")
                                    continue
                else:
                    # Non-streaming response
                    response = await client.post(url, headers=headers, json=payload)
                    
                    if response.status_code != 200:
                        logger.error(f"Gemini API error: {response.status_code} - {response.text}")
                        yield f"Error: Gemini API returned status {response.status_code}"
                        return
                    
                    data = response.json()
                    
                    # Extract text from response
                    if 'candidates' in data and len(data['candidates']) > 0:
                        candidate = data['candidates'][0]
                        if 'content' in candidate and 'parts' in candidate['content']:
                            for part in candidate['content']['parts']:
                                if 'text' in part:
                                    yield part['text']
                    else:
                        yield "No response generated"
        
        except httpx.TimeoutException:
            logger.error("Gemini API request timed out")
            yield "Error: Request timed out"
        except Exception as e:
            logger.error(f"Error calling Gemini API: {e}")
            yield f"Error: {str(e)}"
    
    async def get_model_info(self) -> Dict[str, Any]:
        """Get information about the Gemini model"""
        return {
            "name": "Google Gemini 1.5 Flash",
            "provider": "Google",
            "model_id": self.model_name,
            "max_tokens": 2048,
            "supports_streaming": True,
            "supports_system_message": True
        }

# Global Gemini model instance
gemini_model = GeminiModel()

async def generate_gemini_response(
    messages: List[Dict[str, str]], 
    stream: bool = True,
    **kwargs
) -> AsyncGenerator[str, None]:
    """
    Convenience function to generate Gemini response
    
    Args:
        messages: List of message dictionaries
        stream: Whether to stream the response
        **kwargs: Additional parameters for generation
        
    Yields:
        String chunks of the response
    """
    async for chunk in gemini_model.generate_response(messages, stream=stream, **kwargs):
        yield chunk

if __name__ == "__main__":
    import asyncio
    
    async def test_gemini():
        """Test Gemini model"""
        messages = [
            {"role": "user", "content": "Hello! How are you?"}
        ]
        
        print("Testing Gemini model...")
        response_text = ""
        async for chunk in generate_gemini_response(messages, stream=False):
            response_text += chunk
        
        print(f"Response: {response_text}")
    
    # Run test
    asyncio.run(test_gemini())
