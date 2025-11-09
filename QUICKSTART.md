# Quick Start Guide

Get scraping in 5 minutes!

## Prerequisites

- Docker & Docker Compose installed
- Python 3.8+ installed
- Your Excel files ready

## Setup (First Time)

```bash
# 1. Run setup script
./setup.sh

# 2. Add your Excel files to data/ directory
# - art_schools_final.xlsx
# - School_Admission_Data_FINAL.xlsx

# 3. Check which Ollama models you have
docker exec art-scraper-ollama ollama list

# 4. Update config.yaml to use one of your models
# Edit the "model:" line to match one from the list above
```

## Daily Use

```bash
# 1. Activate virtual environment
source venv/bin/activate

# 2. Test connections
python scraper.py --test-connection

# 3. Scrape a school
python scraper.py --school "School Name"

# 4. Check results
cat results/*.json | tail -1
```

## Common Commands

```bash
# List available schools
python scraper.py --list

# Show fields to extract
python scraper.py --show-fields

# Use different model
python scraper.py --school "Name" --model llama3.2:3b

# Less verbose
python scraper.py --school "Name" --quiet

# View logs
tail -f logs/scraper.log
```

## File Locations

- **Config**: `config.yaml`
- **Input**: `data/*.xlsx`
- **Output**: `results/*.json`
- **Logs**: `logs/scraper.log`

## Troubleshooting

**Services down?**
```bash
docker-compose up -d
```

**Model not found?**
```bash
# List available models
docker exec art-scraper-ollama ollama list

# Update config.yaml to use one of your models
nano config.yaml  # or your preferred editor
```

**Connection fails?**
```bash
docker-compose restart
sleep 30
python scraper.py --test-connection
```

## Model Options

| Model | Speed | Accuracy | RAM |
|-------|-------|----------|-----|
| llama3.2:3b | ⚡⚡⚡ | ⭐⭐ | 4GB |
| qwen2.5:32b | ⚡⚡ | ⭐⭐⭐⭐ | 20GB |
| llama3.3:70b | ⚡ | ⭐⭐⭐⭐⭐ | 40GB |

## Need Help?

1. Check `README.md` for full documentation
2. Check `TESTING.md` for detailed testing
3. Check `logs/scraper.log` for errors
4. Run with `--verbose` for detailed output

## Example Workflow

```bash
# Morning routine
cd art-school-scraper
source venv/bin/activate
docker-compose up -d
sleep 30

# Scrape schools
python scraper.py --school "Stamps School of Art & Design"
python scraper.py --school "College for Creative Studies"
python scraper.py --school "Kendall College of Art"

# Review results
ls -lt results/

# Shutdown when done
docker-compose down
```

That's it! 🚀
