#!/usr/bin/env bash
set -e

# Colors and Emojis
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

print_msg() {
    echo -e "${GREEN}==>${NC} $1"
}
print_warn() {
    echo -e "${YELLOW}==>${NC} $1"
}
print_error() {
    echo -e "${RED}==> ERROR:${NC} $1"
}

cat << "EOF"
  __  __       _                  _     
 |  \/  |     ( )                (_)    
 | \  / |_   _|/ ___ _   _ _ __   _  ___ 
 | |\/| | | | | / __| | | | '__| | |/ __|
 | |  | | |_| | \__ \ |_| | |    | | (__ 
 |_|  |_|\__,_| |___/\__, |_|    |_|\___|
                      __/ |              
                     |___/               
EOF
echo -e "${BLUE}Welcome to the Mu(syr)ic installer! 🎵${NC}\n"

# 2. Detect OS
OS_TYPE="unknown"
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS_TYPE="macos"
elif [[ -f /etc/os-release ]]; then
    . /etc/os-release
    if [[ "$ID_LIKE" == *"debian"* ]] || [[ "$ID" == "debian" ]] || [[ "$ID" == "ubuntu" ]]; then
        OS_TYPE="debian"
    elif [[ "$ID_LIKE" == *"rhel"* ]] || [[ "$ID_LIKE" == *"fedora"* ]] || [[ "$ID" == "fedora" ]]; then
        OS_TYPE="fedora"
    elif [[ "$ID_LIKE" == *"arch"* ]] || [[ "$ID" == "arch" ]]; then
        OS_TYPE="arch"
    fi
fi

if [[ "$OS_TYPE" == "unknown" ]]; then
    print_error "Unsupported operating system. Please install dependencies manually."
    exit 1
fi

print_msg "Detected OS: $OS_TYPE 💻"

# 3. Check Python 3.9+
check_python() {
    if command -v python3 &>/dev/null; then
        local version=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
        local major=${version%.*}
        local minor=${version#*.}
        if [[ "$major" -eq 3 ]] && [[ "$minor" -ge 9 ]]; then
            return 0
        fi
    fi
    return 1
}

install_python() {
    print_warn "Python 3.9+ not found. Attempting to install... 🐍"
    if [[ "$OS_TYPE" == "macos" ]]; then
        if ! command -v brew &>/dev/null; then
            print_warn "Homebrew not found. Installing Homebrew... 🍺"
            /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
            if [[ -x /opt/homebrew/bin/brew ]]; then
                eval "$(/opt/homebrew/bin/brew shellenv)"
            fi
        fi
        brew install python
    elif [[ "$OS_TYPE" == "debian" ]]; then
        sudo apt update
        sudo apt install -y python3 python3-venv python3-pip
    elif [[ "$OS_TYPE" == "fedora" ]]; then
        sudo dnf install -y python3 python3-pip
    elif [[ "$OS_TYPE" == "arch" ]]; then
        sudo pacman -Sy --noconfirm python python-pip
    fi
}

if ! check_python; then
    install_python
    if ! check_python; then
        print_error "Failed to install Python 3.9+. Please install it manually."
        exit 1
    fi
fi
print_msg "Python 3.9+ is installed! ✅"

# 4. Check FFmpeg
install_ffmpeg() {
    print_warn "FFmpeg not found. Attempting to install... 🎬"
    if [[ "$OS_TYPE" == "macos" ]]; then
        brew install ffmpeg
    elif [[ "$OS_TYPE" == "debian" ]]; then
        sudo apt install -y ffmpeg
    elif [[ "$OS_TYPE" == "fedora" ]]; then
        sudo dnf install -y ffmpeg
    elif [[ "$OS_TYPE" == "arch" ]]; then
        sudo pacman -Sy --noconfirm ffmpeg
    fi
}

if ! command -v ffmpeg &>/dev/null; then
    install_ffmpeg
    if ! command -v ffmpeg &>/dev/null; then
        print_error "Failed to install FFmpeg. Please install it manually."
        exit 1
    fi
fi
print_msg "FFmpeg is installed! ✅"

# 5. Create .venv virtual environment
print_msg "Setting up virtual environment... 📦"
if [[ ! -d ".venv" ]]; then
    python3 -m venv .venv
fi
source .venv/bin/activate

# 6. Install dependencies from requirements.txt
if [[ -f "requirements.txt" ]]; then
    print_msg "Installing dependencies... ⚙️"
    pip install --upgrade pip
    pip install -r requirements.txt
else
    print_warn "No requirements.txt found, skipping dependency installation."
fi

# 7. Create a musyric launcher script
print_msg "Creating 'musyric.sh' launcher script... 🚀"
cat << 'EOF' > musyric.sh
#!/usr/bin/env bash

# Get the directory where the script is located
DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Activate the virtual environment
source "$DIR/.venv/bin/activate"

# If no arguments provided, show help
if [ $# -eq 0 ]; then
    python -m musyric.cli --help
else
    python -m musyric.cli "$@"
fi
EOF

chmod +x musyric.sh

# 8. Offer to create a symlink
echo -e "\n${YELLOW}Would you like to install the 'musyric' command globally? (Requires sudo)${NC}"
read -p "(y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [[ -w /usr/local/bin ]] || sudo -n true 2>/dev/null || sudo echo -n ""; then
        sudo ln -sf "$(pwd)/musyric.sh" /usr/local/bin/musyric
        print_msg "Created symlink in /usr/local/bin/musyric! 🔗"
    else
        print_warn "Could not create symlink (sudo failed or cancelled). You can still run it via ./musyric.sh"
    fi
fi

# 9. Show Setup Complete
echo -e "\n${GREEN}🎉 Setup Complete! 🎉${NC}\n"
echo -e "You can now run Mu(syr)ic interactively by executing:"
echo -e "  ${BLUE}./start.sh${NC} (or double-click ${BLUE}start.command${NC} on macOS)"
echo -e "\nOr run CLI commands via:"
echo -e "  ${BLUE}./musyric.sh${NC}"
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "Or simply from anywhere:"
    echo -e "  ${BLUE}musyric${NC}"
fi
echo -e "\nEnjoy your music! 🎵"
