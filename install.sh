#!/bin/bash

echo "Installing AI Shell..."

# Check if Python is installed
if ! command -v python &> /dev/null && ! command -v python3 &> /dev/null; then
    echo "Python is not installed or not in your PATH."
    echo "Please install Python from https://www.python.org/downloads/"
    exit 1
fi

# Determine Python command
PYTHON_CMD="python"
if ! command -v python &> /dev/null; then
    PYTHON_CMD="python3"
fi

# Create requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    echo "Creating minimal requirements.txt..."
    echo "requests" > requirements.txt
fi

# Install Python dependencies
echo "Installing Python dependencies..."

# Try normal install
$PYTHON_CMD -m pip install -r requirements.txt 2> pip_error.log

# If it failed due to externally managed environment, retry with --break-system-packages
if grep -q "externally-managed-environment" pip_error.log; then
    echo "Detected PEP 668 restriction. Retrying with --break-system-packages..."
    $PYTHON_CMD -m pip install --break-system-packages -r requirements.txt
    $PYTHON_CMD -m pip install --break-system-packages boto3
fi

rm -f pip_error.log

# Create the shell script launcher
echo "Creating launcher script..."
mkdir -p bin
cat > bin/ai-shell << EOF
#!/bin/bash
SCRIPT_DIR="\$(cd "\$(dirname "\${BASH_SOURCE[0]}")" && pwd)"
$PYTHON_CMD "\$SCRIPT_DIR/../aishell/ai_shell.py" "\$@"
EOF
chmod +x bin/ai-shell

# Add to PATH if requested
echo
echo "AI Shell has been installed successfully!"
echo
echo "To run AI Shell, you can:"
echo "1. Type './bin/ai-shell' from this directory"
echo "2. Add this directory's bin folder to your PATH to run 'ai-shell' from anywhere"
echo
read -p "Would you like to add AI Shell to your PATH? (y/n) " choice
if [ "$choice" = "y" ] || [ "$choice" = "Y" ]; then
    echo "export PATH=\"\$PATH:$(pwd)/bin\"" >> ~/.bashrc
    echo "AI Shell has been added to your PATH. You may need to restart your terminal or run 'source ~/.bashrc'."
fi

echo
echo "Installation complete! Type 'ai-shell' to start (may require reopening your terminal)."
