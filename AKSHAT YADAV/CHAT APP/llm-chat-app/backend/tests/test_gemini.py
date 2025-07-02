import pytest
import asyncio
from unittest.mock import Mock, patch
from models.gemini import GeminiModel, generate_gemini_response

@pytest.fixture
def gemini_model():
    """Create a GeminiModel instance for testing"""
    return GeminiModel()

@pytest.mark.asyncio
async def test_gemini_format_messages(gemini_model):
    """Test message formatting for Gemini API"""
    messages = [
        {"role": "user", "content": "Hello"},
        {"role": "assistant", "content": "Hi there!"}
    ]
    
    formatted = gemini_model._format_messages(messages)
    
    assert len(formatted) == 2
    assert formatted[0]["role"] == "user"
    assert formatted[1]["role"] == "model"  # assistant -> model
    assert formatted[0]["parts"][0]["text"] == "Hello"

@pytest.mark.asyncio
async def test_gemini_generate_response_no_api_key():
    """Test response generation when API key is not available"""
    with patch.object(GeminiModel, '__init__', lambda x: setattr(x, 'api_key', None)):
        model = GeminiModel()
        messages = [{"role": "user", "content": "Test"}]
        
        response_chunks = []
        async for chunk in model.generate_response(messages):
            response_chunks.append(chunk)
        
        assert len(response_chunks) == 1
        assert "Error: Gemini API key not configured" in response_chunks[0]

def test_gemini_model_info():
    """Test model information"""
    model = GeminiModel()
    
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    
    try:
        info = loop.run_until_complete(model.get_model_info())
        
        assert info["name"] == "Google Gemini 1.5 Pro"
        assert info["provider"] == "Google"
        assert info["supports_streaming"] == True
    finally:
        loop.close()

if __name__ == "__main__":
    pytest.main([__file__])
