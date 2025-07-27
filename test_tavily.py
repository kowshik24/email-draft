#!/usr/bin/env python3
"""
Test script for Tavily integration
"""

import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_tavily():
    try:
        from tavily import TavilyClient
        
        # Get API key from environment
        api_key = os.getenv("TAVILY_API_KEY")
        if not api_key:
            print("❌ TAVILY_API_KEY not found in environment variables")
            return False
        
        # Initialize client
        client = TavilyClient(api_key)
        
        # Test search with advanced parameters
        print("🔍 Testing Tavily search...")
        response = client.search(
            query="Xiaoning Ding New Jersey Institute of Technology hiring",
            search_depth="advanced",
            max_results=5,
            include_raw_content=True,
            chunks_per_source=3
        )
        
        print("✅ Search successful!")
        print(f"Found {len(response.get('results', []))} results")
        
        # Test extraction
        if response.get('results'):
            print("🔍 Testing content extraction...")
            first_result = response['results'][0]
            extract_response = client.extract(
                urls=[first_result['url']],
                extract_depth="advanced",
                format="text"
            )
            
            if extract_response.get('results'):
                print("✅ Extraction successful!")
                print(f"Extracted content length: {len(extract_response['results'][0].get('raw_content', ''))}")
            else:
                print("⚠️ Extraction returned no results")
        
        return True
        
    except ImportError:
        print("❌ Tavily library not installed. Run: pip install tavily-python")
        return False
    except Exception as e:
        print(f"❌ Error testing Tavily: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Tavily Integration")
    print("=" * 40)
    
    success = test_tavily()
    
    if success:
        print("\n✅ Tavily integration test passed!")
    else:
        print("\n❌ Tavily integration test failed!")
        print("\nTo fix:")
        print("1. Install tavily-python: pip install tavily-python")
        print("2. Add TAVILY_API_KEY to your .env file")
        print("3. Get your API key from: https://tavily.com/") 