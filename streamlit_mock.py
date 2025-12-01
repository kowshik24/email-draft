#!/usr/bin/env python3
"""
Streamlit Mock for Testing
This module provides a comprehensive mock of Streamlit to allow testing without a web server.
"""

import os
import sys


def create_streamlit_mock():
    """Create a comprehensive mock of the Streamlit module."""
    
    class MockSessionState:
        def __init__(self):
            self._state = {}
            
        def __getattr__(self, name):
            if name not in self._state:
                self._state[name] = None
            return self._state[name]
            
        def __setattr__(self, name, value):
            if name.startswith('_'):
                super().__setattr__(name, value)
            else:
                if not hasattr(self, '_state'):
                    super().__setattr__('_state', {})
                self._state[name] = value
                
        def __contains__(self, name):
            return name in self._state
            
        def __iter__(self):
            return iter(self._state)
            
        def keys(self):
            return self._state.keys()
            
        def values(self):
            return self._state.values()
            
        def items(self):
            return self._state.items()
    
    class MockSidebar:
        def selectbox(self, *args, **kwargs):
            return kwargs.get('value', 'test')
            
        def text_input(self, *args, **kwargs):
            return kwargs.get('value', 'test')
            
        def text_area(self, *args, **kwargs):
            return kwargs.get('value', 'test')
            
        def button(self, *args, **kwargs):
            return False
            
        def markdown(self, *args, **kwargs):
            return None
            
        def caption(self, *args, **kwargs):
            return None
            
        def write(self, *args, **kwargs):
            return None
            
        def info(self, *args, **kwargs):
            return None
            
        def warning(self, *args, **kwargs):
            return None
            
        def error(self, *args, **kwargs):
            return None
            
        def success(self, *args, **kwargs):
            return None
            
        def header(self, *args, **kwargs):
            return None
            
        def subheader(self, *args, **kwargs):
            return None
            
        def checkbox(self, *args, **kwargs):
            return kwargs.get('value', False)
            
        def expander(self, *args, **kwargs):
            return self  # Return self to allow chaining
    
    class MockEmpty:
        def empty(self):
            return None
    
    class MockColumn:
        def write(self, *args, **kwargs):
            return None
            
        def markdown(self, *args, **kwargs):
            return None
            
        def button(self, *args, **kwargs):
            return False
            
        def selectbox(self, *args, **kwargs):
            return kwargs.get('value', 'test')
            
        def __enter__(self):
            return self
            
        def __exit__(self, *args):
            return None
    
    class MockStreamlit:
        def __init__(self):
            self.session_state = MockSessionState()
            self.sidebar = MockSidebar()
        
        def title(self, *args, **kwargs):
            return None
            
        def write(self, *args, **kwargs):
            return None
            
        def set_page_config(self, **kwargs):
            return None
            
        def markdown(self, *args, **kwargs):
            return None
            
        def header(self, *args, **kwargs):
            return None
            
        def subheader(self, *args, **kwargs):
            return None
            
        def text(self, *args, **kwargs):
            return None
            
        def selectbox(self, *args, **kwargs):
            return kwargs.get('value', 'test')
            
        def text_input(self, *args, **kwargs):
            return kwargs.get('value', 'test')
            
        def text_area(self, *args, **kwargs):
            return kwargs.get('value', 'test')
            
        def button(self, *args, **kwargs):
            return False
            
        def success(self, *args, **kwargs):
            return None
            
        def error(self, *args, **kwargs):
            return None
            
        def warning(self, *args, **kwargs):
            return None
            
        def info(self, *args, **kwargs):
            return None
            
        def empty(self):
            return MockEmpty()
            
        def columns(self, *args, **kwargs):
            if args:
                if isinstance(args[0], (list, tuple)):
                    num_cols = len(args[0])
                else:
                    num_cols = args[0]
            else:
                num_cols = 1
            return [MockColumn() for _ in range(num_cols)]
            
        def form(self, *args, **kwargs):
            return self
            
        def form_submit_button(self, *args, **kwargs):
            return False
            
        def __enter__(self):
            return self
            
        def __exit__(self, *args):
            return None
            
        def checkbox(self, *args, **kwargs):
            return kwargs.get('value', False)
            
        def slider(self, *args, **kwargs):
            return kwargs.get('value', 0)
            
        def expander(self, *args, **kwargs):
            return self
            
        def spinner(self, *args, **kwargs):
            return self
            
        def tabs(self, *args, **kwargs):
            return [self] * len(args[0]) if args else [self]
            
        def download_button(self, *args, **kwargs):
            return False
            
        def json(self, *args, **kwargs):
            return None
    
    return MockStreamlit()


def mock_streamlit_for_testing():
    """Set up Streamlit mock in sys.modules and environment for testing."""
    # Set mock API keys to avoid connection attempts
    os.environ['OPENAI_API_KEY'] = 'test-key'
    os.environ['GEMINI_API_KEY'] = 'test-key'
    os.environ['TAVILY_API_KEY'] = 'test-key'
    
    # Mock streamlit module
    sys.modules['streamlit'] = create_streamlit_mock()


if __name__ == "__main__":
    # Test the mock by importing the app
    mock_streamlit_for_testing()
    
    try:
        import app
        print('✅ Application startup test passed')
    except Exception as e:
        print(f'❌ Application startup test failed: {e}')
        sys.exit(1)