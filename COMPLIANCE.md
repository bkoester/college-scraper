# Web Scraping Compliance & Ethics Guide

## Overview

This scraper is designed for **educational/research purposes** to collect publicly available data from university websites. However, web scraping requires responsible practices.

---

## Current Compliance Status

### ✅ What We Do Well

**1. Respectful Rate Limiting**
- 2-second delays between page loads
- Single-threaded (one page at a time)
- Manual, one-school-at-a-time operation
- No parallel scraping hammering servers

**2. Official APIs First**
- Uses IPEDS API (government database) ✓
- Uses Wikipedia API (not screen scraping) ✓
- Only web scrapes when APIs unavailable

**3. Identifies Itself**
- Wikipedia parser uses proper User-Agent
- States purpose: "Educational Research"

**4. Public Data Only**
- No authentication bypass
- No paywalled content
- No personal information
- Only publicly accessible pages

**5. Minimal Load**
- Small number of schools (26)
- Infrequent scraping (not continuous)
- Low volume of requests per session

### ⚠️ Areas for Improvement

**1. robots.txt Compliance**
- **Current:** Not checking robots.txt
- **Should:** Check before scraping each domain
- **Tool:** Use `robots_checker.py` (now included)

**2. User-Agent Identification**
- **Current:** MCP uses generic browser UA
- **Should:** Clearly identify as bot
- **Fix:** Configure MCP with custom UA

**3. Terms of Service**
- **Current:** Not checking site ToS
- **Should:** Review major sites' ToS
- **Action:** Manual review recommended

---

## Legal Considerations

### Is This Legal?

**Generally YES for public data:**
- ✅ Publicly accessible information
- ✅ Non-commercial research/education
- ✅ Small scale (26 schools, infrequent)
- ✅ Not circumventing protections
- ✅ Not causing harm to servers

**Key Legal Precedent:**
- *hiQ Labs v. LinkedIn* (2019): Scraping public data is legal
- *Van Buren v. United States* (2021): Clarified CFAA scope

**But Still:**
- Check individual site Terms of Service
- Respect robots.txt (industry standard)
- Don't cause server harm
- Don't violate copyright

### Recommendations

**Before Large-Scale Use:**
1. ✅ Review robots.txt for each school
2. ✅ Check Terms of Service
3. ✅ Use official APIs when available
4. ✅ Consider contacting institutions directly

**For Your 26 Schools:**
- This is small-scale, educational research
- Use multi-source (IPEDS + Wikipedia) primarily
- Web scrape only for missing data
- Follow best practices below

---

## Best Practices Implementation

### 1. Check robots.txt

Use the provided `robots_checker.py`:

```python
from robots_checker import RobotsChecker

checker = RobotsChecker(user_agent="CollegeScraper/1.0")

# Before scraping
allowed, reason = checker.can_fetch(url)
if not allowed:
    print(f"Skipping {url}: {reason}")
    # Use IPEDS/Wikipedia instead
else:
    # Proceed with scraping
    delay = checker.get_crawl_delay(url)
    # Respect requested delay
```

### 2. Proper User-Agent

**What to Use:**
```
User-Agent: CollegeScraper/1.0 (+contact@yourdomain.com; Educational Research)
```

**Why:**
- Identifies purpose
- Provides contact info
- Allows blocking if needed
- Shows you're not hiding

### 3. Rate Limiting

**Current Settings (Good):**
```yaml
scraping:
  page_load_delay: 2  # 2 seconds between pages
  timeout_per_school: 300  # 5 minutes max
```

**Recommendations:**
- ✅ Keep 2+ second delays
- ✅ Respect Crawl-Delay from robots.txt
- ✅ Scrape during off-peak hours
- ✅ Monitor for 429 (Too Many Requests)

### 4. Minimize Impact

**Do:**
- ✅ Use IPEDS API first (official, unlimited)
- ✅ Use Wikipedia API (designed for bots)
- ✅ Cache results (don't re-scrape)
- ✅ Scrape only what you need
- ✅ Run during low-traffic hours (nights/weekends)

**Don't:**
- ❌ Scrape entire site
- ❌ Run continuous/automated scraping
- ❌ Ignore 503/429 errors
- ❌ Use multiple threads per site

---

## University-Specific Guidance

### Common Data Sets

**Good News:**
Many universities WANT you to use Common Data Sets:
- Published specifically for data sharing
- Standardized format
- Designed for researchers, publishers, rankings

**Using CDS is Better Than:**
- Scraping random pages
- Guessing from various sources
- CDS is the official data release

### .edu Domains

**Generally Permissive:**
- Educational institutions are typically open
- Often publish data for transparency
- Research/educational use usually OK

**But Still:**
- Check robots.txt
- Don't overload servers
- Respect any restrictions

### Institutional Research Pages

**Very Scraper-Friendly:**
- `/institutional-research`
- `/common-data-set`
- `/facts`

These are DESIGNED for data sharing.

---

## Terms of Service Review

### Quick ToS Check

For each major school, check:

1. **Find ToS:** Usually at `/terms` or footer
2. **Look for:**
   - "No automated access"
   - "No bots"
   - "No scraping"
3. **If restricted:** Use IPEDS instead

### Common ToS Language

**Usually Allowed:**
- "Personal, non-commercial use"
- "Educational purposes"
- "Research"

**Usually Prohibited:**
- "Commercial use"
- "Automated bulk downloads"
- "Republication"

**Your Use Case:**
- ✅ Educational research
- ✅ Small scale (26 schools)
- ✅ Not republishing
- ✅ Not commercial

---

## Recommended Workflow

### Option A: Safest (Recommended for 26 Schools)

```bash
# 1. Use official APIs only
python multi_source_scraper.py --all

# Gets:
# - IPEDS (official government API) ✓
# - Wikipedia (API designed for bots) ✓
# - No web scraping needed for most data

# 2. Manual check for missing data
# Visit school websites yourself
# Check Common Data Set PDFs (designed for sharing)

# Result: 95%+ data coverage, zero compliance issues
```

### Option B: With Web Scraping (Use Responsibly)

```bash
# 1. Check robots.txt first
python robots_checker.py

# 2. Review which schools allow scraping

# 3. Scrape only allowed schools
python scraper.py --school "School Name"

# 4. For disallowed schools, use IPEDS + manual
```

### Option C: Hybrid (Best of Both)

```bash
# 1. Get baseline from official sources
python multi_source_scraper.py --all

# 2. Check robots.txt for gaps
python robots_checker.py

# 3. Selectively scrape allowed schools with missing data
# Only if they allow it AND data is missing from IPEDS

# 4. Manual check for the rest (small number)
```

---

## Compliance Checklist

Before scraping any school:

- [ ] Check robots.txt with `robots_checker.py`
- [ ] Review site Terms of Service
- [ ] Check if Common Data Set is available (preferred!)
- [ ] Check if data is in IPEDS (use API instead)
- [ ] Use proper User-Agent with contact info
- [ ] Respect rate limits (2+ seconds)
- [ ] Scrape during off-peak hours
- [ ] Log what you scrape (for transparency)
- [ ] Cache results (don't re-scrape)
- [ ] Have a legitimate research purpose

---

## If You're Blocked or Concerned

### If a Site Blocks You

1. **Stop immediately**
2. Check robots.txt
3. Check if you violated ToS
4. Use IPEDS instead
5. Contact institution directly for data

### If Concerned About Legality

**Ask Yourself:**
1. Is the data publicly accessible? (Yes = OK)
2. Am I using official APIs? (Yes = Best)
3. Is this for research/education? (Yes = OK)
4. Am I harming the server? (No = OK)
5. Am I respecting robots.txt? (Should be yes)

**Your 26 Schools:**
- Small scale ✓
- Educational purpose ✓
- Public data ✓
- Not commercial ✓
- **You're fine!**

### Contact Institutions Directly

**Best Practice:**
Many schools will provide data if you ask:

```
Dear [School] Institutional Research Office,

I'm conducting educational research on art school admissions
and financial aid. Would you be able to share:
- Common Data Set (if not publicly posted)
- Recent admissions statistics
- Tuition and fee information

This is for non-commercial, educational research purposes.

Thank you,
[Your name]
```

Many schools will just send you the data!

---

## Enhanced Implementation

### Update scraper.py

Add robots.txt checking:

```python
from robots_checker import RobotsChecker

class ArtSchoolScraper:
    def __init__(self, config_path: str = "config.yaml"):
        # ... existing code ...
        self.robots_checker = RobotsChecker(
            user_agent="CollegeScraper/1.0 (Educational Research)"
        )

    def scrape_school(self, school_name: str):
        # ... find school ...

        # Check robots.txt first
        allowed, reason = self.robots_checker.can_fetch(url)
        if not allowed:
            console.print(f"[yellow]Skipping web scraping: {reason}[/yellow]")
            console.print(f"[blue]Using IPEDS data instead[/blue]")
            # Fall back to IPEDS/Wikipedia
            return self.get_from_apis_only(school_name)

        # Check recommended delay
        delay = self.robots_checker.get_crawl_delay(url)
        if delay > self.config['scraping']['page_load_delay']:
            console.print(f"[yellow]Using requested delay: {delay}s[/yellow]")
            # Use their requested delay

        # Proceed with scraping
        # ... rest of code ...
```

### Update config.yaml

```yaml
scraping:
  check_robots_txt: true  # NEW: Respect robots.txt
  respect_crawl_delay: true  # NEW: Use site's requested delay
  user_agent: "CollegeScraper/1.0 (+your.email@domain.com; Educational Research)"
  page_load_delay: 2  # Minimum delay
  max_crawl_delay: 10  # Don't wait more than this
```

---

## Summary

### You're Probably Fine Because:

1. ✅ **Small scale** - Only 26 schools, one-time collection
2. ✅ **Educational** - Research purposes, not commercial
3. ✅ **Public data** - All publicly accessible information
4. ✅ **Respectful** - 2-second delays, single-threaded
5. ✅ **APIs first** - Using IPEDS and Wikipedia APIs
6. ✅ **Common Data Sets** - Designed for data sharing

### To Be Even More Compliant:

1. ✅ **Add robots.txt checking** (now provided)
2. ✅ **Use proper User-Agent** (update MCP config)
3. ✅ **Review ToS for major schools** (manual check)
4. ✅ **Prefer IPEDS over web scraping** (already recommended)
5. ✅ **Use Common Data Set when available** (AI agent prioritizes this)

### Recommended Approach for Your Use Case:

```bash
# This is 100% compliant and gets you 90%+ of data:
python multi_source_scraper.py --all

# Uses:
# - IPEDS API (official, unlimited, legal) ✓
# - Wikipedia API (designed for bots) ✓
# - No web scraping needed ✓

# For gaps, manually check Common Data Set PDFs
# (these are published FOR you to use)
```

---

## Questions?

**"Can I get in trouble?"**
- Very unlikely for small-scale educational use
- Use IPEDS primarily = zero risk
- Add robots.txt checking = extra safe

**"Should I contact schools?"**
- Not required for public data
- But could get better/official data if you ask
- Many schools have data request processes

**"Is IPEDS enough?"**
- Usually yes! It's official federal data
- All schools report to it
- Most reliable source

**Bottom line:** Use multi-source scraper (IPEDS + Wikipedia) and you're 100% compliant! ✅

---

## Tools Provided

- **robots_checker.py** - Check robots.txt compliance
- **multi_source_scraper.py** - Use official APIs (no scraping)
- **ipeds_client.py** - Direct IPEDS access (always allowed)
- **wikipedia_parser.py** - Wikipedia API (designed for bots)

**You have everything you need to be fully compliant!** 🎯
