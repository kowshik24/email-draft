#!/usr/bin/env python3
"""Test script to verify papers are properly loaded and integrated into email prompts."""

import os
import sys
import tempfile

# Add the current directory to the path to import app
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

import app

def test_load_papers_from_folder():
    """Test that papers are loaded correctly from the papers folder."""
    print("Testing load_papers_from_folder...")
    
    papers_content = app.load_papers_from_folder()
    
    # Check that papers were loaded
    assert len(papers_content) > 0, "No papers content loaded"
    print(f"✅ Papers loaded successfully ({len(papers_content)} characters)")
    
    # Check that multiple papers are included (content should be from the papers themselves)
    assert "Abstract" in papers_content, "Papers should contain abstracts"
    print("✅ Papers contain expected content")
    
    # Check for specific expected papers
    expected_papers = [
        "Bayesian Physics-Informed Neural Networks",
        "Physics-Informed Neural Networks for Real-Time Anomaly Detection",
        "Bengali Language"
    ]
    
    found_papers = []
    for paper in expected_papers:
        if paper in papers_content:
            found_papers.append(paper)
    
    assert len(found_papers) > 0, f"No expected papers found in content. Expected: {expected_papers}"
    print(f"✅ Found expected papers: {found_papers}")


def test_create_email_prompt_with_papers():
    """Test that create_email_prompt properly includes papers in the system prompt."""
    print("\nTesting create_email_prompt with papers integration...")
    
    test_cv = "Test CV content with machine learning experience"
    test_prof_info = "Professor researches neural networks and AI"
    test_student_name = "Test Student"
    
    prompt = app.create_email_prompt(test_cv, test_prof_info, test_student_name)
    
    # Check that prompt was generated
    assert len(prompt) > 0, "No prompt generated"
    print(f"✅ Prompt generated successfully ({len(prompt)} characters)")
    
    # Check that publications section is included
    assert "--- PUBLICATIONS START ---" in prompt, "Publications section start marker not found"
    assert "--- PUBLICATIONS END ---" in prompt, "Publications section end marker not found"
    print("✅ Publications section properly included in prompt")
    
    # Check that both CV and publications sections are present
    assert "--- CV START ---" in prompt, "CV section not found"
    assert "--- CV END ---" in prompt, "CV section not found"
    print("✅ CV section still properly included")
    
    # Check that professor info is still included
    assert "--- PROFESSOR INFO START ---" in prompt, "Professor info section not found"
    assert "--- PROFESSOR INFO END ---" in prompt, "Professor info section not found"
    print("✅ Professor info section still properly included")
    
    # Check proper order: CV -> Publications -> Professor Info
    cv_pos = prompt.find("--- CV START ---")
    pub_pos = prompt.find("--- PUBLICATIONS START ---")
    prof_pos = prompt.find("--- PROFESSOR INFO START ---")
    
    assert cv_pos < pub_pos < prof_pos, "Sections are not in correct order"
    print("✅ Sections are in correct order (CV -> Publications -> Professor Info)")


def test_load_papers_with_missing_folder():
    """Test behavior when papers folder doesn't exist."""
    print("\nTesting behavior with missing papers folder...")
    
    # Test with non-existent folder
    papers_content = app.load_papers_from_folder("non_existent_folder")
    
    # Should return empty string for missing folder
    assert papers_content == "", f"Expected empty string for missing folder, got: {papers_content}"
    print("✅ Handles missing papers folder gracefully")


def test_papers_content_format():
    """Test that papers content is properly formatted."""
    print("\nTesting papers content formatting...")
    
    papers_content = app.load_papers_from_folder()
    
    # Check that papers are separated properly
    papers_sections = papers_content.split("\n\n")
    assert len(papers_sections) > 1, "Papers should be separated by double newlines"
    print(f"✅ Papers properly separated ({len(papers_sections)} sections)")
    
    # Check that papers contain expected content (abstracts, conclusions, etc.)
    has_academic_content = "Abstract" in papers_content or "Conclusion" in papers_content
    assert has_academic_content, "Papers should contain academic content like abstracts or conclusions"
    print("✅ Papers contain proper academic content")


if __name__ == "__main__":
    print("Running Papers Integration Tests...")
    print("=" * 50)
    
    try:
        test_load_papers_from_folder()
        test_create_email_prompt_with_papers()
        test_load_papers_with_missing_folder()
        test_papers_content_format()
        
        print("\n" + "=" * 50)
        print("✅ All tests passed! Papers integration is working correctly.")
        
    except AssertionError as e:
        print(f"\n❌ Test failed: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        sys.exit(1)