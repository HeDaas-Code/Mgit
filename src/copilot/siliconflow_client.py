#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
SiliconFlow API Client for MGit Copilot
"""

import requests
import json
from typing import List, Dict, Optional, Generator
from src.utils.logger import info, warning, error

class SiliconFlowClient:
    """Client for SiliconFlow API"""
    
    BASE_URL = "https://api.siliconflow.cn/v1"
    
    # 默认模型列表
    DEFAULT_MODELS = {
        'chat': 'Qwen/Qwen2.5-7B-Instruct',
        'completion': 'Qwen/Qwen2.5-7B-Instruct',
        'embedding': 'BAAI/bge-large-zh-v1.5'
    }
    
    def __init__(self, api_key: str, model: str = None):
        """
        Initialize SiliconFlow client
        
        Args:
            api_key: SiliconFlow API key
            model: Model name to use (defaults to Qwen2.5-7B-Instruct)
        """
        self.api_key = api_key
        self.model = model or self.DEFAULT_MODELS['chat']
        self.headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
    def chat_completion(
        self, 
        messages: List[Dict[str, str]], 
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stream: bool = False
    ) -> Dict:
        """
        Send chat completion request
        
        Args:
            messages: List of message dicts with 'role' and 'content'
            temperature: Sampling temperature (0-1)
            max_tokens: Maximum tokens to generate
            stream: Whether to stream the response
            
        Returns:
            Response dict from API
        """
        url = f"{self.BASE_URL}/chat/completions"
        data = {
            'model': self.model,
            'messages': messages,
            'temperature': temperature,
            'max_tokens': max_tokens,
            'stream': stream
        }
        
        try:
            if stream:
                return self._stream_chat_completion(url, data)
            else:
                response = requests.post(url, headers=self.headers, json=data, timeout=60)
                response.raise_for_status()
                return response.json()
        except requests.exceptions.RequestException as e:
            error(f"SiliconFlow API error: {str(e)}")
            raise
            
    def _stream_chat_completion(self, url: str, data: Dict) -> Generator:
        """
        Stream chat completion response
        
        Args:
            url: API endpoint URL
            data: Request data
            
        Yields:
            Chunks of response text
        """
        try:
            response = requests.post(
                url, 
                headers=self.headers, 
                json=data, 
                stream=True,
                timeout=60
            )
            response.raise_for_status()
            
            for line in response.iter_lines():
                if line:
                    line = line.decode('utf-8')
                    if line.startswith('data: '):
                        data_str = line[6:]
                        if data_str.strip() == '[DONE]':
                            break
                        try:
                            chunk = json.loads(data_str)
                            if 'choices' in chunk and len(chunk['choices']) > 0:
                                delta = chunk['choices'][0].get('delta', {})
                                if 'content' in delta:
                                    yield delta['content']
                        except json.JSONDecodeError:
                            continue
        except requests.exceptions.RequestException as e:
            error(f"SiliconFlow streaming error: {str(e)}")
            raise
            
    def text_completion(
        self,
        prompt: str,
        temperature: float = 0.7,
        max_tokens: int = 2048,
        stop: Optional[List[str]] = None
    ) -> str:
        """
        Generate text completion
        
        Args:
            prompt: Input prompt text
            temperature: Sampling temperature
            max_tokens: Maximum tokens to generate
            stop: List of stop sequences
            
        Returns:
            Generated completion text
        """
        messages = [{'role': 'user', 'content': prompt}]
        response = self.chat_completion(messages, temperature, max_tokens)
        
        if 'choices' in response and len(response['choices']) > 0:
            return response['choices'][0]['message']['content']
        return ""
        
    def get_embedding(self, text: str) -> List[float]:
        """
        Get text embedding
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        url = f"{self.BASE_URL}/embeddings"
        data = {
            'model': self.DEFAULT_MODELS['embedding'],
            'input': text
        }
        
        try:
            response = requests.post(url, headers=self.headers, json=data, timeout=30)
            response.raise_for_status()
            result = response.json()
            
            if 'data' in result and len(result['data']) > 0:
                return result['data'][0]['embedding']
            return []
        except requests.exceptions.RequestException as e:
            error(f"SiliconFlow embedding error: {str(e)}")
            raise
            
    def test_connection(self) -> bool:
        """
        Test API connection
        
        Returns:
            True if connection successful, False otherwise
        """
        try:
            messages = [{'role': 'user', 'content': 'Hello'}]
            self.chat_completion(messages, max_tokens=10)
            return True
        except Exception as e:
            error(f"Connection test failed: {str(e)}")
            return False
