#!/bin/bash
# ============================================================
#  NeuroRift × OpenClaw — Unified Installer
#  Installs: Docker, Docker Compose, Ollama, and all deps.
#  Launches the full stack via Docker Compose.
# ============================================================
set -euo pipefail

# ── Colors ───────────────────────────────────────────────────
RED='\033[0;31m'
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
BOLD='\033[1m'
NC='\033[0m'

# ── Helpers ──────────────────────────────────────────────────
info()    { echo -e "${BLUE}[INFO]${NC}  $*"; }
success() { echo -e "${GREEN}[OK]${NC}    $*"; }
warn()    { echo -e "${YELLOW}[WARN]${NC}  $*"; }
error()   { echo -e "${RED}[ERROR]${NC} $*"; }
step()    { echo -e "\n${BOLD}${CYAN}━━━ $* ━━━${NC}"; }

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# ── Root check ───────────────────────────────────────────────
if [ "$EUID" -eq 0 ]; then
    warn "Running as root. Recommended: run as a normal user with sudo."
    read -rp "Continue anyway? (y/N) " reply
    [[ "${reply,,}" == "y" ]] || exit 1
fi

# ── Detect OS ────────────────────────────────────────────────
step "System Detection"
if [ -f /etc/os-release ]; then
    # shellcheck source=/dev/null
    source /etc/os-release
    OS_NAME="${NAME:-Unknown}"
    OS_ID="${ID:-unknown}"
else
    OS_NAME="Unknown Linux"
    OS_ID="unknown"
fi
ARCH="$(uname -m)"
info "OS:   ${OS_NAME}"
info "ID:   ${OS_ID}"
info "Arch: ${ARCH}"

# ── Package manager ───────────────────────────────────────────
if command -v apt-get &>/dev/null; then
    PKG_MGR="apt"
elif command -v dnf &>/dev/null; then
    PKG_MGR="dnf"
elif command -v yum &>/dev/null; then
    PKG_MGR="yum"
elif command -v pacman &>/dev/null; then
    PKG_MGR="pacman"
else
    PKG_MGR="unknown"
fi
info "Package manager: ${PKG_MGR}"

pkg_install() {
    case "$PKG_MGR" in
        apt)    sudo apt-get install -y --no-install-recommends "$@" ;;
        dnf)    sudo dnf install -y "$@" ;;
        yum)    sudo yum install -y "$@" ;;
        pacman) sudo pacman -S --noconfirm "$@" ;;
        *)      warn "Cannot auto-install: $*. Please install manually." ;;
    esac
}

# ─────────────────────────────────────────────────────────────
# 1. System Base Dependencies
# ─────────────────────────────────────────────────────────────
step "1/7  System Base Dependencies"
case "$PKG_MGR" in
    apt)
        sudo apt-get update -qq
        pkg_install curl wget git ca-certificates gnupg lsb-release \
            build-essential libssl-dev pkg-config python3-full python3-pip \
            python3-venv unzip tor
        ;;
    dnf|yum)
        pkg_install curl wget git ca-certificates gnupg \
            gcc gcc-c++ make openssl-devel pkgconfig python3-pip \
            python3-devel unzip tor
        ;;
    pacman)
        pkg_install curl wget git ca-certificates gnupg \
            base-devel openssl python python-pip unzip tor
        ;;
esac
success "Base dependencies installed"

# ─────────────────────────────────────────────────────────────
# 2. Docker Engine + Docker Compose
# ─────────────────────────────────────────────────────────────
step "2/7  Docker Engine + Docker Compose"

install_docker_apt() {
    info "Adding Docker APT repository..."
    sudo install -m 0755 -d /etc/apt/keyrings
    curl -fsSL "https://download.docker.com/linux/${OS_ID}/gpg" \
        | sudo gpg --dearmor -o /etc/apt/keyrings/docker.gpg
    sudo chmod a+r /etc/apt/keyrings/docker.gpg
    echo \
        "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] \
https://download.docker.com/linux/${OS_ID} $(lsb_release -cs) stable" \
        | sudo tee /etc/apt/sources.list.d/docker.list > /dev/null
    sudo apt-get update -qq
    sudo apt-get install -y docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin
}

install_docker_dnf() {
    sudo dnf config-manager --add-repo \
        https://download.docker.com/linux/centos/docker-ce.repo
    sudo dnf install -y docker-ce docker-ce-cli containerd.io \
        docker-buildx-plugin docker-compose-plugin
}

if command -v docker &>/dev/null; then
    DOCKER_VER="$(docker --version 2>/dev/null || echo 'unknown')"
    success "Docker already installed: ${DOCKER_VER}"
else
    info "Installing Docker Engine..."
    case "$PKG_MGR" in
        apt)    install_docker_apt ;;
        dnf|yum) install_docker_dnf ;;
        pacman) pkg_install docker docker-compose ;;
        *)
            warn "Cannot auto-install Docker. Please install manually:"
            warn "  https://docs.docker.com/engine/install/"
            ;;
    esac
    success "Docker installed"
fi

# Enable and start Docker daemon
if ! systemctl is-active --quiet docker 2>/dev/null; then
    info "Starting Docker daemon..."
    sudo systemctl enable docker --now 2>/dev/null || \
        warn "Could not start Docker via systemctl. Start it manually: sudo dockerd"
fi

# Add current user to docker group (avoids needing sudo for docker commands)
if ! groups "$USER" | grep -q docker; then
    info "Adding ${USER} to docker group..."
    sudo usermod -aG docker "$USER"
    warn "Group change requires a new shell session to take effect."
    warn "After install, run:  newgrp docker  (or log out and back in)"
fi

# Verify docker compose plugin
if docker compose version &>/dev/null; then
    success "Docker Compose plugin available"
elif command -v docker-compose &>/dev/null; then
    success "docker-compose (standalone) available"
else
    # Fallback: install compose plugin manually
    info "Installing Docker Compose plugin manually..."
    COMPOSE_VERSION="$(curl -s https://api.github.com/repos/docker/compose/releases/latest \
        | grep '"tag_name"' | cut -d'"' -f4)"
    COMPOSE_URL="https://github.com/docker/compose/releases/download/${COMPOSE_VERSION}/docker-compose-linux-${ARCH}"
    sudo mkdir -p /usr/local/lib/docker/cli-plugins
    sudo curl -fsSL "$COMPOSE_URL" -o /usr/local/lib/docker/cli-plugins/docker-compose
    sudo chmod +x /usr/local/lib/docker/cli-plugins/docker-compose
    success "Docker Compose ${COMPOSE_VERSION} installed"
fi

# ─────────────────────────────────────────────────────────────
# 3. Ollama (standalone — also runs as the Docker service)
# ─────────────────────────────────────────────────────────────
step "3/7  Ollama AI Runtime"

if command -v ollama &>/dev/null; then
    success "Ollama already installed: $(ollama --version 2>/dev/null || echo 'unknown')"
else
    info "Installing Ollama..."
    curl -fsSL https://ollama.ai/install.sh | sh
    success "Ollama installed"
fi

# Ensure Ollama systemd service exists (the install.sh creates it)
if systemctl list-unit-files --type=service 2>/dev/null | grep -q ollama; then
    info "Enabling Ollama system service..."
    sudo systemctl enable ollama 2>/dev/null || true
fi
success "Ollama ready"

# ─────────────────────────────────────────────────────────────
# 4. Rust Toolchain (for openclaw build)
# ─────────────────────────────────────────────────────────────
step "4/7  Rust Toolchain"

if command -v rustc &>/dev/null; then
    success "Rust already installed: $(rustc --version)"
else
    info "Installing Rust via rustup..."
    curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y --no-modify-path
    success "Rust installed"
fi

# Source cargo env for the rest of the script
if [ -f "$HOME/.cargo/env" ]; then
    # shellcheck source=/dev/null
    source "$HOME/.cargo/env"
fi

# ─────────────────────────────────────────────────────────────
# 5. Node.js (for web-ui local dev, optional for Docker mode)
# ─────────────────────────────────────────────────────────────
step "5/7  Node.js"

if command -v node &>/dev/null; then
    success "Node.js already installed: $(node --version)"
else
    info "Installing Node.js 20.x..."
    case "$PKG_MGR" in
        apt)
            curl -fsSL https://deb.nodesource.com/setup_20.x | sudo -E bash -
            sudo apt-get install -y nodejs
            ;;
        dnf|yum)
            curl -fsSL https://rpm.nodesource.com/setup_20.x | sudo bash -
            pkg_install nodejs npm
            ;;
        pacman)
            pkg_install nodejs npm
            ;;
        *)
            warn "Please install Node.js 20+ manually: https://nodejs.org"
            ;;
    esac
    success "Node.js installed: $(node --version 2>/dev/null || echo 'check manually')"
fi

# ─────────────────────────────────────────────────────────────
# 6. Go + Security Tools (nmap, subfinder, nuclei, httpx…)
# ─────────────────────────────────────────────────────────────
step "6/7  Security Tools"

# nmap (system package)
if ! command -v nmap &>/dev/null; then
    info "Installing nmap..."
    pkg_install nmap
fi
success "nmap: $(nmap --version 2>/dev/null | head -1 || echo 'ok')"

# Go toolchain
if ! command -v go &>/dev/null; then
    info "Installing Go 1.21..."
    GO_VER="1.21.6"
    GO_ARCH="$( [ "$ARCH" = "aarch64" ] && echo "arm64" || echo "amd64" )"
    wget -q "https://go.dev/dl/go${GO_VER}.linux-${GO_ARCH}.tar.gz" -O /tmp/go.tar.gz
    sudo rm -rf /usr/local/go
    sudo tar -C /usr/local -xzf /tmp/go.tar.gz
    rm -f /tmp/go.tar.gz
    export PATH="$PATH:/usr/local/go/bin"
    grep -q '/usr/local/go/bin' "$HOME/.bashrc" 2>/dev/null || \
        echo 'export PATH=$PATH:/usr/local/go/bin:$HOME/go/bin' >> "$HOME/.bashrc"
    success "Go installed"
else
    success "Go already installed: $(go version)"
fi
export PATH="$PATH:$(go env GOPATH 2>/dev/null)/bin:/usr/local/go/bin"

# ProjectDiscovery tools
for tool_pkg in \
    "subfinder:github.com/projectdiscovery/subfinder/v2/cmd/subfinder@latest" \
    "nuclei:github.com/projectdiscovery/nuclei/v3/cmd/nuclei@latest" \
    "httpx:github.com/projectdiscovery/httpx/cmd/httpx@latest"; do
    tool="${tool_pkg%%:*}"
    pkg="${tool_pkg##*:}"
    if ! command -v "$tool" &>/dev/null; then
        info "Installing ${tool}..."
        go install -v "$pkg" 2>/dev/null || warn "Failed to install ${tool} — install Go first"
    fi
    command -v "$tool" &>/dev/null && success "${tool} ready" || warn "${tool} not found in PATH"
done

# ─────────────────────────────────────────────────────────────
# 7. Python Environment (for local dev / non-Docker runs)
# ─────────────────────────────────────────────────────────────
step "7/7  Python Virtual Environment"

VENV_DIR="${SCRIPT_DIR}/.venv"
if [ ! -d "$VENV_DIR" ]; then
    info "Creating Python virtual environment at ${VENV_DIR}..."
    python3 -m venv "$VENV_DIR"
fi
# shellcheck source=/dev/null
source "${VENV_DIR}/bin/activate"
pip install --upgrade pip -q
pip install -q -r "${SCRIPT_DIR}/requirements.txt"
success "Python environment ready"

# ─────────────────────────────────────────────────────────────
# Environment Configuration
# ─────────────────────────────────────────────────────────────
step "Environment Configuration"

if [ ! -f "${SCRIPT_DIR}/.env" ]; then
    info "Creating .env from .env.example..."
    cp "${SCRIPT_DIR}/.env.example" "${SCRIPT_DIR}/.env"
    success ".env created — edit it to customise models / API keys"
else
    success ".env already exists"
fi

chmod +x "${SCRIPT_DIR}"/docker/neurorift/entrypoint.sh \
         "${SCRIPT_DIR}"/docker/openclaw/entrypoint.sh 2>/dev/null || true
[ -d "${SCRIPT_DIR}/scripts" ] && chmod +x "${SCRIPT_DIR}"/scripts/*.sh 2>/dev/null || true

# ─────────────────────────────────────────────────────────────
# Build & Start with Docker Compose
# ─────────────────────────────────────────────────────────────
step "Building Docker Images"

cd "$SCRIPT_DIR"

# Use 'docker compose' (plugin) or 'docker-compose' (standalone)
if docker compose version &>/dev/null 2>&1; then
    COMPOSE_CMD="docker compose"
elif command -v docker-compose &>/dev/null; then
    COMPOSE_CMD="docker-compose"
else
    error "Docker Compose not found. Cannot build images."
    error "Please re-run the installer after Docker is fully set up."
    exit 1
fi

info "Running: ${COMPOSE_CMD} build"
# Use sudo if user is not yet in the docker group this session
if ! docker info &>/dev/null 2>&1; then
    warn "Docker requires sudo for this session (group change pending relogin)."
    COMPOSE_CMD="sudo $COMPOSE_CMD"
fi

$COMPOSE_CMD build
success "All Docker images built"

# ─────────────────────────────────────────────────────────────
# Pull AI Model inside Ollama container
# ─────────────────────────────────────────────────────────────
step "Pre-pulling Ollama Model"

OLLAMA_MODEL="${OLLAMA_MAIN_MODEL:-llama3}"
info "Starting Ollama container to pull model: ${OLLAMA_MODEL}"
$COMPOSE_CMD up -d ollama

info "Waiting for Ollama to be ready..."
for i in $(seq 1 30); do
    if $COMPOSE_CMD exec -T ollama curl -sf http://localhost:11434/api/tags &>/dev/null; then
        success "Ollama is ready"
        break
    fi
    [ "$i" -eq 30 ] && warn "Ollama slow to start — pull may run later" && break
    sleep 3
done

info "Pulling ${OLLAMA_MODEL} (this may take several minutes on first run)..."
$COMPOSE_CMD exec -T ollama ollama pull "${OLLAMA_MODEL}" || \
    warn "Model pull failed. Run manually: docker compose exec ollama ollama pull ${OLLAMA_MODEL}"

# ─────────────────────────────────────────────────────────────
# Start All Services
# ─────────────────────────────────────────────────────────────
step "Starting NeuroRift × OpenClaw"
$COMPOSE_CMD up -d
success "All services started"

# ─────────────────────────────────────────────────────────────
# Done
# ─────────────────────────────────────────────────────────────
echo ""
echo -e "${GREEN}${BOLD}╔══════════════════════════════════════════════════════╗${NC}"
echo -e "${GREEN}${BOLD}║      ✅  NeuroRift × OpenClaw — Ready!               ║${NC}"
echo -e "${GREEN}${BOLD}╚══════════════════════════════════════════════════════╝${NC}"
echo ""
echo -e "  ${CYAN}Web UI:${NC}       http://localhost:3000"
echo -e "  ${CYAN}Logs:${NC}         ${COMPOSE_CMD} logs -f"
echo -e "  ${CYAN}Stop:${NC}         ${COMPOSE_CMD} down"
echo -e "  ${CYAN}Dev mode:${NC}     ${COMPOSE_CMD} -f docker-compose.yml -f docker-compose.dev.yml up"
echo ""
echo -e "  ${YELLOW}If Docker group change is pending, run:${NC}"
echo -e "    newgrp docker"
echo ""
echo -e "  ${CYAN}See DOCKER.md for full documentation.${NC}"
echo ""