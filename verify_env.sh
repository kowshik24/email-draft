#!/bin/bash
# Environment verification script for CI/CD pipeline
# Run this script to verify your local environment is ready

set -e

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

echo "🔍 Environment Verification for CI/CD Pipeline"
echo "=============================================="

# Check Python version
log_info "Checking Python version..."
python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
if python3 -c "import sys; sys.exit(0 if sys.version_info >= (3, 8) else 1)"; then
    log_success "Python $python_version (compatible)"
else
    log_error "Python $python_version (requires 3.8+)"
    exit 1
fi

# Check pip
log_info "Checking pip..."
if command -v pip3 >/dev/null 2>&1; then
    pip_version=$(pip3 --version | cut -d' ' -f2)
    log_success "pip $pip_version available"
else
    log_error "pip3 not found"
    exit 1
fi

# Check git
log_info "Checking git..."
if command -v git >/dev/null 2>&1; then
    git_version=$(git --version | cut -d' ' -f3)
    log_success "git $git_version available"
else
    log_error "git not found"
    exit 1
fi

# Check required files
log_info "Checking required files..."
required_files=(
    "app.py"
    "requirements.txt"
    "env_template.txt"
    "run_app.sh"
    "stop_app.sh"
    "deploy.sh"
    ".github/workflows/deploy.yml"
)

for file in "${required_files[@]}"; do
    if [ -f "$file" ]; then
        log_success "$file exists"
    else
        log_error "$file missing"
        exit 1
    fi
done

# Check if scripts are executable
log_info "Checking script permissions..."
scripts=("run_app.sh" "stop_app.sh" "deploy.sh" "test_pipeline.sh")
for script in "${scripts[@]}"; do
    if [ -x "$script" ]; then
        log_success "$script is executable"
    else
        log_warning "$script is not executable, fixing..."
        chmod +x "$script"
        log_success "$script made executable"
    fi
done

# Check basic dependencies
log_info "Checking basic dependencies..."
if python3 -c "import streamlit, os, sys, json, re" 2>/dev/null; then
    log_success "Basic Python modules available"
else
    log_warning "Some basic modules missing, installing dependencies..."
    pip3 install -r requirements.txt
fi

# Check API keys in environment
log_info "Checking API keys..."
api_keys=("OPENAI_API_KEY" "GEMINI_API_KEY" "TAVILY_API_KEY")
keys_found=0

for key in "${api_keys[@]}"; do
    if [ -n "${!key}" ]; then
        log_success "$key is set"
        keys_found=$((keys_found + 1))
    else
        log_warning "$key not set in environment"
    fi
done

if [ $keys_found -eq 0 ]; then
    log_warning "No API keys found in environment"
    log_info "Create a .env file or set environment variables for full functionality"
else
    log_success "$keys_found API keys found"
fi

# Check .env file
log_info "Checking .env file..."
if [ -f ".env" ]; then
    log_success ".env file exists"
    # Count non-empty, non-comment lines
    env_vars=$(grep -v '^#' .env | grep -v '^$' | wc -l)
    log_info ".env file contains $env_vars variables"
else
    log_warning ".env file not found"
    if [ -f "env_template.txt" ]; then
        log_info "You can copy env_template.txt to .env and add your API keys"
    fi
fi

# Test basic pipeline functionality
log_info "Testing basic pipeline functionality..."
if ./test_pipeline.sh >/dev/null 2>&1; then
    log_success "Pipeline test passed"
else
    log_warning "Pipeline test failed, but basic setup is complete"
    log_info "Run './test_pipeline.sh' for detailed output"
fi

# GitHub integration check
log_info "Checking GitHub integration..."
if git remote -v | grep -q "github.com"; then
    log_success "GitHub remote configured"
    
    # Check if we're in a git repository
    if git rev-parse --git-dir >/dev/null 2>&1; then
        current_branch=$(git branch --show-current)
        log_info "Current branch: $current_branch"
        
        # Check for uncommitted changes
        if git diff-index --quiet HEAD --; then
            log_success "No uncommitted changes"
        else
            log_warning "You have uncommitted changes"
            log_info "Commit changes before pushing to trigger CI/CD"
        fi
    fi
else
    log_warning "No GitHub remote found"
    log_info "Make sure this repository is connected to GitHub for CI/CD"
fi

echo ""
echo "🎉 Environment Verification Complete!"
echo "====================================="

if [ $keys_found -gt 0 ]; then
    echo "✅ Your environment is ready for CI/CD pipeline"
    echo "✅ API keys are configured"
    echo "✅ All required files are present"
    echo "✅ Scripts have correct permissions"
    echo ""
    echo "🚀 Next steps:"
    echo "1. Commit and push to main branch to trigger the pipeline"
    echo "2. Check GitHub Actions for pipeline status"
    echo "3. Monitor deployment logs"
else
    echo "⚠️  Your environment is mostly ready for CI/CD pipeline"
    echo "✅ All required files are present"
    echo "✅ Scripts have correct permissions"
    echo "⚠️  No API keys found in environment"
    echo ""
    echo "🚀 Next steps:"
    echo "1. Set up API keys in .env file or GitHub secrets"
    echo "2. Commit and push to main branch to trigger the pipeline"
    echo "3. Check GitHub Actions for pipeline status"
fi

echo ""
echo "📚 For detailed setup instructions, see CI_CD_GUIDE.md"