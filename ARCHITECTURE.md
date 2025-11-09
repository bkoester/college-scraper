# System Architecture

## Complete Multi-Source Data Collection System

```
┌─────────────────────────────────────────────────────────────────────┐
│                         USER (You)                                  │
│                                                                     │
│  Commands:                                                         │
│  • python scraper.py --school "Name"           (AI web scraping)  │
│  • python multi_source_scraper.py --school "Name"  (Multi-source) │
│  • python ipeds_client.py                      (IPEDS only)       │
│  • python wikipedia_parser.py                  (Wikipedia only)   │
└────────────────────────────┬────────────────────────────────────────┘
                             │
        ┌────────────────────┼────────────────────┐
        │                    │                    │
        ▼                    ▼                    ▼
┌───────────────┐  ┌─────────────────┐  ┌──────────────────┐
│  scraper.py   │  │ multi_source_   │  │ Direct Clients  │
│               │  │ scraper.py      │  │                 │
│ • AI agent    │  │                 │  │ • ipeds_client  │
│ • MCP tools   │  │ Coordinates:    │  │ • wikipedia_    │
│ • CDS detect  │  │ • IPEDS         │  │   parser        │
│ • Ollama      │  │ • Wikipedia     │  │                 │
└───────┬───────┘  │ • Web scraping  │  └────────┬────────┘
        │          │ • Merging       │           │
        │          └────────┬────────┘           │
        │                   │                    │
        └───────────────────┼────────────────────┘
                            │
        ┌───────────────────┼───────────────────┐
        │                   │                   │
        ▼                   ▼                   ▼
┌──────────────┐  ┌──────────────┐  ┌─────────────────┐
│ IPEDS API    │  │ Wikipedia    │  │ School Website  │
│              │  │ API          │  │                 │
│ College      │  │              │  │ Via:            │
│ Scorecard    │  │ en.wikipedia │  │ • Ollama AI     │
│              │  │ .org/w/api   │  │ • MCP Browser   │
│ Confidence:  │  │              │  │                 │
│ 98%          │  │ Confidence:  │  │ Confidence:     │
│              │  │ 70%          │  │ 85% (CDS: 95%)  │
└──────────────┘  └──────────────┘  └─────────────────┘
        │                   │                   │
        └───────────────────┼───────────────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │  Data Merger          │
                │                       │
                │ • Compare confidence  │
                │ • Select best source  │
                │ • Validate conflicts  │
                │ • Flag disagreements  │
                └───────────┬───────────┘
                            │
                            ▼
                ┌───────────────────────┐
                │  Output Files         │
                │                       │
                │ • *_multisource.json  │
                │   (all sources raw)   │
                │                       │
                │ • *_merged.json       │
                │   (best data)         │
                │                       │
                │ • *.json              │
                │   (web scraping only) │
                └───────────────────────┘
```

---

## Component Details

### Input Layer

```
Excel Files (data/)
├── art_schools_final.xlsx
│   • 26 schools
│   • URLs, locations
│   • Existing data
│
└── School_Admission_Data_FINAL.xlsx
    • 29 schools
    • Admission statistics
    • Baseline comparison
```

### Processing Layer

#### 1. Single-Source Scraper (`scraper.py`)

```
scraper.py
├── Load Excel files
├── Find school & URL
├── Create AI mission
├── Agent loop:
│   ├── Look for CDS (NEW!)
│   ├── Navigate pages
│   ├── Extract data
│   └── Return JSON
└── Save results
```

#### 2. Multi-Source Collector (`multi_source_scraper.py`)

```
multi_source_scraper.py
├── Load Excel files
├── For each school:
│   ├── Query IPEDS API
│   ├── Parse Wikipedia
│   ├── (Optional) Web scraping
│   ├── Merge data
│   ├── Validate conflicts
│   └── Save both raw & merged
└── Batch processing support
```

#### 3. Data Source Clients

```
ipeds_client.py
├── College Scorecard API
├── Search by name
├── Get comprehensive data
├── Extract & standardize
└── 98% confidence

wikipedia_parser.py
├── Wikipedia API
├── Search articles
├── Extract infobox
├── Clean markup
└── 70% confidence
```

### Docker Services Layer

```
docker-compose.yml
├── Ollama Service
│   ├── Port: 11434
│   ├── Model: qwen2.5:32b
│   ├── GPU support (optional)
│   └── Tool calling enabled
│
└── MCP Server
    ├── Port: 8931
    ├── Playwright/Chromium
    ├── Browser automation
    └── Headless mode
```

### Configuration Layer

```
config.yaml
├── Ollama settings
├── MCP settings
├── Input/output paths
├── Scraping behavior
├── Fields to extract
├── Data source priorities (NEW!)
│   ├── IPEDS (98%)
│   ├── CDS (95%)
│   ├── Web (85%)
│   └── Wikipedia (70%)
└── Merge strategy (NEW!)
```

### Output Layer

```
results/
├── [school]_multisource_[date].json
│   • Raw data from all sources
│   • Before merging
│   • Full source attribution
│
├── [school]_merged_[date].json
│   • Best data from each source
│   • Confidence-weighted selection
│   • Validation flags
│
└── [school]_[date].json
    • Web scraping only
    • Original format
    • Compatible with v1
```

---

## Data Flow

### Flow 1: Multi-Source Collection

```
User Command
    │
    ▼
Load Config & Excel
    │
    ├──────┬──────┬──────┐
    ▼      ▼      ▼      ▼
 IPEDS  Wiki  Web  (Excel baseline)
    │      │      │      │
    └──────┴──────┴──────┘
              │
              ▼
      Merge by Confidence
              │
        ┌─────┴─────┐
        ▼           ▼
  Raw Output   Merged Output
```

### Flow 2: AI Web Scraping (Enhanced)

```
User Command
    │
    ▼
Load Config & Excel
    │
    ▼
Create AI Mission
    │
    ▼
Agent Loop:
    │
    ├─→ Look for CDS (NEW!)
    │   ├─→ Found? Extract all data
    │   └─→ Not found? Continue
    │
    ├─→ Navigate pages
    │   ├─→ Admissions
    │   ├─→ Tuition
    │   └─→ Statistics
    │
    ├─→ Extract data
    │
    └─→ Return JSON
        │
        ▼
    Save Results
```

### Flow 3: Merge Strategy

```
For each field:
    │
    ▼
Collect from all sources
    │
    ├─→ IPEDS: 17.9% (conf: 0.98)
    ├─→ Wiki:  18.0% (conf: 0.70)
    └─→ Web:   18.2% (conf: 0.85)
    │
    ▼
Compare confidence scores
    │
    ▼
Select highest confidence
    │
    ▼
IPEDS value selected (0.98)
    │
    ▼
Check variance
    │
    ├─→ <15%? OK
    └─→ >15%? FLAG
    │
    ▼
Store result + source
```

---

## Technology Stack

### Python Modules

```
Core Dependencies:
├── pyyaml (config parsing)
├── pandas (Excel reading)
├── openpyxl (Excel format)
├── requests (HTTP client)
├── httpx (async HTTP)
└── rich (CLI formatting)

Custom Modules:
├── scraper.py (main application)
├── ipeds_client.py (IPEDS API)
├── wikipedia_parser.py (Wikipedia API)
└── multi_source_scraper.py (coordinator)
```

### External Services

```
Docker Containers:
├── ollama/ollama:latest
│   • LLM runtime
│   • Tool calling support
│   • Model: qwen2.5:32b
│
└── mcr.microsoft.com/playwright/mcp:latest
    • Browser automation
    • MCP protocol
    • Chromium headless
```

### APIs

```
External APIs:
├── College Scorecard API
│   • api.data.gov/ed/collegescorecard
│   • No key required (optional)
│   • Federal data
│
└── Wikipedia API
    • en.wikipedia.org/w/api.php
    • No auth required
    • Rate limited
```

---

## Confidence Scoring

### Source Base Confidence

| Source | Base | Why |
|--------|------|-----|
| IPEDS | 98% | Federal mandate, standardized |
| Common Data Set | 95% | Official institutional report |
| Web Scraping (CDS) | 90% | Found via CDS link |
| Web Scraping | 85% | AI-extracted from website |
| Wikipedia | 70% | Crowdsourced, may be outdated |

### Adjustment Factors

```
Final Confidence = Base × Adjustment

Adjustments:
• Clear label found: ×1.0
• Inferred from context: ×0.9
• Ambiguous: ×0.8
• Calculated: ×0.95
• Outdated: ×0.7
```

---

## Validation Logic

### Variance Check

```python
def validate(values):
    if len(values) < 2:
        return OK

    max_val = max(values)
    min_val = min(values)
    variance = (max_val - min_val) / min_val

    if variance > 0.15:  # 15% threshold
        return FLAG
    else:
        return OK
```

### Example

```
Field: Enrollment
• IPEDS: 47,907
• Wiki:  47,900
• Web:   51,225

Variance: (51225-47900)/47900 = 6.9% → OK

Field: Tuition
• IPEDS: $17,786
• Web:   $21,000

Variance: (21000-17786)/17786 = 18% → FLAG
```

---

## Performance Characteristics

### Time Complexity

```
Single School:
├── IPEDS query:        O(1)  ~5 sec
├── Wikipedia query:    O(1)  ~3 sec
├── Web scraping:       O(n)  ~2-5 min (n = pages)
└── Merge:              O(k)  <1 sec (k = fields)

Batch (26 schools):
├── IPEDS (parallel):   O(m)  ~2 min
├── Wikipedia (parallel): O(m)  ~1 min
├── Web scraping:       O(m×n) ~1-2 hours
└── Total (no web):     ~15 min
```

### Memory Usage

```
Typical Memory:
├── Python process:     ~100 MB
├── Ollama (32B):      ~20 GB
├── MCP/Playwright:    ~500 MB
└── Total:             ~21 GB

Minimum (small model):
├── Python:            ~100 MB
├── Ollama (3B):       ~4 GB
├── MCP:               ~500 MB
└── Total:             ~5 GB
```

---

## Extension Points

### Adding New Sources

```python
# 1. Create client module
class NewSourceClient:
    def get_school_data(self, school_name):
        # Query source
        # Extract data
        # Return standardized format
        pass

# 2. Add to multi_source_scraper.py
results["sources"]["new_source"] = new_client.get_school_data(name)

# 3. Update config.yaml
data_sources:
  priority_order:
    - name: "new_source"
      confidence_base: 0.85
```

### Adding New Fields

```yaml
# In config.yaml
fields_to_extract:
  - name: "application_deadline"
    column: "Deadline"
    keywords:
      - "application deadline"
      - "apply by"
    data_type: "date"
    validation:
      format: "MM/DD/YYYY"
```

### Custom Merge Strategies

```python
# In multi_source_scraper.py
def weighted_average_merge(values):
    """Average values weighted by confidence"""
    total_weight = sum(v['confidence'] for v in values)
    weighted_sum = sum(v['value'] * v['confidence'] for v in values)
    return weighted_sum / total_weight
```

---

## Security Considerations

### Data Privacy

```
• Excel files not committed to git (.gitignore)
• Results not committed (.gitignore)
• No API keys in code
• API keys in config (gitignored if needed)
```

### Network Security

```
• All API calls over HTTPS
• No credentials stored
• Respects robots.txt
• Rate limiting implemented
• Polite delays between requests
```

### Sandboxing

```
• Docker containers isolated
• Browser runs headless
• No persistent browser data
• No cookies/sessions saved
```

---

## Scalability

### Current Limits

```
• 26 schools: ~15 min (multi-source, no web)
• 100 schools: ~1 hour (multi-source, no web)
• 1000 schools: ~10 hours (multi-source, no web)
```

### Optimization Options

```
1. Parallel processing:
   • Multiple schools simultaneously
   • Async API calls
   • Thread pool for web scraping

2. Caching:
   • Cache IPEDS responses (1 year TTL)
   • Cache Wikipedia data (1 month TTL)
   • Avoid re-scraping recent data

3. Selective scraping:
   • Use IPEDS baseline for all
   • Web scrape only for missing data
   • Wikipedia for validation only
```

---

## Error Handling

### Retry Logic

```python
@retry(max_attempts=3, backoff=exponential)
def query_api(url):
    response = requests.get(url)
    response.raise_for_status()
    return response.json()
```

### Graceful Degradation

```
If IPEDS fails:
    └─→ Try Wikipedia
        └─→ Try Web Scraping
            └─→ Mark as not found

If no sources work:
    └─→ Return partial data
    └─→ Flag as incomplete
    └─→ Log error
```

---

## Monitoring & Logging

### Log Levels

```
DEBUG:   API requests, tool calls
INFO:    Progress, source results
WARNING: Missing data, low confidence
ERROR:   API failures, parsing errors
```

### Metrics Tracked

```
• Sources queried
• Sources with data
• Fields found vs missing
• Average confidence
• Validation flags
• Duration
```

---

## Summary

This is a **production-ready, multi-source data collection system** with:

✅ **4 data sources** (IPEDS, CDS, Website, Wikipedia)
✅ **Intelligent merging** (confidence-weighted)
✅ **Automatic validation** (conflict detection)
✅ **Flexible operation** (single, batch, all)
✅ **Comprehensive logging** (debugging & monitoring)
✅ **Complete documentation** (5 guides)
✅ **Tested components** (test scripts included)

**Ready to collect the most accurate college data possible! 🎯**
