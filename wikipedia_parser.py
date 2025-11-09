#!/usr/bin/env python3
"""
Wikipedia Infobox Parser

Extracts structured data from Wikipedia college/university infoboxes.
Surprisingly reliable for basic statistics.
"""

import logging
import re
from typing import Dict, Optional
import requests

logger = logging.getLogger(__name__)


class WikipediaParser:
    """Parser for Wikipedia college data"""

    API_URL = "https://en.wikipedia.org/w/api.php"

    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'CollegeScraper/1.0 (Educational Research)'
        })

    def search_page(self, school_name: str) -> Optional[str]:
        """
        Search for Wikipedia page by school name

        Args:
            school_name: Name of the school

        Returns:
            Page title if found, None otherwise
        """
        params = {
            "action": "query",
            "list": "search",
            "srsearch": school_name,
            "format": "json",
            "srlimit": 5
        }

        try:
            response = self.session.get(self.API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            results = data.get("query", {}).get("search", [])
            if results:
                return results[0]["title"]

            return None

        except Exception as e:
            logger.error(f"Error searching Wikipedia for '{school_name}': {e}")
            return None

    def get_page_content(self, page_title: str) -> Optional[str]:
        """
        Get Wikipedia page content

        Args:
            page_title: Wikipedia page title

        Returns:
            Page wikitext content
        """
        params = {
            "action": "query",
            "titles": page_title,
            "prop": "revisions",
            "rvprop": "content",
            "format": "json",
            "rvslots": "main"
        }

        try:
            response = self.session.get(self.API_URL, params=params, timeout=10)
            response.raise_for_status()
            data = response.json()

            pages = data.get("query", {}).get("pages", {})
            page = next(iter(pages.values()))

            if "revisions" in page:
                return page["revisions"][0]["slots"]["main"]["*"]

            return None

        except Exception as e:
            logger.error(f"Error fetching Wikipedia page '{page_title}': {e}")
            return None

    def extract_infobox(self, wikitext: str) -> Dict[str, str]:
        """
        Extract infobox data from wikitext

        Args:
            wikitext: Wikipedia page wikitext

        Returns:
            Dictionary of infobox fields
        """
        infobox = {}

        # Find infobox
        infobox_pattern = r'\{\{Infobox [Uu]niversity(.*?)\n\}\}'
        match = re.search(infobox_pattern, wikitext, re.DOTALL)

        if not match:
            return infobox

        infobox_text = match.group(1)

        # Extract fields
        # Pattern: | field = value
        field_pattern = r'\|\s*([^=\n]+?)\s*=\s*([^\n]+)'
        matches = re.finditer(field_pattern, infobox_text)

        for match in matches:
            field = match.group(1).strip()
            value = match.group(2).strip()

            # Clean value (remove wiki markup)
            value = self._clean_value(value)

            infobox[field] = value

        return infobox

    def _clean_value(self, value: str) -> str:
        """Clean Wikipedia markup from value"""
        # Remove references
        value = re.sub(r'<ref[^>]*>.*?</ref>', '', value, flags=re.DOTALL)
        value = re.sub(r'<ref[^/>]*/?>', '', value)

        # Remove HTML comments
        value = re.sub(r'<!--.*?-->', '', value, flags=re.DOTALL)

        # Extract from links [[Link|Text]] -> Text
        value = re.sub(r'\[\[(?:[^|\]]*\|)?([^\]]+)\]\]', r'\1', value)

        # Remove formatting
        value = re.sub(r"'''([^']+)'''", r'\1', value)  # Bold
        value = re.sub(r"''([^']+)''", r'\1', value)    # Italic

        # Remove templates (simplified)
        value = re.sub(r'\{\{[^}]+\}\}', '', value)

        return value.strip()

    def parse_number(self, value: str) -> Optional[float]:
        """Parse number from string with commas, etc."""
        if not value:
            return None

        # Remove non-numeric characters except decimal point
        cleaned = re.sub(r'[^\d.]', '', value)

        try:
            return float(cleaned)
        except ValueError:
            return None

    def parse_percentage(self, value: str) -> Optional[float]:
        """Parse percentage from string"""
        if not value:
            return None

        # Extract number
        match = re.search(r'([\d.]+)%?', value)
        if match:
            try:
                num = float(match.group(1))
                # Convert to decimal if it looks like a percentage
                if num > 1:
                    num = num / 100
                return num
            except ValueError:
                pass

        return None

    def extract_standardized_data(self, page_title: str, infobox: Dict) -> Dict:
        """
        Extract and normalize data to match our schema

        Args:
            page_title: Wikipedia page title
            infobox: Parsed infobox dictionary

        Returns:
            Standardized data dictionary
        """
        page_url = f"https://en.wikipedia.org/wiki/{page_title.replace(' ', '_')}"

        # Map common field variations
        enrollment = (
            infobox.get('students') or
            infobox.get('enrollment') or
            infobox.get('undergrad')
        )

        tuition = infobox.get('tuition') or infobox.get('annual_tuition')

        # Try to extract tuition for in-state vs out-of-state
        in_state_tuition = None
        out_state_tuition = None

        if tuition:
            # Check if tuition string contains both in-state and out-of-state
            in_state_match = re.search(r'(?:in-state|resident)[^\d]*([\d,]+)', tuition, re.IGNORECASE)
            out_state_match = re.search(r'(?:out-of-state|non-resident)[^\d]*([\d,]+)', tuition, re.IGNORECASE)

            if in_state_match:
                in_state_tuition = self.parse_number(in_state_match.group(1))
            if out_state_match:
                out_state_tuition = self.parse_number(out_state_match.group(1))

        result = {
            "school_info": {
                "name": infobox.get('name', page_title),
                "url": infobox.get('website') or page_url,
                "location": infobox.get('city'),
                "state": infobox.get('state'),
                "founded": infobox.get('established')
            },
            "data": {
                "in_state_tuition": {
                    "value": in_state_tuition,
                    "formatted": f"${in_state_tuition:,.0f}" if in_state_tuition else None,
                    "confidence": 0.70,
                    "source": "Wikipedia",
                    "source_url": page_url,
                    "notes": "Extracted from Wikipedia infobox, verify with official source"
                },
                "out_state_tuition": {
                    "value": out_state_tuition,
                    "formatted": f"${out_state_tuition:,.0f}" if out_state_tuition else None,
                    "confidence": 0.70,
                    "source": "Wikipedia",
                    "source_url": page_url,
                    "notes": "Extracted from Wikipedia infobox, verify with official source"
                },
                "enrollment_size": {
                    "value": self.parse_number(enrollment) if enrollment else None,
                    "formatted": f"{self.parse_number(enrollment):,.0f}" if enrollment and self.parse_number(enrollment) else None,
                    "confidence": 0.75,
                    "source": "Wikipedia",
                    "source_url": page_url,
                    "notes": "Total enrollment from Wikipedia infobox"
                },
                "admission_rate": {
                    "value": self.parse_percentage(infobox.get('admissions')),
                    "formatted": f"{self.parse_percentage(infobox.get('admissions')) * 100:.1f}%" if self.parse_percentage(infobox.get('admissions')) else None,
                    "confidence": 0.70,
                    "source": "Wikipedia",
                    "source_url": page_url,
                    "notes": "Admission rate from Wikipedia infobox"
                }
            },
            "source": "wikipedia",
            "wikipedia_url": page_url
        }

        return result

    def get_school_data(self, school_name: str) -> Optional[Dict]:
        """
        Get school data from Wikipedia

        Args:
            school_name: Name of the school

        Returns:
            Standardized data dictionary or None
        """
        # Search for page
        page_title = self.search_page(school_name)
        if not page_title:
            logger.warning(f"No Wikipedia page found for: {school_name}")
            return None

        logger.info(f"Found Wikipedia page: {page_title}")

        # Get content
        content = self.get_page_content(page_title)
        if not content:
            return None

        # Extract infobox
        infobox = self.extract_infobox(content)
        if not infobox:
            logger.warning(f"No infobox found on page: {page_title}")
            return None

        # Standardize data
        return self.extract_standardized_data(page_title, infobox)


def test_wikipedia_parser():
    """Test the Wikipedia parser"""
    print("Testing Wikipedia Parser...")
    print("=" * 60)

    parser = WikipediaParser()

    schools = [
        "University of Michigan",
        "Rhode Island School of Design",
        "California Institute of the Arts"
    ]

    for school in schools:
        print(f"\nTesting: {school}")
        print("-" * 60)

        data = parser.get_school_data(school)

        if data:
            print(f"✓ Found data")
            print(f"  Name: {data['school_info']['name']}")
            print(f"  Enrollment: {data['data']['enrollment_size']['formatted']}")
            print(f"  Admission Rate: {data['data']['admission_rate']['formatted']}")
            print(f"  URL: {data['wikipedia_url']}")
        else:
            print(f"✗ No data found")

    print("\n" + "=" * 60)
    print("Test complete!")


if __name__ == "__main__":
    test_wikipedia_parser()
