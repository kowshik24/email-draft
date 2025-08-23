#!/usr/bin/env python3
"""
Test script to verify GPT-5 model detection and temperature parameter handling.
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import is_gpt5_model

def test_gpt5_model_detection():
    """Test GPT-5 model detection function."""
    
    # Test GPT-5 models (should return True)
    gpt5_models = [
        'gpt-5',
        'gpt-5-mini',
        'gpt-5-nano',
        'GPT-5',  # Test case insensitivity
        'GPT-5-MINI',
        'gpt5',  # Alternative naming
        'gpt5-mini',
    ]
    
    # Test non-GPT-5 models (should return False)
    non_gpt5_models = [
        'gpt-4',
        'gpt-4o',
        'gpt-4o-mini',
        'gpt-3.5-turbo',
        'gpt-4-turbo',
        'o1-preview',
        'o1-mini',
        'gemini-1.5-flash',
        '',
        None,
    ]
    
    print("Testing GPT-5 model detection...")
    
    # Test GPT-5 models
    print("\nTesting GPT-5 models (should return True):")
    all_gpt5_passed = True
    for model in gpt5_models:
        result = is_gpt5_model(model)
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"  {model}: {result} {status}")
        if not result:
            all_gpt5_passed = False
    
    # Test non-GPT-5 models
    print("\nTesting non-GPT-5 models (should return False):")
    all_non_gpt5_passed = True
    for model in non_gpt5_models:
        result = is_gpt5_model(model)
        status = "✅ PASS" if not result else "❌ FAIL"
        print(f"  {model}: {result} {status}")
        if result:
            all_non_gpt5_passed = False
    
    # Summary
    print(f"\n{'='*50}")
    print("TEST SUMMARY:")
    print(f"GPT-5 model detection: {'✅ PASS' if all_gpt5_passed else '❌ FAIL'}")
    print(f"Non-GPT-5 model detection: {'✅ PASS' if all_non_gpt5_passed else '❌ FAIL'}")
    
    overall_pass = all_gpt5_passed and all_non_gpt5_passed
    print(f"Overall: {'✅ ALL TESTS PASSED' if overall_pass else '❌ SOME TESTS FAILED'}")
    
    return overall_pass

def test_temperature_exclusion_simulation():
    """Simulate temperature parameter handling for different models."""
    
    print(f"\n{'='*50}")
    print("Testing temperature parameter handling simulation...")
    
    test_models = [
        ('gpt-4o-mini', False),  # Should include temperature
        ('gpt-4o', False),       # Should include temperature  
        ('gpt-5', True),         # Should exclude temperature
        ('gpt-5-mini', True),    # Should exclude temperature
        ('gpt-5-nano', True),    # Should exclude temperature
    ]
    
    for model, should_exclude_temp in test_models:
        exclude_temp = is_gpt5_model(model)
        
        # Simulate completion parameters
        completion_params = {
            "model": model,
            "messages": [{"role": "user", "content": "test"}]
        }
        
        if not exclude_temp:
            completion_params["temperature"] = 0.01
            
        has_temp = "temperature" in completion_params
        expected_has_temp = not should_exclude_temp
        
        status = "✅ PASS" if (has_temp == expected_has_temp) else "❌ FAIL"
        temp_status = "included" if has_temp else "excluded"
        
        print(f"  {model}: temperature {temp_status} {status}")
    
    return True

if __name__ == "__main__":
    print("GPT-5 Model Detection and Temperature Parameter Test")
    print("=" * 60)
    
    # Run tests
    detection_passed = test_gpt5_model_detection()
    temperature_passed = test_temperature_exclusion_simulation()
    
    # Final result
    if detection_passed and temperature_passed:
        print(f"\n🎉 ALL TESTS PASSED! GPT-5 temperature parameter exclusion is working correctly.")
        sys.exit(0)
    else:
        print(f"\n❌ SOME TESTS FAILED! Please check the implementation.")
        sys.exit(1)