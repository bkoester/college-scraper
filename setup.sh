#!/bin/bash
# Quick setup script for Art School Scraper

set -e

echo "=========================================="
echo "Art School Scraper - Setup"
echo "=========================================="
echo ""

# Check Docker
echo "Checking Docker..."
if ! command -v docker &> /dev/null; then
    echo "❌ Docker not found. Please install Docker first."
    exit 1
fi
echo "✓ Docker found"

# Check Docker Compose
echo "Checking Docker Compose..."
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose not found. Please install Docker Compose first."
    exit 1
fi
echo "✓ Docker Compose found"

# Check Python
echo "Checking Python..."
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found. Please install Python 3.8+ first."
    exit 1
fi
PYTHON_VERSION=$(python3 --version | cut -d' ' -f2)
echo "✓ Python $PYTHON_VERSION found"

# Create virtual environment
echo ""
echo "Creating Python virtual environment..."
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo "✓ Virtual environment created"
else
    echo "✓ Virtual environment already exists"
fi

# Activate and install dependencies
echo ""
echo "Installing Python dependencies..."
source venv/bin/activate
pip install --upgrade pip -q
pip install -r requirements.txt -q
echo "✓ Dependencies installed"

# Start Docker services
echo ""
echo "Starting Docker services..."
docker-compose up -d
echo "✓ Docker services started"

# Wait for services
echo ""
echo "Waiting for services to start (30 seconds)..."
sleep 30

# Check Ollama
echo ""
echo "Testing Ollama connection..."
if curl -s http://localhost:11434/api/tags > /dev/null; then
    echo "✓ Ollama is running"
else
    echo "⚠ Ollama might not be ready yet. Give it another minute."
fi

# Check MCP
echo ""
echo "Testing MCP Server connection..."
if curl -s http://localhost:8931/health > /dev/null; then
    echo "✓ MCP Server is running"
else
    echo "⚠ MCP Server might not be ready yet. Give it another minute."
fi

# Check for model
echo ""
echo "Checking available Ollama models..."
echo "Available models:"
docker exec art-scraper-ollama ollama list 2>/dev/null || echo "  (Ollama not ready yet)"
echo ""
MODEL=$(grep "model:" config.yaml | head -1 | cut -d'"' -f2)
echo "Config is set to use: $MODEL"
if docker exec art-scraper-ollama ollama list 2>/dev/null | grep -q "$MODEL"; then
    echo "✓ Model $MODEL is available"
else
    echo "⚠ Model $MODEL not found in available models"
    echo ""
    echo "Update config.yaml to use one of your available models above"
fi

# Check for Excel files
echo ""
echo "Checking for Excel files..."
if [ -f "data/art_schools_final.xlsx" ] && [ -f "data/School_Admission_Data_FINAL.xlsx" ]; then
    echo "✓ Excel files found"
else
    echo "⚠ Excel files not found in data/ directory"
    echo "  Please add:"
    echo "  - data/art_schools_final.xlsx"
    echo "  - data/School_Admission_Data_FINAL.xlsx"
fi

# Summary
echo ""
echo "=========================================="
echo "Setup Complete!"
echo "=========================================="
echo ""
echo "Next steps:"
echo "1. Activate virtual environment: source venv/bin/activate"
echo "2. Test connections: python scraper.py --test-connection"
echo "3. List schools: python scraper.py --list"
echo "4. Scrape a school: python scraper.py --school 'School Name'"
echo ""
echo "See README.md for full documentation."
echo ""
