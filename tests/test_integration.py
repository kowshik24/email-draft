#!/usr/bin/env python3
"""Integration tests for the email draft application (require API keys)."""

import os
import sys
import unittest
import pytest

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


@pytest.mark.integration
class TestAPIIntegration(unittest.TestCase):
    """Integration tests that require API keys."""

    def setUp(self):
        """Set up test environment."""
        # Skip tests if API keys are not available
        self.openai_key = os.getenv('OPENAI_API_KEY')
        self.gemini_key = os.getenv('GEMINI_API_KEY')
        self.tavily_key = os.getenv('TAVILY_API_KEY')

    def test_openai_integration_available(self):
        """Test if OpenAI integration can be set up."""
        if not self.openai_key:
            self.skipTest("OPENAI_API_KEY not available")
        
        try:
            from openai import OpenAI
            # Don't actually make API calls in tests
            self.assertTrue(True, "OpenAI client available")
        except ImportError:
            self.fail("OpenAI library not available")

    def test_gemini_integration_available(self):
        """Test if Gemini integration can be set up."""
        if not self.gemini_key:
            self.skipTest("GEMINI_API_KEY not available")
            
        try:
            import google.generativeai as genai
            self.assertTrue(True, "Gemini client available")
        except ImportError:
            self.fail("Google Generative AI library not available")

    def test_tavily_integration_available(self):
        """Test if Tavily integration can be set up."""
        if not self.tavily_key:
            self.skipTest("TAVILY_API_KEY not available")
            
        try:
            from tavily import TavilyClient
            self.assertTrue(True, "Tavily client available")
        except ImportError:
            self.fail("Tavily library not available")


if __name__ == '__main__':
    unittest.main()