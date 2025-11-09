#!/bin/bash
# Helper script to check available Ollama models and config

echo "=========================================="
echo "Ollama Model Configuration Check"
echo "=========================================="
echo ""

# Detect Ollama installation type
OLLAMA_TYPE=""
OLLAMA_CMD=""

# Check for local Ollama first (macOS/Linux)
if command -v ollama &> /dev/null; then
    echo "✓ Found local Ollama installation"
    OLLAMA_TYPE="local"
    OLLAMA_CMD="ollama"

    # Check if Ollama is running
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✓ Ollama service is running"
    else
        echo "⚠ Ollama is installed but not running"
        echo "  Start it with: ollama serve"
        echo "  Or it may start automatically"
    fi
    echo ""

# Check for Docker Ollama
elif docker ps 2>/dev/null | grep -q "art-scraper-ollama"; then
    echo "✓ Found Ollama in Docker container"
    OLLAMA_TYPE="docker"
    OLLAMA_CMD="docker exec art-scraper-ollama ollama"
    echo ""

else
    echo "❌ Ollama not found!"
    echo ""
    echo "Options:"
    echo "1. Local Ollama (you have this installed):"
    echo "   - Make sure Ollama is running"
    echo "   - Check: curl http://localhost:11434/api/tags"
    echo ""
    echo "2. Docker Ollama:"
    echo "   - Run: docker-compose up -d"
    echo ""
    exit 1
fi

# List available models
echo "Your available Ollama models:"
echo "-------------------------------------------"
$OLLAMA_CMD list
echo "-------------------------------------------"
echo ""

# Check current config
CURRENT_MODEL=$(grep "model:" config.yaml | head -1 | awk -F'"' '{print $2}')
CONFIG_URL=$(grep "base_url:" config.yaml | grep -A1 "ollama:" | tail -1 | awk -F'"' '{print $2}')

echo "Current config.yaml settings:"
echo "  model: \"$CURRENT_MODEL\""
echo "  base_url: \"$CONFIG_URL\""
echo ""

# Check if base_url matches Ollama type
if [ "$OLLAMA_TYPE" = "local" ] && [ "$CONFIG_URL" != "http://localhost:11434" ]; then
    echo "⚠ Config points to $CONFIG_URL but you're using local Ollama"
    echo "  Update config.yaml base_url to: http://localhost:11434"
    echo ""
fi

# Verify if current model is available
if $OLLAMA_CMD list | grep -q "$CURRENT_MODEL"; then
    echo "✓ Model '$CURRENT_MODEL' is available and ready to use"
    echo ""
    echo "You're all set! Run:"
    echo "  python scraper.py --test-connection"
else
    echo "⚠ Model '$CURRENT_MODEL' not found in available models"
    echo ""
    echo "To fix this:"
    echo "1. Choose a model from the list above"
    echo "2. Edit config.yaml and update the model line:"
    echo "   nano config.yaml  # or your preferred editor"
    echo "3. Change: model: \"$CURRENT_MODEL\""
    echo "   To:     model: \"<your-chosen-model>\""
    echo ""
    echo "Example models you might have:"
    echo "  - llama3.2:3b (fast, small)"
    echo "  - qwen2.5:32b (balanced)"
    echo "  - llama3.3:70b (best quality)"
fi

echo ""
echo "=========================================="
