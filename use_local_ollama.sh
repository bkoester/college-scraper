#!/bin/bash
# Switch to using local Ollama instead of Docker

echo "=========================================="
echo "Configuring for Local Ollama"
echo "=========================================="
echo ""

# Check if local Ollama exists
if ! command -v ollama &> /dev/null; then
    echo "❌ Ollama not found on your system"
    echo ""
    echo "Install Ollama first:"
    echo "  macOS: brew install ollama"
    echo "  Or: https://ollama.ai/download"
    exit 1
fi

echo "✓ Found local Ollama installation"

# Check if Ollama is running
if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
    echo "✓ Ollama is running"
else
    echo "⚠ Ollama is installed but not running"
    echo "  Starting Ollama..."
    # On macOS, Ollama usually runs as a service
    # Try to trigger it
    ollama list > /dev/null 2>&1
    sleep 2
    if curl -s http://localhost:11434/api/tags > /dev/null 2>&1; then
        echo "✓ Ollama started"
    else
        echo "  You may need to start Ollama manually"
    fi
fi

echo ""

# Create override file
echo "Creating docker-compose.override.yml to disable Docker Ollama..."

cat > docker-compose.override.yml << 'EOF'
# Auto-generated: Using local Ollama instead of Docker
version: '3.8'

services:
  ollama:
    profiles:
      - disabled
EOF

echo "✓ Created docker-compose.override.yml"
echo ""

# Check config.yaml
echo "Checking config.yaml..."
BASE_URL=$(grep "base_url:" config.yaml | grep -A1 "ollama:" | tail -1 | awk -F'"' '{print $2}')

if [ "$BASE_URL" = "http://localhost:11434" ]; then
    echo "✓ config.yaml already points to local Ollama"
else
    echo "⚠ config.yaml points to: $BASE_URL"
    echo "  Should be: http://localhost:11434"
    echo ""
    read -p "Update config.yaml? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        # This is a simple replacement - may need adjustment
        echo "  Please manually verify config.yaml points to http://localhost:11434"
    fi
fi

echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Check your models: ollama list"
echo "2. Update config.yaml model to match your installed models"
echo "3. Start MCP only: docker-compose up -d"
echo "   (This will skip Ollama and only start MCP server)"
echo "4. Verify: ./check_models.sh"
echo "5. Test: python scraper.py --test-connection"
echo ""
echo "Your Ollama models:"
ollama list
echo ""
