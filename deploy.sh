#!/bin/bash

set -e  # Exit on error

# Configuration
REPO_URL="https://github.com/Koheyo/ChatDB.git"
REPO_DIR="chatdb-project"
LOG_DIR="logs"
APP_PORT=8501

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to handle errors
handle_error() {
    log "ERROR: $1"
    exit 1
}

# Create logs directory if it doesn't exist
mkdir -p "$LOG_DIR" || handle_error "Failed to create logs directory"

# Step 1: Clone or Pull latest code
if [ -d "$REPO_DIR/.git" ]; then
    log "Pulling latest code from main branch..."
    cd "$REPO_DIR" || handle_error "Failed to enter $REPO_DIR directory"
    git checkout main || handle_error "Failed to checkout main branch"
    git pull origin main || handle_error "Failed to pull latest changes"
else
    log "Cloning repo for the first time..."
    git clone -b main "$REPO_URL" "$REPO_DIR" || handle_error "Failed to clone repository"
    cd "$REPO_DIR" || handle_error "Failed to enter $REPO_DIR directory"
fi

# Step 2: Set up virtual environment
if [ ! -d "venv" ]; then
    log "Creating virtual environment..."
    python3 -m venv venv || handle_error "Failed to create virtual environment"
fi

log "Activating virtual environment..."
source venv/bin/activate || handle_error "Failed to activate virtual environment"

# Step 3: Install dependencies
log "Installing Python packages..."
pip install --upgrade pip || handle_error "Failed to upgrade pip"
pip install -r requirements.txt || handle_error "Failed to install requirements"

# Step 4: Kill existing Streamlit process if running
log "Checking for existing Streamlit processes..."
pkill -f "streamlit run" || true

# Step 5: Run Streamlit app
log "Starting Streamlit app..."
nohup streamlit run src/main.py \
    --server.port $APP_PORT \
    --server.address 0.0.0.0 \
    > "$LOG_DIR/streamlit.log" 2>&1 &

# Wait for the process to start
sleep 5

# Check if the process is running
if pgrep -f "streamlit run" > /dev/null; then
    log "Deployment successful! App is running at: http://$(curl -s ifconfig.me):$APP_PORT"
    log "Check logs at: $LOG_DIR/streamlit.log"
else
    handle_error "Failed to start Streamlit application"
fi
