# Professor Outreach Assistant

A Streamlit application to help students draft professional emails to professors.

## Setup

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Create a `.env` file with your API keys:
```bash
OPENAI_API_KEY=your_openai_key_here
GEMINI_API_KEY=your_gemini_key_here
```

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

## Note
Make sure to make the shell scripts executable:
```bash
chmod +x run_app.sh stop_app.sh
```