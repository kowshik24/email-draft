#!/usr/bin/env python3
"""Basic unit tests for the email draft application that don't require API keys."""

import os
import sys
import unittest
from unittest.mock import patch, MagicMock

# Add parent directory to path to import app
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


class TestAppImports(unittest.TestCase):
    """Test that the application imports correctly."""

    def test_app_imports(self):
        """Test that app.py imports without errors."""
        # Mock environment variables to avoid API connections
        with patch.dict(os.environ, {
            'OPENAI_API_KEY': 'test-key-mock',
            'GEMINI_API_KEY': 'test-key-mock', 
            'TAVILY_API_KEY': 'test-key-mock'
        }):
            # Mock OpenAI client to avoid network calls
            with patch('openai.OpenAI') as mock_openai:
                # Create mock model list response with the expected structure
                mock_model = MagicMock()
                mock_model.id = 'gpt-4o-mini'
                
                mock_models = MagicMock()
                mock_models.data = [mock_model]
                
                mock_client = MagicMock()
                mock_client.models.list.return_value = mock_models
                mock_openai.return_value = mock_client
                
                try:
                    import app
                    self.assertTrue(True, "App imported successfully")
                except ImportError as e:
                    self.fail(f"Failed to import app: {e}")

    def test_basic_dependencies_available(self):
        """Test that basic dependencies are available."""
        try:
            import streamlit
            import os
            import re
            import json
            from datetime import datetime, timedelta
            import pytz
            self.assertTrue(True, "Basic dependencies available")
        except ImportError as e:
            self.fail(f"Failed to import dependencies: {e}")


class TestConfigurationHandling(unittest.TestCase):
    """Test configuration and environment handling."""

    def test_env_template_exists(self):
        """Test that env_template.txt exists."""
        template_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            'env_template.txt'
        )
        self.assertTrue(
            os.path.exists(template_path), 
            "env_template.txt should exist"
        )

    def test_requirements_file_exists(self):
        """Test that requirements.txt exists."""
        req_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            'requirements.txt'
        )
        self.assertTrue(
            os.path.exists(req_path), 
            "requirements.txt should exist"
        )


class TestScriptFiles(unittest.TestCase):
    """Test that deployment scripts exist and are executable."""

    def test_run_script_exists(self):
        """Test that run_app.sh exists."""
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            'run_app.sh'
        )
        self.assertTrue(
            os.path.exists(script_path), 
            "run_app.sh should exist"
        )
        # Check if executable
        self.assertTrue(
            os.access(script_path, os.X_OK),
            "run_app.sh should be executable"
        )

    def test_stop_script_exists(self):
        """Test that stop_app.sh exists."""
        script_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
            'stop_app.sh'
        )
        self.assertTrue(
            os.path.exists(script_path), 
            "stop_app.sh should exist"
        )
        # Check if executable
        self.assertTrue(
            os.access(script_path, os.X_OK),
            "stop_app.sh should be executable"
        )


if __name__ == '__main__':
    unittest.main()