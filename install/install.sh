#!/bin/bash

# Voice-to-Text System Installation Script
# This script installs the voice-to-text system and its dependencies

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
PROJECT_NAME="voice-to-text-system"
INSTALL_DIR="/opt/$PROJECT_NAME"
SERVICE_NAME="voice-to-text"
CONFIG_DIR="/etc/$PROJECT_NAME"
LOG_DIR="/var/log/$PROJECT_NAME"
BIN_DIR="/usr/local/bin"

# Get current directory (where the script is located)
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_DIR="$( cd "$SCRIPT_DIR/.." && pwd )"

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

check_root() {
    if [[ $EUID -ne 0 ]]; then
        print_error "This script must be run as root (use sudo)"
        exit 1
    fi
}

check_system() {
    print_status "Checking system requirements..."
    
    # Check if running on Linux
    if [[ "$OSTYPE" != "linux-gnu"* ]]; then
        print_error "This system is only supported on Linux"
        exit 1
    fi
    
    # Check if Python 3 is installed
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is required but not installed"
        exit 1
    fi
    
    # Check if pip is installed
    if ! command -v pip3 &> /dev/null; then
        print_error "pip3 is required but not installed"
        exit 1
    fi
    
    print_success "System requirements met"
}

install_system_deps() {
    print_status "Installing system dependencies..."
    
    # Detect package manager and install dependencies
    if command -v apt-get &> /dev/null; then
        apt-get update
        apt-get install -y \
            python3-dev \
            python3-pip \
            python3-venv \
            portaudio19-dev \
            libsndfile1 \
            ffmpeg \
            alsa-utils \
            pulseaudio \
            xdotool
    elif command -v dnf &> /dev/null; then
        dnf install -y \
            python3-devel \
            python3-pip \
            portaudio-devel \
            libsndfile \
            ffmpeg \
            alsa-utils \
            pulseaudio \
            xdotool
    elif command -v yum &> /dev/null; then
        yum install -y \
            python3-devel \
            python3-pip \
            portaudio-devel \
            libsndfile \
            ffmpeg \
            alsa-utils \
            pulseaudio \
            xdotool
    else
        print_warning "Unknown package manager. Please install the following packages manually:"
        print_warning "- Python 3 development headers"
        print_warning "- PortAudio development library"
        print_warning "- libsndfile"
        print_warning "- FFmpeg"
        print_warning "- ALSA utilities"
        print_warning "- PulseAudio"
        print_warning "- xdotool"
    fi
    
    print_success "System dependencies installed"
}

create_directories() {
    print_status "Creating directories..."
    
    # Create directories with proper permissions
    mkdir -p "$INSTALL_DIR"
    mkdir -p "$CONFIG_DIR"
    mkdir -p "$LOG_DIR"
    
    # Set permissions
    chmod 755 "$INSTALL_DIR"
    chmod 755 "$CONFIG_DIR"
    chmod 755 "$LOG_DIR"
    
    print_success "Directories created"
}

install_application() {
    print_status "Installing application files..."
    
    # Copy source files
    cp -r "$PROJECT_DIR/src"/* "$INSTALL_DIR/"
    
    # Copy configuration files
    cp "$PROJECT_DIR/config/default_settings.json" "$CONFIG_DIR/"
    
    # Create user config if it doesn't exist
    if [[ ! -f "$CONFIG_DIR/user_settings.json" ]]; then
        echo '{}' > "$CONFIG_DIR/user_settings.json"
    fi
    
    # Copy sounds directory if it exists
    if [[ -d "$PROJECT_DIR/sounds" ]]; then
        cp -r "$PROJECT_DIR/sounds" "$INSTALL_DIR/"
    fi
    
    # Make main script executable
    chmod +x "$INSTALL_DIR/main.py"
    
    # Update config paths in the default config
    sed -i "s|/home/vshnsngh/Desktop/Coding/voice-to-text-system/logs/|$LOG_DIR/|g" "$CONFIG_DIR/default_settings.json"
    
    print_success "Application files installed"
}

install_python_deps() {
    print_status "Installing Python dependencies..."
    
    # Create virtual environment
    python3 -m venv "$INSTALL_DIR/venv"
    
    # Activate virtual environment and install dependencies
    source "$INSTALL_DIR/venv/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip
    
    # Install required packages
    pip install \
        whisper \
        sounddevice \
        soundfile \
        numpy \
        pyautogui \
        pyperclip \
        pynput
    
    deactivate
    
    print_success "Python dependencies installed"
}

create_launcher() {
    print_status "Creating launcher script..."
    
    # Create launcher script
    cat > "$BIN_DIR/voice-to-text" << EOF
#!/bin/bash
# Voice-to-Text System Launcher

cd "$INSTALL_DIR"
source "$INSTALL_DIR/venv/bin/activate"
exec python3 "$INSTALL_DIR/main.py" --config "$CONFIG_DIR" "\$@"
EOF

    chmod +x "$BIN_DIR/voice-to-text"
    
    print_success "Launcher script created"
}

install_service() {
    print_status "Installing systemd service..."
    
    # Copy service file
    cp "$PROJECT_DIR/install/voice-to-text.service" "/etc/systemd/system/"
    
    # Update service file with correct paths
    sed -i "s|/opt/voice-to-text-system|$INSTALL_DIR|g" "/etc/systemd/system/voice-to-text.service"
    sed -i "s|/etc/voice-to-text-system|$CONFIG_DIR|g" "/etc/systemd/system/voice-to-text.service"
    
    # Reload systemd
    systemctl daemon-reload
    
    # Enable service (but don't start it yet)
    systemctl enable voice-to-text.service
    
    print_success "Systemd service installed"
}

show_post_install() {
    print_success "Installation completed successfully!"
    echo
    echo -e "${BLUE}Usage:${NC}"
    echo "  voice-to-text                 # Run in foreground"
    echo "  voice-to-text --daemon        # Run as daemon"
    echo "  voice-to-text --status        # Check status"
    echo "  voice-to-text --stop          # Stop daemon"
    echo
    echo -e "${BLUE}Service Management:${NC}"
    echo "  sudo systemctl start voice-to-text     # Start service"
    echo "  sudo systemctl stop voice-to-text      # Stop service"
    echo "  sudo systemctl status voice-to-text    # Check service status"
    echo
    echo -e "${BLUE}Configuration:${NC}"
    echo "  Config files: $CONFIG_DIR/"
    echo "  Logs: $LOG_DIR/"
    echo "  Application: $INSTALL_DIR/"
    echo
    echo -e "${YELLOW}Note:${NC} Default hotkey is Ctrl+Alt+V"
    echo -e "${YELLOW}Note:${NC} Make sure your microphone is working and accessible"
}

# Main installation process
main() {
    echo -e "${GREEN}Voice-to-Text System Installer${NC}"
    echo "================================"
    echo
    
    check_root
    check_system
    install_system_deps
    create_directories
    install_application
    install_python_deps
    create_launcher
    install_service
    
    echo
    show_post_install
}

# Handle command line arguments
case "$1" in
    --help|-h)
        echo "Usage: $0 [--help]"
        echo "Install the Voice-to-Text System"
        exit 0
        ;;
    *)
        main
        ;;
esac