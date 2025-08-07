#!/bin/bash
set -e  # Exit on any error

# Deploy script for Email Draft Application
# This script handles deployment to various environments

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
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

# Configuration
APP_NAME="email-draft"
DEFAULT_PORT=8501
DEPLOYMENT_MODE=${DEPLOYMENT_MODE:-"production"}
HEALTH_CHECK_TIMEOUT=30
BACKUP_ENABLED=${BACKUP_ENABLED:-"true"}

# Environment validation
validate_environment() {
    log_info "Validating deployment environment..."
    
    # Check required environment variables
    required_vars=("OPENAI_API_KEY" "GEMINI_API_KEY" "TAVILY_API_KEY")
    missing_vars=()
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            missing_vars+=("$var")
        fi
    done
    
    if [ ${#missing_vars[@]} -ne 0 ]; then
        log_warning "Missing API keys: ${missing_vars[*]}"
        log_warning "Application may not function fully without all API keys"
    fi
    
    # Check Python version
    python_version=$(python3 --version 2>&1 | cut -d' ' -f2)
    log_info "Python version: $python_version"
    
    # Check if requirements are installable
    if ! python3 -m pip list &>/dev/null; then
        log_error "pip is not available"
        return 1
    fi
    
    log_success "Environment validation completed"
}

# Backup current deployment (if exists)
backup_deployment() {
    if [ "$BACKUP_ENABLED" = "true" ] && [ -d "$APP_NAME" ]; then
        log_info "Creating backup of current deployment..."
        backup_dir="${APP_NAME}_backup_$(date +%Y%m%d_%H%M%S)"
        cp -r "$APP_NAME" "$backup_dir"
        log_success "Backup created: $backup_dir"
    fi
}

# Install dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."
    
    # Upgrade pip
    python3 -m pip install --upgrade pip
    
    # Install main dependencies
    if [ -f "requirements.txt" ]; then
        python3 -m pip install -r requirements.txt
        log_success "Main dependencies installed"
    else
        log_error "requirements.txt not found"
        return 1
    fi
    
    # Install development dependencies if available
    if [ -f "requirements-dev.txt" ] && [ "$DEPLOYMENT_MODE" = "development" ]; then
        python3 -m pip install -r requirements-dev.txt || log_warning "Some dev dependencies failed to install"
    fi
}

# Environment-specific deployment
deploy_local() {
    log_info "Deploying locally..."
    
    # Stop existing instance if running
    if [ -f "app.pid" ]; then
        log_info "Stopping existing application..."
        ./stop_app.sh || log_warning "Failed to stop existing app (may not be running)"
    fi
    
    # Create .env file from template if it doesn't exist
    if [ ! -f ".env" ] && [ -f "env_template.txt" ]; then
        log_info "Creating .env file from template..."
        cp env_template.txt .env
        log_warning "Please update .env file with your actual API keys"
    fi
    
    # Make scripts executable
    chmod +x run_app.sh stop_app.sh
    
    # Start application
    log_info "Starting application..."
    ./run_app.sh
    
    # Wait a moment for startup
    sleep 5
    
    # Check if application started successfully
    if [ -f "app.pid" ]; then
        pid=$(cat app.pid)
        if kill -0 "$pid" 2>/dev/null; then
            log_success "Application started successfully (PID: $pid)"
            log_info "Application should be available at: http://localhost:$DEFAULT_PORT"
        else
            log_error "Application failed to start"
            return 1
        fi
    else
        log_error "PID file not found, application may have failed to start"
        return 1
    fi
}

deploy_remote() {
    log_info "Deploying to remote server..."
    
    # Check required remote deployment variables
    if [ -z "$DEPLOY_HOST" ] || [ -z "$DEPLOY_USER" ] || [ -z "$DEPLOY_PATH" ]; then
        log_error "Remote deployment requires DEPLOY_HOST, DEPLOY_USER, and DEPLOY_PATH"
        return 1
    fi
    
    # Create deployment package
    log_info "Creating deployment package..."
    tar -czf "${APP_NAME}_deploy.tar.gz" \
        --exclude='.git' \
        --exclude='__pycache__' \
        --exclude='*.pyc' \
        --exclude='venv' \
        --exclude='.venv' \
        --exclude='node_modules' \
        --exclude='*.log' \
        --exclude='app.pid' \
        .
    
    # Upload and deploy
    if [ -n "$DEPLOY_KEY" ]; then
        # Use SSH key
        log_info "Uploading via SSH key..."
        scp -i "$DEPLOY_KEY" "${APP_NAME}_deploy.tar.gz" "$DEPLOY_USER@$DEPLOY_HOST:$DEPLOY_PATH/"
        ssh -i "$DEPLOY_KEY" "$DEPLOY_USER@$DEPLOY_HOST" "
            cd $DEPLOY_PATH &&
            tar -xzf ${APP_NAME}_deploy.tar.gz &&
            chmod +x *.sh &&
            ./deploy.sh local
        "
    else
        log_error "SSH key (DEPLOY_KEY) required for remote deployment"
        return 1
    fi
    
    # Cleanup local deployment package
    rm -f "${APP_NAME}_deploy.tar.gz"
    
    log_success "Remote deployment completed"
}

# Health check
health_check() {
    log_info "Performing health check..."
    
    # Check if application is responding
    local timeout=$HEALTH_CHECK_TIMEOUT
    local count=0
    
    while [ $count -lt $timeout ]; do
        if curl -s "http://localhost:$DEFAULT_PORT" >/dev/null 2>&1; then
            log_success "Health check passed - application is responding"
            return 0
        fi
        
        count=$((count + 1))
        sleep 1
    done
    
    log_error "Health check failed - application not responding after ${timeout}s"
    return 1
}

# Rollback function
rollback() {
    log_warning "Rolling back deployment..."
    
    # Find most recent backup
    backup_dir=$(ls -td ${APP_NAME}_backup_* 2>/dev/null | head -1)
    
    if [ -n "$backup_dir" ] && [ -d "$backup_dir" ]; then
        log_info "Rolling back to: $backup_dir"
        
        # Stop current application
        ./stop_app.sh 2>/dev/null || true
        
        # Restore backup
        rm -rf "$APP_NAME" 2>/dev/null || true
        mv "$backup_dir" "$APP_NAME"
        cd "$APP_NAME"
        
        # Restart application
        ./run_app.sh
        
        log_success "Rollback completed"
    else
        log_error "No backup found for rollback"
        return 1
    fi
}

# Cleanup old backups (keep last 5)
cleanup_backups() {
    log_info "Cleaning up old backups..."
    ls -td ${APP_NAME}_backup_* 2>/dev/null | tail -n +6 | xargs rm -rf
    log_success "Backup cleanup completed"
}

# Main deployment logic
main() {
    log_info "Starting deployment of $APP_NAME..."
    log_info "Deployment mode: $DEPLOYMENT_MODE"
    
    # Parse command line arguments
    case "${1:-local}" in
        local)
            validate_environment || exit 1
            backup_deployment
            install_dependencies || exit 1
            deploy_local || {
                log_error "Local deployment failed"
                if [ "$BACKUP_ENABLED" = "true" ]; then
                    rollback
                fi
                exit 1
            }
            health_check || {
                log_warning "Health check failed, but deployment may still be successful"
            }
            cleanup_backups
            ;;
        remote)
            validate_environment || exit 1
            deploy_remote || exit 1
            ;;
        rollback)
            rollback || exit 1
            ;;
        health-check)
            health_check || exit 1
            ;;
        *)
            echo "Usage: $0 {local|remote|rollback|health-check}"
            echo "  local       - Deploy locally (default)"
            echo "  remote      - Deploy to remote server"
            echo "  rollback    - Rollback to previous deployment"
            echo "  health-check - Check application health"
            exit 1
            ;;
    esac
    
    log_success "Deployment completed successfully!"
}

# Trap to handle script interruption
trap 'log_error "Deployment interrupted"; exit 1' INT TERM

# Run main function
main "$@"