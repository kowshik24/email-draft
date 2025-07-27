# Professor Outreach Assistant

A Streamlit application to help students draft professional emails to professors and find PhD positions.

## Features

- **✉️ Email Draft**: Generate personalized emails to professors based on your CV and their research
- **👨‍🏫 Professor Suggestions**: Find matching professors at specific universities
- **🎓 PhD Position Finder**: Enhanced search for professors using real-time web data and analyze their hiring status

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your API keys:
```bash
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here
TAVILY_API_KEY=your_tavily_key_here
```

### API Keys Required

- **OpenAI API Key**: For GPT models (get from [OpenAI](https://platform.openai.com/))
- **Gemini API Key**: For Google's Gemini models (get from [Google AI Studio](https://makersuite.google.com/app/apikey))
- **Tavily API Key**: For web search functionality in PhD Position Finder (get from [Tavily](https://tavily.com/))

## Running the Application

### Start the app
```bash
./run_app.sh
```

### Stop the app
```bash
./stop_app.sh
```

### Check if app is running
```bash
ps aux | grep streamlit
```

### View logs
```bash
tail -f streamlit.log
```

## Access the Application
Once running, access the app at: http://localhost:8501

## Testing Tavily Integration

To test if your Tavily API key is working correctly:

```bash
python test_tavily.py
```

To test the enhanced professor search functionality:

```bash
python test_enhanced_search.py
```

To test all the new enhanced features:

```bash
python test_enhanced_features.py
```

## Enhanced PhD Position Finder

The PhD Position Finder now uses a two-step approach for more accurate and up-to-date results:

1. **Tavily Web Search**: Searches for current faculty information from university websites
2. **AI Processing**: Uses the retrieved information to find professors matching your profile
3. **Configurable Parameters**: Customize search depth, results count, and content extraction

### Key Features:
- **Real-time Data**: Uses current web information instead of outdated training data
- **Smart Research Area Detection**: Automatically extracts research areas from CV for targeted searches
- **Enhanced Search Queries**: Multiple targeted queries based on research interests
- **Configurable Search**: Adjust search parameters for better results
- **Robust Fallbacks**: Multiple fallback mechanisms for content extraction
- **Additional Profile Links**: Automatic search for Google Scholar and LinkedIn profiles
- **Improved AI Matching**: Better prompts and criteria for professor-student matching
- **Post-processing Enhancement**: Additional searches to fill missing information
- **Comprehensive Results**: Includes personal websites, Google Scholar, and LinkedIn profiles

### Search Parameters:
- **Search Depth**: Basic (faster) or Advanced (comprehensive)
- **Max Results**: Number of search results per query (1-20)
- **Content Extraction**: Basic or Advanced content extraction from URLs
- **Time Range**: Filter results by recency (day, week, month, year)
- **Domain Filters**: Include/exclude specific domains

## Note
Make sure to make the shell scripts executable:
```bash
chmod +x run_app.sh stop_app.sh
```