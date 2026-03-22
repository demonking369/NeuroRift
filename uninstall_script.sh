#!/bin/bash

# ╔══════════════════════════════════════════════════════════╗
# ║ NeuroRift Uninstall Script                               ║
# ║ Designed and developed by demonking369 🧠                ║
# ║ GitHub: https://github.com/demonking369/NeuroRift        ║
# ╚══════════════════════════════════════════════════════════╝

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${RED}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${RED}║           NeuroRift Uninstall Utility                    ║${NC}"
echo -e "${RED}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${YELLOW}This will help you remove NeuroRift components from your system.${NC}"
echo ""

# Function to ask yes/no question
ask_yes_no() {
    local prompt=$1
    local default=${2:-N}
    
    if [ "$default" = "Y" ]; then
        read -p "$prompt [Y/n]: " response
        response=${response:-Y}
    else
        read -p "$prompt [y/N]: " response
        response=${response:-N}
    fi
    
    [[ "$response" =~ ^[Yy]$ ]]
}

# Display what will be uninstalled
echo -e "${BLUE}Select components to uninstall:${NC}"
echo ""

# Ask about each component
UNINSTALL_APP=false
UNINSTALL_MODELS=false
UNINSTALL_TOOLS=false
UNINSTALL_CONFIG=false
UNINSTALL_SESSIONS=false

if ask_yes_no "Remove NeuroRift application (Python package)?"; then
    UNINSTALL_APP=true
fi

if command -v ollama &> /dev/null; then
    if ask_yes_no "Remove AI models (llama.cpp models)?"; then
        UNINSTALL_MODELS=true
    fi
fi

if ask_yes_no "Remove security tools (subfinder, httpx, nuclei, etc.)?"; then
    UNINSTALL_TOOLS=true
fi

if ask_yes_no "Remove configuration files (~/.neurorift/configs)?"; then
    UNINSTALL_CONFIG=true
fi

if ask_yes_no "Remove session data (~/.neurorift/sessions)?"; then
    UNINSTALL_SESSIONS=true
fi

# Confirm before proceeding
echo ""
echo -e "${YELLOW}Summary of what will be removed:${NC}"
[ "$UNINSTALL_APP" = true ] && echo -e "  ${RED}✗${NC} NeuroRift application"
[ "$UNINSTALL_MODELS" = true ] && echo -e "  ${RED}✗${NC} AI models"
[ "$UNINSTALL_TOOLS" = true ] && echo -e "  ${RED}✗${NC} Security tools"
[ "$UNINSTALL_CONFIG" = true ] && echo -e "  ${RED}✗${NC} Configuration files"
[ "$UNINSTALL_SESSIONS" = true ] && echo -e "  ${RED}✗${NC} Session data (.nrs files)"
echo ""

if ! ask_yes_no "${RED}Proceed with uninstallation?${NC}"; then
    echo -e "${GREEN}Uninstallation cancelled.${NC}"
    exit 0
fi

echo ""
echo -e "${BLUE}Starting uninstallation...${NC}"
echo ""

# Uninstall NeuroRift application
if [ "$UNINSTALL_APP" = true ]; then
    echo -e "${YELLOW}Removing NeuroRift application...${NC}"
    
    # Try pipx first
    if command -v pipx &> /dev/null; then
        if pipx list | grep -q neurorift; then
            pipx uninstall neurorift
            echo -e "${GREEN}[✓] Removed via pipx${NC}"
        fi
    fi
    
    # Try pip user install
    if pip list --user 2>/dev/null | grep -q neurorift; then
        pip uninstall -y neurorift
        echo -e "${GREEN}[✓] Removed via pip (user)${NC}"
    fi
    
    # Try system pip
    if command -v sudo &> /dev/null; then
        if pip list 2>/dev/null | grep -q neurorift; then
            sudo pip uninstall -y neurorift
            echo -e "${GREEN}[✓] Removed via pip (system)${NC}"
        fi
    fi
    
    # Remove from /usr/local/bin if exists
    if [ -f "/usr/local/bin/neurorift" ]; then
        if command -v sudo &> /dev/null; then
            sudo rm -f /usr/local/bin/neurorift
            echo -e "${GREEN}[✓] Removed /usr/local/bin/neurorift${NC}"
        else
            rm -f /usr/local/bin/neurorift 2>/dev/null || echo -e "${YELLOW}[!] Could not remove /usr/local/bin/neurorift (permission denied)${NC}"
        fi
    fi
fi

# Uninstall AI models
if [ "$UNINSTALL_MODELS" = true ]; then
    echo -e "${YELLOW}Removing AI models...${NC}"
    
    if command -v ollama &> /dev/null; then
        # List models and remove them
        MODELS=$(ollama list | tail -n +2 | awk '{print $1}')
        
        if [ -n "$MODELS" ]; then
            echo "Found models:"
            echo "$MODELS"
            echo ""
            
            if ask_yes_no "Remove ALL llama.cpp models?"; then
                for model in $MODELS; do
                    echo "Removing $model..."
                    ollama rm "$model"
                done
                echo -e "${GREEN}[✓] Removed all AI models${NC}"
            else
                echo "Skipping model removal"
            fi
        else
            echo -e "${YELLOW}[!] No models found${NC}"
        fi
    fi
fi

# Uninstall security tools
if [ "$UNINSTALL_TOOLS" = true ]; then
    echo -e "${YELLOW}Removing security tools...${NC}"
    
    GOBIN="${GOBIN:-$HOME/go/bin}"
    
    TOOLS=(
        "subfinder"
        "httpx"
        "nuclei"
        "ffuf"
        "gobuster"
    )
    
    for tool in "${TOOLS[@]}"; do
        if [ -f "$GOBIN/$tool" ]; then
            rm -f "$GOBIN/$tool"
            echo -e "${GREEN}[✓] Removed $tool${NC}"
        fi
    done
fi

# Remove session data
if [ "$UNINSTALL_SESSIONS" = true ]; then
    echo -e "${YELLOW}Removing session data...${NC}"
    
    if [ -d "$HOME/.neurorift/sessions" ]; then
        # Count sessions
        SESSION_COUNT=$(find "$HOME/.neurorift/sessions" -name "*.nrs" 2>/dev/null | wc -l)
        
        if [ "$SESSION_COUNT" -gt 0 ]; then
            echo -e "${YELLOW}Found $SESSION_COUNT session(s)${NC}"
            if ask_yes_no "Delete all sessions? (This cannot be undone)" "N"; then
                rm -rf "$HOME/.neurorift/sessions"
                rm -rf "$HOME/.neurorift/session_data"
                echo -e "${GREEN}[✓] Removed all sessions${NC}"
            else
                echo -e "${YELLOW}[!] Keeping session data${NC}"
            fi
        else
            rm -rf "$HOME/.neurorift/sessions"
            rm -rf "$HOME/.neurorift/session_data"
            echo -e "${GREEN}[✓] Removed session directories${NC}"
        fi
    fi
fi

# Remove configuration files
if [ "$UNINSTALL_CONFIG" = true ]; then
    echo -e "${YELLOW}Removing configuration files...${NC}"
    
    if [ -d "$HOME/.neurorift/configs" ]; then
        rm -rf "$HOME/.neurorift/configs"
        echo -e "${GREEN}[✓] Removed ~/.neurorift/configs${NC}"
    fi
    
    # Remove .env file from project directory if it exists
    if [ -f ".env" ]; then
        rm -f .env
        echo -e "${GREEN}[✓] Removed .env${NC}"
    fi
    
    # Remove entire .neurorift directory if empty
    if [ -d "$HOME/.neurorift" ]; then
        if [ -z "$(ls -A $HOME/.neurorift)" ]; then
            rm -rf "$HOME/.neurorift"
            echo -e "${GREEN}[✓] Removed ~/.neurorift (empty)${NC}"
        else
            echo -e "${YELLOW}[!] ~/.neurorift not empty, keeping directory${NC}"
        fi
    fi
fi

echo ""
echo -e "${GREEN}╔══════════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}║           Uninstallation Complete!                       ║${NC}"
echo -e "${GREEN}╚══════════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "${BLUE}Thank you for using NeuroRift!${NC}"
echo -e "${BLUE}Designed and developed by demonking369${NC}"
echo -e "${BLUE}To reinstall, run: ./install_script.sh${NC}"
