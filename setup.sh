#!/bin/bash
# Setup script for Sunday voice assistant
# Installs system dependencies required for file manager integration

echo "==================================="
echo "Sunday Voice Assistant - Setup"
echo "==================================="
echo ""

# Check if running on Linux
if [[ "$OSTYPE" != "linux-gnu"* ]]; then
    echo "⚠️  This script is for Linux systems only"
    echo "For Windows/Mac, file selection detection may not work"
    exit 1
fi

echo "Installing system dependencies..."
echo ""

# Install xdotool and xclip for file selection detection
echo "📦 Installing xdotool and xclip..."
sudo apt update
sudo apt install -y xdotool xclip

if [ $? -eq 0 ]; then
    echo "✅ System dependencies installed successfully"
else
    echo "❌ Failed to install system dependencies"
    echo "Please run manually: sudo apt install xdotool xclip"
    exit 1
fi

echo ""
echo "Installing Python dependencies..."
pip3 install -r requirements.txt

if [ $? -eq 0 ]; then
    echo "✅ Python dependencies installed successfully"
else
    echo "❌ Failed to install Python dependencies"
    exit 1
fi

echo ""
echo "Setting up system permissions..."
chmod +x scripts/sunday-permissions.sh
./scripts/sunday-permissions.sh

echo ""
echo "==================================="
echo "✅ Setup complete!"
echo "==================================="
echo ""
echo "You can now run Sunday with: python3 main.py"
echo ""
