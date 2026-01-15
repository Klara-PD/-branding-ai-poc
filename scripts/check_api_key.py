#!/usr/bin/env python3
"""
Quick script to check OpenRouter API key and credits status
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

try:
    from openai import OpenAI
except ImportError:
    print("Error: Missing openai package. Install with: pip install openai")
    sys.exit(1)

def check_api_key():
    project_root = Path(__file__).parent.parent
    env_path = project_root / '.env.local'
    
    if not env_path.exists():
        print("❌ .env.local file not found")
        return
    
    load_dotenv(env_path)
    api_key = os.getenv('OPENROUTER_API_KEY')
    
    if not api_key:
        print("❌ OPENROUTER_API_KEY not found in .env.local")
        return
    
    print(f"✅ API Key found: {api_key[:20]}...{api_key[-10:]}")
    print("\n🔍 Testing API connection...")
    
    try:
        client = OpenAI(
            api_key=api_key,
            base_url="https://openrouter.ai/api/v1"
        )
        
        # Try a simple test call
        response = client.chat.completions.create(
            model="openai/gpt-4o-mini",
            messages=[
                {"role": "user", "content": "Say 'test'"}
            ],
            max_tokens=10
        )
        
        print("✅ API connection successful!")
        print(f"   Response: {response.choices[0].message.content}")
        
        # Check for rate limit or credit info in headers
        if hasattr(response, 'headers'):
            print("\n📊 Response headers:")
            for key, value in response.headers.items():
                if 'rate' in key.lower() or 'credit' in key.lower() or 'limit' in key.lower():
                    print(f"   {key}: {value}")
        
    except Exception as e:
        error_str = str(e)
        print(f"❌ API Error: {e}")
        
        if '402' in error_str or 'payment' in error_str.lower() or 'credit' in error_str.lower():
            print("\n⚠️  Insufficient credits detected!")
            print("   Please add credits at: https://openrouter.ai/settings/credits")
        elif '403' in error_str or 'limit' in error_str.lower():
            print("\n⚠️  Rate limit or permission issue detected!")
            print("   Check your API key limits at: https://openrouter.ai/settings/keys")
        elif '401' in error_str or 'unauthorized' in error_str.lower():
            print("\n⚠️  Invalid API key!")
            print("   Check your API key at: https://openrouter.ai/settings/keys")

if __name__ == '__main__':
    check_api_key()
