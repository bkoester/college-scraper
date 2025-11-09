# Data Sources Guide

This guide explains all available data sources and how to use them effectively.

## Overview

The scraper can collect data from multiple sources to ensure accuracy and completeness:

1. **IPEDS** (Federal Database) - Most reliable, comprehensive
2. **Common Data Set** (CDS) - Standardized institutional reports
3. **School Websites** (AI Scraping) - Most current, variable quality
4. **Wikipedia** - Good for validation and basic facts

## Source Details

### 1. IPEDS (Integrated Postsecondary Education Data System)

**What it is:**
- Federal database maintained by National Center for Education Statistics (NCES)
- ALL institutions receiving federal financial aid must report annually
- Standardized format, very reliable

**Data available:**
- ✅ Tuition (in-state, out-of-state)
- ✅ Enrollment (total, undergraduate)
- ✅ Admission rates
- ✅ SAT/ACT scores (25th-75th percentile)
- ✅ Completion rates
- ✅ Financial aid statistics
- ❌ Yield rates (not always available)

**Access:**
- API: College Scorecard API (`api.data.gov/ed/collegescorecard`)
- No API key required (but recommended for production)
- Get free key at: https://api.data.gov/signup/

**Confidence Level:** 98%

**Usage:**
```bash
# Test IPEDS connection
python ipeds_client.py

# Use in multi-source scraper
python multi_source_scraper.py --school "School Name"
```

**Example:**
```python
from ipeds_client import IPEDSClient

client = IPEDSClient()
data = client.get_school_by_name("University of Michigan")
standardized = client.extract_standardized_data(data)
```

**Pros:**
- Highly reliable federal data
- Comprehensive coverage
- Standardized format
- Updated annually

**Cons:**
- Data may be 1-2 years old
- API can be slow
- Some schools report incomplete data

---

### 2. Common Data Set (CDS)

**What it is:**
- Standardized format created by colleges and publishers
- Many institutions publish CDS annually (PDF or Excel)
- Contains comprehensive admissions and financial data

**Data available:**
- ✅ Admission rates, yield rates
- ✅ SAT/ACT scores (detailed percentiles)
- ✅ Tuition and fees (detailed breakdown)
- ✅ Enrollment (by level, full-time/part-time)
- ✅ Class rank data
- ✅ Application requirements
- ✅ Financial aid statistics

**Common URL Patterns:**
- `[school-domain]/common-data-set`
- `[school-domain]/institutional-research`
- `[school-domain]/ir`
- `[school-domain]/about/facts`
- `[school-domain]/fast-facts`

**Confidence Level:** 95%

**CDS Sections:**
- **Section C**: First-time, First-year Admission (the goldmine!)
  - C1: Applications, admissions, enrollees
  - C9: SAT/ACT scores
  - C11: Wait list data
- **Section H**: Financial Aid
  - H1: Tuition, room, board
  - H2: Financial aid policies

**Usage:**
The AI scraper now **automatically looks for CDS first** before scraping general pages.

**Example Schools with CDS:**
- University of Michigan: https://oira.umich.edu/campus/common-data-set/
- Stanford: https://ucomm.stanford.edu/cds/
- MIT: https://ir.mit.edu/common-data-set

**Pros:**
- Comprehensive and detailed
- Standardized format across schools
- Usually most current year
- Contains explanatory notes

**Cons:**
- Not all schools publish CDS publicly
- Some schools publish as PDF (harder to parse)
- May require multiple page clicks to find
- Updated annually (once per year)

---

### 3. School Websites (AI Scraping)

**What it is:**
- Direct scraping of school's official website
- AI agent navigates and extracts data
- Now prioritizes Common Data Set when available

**Data available:**
- ✅ All fields (depends on website structure)
- ✅ Most current information
- ✅ Program-specific details
- ✅ Recent announcements/changes

**Confidence Level:** 80-90% (variable)

**How it works:**
1. AI agent starts at school's homepage
2. Looks for Common Data Set first
3. Falls back to dedicated pages (Admissions, Tuition)
4. Uses browser automation tools to navigate
5. Extracts and structures data

**Usage:**
```bash
# Use main scraper
python scraper.py --school "School Name"

# The agent now automatically:
# 1. Looks for CDS links
# 2. Checks institutional research pages
# 3. Falls back to admissions pages
```

**Pros:**
- Most current data
- Can find program-specific info
- Adapts to different site structures
- Can follow multi-step navigation

**Cons:**
- Variable reliability
- Depends on website design
- May miss data if site is complex
- Takes longer than API access

---

### 4. Wikipedia

**What it is:**
- Crowdsourced encyclopedia
- Many colleges have detailed infoboxes
- Surprisingly reliable for basic statistics

**Data available:**
- ✅ Enrollment
- ✅ Admission rates (sometimes)
- ✅ Tuition (general ranges)
- ✅ Basic facts
- ❌ Detailed breakdowns (limited)

**Confidence Level:** 70-75%

**Usage:**
```bash
# Test Wikipedia parser
python wikipedia_parser.py

# Use in multi-source scraper
python multi_source_scraper.py --school "School Name"
```

**Example:**
```python
from wikipedia_parser import WikipediaParser

parser = WikipediaParser()
data = parser.get_school_data("University of Michigan")
```

**Pros:**
- Fast to access
- Good for validation
- Works when other sources fail
- Includes citations

**Cons:**
- Lower confidence
- May be outdated
- General data only (not detailed)
- Subject to editing errors

---

## Multi-Source Collection

### How It Works

The `multi_source_scraper.py` collects from all sources and merges intelligently:

```bash
# Collect from all sources for one school
python multi_source_scraper.py --school "School Name"

# Test all sources
python multi_source_scraper.py --test

# Batch collect for all schools
python multi_source_scraper.py --all
```

### Merge Strategy

**Highest Confidence Wins:**
For each data field, the system:
1. Collects from all enabled sources
2. Compares confidence scores
3. Selects value with highest confidence
4. Flags significant disagreements

**Example:**
```
Field: Admission Rate

IPEDS:     17.9% (confidence: 0.98) ← SELECTED
Wikipedia: 18.0% (confidence: 0.70)
Website:   18.2% (confidence: 0.85)

Result: 17.9% from IPEDS
```

### Configuration

Edit `config.yaml` to enable/disable sources:

```yaml
data_sources:
  enabled: true

  priority_order:
    - name: "ipeds"
      enabled: true
      confidence_base: 0.98

    - name: "common_data_set"
      enabled: true
      confidence_base: 0.95

    - name: "web_scraping"
      enabled: true
      confidence_base: 0.85

    - name: "wikipedia"
      enabled: true
      confidence_base: 0.70

  merge_strategy: "highest_confidence"

  validation:
    enabled: true
    variance_threshold: 0.15  # Flag if >15% difference
```

---

## Comparison Table

| Source | Reliability | Coverage | Timeliness | Speed | Confidence |
|--------|-------------|----------|------------|-------|------------|
| IPEDS | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐ | 98% |
| Common Data Set | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐ | 95% |
| Web Scraping | ⭐⭐⭐⭐ | ⭐⭐⭐⭐ | ⭐⭐⭐⭐⭐ | ⭐⭐ | 85% |
| Wikipedia | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐ | ⭐⭐⭐⭐⭐ | 70% |

---

## Best Practices

### 1. Always Start with Multi-Source

```bash
# Instead of single-source scraping
python scraper.py --school "Name"

# Use multi-source for best results
python multi_source_scraper.py --school "Name"
```

### 2. Check for Disagreements

Review the output for fields where sources disagree:

```json
{
  "validation_flags": {
    "tuition": {
      "variance": 0.18,
      "ipeds": 50000,
      "website": 59000,
      "warning": "Sources differ by >15%"
    }
  }
}
```

### 3. Prioritize CDS When Available

The AI agent now automatically looks for CDS, but you can verify:
- Check if school publishes CDS
- Note the URL pattern for future reference
- CDS gives you everything in one document

### 4. Use IPEDS as Baseline

IPEDS is always a good starting point:
```bash
# Quick IPEDS lookup
python ipeds_client.py
# Enter school name when prompted
```

### 5. Wikipedia for Quick Validation

If you get unexpected results, check Wikipedia:
```bash
python wikipedia_parser.py
```

---

## Troubleshooting

### IPEDS API Returns No Results

**Problem:** School not found in IPEDS

**Solutions:**
1. Try full official name: "University of Michigan-Ann Arbor"
2. Search manually: https://nces.ed.gov/collegenavigator/
3. School might not receive federal aid (not required to report)

### Common Data Set Not Found

**Problem:** Agent can't find CDS

**Solutions:**
1. Check manually if school publishes CDS
2. Try institutional research page directly
3. Some schools don't publish CDS publicly
4. Use IPEDS as alternative

### Wikipedia Has No Data

**Problem:** No infobox or incomplete data

**Solutions:**
1. Check if Wikipedia page exists
2. Page might not have university infobox
3. Data might be in article text (not parsed)

### Sources Disagree Significantly

**Problem:** Different sources show very different numbers

**Solutions:**
1. Check data years (might be from different years)
2. Verify in-state vs out-of-state distinction
3. Check if one includes fees, other doesn't
4. Manually verify on school's website
5. Note the discrepancy in your records

---

## API Keys (Optional)

### College Scorecard API Key

Get a free API key for better rate limits:

1. Visit: https://api.data.gov/signup/
2. Receive key via email
3. Add to `config.yaml`:

```yaml
data_sources:
  priority_order:
    - name: "ipeds"
      api_key: "YOUR_KEY_HERE"
```

---

## Additional Resources

### IPEDS
- Main site: https://nces.ed.gov/ipeds/
- College Scorecard: https://collegescorecard.ed.gov/
- Data Center: https://nces.ed.gov/ipeds/datacenter/
- API Docs: https://github.com/RTICWDT/open-data-maker/blob/master/API.md

### Common Data Set
- Overview: https://commondataset.org/
- School search: Search "[school name] common data set"
- Initiative site: https://www.commonapp.org/counselors-and-recommenders/common-data-set

### College Navigator
- Tool: https://nces.ed.gov/collegenavigator/
- User-friendly interface to IPEDS data

### Other Useful Sites
- Niche.com: https://www.niche.com/colleges/
- CollegeData: https://www.collegedata.com/
- Peterson's: https://www.petersons.com/

---

## Output Files

### Multi-Source Raw Data
`results/[school]_multisource_[date].json`

Contains data from all sources before merging.

### Merged Data
`results/[school]_merged_[date].json`

Contains best data from all sources after intelligent merging.

### Single-Source Data
`results/[school]_[date].json`

Contains data from web scraping only (from `scraper.py`).

---

## Summary

**For best results:**
1. ✅ Use `multi_source_scraper.py` instead of single scraper
2. ✅ Enable all data sources in config
3. ✅ Let AI agent look for CDS first (now automatic)
4. ✅ Review merged results for validation flags
5. ✅ Cross-reference when sources disagree

**Priority order:**
1. Common Data Set (if available) - comprehensive, standardized
2. IPEDS - reliable federal data
3. School Website - most current
4. Wikipedia - validation/fallback

This multi-source approach gives you the most accurate and complete data possible! 🎯
