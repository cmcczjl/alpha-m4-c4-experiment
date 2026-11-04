#!/usr/bin/env bash
set -e

# -------------------------------------------------
# Install make if missing
# -------------------------------------------------
install_make() {
    if command -v make >/dev/null 2>&1; then
        echo "make is already installed"
        return
    fi
    echo "make not found, attempting installation..."
    if command -v apt-get >/dev/null 2>&1; then
        sudo apt-get update -y
        sudo apt-get install -y make
    elif command -v brew >/dev/null 2>&1; then
        brew install make
    else
        echo "Neither apt-get nor brew found. Please install make manually."
        exit 1
    fi
    echo "make installed successfully"
}

# -------------------------------------------------
# Install n8n via npm if possible
# -------------------------------------------------
install_n8n_npm() {
    if command -v n8n >/dev/null 2>&1; then
        echo "n8n is already installed"
        return 0
    fi
    echo "n8n not found, attempting npm installation..."
    if ! command -v npm >/dev/null 2>&1; then
        echo "npm not found, installing Node.js..."
        if command -v apt-get >/dev/null 2>&1; then
            sudo apt-get update -y
            sudo apt-get install -y nodejs npm
        elif command -v brew >/dev/null 2>&1; then
            brew install node
        else
            echo "Cannot install Node.js automatically. Please install it manually."
            return 1
        fi
    fi
    npm install -g n8n
    echo "n8n installed successfully"
    return 0
}

# -------------------------------------------------
# Fallback: run n8n via Docker
# -------------------------------------------------
run_n8n_docker() {
    if command -v n8n >/dev/null 2>&1; then
        return
    fi
    echo "Falling back to Docker deployment for n8n..."
    if ! command -v docker >/dev/null 2>&1; then
        echo "Docker not found, installing Docker..."
        if command -v apt-get >/dev/null 2>&1; then
            sudo apt-get update -y
            sudo apt-get install -y docker.io
        elif command -v brew >/dev/null 2>&1; then
            brew install --cask docker
        else
            echo "Cannot install Docker automatically. Please install it manually."
            exit 1
        fi
    fi
    # Pull and run n8n container
    docker run -d --name n8n -p 5678:5678 n8nio/n8n
    echo "n8n Docker container started"
}

# -------------------------------------------------
# Execute steps
# -------------------------------------------------
install_make
if ! install_n8n_npm; then
    run_n8n_docker
fi

echo "Setup completed."