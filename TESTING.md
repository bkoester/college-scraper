# Testing Guide

This guide will help you verify that the Art School Scraper is working correctly.

## Quick Test Checklist

- [ ] Docker services are running
- [ ] Ollama is accessible and model is pulled
- [ ] MCP Server is accessible
- [ ] Python dependencies are installed
- [ ] Excel files are in place
- [ ] Scraper can read Excel files
- [ ] Scraper can list schools
- [ ] Connection test passes
- [ ] Can scrape a test school

## Step-by-Step Testing

### 1. Verify Docker Services

```bash
docker-compose ps
```

Expected output:
```
NAME                   STATUS
art-scraper-ollama     Up
art-scraper-mcp        Up (healthy)
```

If services are down:
```bash
docker-compose up -d
```

### 2. Check Ollama

```bash
# Check Ollama is accessible
curl http://localhost:11434/api/tags

# List your available models
docker exec art-scraper-ollama ollama list

# Verify the model in config.yaml is in the list
grep "model:" config.yaml
```

Expected: JSON response from first command, your models listed in second.

### 3. Check MCP Server

```bash
# Check MCP health endpoint
curl http://localhost:8931/health
```

Expected: 200 OK response

### 4. Test Python Environment

```bash
# Activate virtual environment
source venv/bin/activate

# Check Python packages
pip list | grep -E "(pandas|pyyaml|requests|rich)"
```

Expected: All packages shown with versions

### 5. Test Scraper CLI

```bash
# Show help
python scraper.py --help

# Test connection
python scraper.py --test-connection
```

Expected output:
```
Testing Ollama connection...
  ✓ Ollama connected
  Available models: qwen2.5:32b

Testing MCP Server connection...
  ✓ MCP Server connected
```

### 6. Test Excel Reading

```bash
# List schools (requires Excel files in data/)
python scraper.py --list
```

Expected: Table showing all schools from Excel files

If you get an error, make sure:
- Files are in `data/` directory
- Files are named exactly: `art_schools_final.xlsx` and `School_Admission_Data_FINAL.xlsx`
- Files are valid Excel format

### 7. Show Extractable Fields

```bash
python scraper.py --show-fields
```

Expected: Table showing all data fields that will be extracted

### 8. Test Scraping

```bash
# Try scraping one school
python scraper.py --school "Stamps School of Art & Design"
```

Expected:
- Connection test passes
- Agent begins navigation
- Tool calls are made
- Results saved to `results/` directory

Check the output file:
```bash
# Find the latest result
ls -lt results/*.json | head -1

# View the result
cat results/stamps_school_*.json | python -m json.tool
```

## Troubleshooting Tests

### Test: Docker Services Won't Start

**Problem:** `docker-compose up -d` fails

**Solutions:**
1. Check Docker is running: `docker ps`
2. Check for port conflicts: `netstat -an | grep -E "(11434|8931)"`
3. View logs: `docker-compose logs`
4. Try recreating: `docker-compose down && docker-compose up -d`

### Test: Ollama Connection Fails

**Problem:** `curl http://localhost:11434/api/tags` fails

**Solutions:**
1. Wait longer - Ollama takes 30-60 seconds to start
2. Check Ollama logs: `docker-compose logs ollama`
3. Restart Ollama: `docker-compose restart ollama`
4. Check container is running: `docker ps | grep ollama`

### Test: Model Not Found

**Problem:** Scraper says "Model not found"

**Solutions:**
1. List your available models: `docker exec art-scraper-ollama ollama list`
2. Update `config.yaml` to use one of your available models
3. Verify: `grep "model:" config.yaml`
4. Ensure the model name matches exactly what's shown in the list

### Test: MCP Server Connection Fails

**Problem:** `curl http://localhost:8931/health` fails

**Solutions:**
1. Check MCP logs: `docker-compose logs mcp-server`
2. Verify container is healthy: `docker ps`
3. Restart MCP: `docker-compose restart mcp-server`
4. Check if port 8931 is available

### Test: Excel Files Not Found

**Problem:** `python scraper.py --list` fails with FileNotFoundError

**Solutions:**
1. Check files exist: `ls -la data/`
2. Check filenames match exactly:
   - `data/art_schools_final.xlsx`
   - `data/School_Admission_Data_FINAL.xlsx`
3. Check files are readable: `file data/*.xlsx`

### Test: Scraping Times Out

**Problem:** Scraper runs for 5 minutes then stops

**Solutions:**
1. Increase timeout in `config.yaml`:
   ```yaml
   scraping:
     timeout_per_school: 600  # 10 minutes
   ```
2. Use smaller model for faster responses
3. Check website is accessible manually
4. Review logs: `cat logs/scraper.log`

### Test: No Data Extracted

**Problem:** Scraper completes but finds no data

**Solutions:**
1. Run with verbose: `python scraper.py --school "Name" --verbose`
2. Check the website manually - is data publicly accessible?
3. Try different model: `python scraper.py --school "Name" --model llama3.3:70b`
4. Check `logs/scraper.log` for details
5. Verify field keywords in `config.yaml` match website terminology

## Performance Tests

### Test Model Speed

```bash
# Small model (fastest)
time python scraper.py --school "Test School" --model llama3.2:3b

# Medium model (balanced)
time python scraper.py --school "Test School" --model qwen2.5:32b

# Large model (most accurate)
time python scraper.py --school "Test School" --model llama3.3:70b
```

Compare execution times and accuracy.

### Test Memory Usage

```bash
# Monitor Docker stats while scraping
docker stats

# Run scraper in another terminal
python scraper.py --school "Test School"
```

Check if you have enough RAM for your chosen model.

## Validation Tests

### Verify Output Format

```bash
# Check JSON is valid
cat results/*.json | python -m json.tool > /dev/null && echo "Valid JSON"

# Check required fields exist
cat results/*.json | python -c "
import json, sys
data = json.load(sys.stdin)
required = ['school_name', 'url', 'scraped_at', 'data', 'agent_summary']
missing = [f for f in required if f not in data]
if missing:
    print(f'Missing fields: {missing}')
    sys.exit(1)
else:
    print('All required fields present')
"
```

### Verify Confidence Scores

```bash
# Check all confidence scores are between 0 and 1
cat results/*.json | python -c "
import json, sys
data = json.load(sys.stdin)
for field, info in data.get('data', {}).items():
    conf = info.get('confidence', 0)
    if not 0 <= conf <= 1:
        print(f'Invalid confidence for {field}: {conf}')
        sys.exit(1)
print('All confidence scores valid')
"
```

## Success Criteria

Your scraper is working correctly if:

✅ All Docker services are running and healthy
✅ Connection test passes
✅ Can list schools from Excel files
✅ Can scrape at least one school successfully
✅ Output JSON is valid and complete
✅ Confidence scores are reasonable (>0.7 for most fields)
✅ Source URLs are included
✅ Scraping completes within timeout
✅ Logs show clear agent activity

## Getting Help

If tests continue to fail:

1. Review README.md Troubleshooting section
2. Check logs in `logs/scraper.log`
3. Verify system requirements (RAM, disk space)
4. Try with a simpler configuration
5. Test with a school that has simple website structure

## Next Steps

Once all tests pass:

1. ✅ Scrape all schools in your Excel file
2. ✅ Review and validate results
3. ✅ Adjust field keywords in config if needed
4. ✅ Experiment with different models
5. ✅ Fine-tune timeout and retry settings
