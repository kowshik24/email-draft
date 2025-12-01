# CI/CD Pipeline Setup Guide

This guide explains how to set up and use the CI/CD pipeline for the Professor Outreach Assistant application.

## 🚀 Quick Start

### 1. GitHub Secrets Configuration

In your GitHub repository, go to **Settings > Secrets and variables > Actions** and add the following secrets:

#### Required API Keys
- `OPENAI_API_KEY`: Your OpenAI API key from [OpenAI Platform](https://platform.openai.com/)
- `GEMINI_API_KEY`: Your Google Gemini API key from [Google AI Studio](https://makersuite.google.com/app/apikey)
- `TAVILY_API_KEY`: Your Tavily API key from [Tavily](https://tavily.com/)

#### Optional Deployment Secrets (for remote deployment)
- `DEPLOY_HOST`: Remote server hostname or IP address
- `DEPLOY_USER`: SSH username for remote server
- `DEPLOY_KEY`: SSH private key for authentication
- `DEPLOY_PATH`: Deployment path on remote server

### 2. Trigger the Pipeline

The CI/CD pipeline automatically triggers when you:
- Push code to the `main` branch
- Create a pull request targeting the `main` branch

## 📋 Pipeline Overview

### Workflow Steps

1. **Code Checkout**: Downloads the latest code
2. **Environment Setup**: Installs Python and caches dependencies
3. **Dependency Installation**: Installs application and development dependencies
4. **Code Quality Checks**:
   - Linting with flake8
   - Code formatting with black
   - Import sorting with isort
   - Security scanning with bandit
   - Vulnerability checking with safety
5. **Testing**:
   - Unit tests (always run)
   - Integration tests (only if API keys are available)
   - Application startup validation
6. **Deployment** (only on main branch):
   - Local or remote deployment
   - Health checks
   - Rollback on failure
7. **Notifications**: Status reporting and summary

### Testing Strategy

- **Unit Tests**: Test basic functionality without external dependencies
- **Integration Tests**: Test API integrations (skipped if keys unavailable)
- **Startup Tests**: Validate application can start correctly
- **Deployment Tests**: Verify deployment scripts work correctly

## 🛠️ Local Testing

### Run Full Pipeline Test
```bash
./test_pipeline.sh
```

### Run Individual Components
```bash
# Unit tests only
python -m unittest tests.test_basic -v

# Integration tests (requires API keys)
python -m unittest tests.test_integration -v

# Test application startup
python streamlit_mock.py

# Test deployment script
./deploy.sh health-check
```

### Code Quality Checks
```bash
# Linting
python -m flake8 .

# Code formatting
python -m black --check .

# Import sorting
python -m isort --check-only .

# Security scanning
python -m bandit -r .
python -m safety check
```

## 🔧 Manual Deployment

### Local Deployment
```bash
./deploy.sh local
```

### Remote Deployment
```bash
# Requires deployment secrets to be set
./deploy.sh remote
```

### Other Deployment Commands
```bash
# Health check
./deploy.sh health-check

# Rollback to previous deployment
./deploy.sh rollback
```

## 📊 Monitoring

### GitHub Actions
- Monitor pipeline status in the **Actions** tab
- View detailed logs for each step
- Check deployment status and notifications

### Application Health
- The deployment script includes health checks
- Failed deployments trigger automatic rollback
- Logs are available for debugging

### Status Badges
The README includes status badges showing:
- CI/CD Pipeline status
- Python version compatibility
- Code quality rating

## 🚨 Troubleshooting

### Common Issues

**Pipeline Fails on Dependency Installation**
- Check if all dependencies in `requirements.txt` are available
- Verify Python version compatibility

**Tests Fail Due to Missing API Keys**
- Unit tests should work without API keys
- Integration tests are skipped if keys are missing
- Check secret names match exactly

**Deployment Fails**
- Verify deployment secrets are correctly configured
- Check server connectivity and permissions
- Review deployment logs for specific errors

**Application Won't Start**
- Check if all required files are present
- Verify environment variables are set correctly
- Test locally with `./deploy.sh local`

### Debug Commands
```bash
# Check if all required files exist
ls -la app.py requirements.txt run_app.sh stop_app.sh deploy.sh

# Verify scripts are executable
ls -la *.sh

# Test dependencies
python -c "import streamlit, openai, google.generativeai"

# Check GitHub Actions workflow syntax
python -c "import yaml; yaml.safe_load(open('.github/workflows/deploy.yml'))"
```

## 🔒 Security Considerations

### Best Practices
- Never commit API keys or secrets to code
- Use GitHub secrets for sensitive information
- Regularly rotate API keys
- Monitor for security vulnerabilities
- Keep dependencies updated

### Included Security Measures
- Bandit security scanning
- Safety vulnerability checking
- No hardcoded secrets
- Secure secret handling in CI/CD
- Error handling to prevent secret exposure

## 📚 Additional Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Python CI/CD Best Practices](https://docs.python.org/3/devguide/ci.html)
- [Streamlit Deployment Guide](https://docs.streamlit.io/deploy)
- [OpenAI API Documentation](https://platform.openai.com/docs)
- [Google AI Documentation](https://ai.google.dev/)

## 🤝 Contributing

When contributing to this project:
1. Create a feature branch from `main`
2. Make your changes
3. Ensure all tests pass locally
4. Create a pull request
5. The CI/CD pipeline will automatically test your changes
6. Merge to `main` triggers deployment

## 📞 Support

If you encounter issues with the CI/CD pipeline:
1. Check the troubleshooting section above
2. Review GitHub Actions logs
3. Test locally using the provided scripts
4. Create an issue with detailed error information