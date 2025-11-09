# Performance Optimizations

This document describes the performance improvements made to the scraper to address slow startup and operation times.

## Issues Identified

### 1. **Redundant Connection Testing**
**Problem:** Every scrape operation ran full connection tests to Ollama and MCP server, even if already tested.
- Each test had 10-second timeouts
- Total wait time: 20+ seconds per operation when services unavailable

**Solution:**
- Added connection test result caching via `_connections_tested` flag
- Reduced timeout from 10s to 5s for faster failure
- Added `--skip-connection-test` flag to bypass checks entirely

**Impact:** ~20 seconds saved on repeat operations

### 2. **Repeated Excel File Loading**
**Problem:** Excel files were loaded from disk on every operation that needed school data.

**Solution:**
- Added caching check: skip reload if DataFrames already populated
- Added fast-fail: check file existence before attempting pandas load
- Better error messages for missing files

**Impact:** 1-2 seconds saved per operation after first load

### 3. **Unnecessary Delays**
**Problem:** 2-second delay (`page_load_delay`) before EVERY tool execution, even non-navigation tools.

**Solution:**
- Only apply delay to `browser_navigate` calls
- Skip delay for `browser_snapshot`, `browser_click`, etc.

**Impact:** 2 seconds saved per non-navigation tool call

### 4. **Slow Failure on Missing Data**
**Problem:** No fast-fail when Excel files missing - waited for pandas to fail.

**Solution:**
- Pre-check file existence with `Path.exists()`
- Immediate, clear error message

**Impact:** Instant failure vs. waiting for pandas exception

## Performance Improvements Summary

| Operation | Before | After | Savings |
|-----------|--------|-------|---------|
| First scrape (services down) | ~25s timeout | ~12s timeout | ~13s (50%) |
| Repeat scrape (cached) | ~25s timeout | ~2s | ~23s (92%) |
| Excel load (repeat) | ~1-2s | <0.01s | ~1-2s |
| Non-nav tool calls | 2s delay each | instant | 2s each |

## Usage Tips

### Fast Operation (Skip Connection Test)
```bash
# Skip connection testing for faster startup
python scraper.py --school "Art School" --skip-connection-test
```

### Batch Operations
For batch operations, connections are only tested once at the start.

### Recommended Settings

For slower/unreliable connections:
```yaml
scraping:
  page_load_delay: 3  # Increase if pages load slowly
```

For fast local development:
```yaml
scraping:
  page_load_delay: 1  # Faster when testing locally
```

## Technical Details

### Connection Test Caching
```python
# scraper.py:127
self._connections_tested = False  # Cache connection test results

# scraper.py:190-194
def test_connections(self, force: bool = False) -> bool:
    # Return cached result unless forced
    if self._connections_tested and not force:
        return True
```

### Excel File Caching
```python
# scraper.py:164-166
# Skip if already loaded
if self.art_schools_df is not None and self.admission_data_df is not None:
    return True, "Excel files already loaded"
```

### Smart Delays
```python
# scraper.py:473-477
# Only delay for navigation
if tool_name == "browser_navigate":
    delay = self.config['scraping']['page_load_delay']
    time.sleep(delay)
```

## Future Optimizations

Potential improvements not yet implemented:

1. **Async HTTP requests** - Use aiohttp for parallel connection testing
2. **Lazy loading** - Only load Excel rows that match search criteria
3. **Database caching** - Cache school data in SQLite instead of Excel
4. **Connection pooling** - Reuse MCP client connections across scrapes
5. **Parallel scraping** - Scrape multiple schools concurrently
6. **Incremental snapshots** - Only fetch changed page elements

## Monitoring Performance

To monitor performance in your environment:

```python
import time

start = time.time()
# Run scraper operation
duration = time.time() - start
print(f"Operation took {duration:.2f}s")
```

Enable verbose logging to see timing for each operation:
```yaml
scraping:
  verbose: true

logging:
  level: "DEBUG"
```
