#!/usr/bin/env python3
"""
Test script for structured outputs in professor search
"""

import os
import json
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def test_structured_output():
    try:
        from app import search_professors_by_university
        
        # Get API key from environment
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            print("❌ OPENAI_API_KEY not found in environment variables")
            return False
        
        # Test CV text
        cv_text = """
        Koshik Debanath
        Computer Science Student
        
        Education:
        - Bachelor's in Computer Science
        - Research experience in Machine Learning
        - Projects in AI and Data Science
        
        Skills:
        - Python, Java, C++
        - Machine Learning, Deep Learning
        - Data Analysis, Statistics
        """
        
        print("🔍 Testing structured professor search...")
        result = search_professors_by_university(
            university_name="New Jersey Institute of Technology",
            cv_text=cv_text,
            api_key=api_key,
            model="gpt-4o-mini",
            api_choice="OpenAI"
        )
        
        if hasattr(result, 'professors'):
            print("✅ Structured output successful!")
            print(f"Found {len(result.professors)} professors")
            print(f"University: {result.university}")
            
            for i, prof in enumerate(result.professors[:2]):  # Show first 2
                print(f"\nProfessor {i+1}:")
                print(f"  Name: {prof.name}")
                print(f"  Title: {prof.title}")
                print(f"  Department: {prof.department}")
                print(f"  Research Areas: {', '.join(prof.research_areas)}")
            
            return True
        else:
            print(f"❌ Error: {result}")
            return False
        
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False
    except Exception as e:
        print(f"❌ Error testing structured output: {e}")
        return False

if __name__ == "__main__":
    print("🧪 Testing Structured Outputs")
    print("=" * 40)
    
    success = test_structured_output()
    
    if success:
        print("\n✅ Structured output test passed!")
    else:
        print("\n❌ Structured output test failed!")
        print("\nTo fix:")
        print("1. Make sure OPENAI_API_KEY is set in your .env file")
        print("2. Ensure you have sufficient OpenAI credits")
        print("3. Check that the model name is correct") 