# Art School Web Scraper

An intelligent web scraping application that uses local AI (Ollama) and browser automation (Microsoft MCP Playwright) to extract data from university websites.

## Features

- **Local AI**: Uses Ollama for intelligent decision-making (no API costs!)
- **Browser Automation**: Microsoft's official Playwright MCP server
- **Configuration-Driven**: All settings in `config.yaml`
- **Manual Operation**: You specify which school to scrape
- **Adaptive Navigation**: AI agent intelligently explores websites
- **Structured Output**: Clean JSON results with confidence scores
- **Excel Integration**: Reads input from Excel, optionally updates with new data

## Architecture

```
┌─────────────────────────────────────────────┐
│  YOU (User)                                 │
│  python scraper.py --school "School Name"   │
└────────────────┬────────────────────────────┘
                 │
┌────────────────▼────────────────────────────┐
│  Scraper Application (Python)               │
│  - Reads Excel files                        │
│  - Coordinates Ollama + MCP                 │
│  - Saves results                            │
└─────┬──────────────────────────┬────────────┘
      │                          │
┌─────▼──────────┐        ┌──────▼─────────────┐
│  Ollama        │◄──────►│  MCP Server        │
│  (Local AI)    │  Uses  │  (Browser Control) │
│  Port 11434    │  Tools │  Port 8931         │
└────────────────┘        └────────────────────┘
```

## Quick Start

### 1. Prerequisites

- Docker and Docker Compose
- Python 3.8+
- Your Excel files in the `data/` directory

### 2. Start Services

```bash
# Start Ollama and MCP Server
docker-compose up -d

# Wait for services to start (about 30 seconds)
docker-compose ps

# Check which Ollama models you have available
docker exec art-scraper-ollama ollama list

# Or use the helper script
./check_models.sh
```

**Note:** Make sure the model in `config.yaml` matches one from your list above.

### 3. Install Python Dependencies

```bash
# Create virtual environment (recommended)
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

### 4. Add Your Excel Files

Place your Excel files in the `data/` directory:
- `data/art_schools_final.xlsx`
- `data/School_Admission_Data_FINAL.xlsx`

### 5. Test Connections

```bash
python scraper.py --test-connection
```

You should see:
```
Testing Ollama connection...
  ✓ Ollama connected
  Available models: qwen2.5:32b

Testing MCP Server connection...
  ✓ MCP Server connected
```

### 6. Scrape a School

```bash
# See available schools
python scraper.py --list

# Scrape one school
python scraper.py --school "Stamps School of Art & Design"

# Results saved to: results/stamps_school_2024-11-09.json
```

## Usage

### List Available Schools

```bash
python scraper.py --list
```

Shows all schools from your Excel files with their URLs.

### Show Fields to Extract

```bash
python scraper.py --show-fields
```

Shows what data fields will be extracted and the keywords used.

### Scrape a School

```bash
# Basic usage
python scraper.py --school "School Name"

# Use different model
python scraper.py --school "CCS" --model llama3.3:70b

# Less verbose output
python scraper.py --school "Eastern Michigan" --quiet

# Use different config file
python scraper.py --school "RISD" --config custom-config.yaml
```

### Test Connections

```bash
python scraper.py --test-connection
```

## Configuration

All settings are in `config.yaml`:

### Change Ollama Model

Edit `config.yaml` to use one of your downloaded models:

```yaml
ollama:
  model: "llama3.2:3b"  # Faster, less accurate
  # model: "qwen2.5:32b"  # Good balance
  # model: "llama3.3:70b"  # Best quality, slower
  # model: "your-model-name"  # Use any model you've downloaded
```

To see which models you have available:
```bash
docker exec art-scraper-ollama ollama list
```

### Adjust Scraping Behavior

```yaml
scraping:
  max_retries: 3
  timeout_per_school: 300  # 5 minutes
  page_load_delay: 2  # Seconds between pages
  verbose: true  # Show detailed progress
```

### Add/Remove Fields to Extract

Edit the `fields_to_extract` section in `config.yaml`:

```yaml
fields_to_extract:
  - name: "in_state_tuition"
    column: "In-State"
    keywords:
      - "in-state tuition"
      - "resident tuition"
    data_type: "currency"
    validation:
      min: 0
      max: 100000
```

## Output Format

Results are saved as JSON files in the `results/` directory.

Example: `results/stamps_school_2024-11-09.json`

```json
{
  "school_name": "Stamps School of Art & Design",
  "url": "https://stamps.umich.edu/",
  "scraped_at": "2024-11-09T14:30:00Z",
  "scrape_duration_seconds": 127,
  "model_used": "qwen2.5:32b",
  "data": {
    "in_state_tuition": {
      "value": 17786,
      "formatted": "$17,786",
      "confidence": 0.95,
      "source_url": "https://stamps.umich.edu/admissions/tuition",
      "notes": "2024-2025 academic year"
    },
    "out_state_tuition": {
      "value": 57273,
      "formatted": "$57,273",
      "confidence": 0.95,
      "source_url": "https://stamps.umich.edu/admissions/tuition"
    },
    "admission_rate": {
      "value": 0.179,
      "formatted": "17.9%",
      "confidence": 0.90,
      "source_url": "https://stamps.umich.edu/admissions/statistics"
    }
  },
  "agent_summary": "Successfully found tuition and admission data...",
  "navigation_path": [
    "https://stamps.umich.edu/",
    "https://stamps.umich.edu/admissions"
  ],
  "tool_calls_made": 12,
  "errors": []
}
```

### Confidence Scores

The AI assigns confidence scores to each extracted value:

- **0.95+**: Found on official page with clear labels
- **0.85-0.94**: Found with good context but some ambiguity
- **0.70-0.84**: Inferred from related information
- **0.50-0.69**: Uncertain, needs manual verification
- **<0.50**: Not included in results

## Troubleshooting

### Docker Issues

**Services won't start:**
```bash
# Check Docker is running
docker ps

# Check service logs
docker-compose logs ollama
docker-compose logs mcp-server

# Restart services
docker-compose restart
```

**MCP Server health check failing:**
```bash
# Check MCP server logs
docker-compose logs mcp-server

# Try rebuilding
docker-compose down
docker-compose up -d --build
```

### Ollama Issues

**Model not found:**
```bash
# List your available models
docker exec art-scraper-ollama ollama list

# Check if the model in config.yaml is available
grep "model:" config.yaml
```

**Ollama timeout:**
- Increase `timeout` in `config.yaml` under `ollama` section
- Use a smaller/faster model
- Check if your system has enough RAM (32B models need ~20GB)

**GPU not detected:**
- Comment out the GPU section in `docker-compose.yml` if you don't have a GPU
- Ollama will run on CPU (slower but works)

### Scraping Issues

**School not found:**
```bash
# List available schools
python scraper.py --list

# Use exact name or partial match
python scraper.py --school "Stamps"
```

**No data extracted:**
- Check the school's website is accessible
- Try increasing `timeout_per_school` in config
- Use `--verbose` to see what the agent is doing
- Check `logs/scraper.log` for detailed errors

**Agent gets stuck:**
- The scraper has a timeout (default 5 minutes)
- Reduce `max_tokens` in config if agent is too verbose
- Try a different model

### Connection Test Failures

**"Cannot connect to Ollama":**
```bash
# Make sure services are running
docker-compose up -d

# Wait a bit for startup
sleep 10

# Test again
python scraper.py --test-connection
```

**"Cannot connect to MCP Server":**
```bash
# Check if port 8931 is available
netstat -an | grep 8931

# Check MCP logs
docker-compose logs mcp-server

# Try different port in config.yaml and docker-compose.yml
```

## Available Ollama Models

| Model | Size | Speed | Accuracy | RAM Required |
|-------|------|-------|----------|--------------|
| llama3.2:3b | 3B | ⚡⚡⚡ | ⭐⭐ | ~4GB |
| qwen2.5:32b | 32B | ⚡⚡ | ⭐⭐⭐⭐ | ~20GB |
| llama3.3:70b | 70B | ⚡ | ⭐⭐⭐⭐⭐ | ~40GB |

To change models:
1. Check available models: `docker exec art-scraper-ollama ollama list`
2. Update `config.yaml` with your chosen model
3. Run scraper

## How It Works

1. **Load Configuration**: Read settings from `config.yaml`
2. **Load Excel Files**: Parse both spreadsheets to get school list
3. **Find School**: Lookup school by name, get URL
4. **Create Mission**: Generate detailed instructions for AI agent
5. **Agent Loop**:
   - AI decides which browser tool to use
   - Scraper executes the tool (navigate, click, snapshot)
   - Result returned to AI
   - AI analyzes and decides next action
   - Repeat until data found or timeout
6. **Parse Results**: Extract structured JSON from AI's final response
7. **Save Output**: Write JSON file, optionally update Excel

## MCP Tools Available

The AI agent has access to these browser automation tools:

- `browser_navigate`: Go to a URL
- `browser_snapshot`: Get page structure (best for data extraction!)
- `browser_click`: Click elements
- `browser_evaluate`: Run JavaScript
- `browser_wait_for`: Wait for content

The most important tool is **`browser_snapshot`** - it returns structured accessibility data that's perfect for LLMs to analyze.

## Project Structure

```
art-school-scraper/
├── README.md                    # This file
├── docker-compose.yml           # Ollama + MCP server
├── config.yaml                  # Configuration
├── requirements.txt             # Python dependencies
├── scraper.py                   # Main application
├── data/
│   ├── art_schools_final.xlsx           # Input
│   └── School_Admission_Data_FINAL.xlsx # Input
├── results/
│   ├── stamps_school_2024-11-09.json    # Output
│   └── ...
└── logs/
    └── scraper.log              # Detailed logs
```

## Tips for Best Results

1. **Start with Test Connection**: Always run `--test-connection` first
2. **Check Website First**: Visit the school's website manually to see if data is accessible
3. **Use Verbose Mode**: Keep `verbose: true` to see what's happening
4. **Review Confidence Scores**: Low confidence (<0.70) may need manual verification
5. **Check Source URLs**: Verify the agent found the right pages
6. **Try Different Models**: Larger models are more accurate but slower
7. **Adjust Timeouts**: Some websites are slow, increase timeout if needed
8. **Read the Logs**: Check `logs/scraper.log` for detailed debugging info

## Limitations

- **Manual Operation**: You must specify one school at a time
- **Website Structure**: Results depend on website accessibility
- **AI Accuracy**: Not 100% accurate, always verify important data
- **Rate Limiting**: Add delays to be respectful to servers
- **JavaScript-Heavy Sites**: May have trouble with dynamic content
- **Login Required**: Cannot access pages that need authentication

## Future Enhancements

Potential features (not currently implemented):

- Batch mode to scrape multiple schools
- Web UI for easier operation
- Automatic retry with different strategies
- Export to CSV format
- Data validation and comparison
- Progress tracking across multiple runs
- Email notifications
- Scheduled/cron support

## Support

If you encounter issues:

1. Check this README's Troubleshooting section
2. Review `logs/scraper.log`
3. Test connections with `--test-connection`
4. Try with a simpler school website first
5. Use `--verbose` to see detailed progress

## License

This is a custom tool built for art school data collection.

---

**Built with:**
- [Ollama](https://ollama.ai/) - Local LLM runtime
- [Microsoft MCP](https://github.com/microsoft/mcp) - Browser automation via Model Context Protocol
- [Playwright](https://playwright.dev/) - Browser automation framework
- Python, Pandas, Rich
