# Ollama Models Setup

Since you already have Ollama models downloaded, here's how to use them with the scraper.

## Quick Check

Run the helper script to see your models and verify your config:

```bash
./check_models.sh
```

This will show:
- ✓ Which models you have available
- ✓ Which model is configured in config.yaml
- ✓ Whether they match (ready to use)

## Manual Check

### 1. List Your Models

```bash
# See all available models
docker exec art-scraper-ollama ollama list
```

Example output:
```
NAME              ID          SIZE    MODIFIED
llama3.2:3b       a80c4f17a9  2.0GB   2 weeks ago
qwen2.5:32b       61e88e884a  20GB    1 week ago
llama3.3:70b      2b0e3a8e9b  39GB    3 days ago
```

### 2. Check Your Config

```bash
# See which model is configured
grep "model:" config.yaml
```

Example output:
```
  model: "qwen2.5:32b"  # The Ollama model to use
```

### 3. Update if Needed

If the model in config.yaml is not in your list:

```bash
# Edit config.yaml
nano config.yaml  # or your preferred editor

# Change this line:
  model: "qwen2.5:32b"

# To match one of your available models:
  model: "llama3.3:70b"
```

## Model Recommendations

### For Your Art School Scraper

| Model | When to Use | Speed | Quality | RAM Needed |
|-------|-------------|-------|---------|------------|
| llama3.2:3b | Quick testing, limited RAM | ⚡⚡⚡ | ⭐⭐ | ~4GB |
| qwen2.5:32b | Production, balanced | ⚡⚡ | ⭐⭐⭐⭐ | ~20GB |
| llama3.3:70b | Best accuracy needed | ⚡ | ⭐⭐⭐⭐⭐ | ~40GB |

### Recommendations by Task

**Quick testing (26 schools):**
- Use: `llama3.2:3b`
- Time: ~30 min total
- Good enough for testing the pipeline

**Production run (26 schools):**
- Use: `qwen2.5:32b` or `llama3.3:70b`
- Time: ~1-2 hours total
- Better data extraction accuracy

**Multi-source collection:**
- Model doesn't matter as much
- IPEDS + Wikipedia don't use the AI
- Only web scraping component uses Ollama

## Using Different Models

### Switch Models Anytime

You can override the config model with command-line:

```bash
# Use specific model for this run
python scraper.py --school "Name" --model llama3.2:3b

# Use different model for another run
python scraper.py --school "Name" --model llama3.3:70b
```

### Test Different Models

Compare results from different models:

```bash
# Try with small model
python scraper.py --school "Test School" --model llama3.2:3b > results/test_small.json

# Try with large model
python scraper.py --school "Test School" --model llama3.3:70b > results/test_large.json

# Compare
diff results/test_small.json results/test_large.json
```

## Troubleshooting

### "Model not found" Error

**Symptom:**
```
Error: Model 'qwen2.5:32b' not found
```

**Solution:**
```bash
# 1. Check what you have
docker exec art-scraper-ollama ollama list

# 2. Update config.yaml to match
nano config.yaml

# 3. Or use command-line override
python scraper.py --school "Name" --model llama3.2:3b
```

### Model Name Mismatch

**Problem:** Config says "qwen2.5:32b" but list shows "qwen2.5:32b-instruct"

**Solution:** Use the EXACT name from the list:
```yaml
model: "qwen2.5:32b-instruct"  # Must match exactly
```

### Container Access Issues

**Problem:** Can't access Ollama container

**Solutions:**
```bash
# 1. Check Docker is running
docker ps

# 2. Check Ollama container
docker ps | grep ollama

# 3. Restart if needed
docker-compose restart ollama

# 4. Wait 30 seconds then check models
sleep 30
docker exec art-scraper-ollama ollama list
```

## Model Performance Tips

### Memory Management

**If you're running out of RAM:**

1. Use smaller model:
   ```yaml
   model: "llama3.2:3b"  # Only needs 4GB
   ```

2. Close other applications

3. Monitor memory:
   ```bash
   # While scraping runs
   docker stats art-scraper-ollama
   ```

### Speed Optimization

**To speed up scraping:**

1. Use smaller model (faster inference)
2. Reduce `max_tokens` in config.yaml:
   ```yaml
   ollama:
     max_tokens: 2000  # Instead of 4000
   ```
3. Use multi-source instead of web scraping:
   ```bash
   # Much faster - doesn't use Ollama
   python multi_source_scraper.py --all
   ```

## Multi-Source vs Web Scraping

### When Model Choice Matters

**Web scraping (uses Ollama):**
```bash
python scraper.py --school "Name"
# Model quality affects results
# Use larger model for better extraction
```

**Multi-source (doesn't use Ollama for IPEDS/Wikipedia):**
```bash
python multi_source_scraper.py --school "Name"
# Model doesn't matter for IPEDS/Wikipedia
# Only matters if you enable web scraping component
```

### Recommended Workflow

For your 26 schools:

```bash
# Step 1: Fast baseline (no Ollama needed)
python multi_source_scraper.py --all
# Gets IPEDS + Wikipedia data
# ~15 minutes, model doesn't matter

# Step 2: Selective web scraping (uses Ollama)
# Only for schools with missing data
# Use best model you have
python scraper.py --school "School X" --model llama3.3:70b
```

## Summary

✅ **You have models downloaded - you're ready!**

Just make sure:
1. Model in config.yaml matches your available models
2. You have enough RAM for the model
3. Docker and Ollama container are running

Run `./check_models.sh` to verify everything is set up correctly!

---

**Need help?** Check README.md or run:
```bash
python scraper.py --test-connection
```
