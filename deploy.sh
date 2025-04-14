#!/bin/bash

set -e  # Exit on error

# Configuration
GITHUB_TOKEN="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"
REPO_URL="https://${GITHUB_TOKEN}@github.com/Koheyo/ChatDB.git"
REPO_DIR="chatdb-project"
APP_PORT=8501
TEMP_DIR=".deploy_temp"

# Function to log messages
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to handle errors
handle_error() {
    log "ERROR: $1"
    exit 1
}

# Cleanup function
cleanup() {
    if [ -d "$TEMP_DIR" ]; then
        rm -rf "$TEMP_DIR"
    fi
}

# Register cleanup on script exit
trap cleanup EXIT

# Step 1: Clone or Pull latest code
if [ -d "$REPO_DIR/.git" ]; then
    log "Resetting any local changes..."
    cd "$REPO_DIR" || handle_error "Failed to enter $REPO_DIR directory"
    git reset --hard HEAD || handle_error "Failed to reset local changes"
    git clean -fd || handle_error "Failed to clean untracked files"
    git pull origin main || handle_error "Failed to pull latest changes"
else
    log "Cloning repo for the first time..."
    git clone -b main "$REPO_URL" "$REPO_DIR" || handle_error "Failed to clone repository"
    cd "$REPO_DIR" || handle_error "Failed to enter $REPO_DIR directory"
fi

# Now we're in the project directory, set up logs and temp directory
LOG_DIR="logs"
mkdir -p "$LOG_DIR" || handle_error "Failed to create logs directory"
mkdir -p "$TEMP_DIR" || handle_error "Failed to create temp directory"
log "Created logs directory at: $(pwd)/$LOG_DIR"

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
# Create a temporary script to run Streamlit in the temp directory
cat > "$TEMP_DIR/run_streamlit.sh" << 'EOF'
#!/bin/bash
source venv/bin/activate
streamlit run app.py --server.port 8501 --server.address 0.0.0.0
EOF

chmod +x "$TEMP_DIR/run_streamlit.sh"

# Run Streamlit in the background and redirect output
nohup "$TEMP_DIR/run_streamlit.sh" > "$LOG_DIR/streamlit.log" 2>&1 &

# Wait for the process to start
sleep 10

# Check if the process is running
if pgrep -f "streamlit run" > /dev/null; then
    log "Deployment successful! App is running at: http://$(curl -s ifconfig.me):$APP_PORT"
    log "Check logs at: $(pwd)/$LOG_DIR/streamlit.log"
    # Print the last few lines of the log for verification
    log "Last few lines of the log:"
    tail -n 10 "$LOG_DIR/streamlit.log"
else
    log "Streamlit process not found. Checking logs for errors..."
    if [ -f "$LOG_DIR/streamlit.log" ]; then
        cat "$LOG_DIR/streamlit.log"
    else
        log "No log file found at: $(pwd)/$LOG_DIR/streamlit.log"
    fi
    handle_error "Failed to start Streamlit application"
fi
