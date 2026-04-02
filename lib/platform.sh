#!/usr/bin/env bash
#
# platform.sh - Platform detection and package management
#
# Assumes lib/common.sh has been sourced (provides: info, success, warn, error, debug, has_cmd).

# ============================================================================
# Platform Detection
# ============================================================================

detect_platform() {
    OS="$(uname -s)"
    ARCH="$(uname -m)"
    IS_WSL=false
    IS_DARWIN=false
    IS_LINUX=false
    PKGMGR=""
    DISTRO=""

    case "$OS" in
        Darwin)
            IS_DARWIN=true
            PKGMGR="brew"
            DISTRO="macos"
            ;;
        Linux)
            IS_LINUX=true
            # Check for WSL
            if [[ -f /proc/sys/fs/binfmt_misc/WSLInterop ]] || grep -qi microsoft /proc/version 2>/dev/null; then
                IS_WSL=true
            fi
            # Detect distro and package manager
            if [[ -f /etc/os-release ]]; then
                . /etc/os-release
                DISTRO="${ID:-unknown}"
                case "$ID" in
                    ubuntu|debian|pop|linuxmint|elementary|zorin)
                        PKGMGR="apt"
                        ;;
                    amzn|amazonlinux|fedora|rhel|centos|rocky|almalinux)
                        PKGMGR="dnf"
                        # Amazon Linux 2 uses yum
                        if [[ "$VERSION_ID" == "2" ]] && command -v yum &>/dev/null && ! command -v dnf &>/dev/null; then
                            PKGMGR="yum"
                        fi
                        ;;
                    arch|manjaro|endeavouros)
                        PKGMGR="pacman"
                        ;;
                    opensuse*|sles)
                        PKGMGR="zypper"
                        ;;
                    *)
                        # Fallback detection
                        if command -v apt &>/dev/null; then
                            PKGMGR="apt"
                        elif command -v dnf &>/dev/null; then
                            PKGMGR="dnf"
                        elif command -v yum &>/dev/null; then
                            PKGMGR="yum"
                        elif command -v pacman &>/dev/null; then
                            PKGMGR="pacman"
                        elif command -v zypper &>/dev/null; then
                            PKGMGR="zypper"
                        fi
                        ;;
                esac
            fi
            ;;
        *)
            error "Unsupported OS: $OS"
            exit 1
            ;;
    esac

    debug "Platform: OS=$OS ARCH=$ARCH DISTRO=$DISTRO PKGMGR=$PKGMGR IS_WSL=$IS_WSL"
}

# ============================================================================
# Package Installation Helpers
# ============================================================================

# Install packages based on package manager
pkg_install() {
    local packages=("$@")

    case "$PKGMGR" in
        apt)
            sudo apt update
            sudo apt install -y "${packages[@]}"
            ;;
        dnf)
            sudo dnf install -y "${packages[@]}"
            ;;
        yum)
            sudo yum install -y "${packages[@]}"
            ;;
        pacman)
            sudo pacman -Syu --noconfirm --needed "${packages[@]}"
            ;;
        zypper)
            sudo zypper install -y "${packages[@]}"
            ;;
        brew)
            brew install "${packages[@]}"
            ;;
        *)
            error "Unknown package manager: $PKGMGR"
            return 1
            ;;
    esac
}

# Update packages based on package manager
pkg_update() {
    case "$PKGMGR" in
        apt)
            sudo apt update && sudo apt upgrade -y
            ;;
        dnf)
            sudo dnf upgrade -y
            ;;
        yum)
            sudo yum update -y
            ;;
        pacman)
            sudo pacman -Syu --noconfirm
            ;;
        zypper)
            sudo zypper update -y
            ;;
        brew)
            brew update && brew upgrade
            ;;
    esac
}

# Map package names across distributions
get_pkg_name() {
    local pkg="$1"

    case "$pkg" in
        fd)
            case "$PKGMGR" in
                apt) echo "fd-find" ;;
                dnf|yum) echo "fd-find" ;;
                *) echo "fd" ;;
            esac
            ;;
        bat)
            echo "bat"
            ;;
        ripgrep)
            case "$PKGMGR" in
                *) echo "ripgrep" ;;
            esac
            ;;
        shellcheck)
            case "$PKGMGR" in
                dnf|yum) echo "ShellCheck" ;;
                *) echo "shellcheck" ;;
            esac
            ;;
        *)
            echo "$pkg"
            ;;
    esac
}

# Install Homebrew on macOS
install_homebrew() {
    if ! has_cmd brew; then
        info "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

        # Add to PATH for current session
        if [[ -f /opt/homebrew/bin/brew ]]; then
            eval "$(/opt/homebrew/bin/brew shellenv)"
        elif [[ -f /usr/local/bin/brew ]]; then
            eval "$(/usr/local/bin/brew shellenv)"
        fi
        success "Homebrew installed"
    else
        success "Homebrew already installed"
    fi
}

# Install 1Password CLI
install_1password_cli() {
    if has_cmd op; then
        local op_version
        op_version=$(op --version 2>/dev/null || echo "unknown")
        success "1Password CLI already installed (v${op_version})"
        return 0
    fi

    info "Installing 1Password CLI..."

    case "$PKGMGR" in
        apt)
            # Add 1Password apt repository
            curl -sS https://downloads.1password.com/linux/keys/1password.asc | \
                sudo gpg --dearmor --output /usr/share/keyrings/1password-archive-keyring.gpg 2>/dev/null || true
            echo "deb [arch=$(dpkg --print-architecture) signed-by=/usr/share/keyrings/1password-archive-keyring.gpg] https://downloads.1password.com/linux/debian/$(dpkg --print-architecture) stable main" | \
                sudo tee /etc/apt/sources.list.d/1password.list >/dev/null
            sudo mkdir -p /etc/debsig/policies/AC2D62742012EA22/
            curl -sS https://downloads.1password.com/linux/debian/debsig/1password.pol | \
                sudo tee /etc/debsig/policies/AC2D62742012EA22/1password.pol >/dev/null
            sudo mkdir -p /usr/share/debsig/keyrings/AC2D62742012EA22
            curl -sS https://downloads.1password.com/linux/keys/1password.asc | \
                sudo gpg --dearmor --output /usr/share/debsig/keyrings/AC2D62742012EA22/debsig.gpg 2>/dev/null || true
            sudo apt update && sudo apt install -y 1password-cli
            ;;
        dnf|yum)
            sudo rpm --import https://downloads.1password.com/linux/keys/1password.asc
            sudo sh -c 'echo -e "[1password]\nname=1Password Stable Channel\nbaseurl=https://downloads.1password.com/linux/rpm/stable/\$basearch\nenabled=1\ngpgcheck=1\nrepo_gpgcheck=1\ngpgkey=https://downloads.1password.com/linux/keys/1password.asc" > /etc/yum.repos.d/1password.repo'
            if [[ "$PKGMGR" == "dnf" ]]; then
                sudo dnf install -y 1password-cli
            else
                sudo yum install -y 1password-cli
            fi
            ;;
        pacman)
            if has_cmd yay; then
                yay -S --noconfirm 1password-cli
            elif has_cmd paru; then
                paru -S --noconfirm 1password-cli
            else
                warn "Please install 1password-cli from AUR manually (yay -S 1password-cli)"
                return 1
            fi
            ;;
        brew)
            brew install --cask 1password-cli
            ;;
        zypper)
            sudo rpm --import https://downloads.1password.com/linux/keys/1password.asc
            sudo zypper addrepo https://downloads.1password.com/linux/rpm/stable/x86_64 1password
            sudo zypper install -y 1password-cli
            ;;
        *)
            warn "Cannot auto-install 1Password CLI for $PKGMGR"
            echo "  Please visit: https://1password.com/downloads/command-line/"
            return 1
            ;;
    esac

    if has_cmd op; then
        success "1Password CLI installed (v$(op --version))"
    else
        error "1Password CLI installation failed"
        return 1
    fi
}
