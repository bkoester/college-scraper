# Using Local Ollama (Instead of Docker)

If you already have Ollama installed on your Mac/Linux system, you can use it directly instead of running Ollama in Docker.

## Quick Setup

### 1. Verify Local Ollama

```bash
# Check if Ollama is installed
which ollama

# Check your models
ollama list

# Test connection
curl http://localhost:11434/api/tags
```

### 2. Update Configuration

The `config.yaml` should already point to `http://localhost:11434`, but verify:

```bash
# Check current config
grep -A2 "^ollama:" config.yaml

# Should show:
# ollama:
#   model: "llama3:8b"  # or your model
#   base_url: "http://localhost:11434"
```

If it points to something else, edit it:

```yaml
ollama:
  model: "llama3:8b"  # Use one of your models
  base_url: "http://localhost:11434"  # Local Ollama
  temperature: 0.1
  max_tokens: 4000
  timeout: 120
```

### 3. Run Only MCP in Docker

Since you're using local Ollama, you only need the MCP server in Docker:

```bash
# Start only MCP server
docker-compose up -d mcp-server

# Check it's running
docker-compose ps
```

### 4. Verify Setup

```bash
# Run the check script
./check_models.sh

# Should show:
# ✓ Found local Ollama installation
# ✓ Ollama service is running
# Your available models listed
# ✓ Model 'llama3:8b' is available
```

### 5. Test Everything

```bash
# Test connections
python scraper.py --test-connection

# Should show:
# ✓ Ollama connected
# Available models: llama3:8b (or whatever you have)
# ✓ MCP Server connected
```

---

## Updated docker-compose.yml

You can comment out the Ollama service since you're using local:

```yaml
version: '3.8'

services:
  # Commented out - using local Ollama instead
  # ollama:
  #   image: ollama/ollama:latest
  #   container_name: art-scraper-ollama
  #   ports:
  #     - "11434:11434"
  #   ...

  mcp-server:
    image: mcr.microsoft.com/playwright/mcp:latest
    container_name: art-scraper-mcp
    ports:
      - "8931:8931"
    command: ["node", "/app/dist/index.js", "--port", "8931"]
    environment:
      - NODE_ENV=production
      - PLAYWRIGHT_BROWSERS_PATH=/ms-playwright
    restart: unless-stopped
```

Or use profiles to make it optional:

```yaml
version: '3.8'

services:
  ollama:
    image: ollama/ollama:latest
    container_name: art-scraper-ollama
    profiles: ["ollama-docker"]  # Only start if explicitly requested
    ports:
      - "11434:11434"
    # ... rest of config

  mcp-server:
    # No profile - always starts
    image: mcr.microsoft.com/playwright/mcp:latest
    # ... rest of config
```

Then start only MCP:
```bash
docker-compose up -d  # Starts only mcp-server
```

---

## Common Issues

### Issue: "Ollama not found"

**Check:**
```bash
# Is Ollama installed?
which ollama

# Is Ollama running?
curl http://localhost:11434/api/tags

# If not, start it (usually auto-starts)
ollama serve
```

### Issue: "Model not found"

**Solution:**
```bash
# List your models
ollama list

# Update config.yaml to use one from the list
nano config.yaml

# Example: Change to llama3:8b if that's what you have
```

### Issue: "Connection refused on port 11434"

**Possible causes:**

1. **Ollama not running:**
   ```bash
   # Check if running
   pgrep -f ollama

   # Start manually
   ollama serve
   ```

2. **Port conflict:**
   ```bash
   # Check what's on port 11434
   lsof -i :11434

   # Kill conflicting process or use different port
   ```

3. **Docker Ollama interfering:**
   ```bash
   # Stop Docker Ollama
   docker-compose down ollama
   ```

### Issue: "Both local and Docker Ollama running"

**Solution:**
```bash
# Stop Docker Ollama
docker-compose stop ollama

# Use local Ollama
./check_models.sh

# Should show: ✓ Found local Ollama installation
```

---

## Advantages of Local Ollama

✅ **Faster** - No Docker overhead
✅ **Simpler** - One less container
✅ **Easier model management** - Use `ollama pull` directly
✅ **Better GPU access** - Direct hardware access
✅ **Shared models** - Use same models for other projects

---

## Model Management

### List Models

```bash
ollama list
```

### Pull New Models

```bash
# Pull a model
ollama pull llama3.2:3b

# Pull specific version
ollama pull qwen2.5:32b
```

### Remove Models

```bash
ollama rm llama3.2:3b
```

### Update config.yaml

After pulling a model, update config:

```yaml
ollama:
  model: "llama3.2:3b"  # Match your downloaded model
```

---

## Testing

### Test Local Ollama

```bash
# Test with curl
curl http://localhost:11434/api/tags

# Test with ollama CLI
ollama list

# Test generation
ollama run llama3:8b "Hello!"
```

### Test with Scraper

```bash
# Full connection test
python scraper.py --test-connection

# Try listing schools (doesn't use Ollama)
python scraper.py --list

# Try quick IPEDS collection (doesn't use Ollama)
python multi_source_scraper.py --test
```

---

## Performance Notes

### Local vs Docker Ollama

**Local Ollama:**
- ✅ Slightly faster (no Docker layer)
- ✅ Easier to manage
- ✅ Better GPU utilization
- ✅ Can use `ollama` CLI directly

**Docker Ollama:**
- ✅ Isolated environment
- ✅ Consistent across systems
- ✅ Easier for deployment

**For your use case (local development), local Ollama is better!**

---

## Complete Setup Example

```bash
# 1. Verify local Ollama
ollama list
# Output: llama3:8b, qwen2.5:32b, etc.

# 2. Check config
./check_models.sh
# Should show: ✓ Found local Ollama installation

# 3. Update config.yaml if needed
nano config.yaml
# Set model to one from your list

# 4. Start only MCP (not Ollama)
docker-compose up -d mcp-server

# 5. Install Python deps
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 6. Add your Excel files
# Copy to data/

# 7. Test everything
python scraper.py --test-connection

# 8. Run a collection
python multi_source_scraper.py --school "Stamps School of Art & Design"
```

---

## Summary

Since you have local Ollama installed:

1. ✅ **Keep using local Ollama** (faster, simpler)
2. ✅ **Verify config.yaml** points to `http://localhost:11434`
3. ✅ **Start only MCP in Docker**: `docker-compose up -d mcp-server`
4. ✅ **Use check script**: `./check_models.sh`
5. ✅ **You're ready!** No need for Docker Ollama

The scraper will work exactly the same whether using local or Docker Ollama - it just connects to `localhost:11434` either way!
