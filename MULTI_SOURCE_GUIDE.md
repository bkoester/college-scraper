# Multi-Source Data Collection Guide

**Get the most accurate data by combining multiple sources!**

## Why Multi-Source?

Individual school websites can be:
- ❌ Incomplete
- ❌ Outdated
- ❌ Inconsistent
- ❌ Hard to navigate

**Multi-source collection solves this** by gathering data from:
1. **IPEDS** - Federal database (98% confidence)
2. **Common Data Set** - Standardized reports (95% confidence)
3. **School Websites** - Most current info (85% confidence)
4. **Wikipedia** - Quick validation (70% confidence)

The system intelligently merges data, selecting the most reliable source for each field.

---

## Quick Start

### Single School

```bash
# Collect from all sources and merge
python multi_source_scraper.py --school "Stamps School of Art & Design"

# Output:
# - Raw data from each source: results/stamps_school_multisource_2024-11-09.json
# - Merged best data: results/stamps_school_merged_2024-11-09.json
```

### All Schools

```bash
# Collect for all schools in Excel file
python multi_source_scraper.py --all
```

### Test Sources

```bash
# Verify all data sources are working
python multi_source_scraper.py --test
```

---

## What You Get

### Raw Multi-Source Data

Contains data from ALL sources before merging:

```json
{
  "school_name": "Stamps School",
  "sources": {
    "ipeds": {
      "data": {
        "admission_rate": {
          "value": 0.179,
          "confidence": 0.98
        }
      }
    },
    "wikipedia": {
      "data": {
        "admission_rate": {
          "value": 0.179,
          "confidence": 0.70
        }
      }
    },
    "web_scraping": {
      "data": {
        "admission_rate": {
          "value": 0.182,
          "confidence": 0.85
        }
      }
    }
  }
}
```

### Merged Data

Best value from each source:

```json
{
  "school_name": "Stamps School",
  "data": {
    "admission_rate": {
      "value": 0.179,
      "confidence": 0.98,
      "source": "IPEDS"
    }
  },
  "sources_used": {
    "admission_rate": "ipeds"
  },
  "validation": {
    "flagged_fields": []
  }
}
```

---

## Data Sources Explained

### 1. IPEDS (Integrated Postsecondary Education Data System)

**What:** Federal database, ALL schools must report
**Confidence:** 98%
**Best for:** Tuition, enrollment, admission rates, test scores

**Pros:**
- Highly reliable federal data
- Comprehensive coverage
- Standardized format

**Cons:**
- May be 1-2 years old
- Some schools report incomplete data

**Example:**
```bash
# Test IPEDS directly
python ipeds_client.py
```

---

### 2. Common Data Set (CDS)

**What:** Standardized institutional reports (PDF/Excel)
**Confidence:** 95%
**Best for:** Everything! Detailed admissions, tuition, enrollment

**The AI agent now automatically looks for CDS first!**

**Sections:**
- **Section C**: Admissions (applications, rates, test scores)
- **Section H**: Financial Aid (tuition, fees, aid)

**URL Patterns:**
- `/common-data-set`
- `/institutional-research`
- `/ir`
- `/fast-facts`

**Example Schools:**
- UMich: https://oira.umich.edu/campus/common-data-set/
- Stanford: https://ucomm.stanford.edu/cds/

---

### 3. School Websites (AI Scraping)

**What:** Direct scraping with intelligent navigation
**Confidence:** 85% (variable)
**Best for:** Most current data, program-specific info

**Now prioritizes Common Data Set!**

The AI agent:
1. ✅ Looks for CDS links first
2. ✅ Checks institutional research pages
3. ✅ Falls back to admissions/tuition pages
4. ✅ Adapts to different site structures

---

### 4. Wikipedia

**What:** Crowdsourced encyclopedia with infoboxes
**Confidence:** 70%
**Best for:** Quick validation, basic facts

**Example:**
```bash
# Test Wikipedia parser
python wikipedia_parser.py
```

---

## How Merging Works

### Highest Confidence Wins

For each field:
1. Collect from all sources
2. Compare confidence scores
3. Select highest confidence value
4. Flag significant disagreements

**Example:**

```
Field: In-State Tuition

IPEDS:     $17,786 (98%) ← SELECTED
Wikipedia: $17,786 (70%)
Website:   $17,950 (85%)

Result: $17,786 from IPEDS
```

### Validation Flags

If sources disagree by >15%:

```json
{
  "validation": {
    "flagged_fields": ["enrollment_size"],
    "details": {
      "enrollment_size": {
        "ipeds": 47907,
        "website": 51225,
        "variance": 0.07,
        "note": "Difference may be due to university-wide vs program-specific enrollment"
      }
    }
  }
}
```

---

## Configuration

Edit `config.yaml` to customize:

```yaml
data_sources:
  enabled: true  # Turn on multi-source

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
      check_common_data_set_first: true

    - name: "wikipedia"
      enabled: true
      confidence_base: 0.70

  merge_strategy: "highest_confidence"

  validation:
    enabled: true
    variance_threshold: 0.15  # Flag >15% difference
```

---

## Usage Examples

### Example 1: Single School

```bash
python multi_source_scraper.py --school "College for Creative Studies"
```

**Output:**
```
Collecting data for: College for Creative Studies

1. Querying IPEDS database...
  ✓ IPEDS data collected
    Found: in_state_tuition (98%), admission_rate (98%), enrollment (98%)...

2. Checking Wikipedia...
  ✓ Wikipedia data collected
    Found: enrollment (75%), admission_rate (70%)...

3. Web scraping (via AI agent)...
  ⚠ Use scraper.py for web scraping

Merged Data Summary:
┌───────────────────┬──────────┬─────────┬────────────┐
│ Field             │ Value    │ Source  │ Confidence │
├───────────────────┼──────────┼─────────┼────────────┤
│ in_state_tuition  │ $48,000  │ ipeds   │ 98%        │
│ admission_rate    │ 62.0%    │ ipeds   │ 98%        │
│ enrollment_size   │ 1,450    │ ipeds   │ 98%        │
└───────────────────┴──────────┴─────────┴────────────┘

Raw data saved to: results/ccs_multisource_2024-11-09.json
Merged data saved to: results/ccs_merged_2024-11-09.json
```

### Example 2: Batch Collection

```bash
# Create a file with school names
cat > schools.txt << EOF
Stamps School of Art & Design
College for Creative Studies
Kendall College of Art and Design
Rhode Island School of Design
EOF

# Collect for all
python multi_source_scraper.py --batch schools.txt
```

### Example 3: All Schools

```bash
# Collect for every school in your Excel file
python multi_source_scraper.py --all
```

**Progress bar:**
```
Processing schools... ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━ 26/26 100%
Batch collection complete!
```

---

## Combining with AI Scraping

For best results, use both tools:

### Step 1: Multi-Source Collection

```bash
# Get baseline from IPEDS + Wikipedia
python multi_source_scraper.py --school "School Name"
```

### Step 2: AI Web Scraping

```bash
# Get detailed current data from website
python scraper.py --school "School Name"
```

### Step 3: Compare

Review both outputs and combine manually or use the merged data.

---

## Workflow Recommendations

### For 26 Art Schools

**Option A: Fast & Reliable (IPEDS + Wikipedia only)**
```bash
# 2-3 minutes per school
python multi_source_scraper.py --all
```

**Option B: Comprehensive (All sources)**
```bash
# Collect from IPEDS + Wikipedia
python multi_source_scraper.py --all

# Then selectively scrape websites for missing data
python scraper.py --school "School with missing data"
```

**Option C: Manual per school**
```bash
# Review each school individually
for school in "School 1" "School 2" "School 3"; do
    python multi_source_scraper.py --school "$school"
    python scraper.py --school "$school"
done
```

---

## Interpreting Results

### High Confidence (95%+)

✅ **Trust this data**
- From IPEDS or Common Data Set
- Use as-is

### Medium Confidence (70-94%)

⚠️ **Good but verify**
- From Wikipedia or website
- Cross-check if critical

### Low Confidence (<70%)

❌ **Needs verification**
- Manually verify on official website
- Consider as placeholder only

### Validation Flags

🚩 **Review carefully**
- Sources disagree significantly
- Check which source is correct
- Note discrepancy in your records

---

## Troubleshooting

### No IPEDS Data

**Problem:** School not found in IPEDS

**Solutions:**
1. Try full official name
2. School might not receive federal aid (rare)
3. Use other sources

### Wikipedia Has No Page

**Problem:** No Wikipedia article

**Solutions:**
1. Check if page exists manually
2. Some small schools don't have pages
3. Use IPEDS + website only

### All Sources Disagree

**Problem:** Significant variance between sources

**Solutions:**
1. Check data years (may be from different years)
2. Verify units (annual vs semester, with/without fees)
3. Check in-state vs out-of-state distinction
4. Manually verify on official website

---

## API Keys (Optional)

### College Scorecard API Key

For better rate limits:

1. Get free key: https://api.data.gov/signup/
2. Add to config:

```yaml
data_sources:
  priority_order:
    - name: "ipeds"
      api_key: "YOUR_KEY_HERE"
```

---

## Output Structure

### Directory Structure

```
results/
├── stamps_school_multisource_2024-11-09.json  # Raw from all sources
├── stamps_school_merged_2024-11-09.json       # Best merged data
├── stamps_school_2024-11-09.json              # Web scraping only
└── example_*.json                              # Examples
```

### File Naming

- `[school]_multisource_[date].json` - All sources, raw
- `[school]_merged_[date].json` - Merged best data
- `[school]_[date].json` - Web scraping only

---

## Best Practices

### ✅ DO

- Use multi-source for best accuracy
- Review validation flags
- Cross-check unexpected values
- Keep both raw and merged files
- Note data years in your records

### ❌ DON'T

- Blindly trust single source
- Ignore validation flags
- Assume all data is current year
- Delete raw multi-source files
- Mix data from different years

---

## Comparison: Single vs Multi-Source

| Aspect | Single Source (scraper.py) | Multi-Source |
|--------|---------------------------|--------------|
| **Reliability** | Variable (70-90%) | High (95%+) |
| **Coverage** | Depends on website | Comprehensive |
| **Speed** | 2-5 min/school | 30-60 sec/school* |
| **Completeness** | May have gaps | More complete |
| **Validation** | None | Automatic |
| **Confidence** | Single score | Best of all |

*Not including web scraping component

---

## Summary

**For best results:**

1. ✅ Start with multi-source collection
2. ✅ Review merged data
3. ✅ Check validation flags
4. ✅ Use web scraping for gaps/details
5. ✅ Keep both raw and merged files

**Data quality priority:**
1. IPEDS (98%) - Most reliable
2. Common Data Set (95%) - Most comprehensive
3. Website (85%) - Most current
4. Wikipedia (70%) - Quick validation

**The multi-source approach gives you the most accurate, complete, and validated data! 🎯**

---

## Quick Reference

```bash
# Test all sources
python multi_source_scraper.py --test

# Single school
python multi_source_scraper.py --school "Name"

# All schools
python multi_source_scraper.py --all

# Batch from file
python multi_source_scraper.py --batch schools.txt

# Test individual sources
python ipeds_client.py
python wikipedia_parser.py

# Original web scraper
python scraper.py --school "Name"
```

For detailed source information, see: **DATA_SOURCES.md**
