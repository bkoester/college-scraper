# Data Directory

Place your Excel files here:

## Required Files

1. **art_schools_final.xlsx**
   - Contains list of art schools with URLs
   - Expected columns:
     - School Name
     - Location
     - Webpage
     - Type
     - Est. Tuition (Per Year)
     - Approx. Size
     - In-State
     - Out-State
     - Private/Other

2. **School_Admission_Data_FINAL.xlsx**
   - Contains admission statistics
   - Expected columns:
     - School Name
     - Admission Rate
     - Yield Rate
     - SAT Range (25th-75th percentile)
     - Median/Average SAT
     - ACT Range (25th-75th percentile)
     - Median/Average ACT
     - Notes

## File Format

Both files should be:
- Excel format (.xlsx)
- First row contains column headers
- School names should match between files

## Example

```
data/
├── art_schools_final.xlsx          # Your file here
├── School_Admission_Data_FINAL.xlsx # Your file here
└── README.md                        # This file
```

## Usage

Once files are in place, run:

```bash
# List schools from your Excel files
python scraper.py --list

# Scrape a school
python scraper.py --school "School Name"
```
