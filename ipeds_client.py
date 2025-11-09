#!/usr/bin/env python3
"""
IPEDS (Integrated Postsecondary Education Data System) API Client

Fetches standardized college data from the federal IPEDS database.
All institutions receiving federal financial aid must report to IPEDS.
"""

import logging
import time
from typing import Dict, List, Optional, Tuple
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

logger = logging.getLogger(__name__)


class IPEDSClient:
    """Client for querying IPEDS data"""

    # College Scorecard API (easier to use than raw IPEDS)
    BASE_URL = "https://api.data.gov/ed/collegescorecard/v1"

    # No API key needed for basic queries, but recommended for production
    # Get free key at: https://api.data.gov/signup/

    def __init__(self, api_key: Optional[str] = None):
        """
        Initialize IPEDS client

        Args:
            api_key: Optional College Scorecard API key (recommended for production)
        """
        self.api_key = api_key
        self.session = self._create_session()

    def _create_session(self) -> requests.Session:
        """Create session with retry logic"""
        session = requests.Session()

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504]
        )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        session.mount("http://", adapter)
        session.mount("https://", adapter)

        return session

    def search_school(self, school_name: str) -> List[Dict]:
        """
        Search for school by name

        Args:
            school_name: Name of the school to search for

        Returns:
            List of matching schools with basic info
        """
        params = {
            "school.name": school_name,
            "fields": "id,school.name,school.city,school.state,school.school_url",
            "per_page": 20
        }

        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = self.session.get(
                f"{self.BASE_URL}/schools",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            return data.get("results", [])

        except Exception as e:
            logger.error(f"Error searching for school '{school_name}': {e}")
            return []

    def get_school_data(self, school_id: int, year: Optional[int] = None) -> Optional[Dict]:
        """
        Get detailed data for a specific school

        Args:
            school_id: IPEDS unit ID (UnitID)
            year: Optional year for data (default: latest)

        Returns:
            Dictionary with school data or None if not found
        """
        # Comprehensive field list
        fields = [
            # Basic info
            "id", "school.name", "school.city", "school.state",
            "school.school_url", "school.main_campus",

            # Admissions
            "latest.admissions.admission_rate.overall",
            "latest.admissions.sat_scores.25th_percentile.critical_reading",
            "latest.admissions.sat_scores.75th_percentile.critical_reading",
            "latest.admissions.sat_scores.25th_percentile.math",
            "latest.admissions.sat_scores.75th_percentile.math",
            "latest.admissions.sat_scores.midpoint.critical_reading",
            "latest.admissions.sat_scores.midpoint.math",
            "latest.admissions.act_scores.25th_percentile.cumulative",
            "latest.admissions.act_scores.75th_percentile.cumulative",
            "latest.admissions.act_scores.midpoint.cumulative",

            # Enrollment
            "latest.student.size",
            "latest.student.enrollment.all",
            "latest.student.enrollment.undergrad",

            # Costs
            "latest.cost.tuition.in_state",
            "latest.cost.tuition.out_of_state",
            "latest.cost.tuition.program_year",
            "latest.cost.attendance.academic_year",

            # Institutional characteristics
            "school.ownership",
            "school.Carnegie_size_setting",

            # Completion
            "latest.completion.completion_rate_4yr_150nt",
            "latest.completion.completion_rate_4yr_150nt_pooled",

            # Aid
            "latest.aid.median_debt.completers.overall",
            "latest.aid.students.federal_loan_rate"
        ]

        params = {
            "id": school_id,
            "fields": ",".join(fields)
        }

        if self.api_key:
            params["api_key"] = self.api_key

        try:
            response = self.session.get(
                f"{self.BASE_URL}/schools",
                params=params,
                timeout=30
            )
            response.raise_for_status()
            data = response.json()

            results = data.get("results", [])
            return results[0] if results else None

        except Exception as e:
            logger.error(f"Error fetching data for school ID {school_id}: {e}")
            return None

    def get_school_by_name(self, school_name: str) -> Optional[Dict]:
        """
        Search for school and get detailed data

        Args:
            school_name: Name of the school

        Returns:
            Dictionary with school data or None if not found
        """
        # Search for school
        matches = self.search_school(school_name)

        if not matches:
            logger.warning(f"No IPEDS data found for: {school_name}")
            return None

        # Use first match
        school = matches[0]
        school_id = school.get("id")

        if not school_id:
            return None

        # Get detailed data
        return self.get_school_data(school_id)

    def extract_standardized_data(self, ipeds_data: Dict) -> Dict:
        """
        Extract and normalize data to match our schema

        Args:
            ipeds_data: Raw IPEDS API response

        Returns:
            Standardized data dictionary
        """
        if not ipeds_data:
            return {}

        def safe_get(data: Dict, path: str, default=None):
            """Safely navigate nested dictionary"""
            keys = path.split(".")
            for key in keys:
                if isinstance(data, dict):
                    data = data.get(key)
                else:
                    return default
            return data if data is not None else default

        # Calculate SAT composite ranges
        sat_reading_25 = safe_get(ipeds_data, "latest.admissions.sat_scores.25th_percentile.critical_reading")
        sat_reading_75 = safe_get(ipeds_data, "latest.admissions.sat_scores.75th_percentile.critical_reading")
        sat_math_25 = safe_get(ipeds_data, "latest.admissions.sat_scores.25th_percentile.math")
        sat_math_75 = safe_get(ipeds_data, "latest.admissions.sat_scores.75th_percentile.math")

        sat_25 = None
        sat_75 = None
        sat_median = None

        if sat_reading_25 and sat_math_25:
            sat_25 = sat_reading_25 + sat_math_25
            sat_75 = (sat_reading_75 or 0) + (sat_math_75 or 0) if sat_reading_75 and sat_math_75 else None
            if sat_25 and sat_75:
                sat_median = int((sat_25 + sat_75) / 2)

        # Extract data
        result = {
            "school_info": {
                "ipeds_id": safe_get(ipeds_data, "id"),
                "name": safe_get(ipeds_data, "school.name"),
                "city": safe_get(ipeds_data, "school.city"),
                "state": safe_get(ipeds_data, "school.state"),
                "url": safe_get(ipeds_data, "school.school_url"),
                "ownership": safe_get(ipeds_data, "school.ownership")  # 1=Public, 2=Private nonprofit, 3=Private for-profit
            },
            "data": {
                "in_state_tuition": {
                    "value": safe_get(ipeds_data, "latest.cost.tuition.in_state"),
                    "formatted": f"${safe_get(ipeds_data, 'latest.cost.tuition.in_state', 0):,.0f}" if safe_get(ipeds_data, "latest.cost.tuition.in_state") else None,
                    "confidence": 0.98,
                    "source": "IPEDS College Scorecard API",
                    "source_url": "https://collegescorecard.ed.gov/",
                    "notes": "Federal data, annually updated"
                },
                "out_state_tuition": {
                    "value": safe_get(ipeds_data, "latest.cost.tuition.out_of_state"),
                    "formatted": f"${safe_get(ipeds_data, 'latest.cost.tuition.out_of_state', 0):,.0f}" if safe_get(ipeds_data, "latest.cost.tuition.out_of_state") else None,
                    "confidence": 0.98,
                    "source": "IPEDS College Scorecard API",
                    "source_url": "https://collegescorecard.ed.gov/",
                    "notes": "Federal data, annually updated"
                },
                "enrollment_size": {
                    "value": safe_get(ipeds_data, "latest.student.size"),
                    "formatted": f"{safe_get(ipeds_data, 'latest.student.size', 0):,}" if safe_get(ipeds_data, "latest.student.size") else None,
                    "confidence": 0.98,
                    "source": "IPEDS College Scorecard API",
                    "source_url": "https://collegescorecard.ed.gov/",
                    "notes": "Total student enrollment"
                },
                "admission_rate": {
                    "value": safe_get(ipeds_data, "latest.admissions.admission_rate.overall"),
                    "formatted": f"{safe_get(ipeds_data, 'latest.admissions.admission_rate.overall', 0) * 100:.1f}%" if safe_get(ipeds_data, "latest.admissions.admission_rate.overall") else None,
                    "confidence": 0.98,
                    "source": "IPEDS College Scorecard API",
                    "source_url": "https://collegescorecard.ed.gov/",
                    "notes": "Overall admission rate"
                },
                "sat_range": {
                    "value": f"{sat_25}-{sat_75}" if sat_25 and sat_75 else None,
                    "min": sat_25,
                    "max": sat_75,
                    "formatted": f"{sat_25}-{sat_75} (25th-75th percentile)" if sat_25 and sat_75 else None,
                    "confidence": 0.95,
                    "source": "IPEDS College Scorecard API",
                    "source_url": "https://collegescorecard.ed.gov/",
                    "notes": "SAT composite score range (Critical Reading + Math)"
                },
                "sat_median": {
                    "value": sat_median,
                    "formatted": str(sat_median) if sat_median else None,
                    "confidence": 0.95,
                    "source": "IPEDS College Scorecard API",
                    "source_url": "https://collegescorecard.ed.gov/",
                    "notes": "Calculated midpoint of 25th-75th percentile"
                },
                "act_range": {
                    "value": f"{safe_get(ipeds_data, 'latest.admissions.act_scores.25th_percentile.cumulative')}-{safe_get(ipeds_data, 'latest.admissions.act_scores.75th_percentile.cumulative')}" if safe_get(ipeds_data, "latest.admissions.act_scores.25th_percentile.cumulative") else None,
                    "min": safe_get(ipeds_data, "latest.admissions.act_scores.25th_percentile.cumulative"),
                    "max": safe_get(ipeds_data, "latest.admissions.act_scores.75th_percentile.cumulative"),
                    "formatted": f"{safe_get(ipeds_data, 'latest.admissions.act_scores.25th_percentile.cumulative')}-{safe_get(ipeds_data, 'latest.admissions.act_scores.75th_percentile.cumulative')} (25th-75th percentile)" if safe_get(ipeds_data, "latest.admissions.act_scores.25th_percentile.cumulative") else None,
                    "confidence": 0.95,
                    "source": "IPEDS College Scorecard API",
                    "source_url": "https://collegescorecard.ed.gov/",
                    "notes": "ACT composite score range"
                },
                "act_median": {
                    "value": safe_get(ipeds_data, "latest.admissions.act_scores.midpoint.cumulative"),
                    "formatted": str(safe_get(ipeds_data, "latest.admissions.act_scores.midpoint.cumulative")) if safe_get(ipeds_data, "latest.admissions.act_scores.midpoint.cumulative") else None,
                    "confidence": 0.95,
                    "source": "IPEDS College Scorecard API",
                    "source_url": "https://collegescorecard.ed.gov/",
                    "notes": "ACT midpoint score"
                }
            },
            "source": "ipeds",
            "data_year": "latest"
        }

        return result


def test_ipeds_client():
    """Test the IPEDS client"""
    print("Testing IPEDS Client...")
    print("=" * 60)

    client = IPEDSClient()

    # Test search
    print("\n1. Searching for 'University of Michigan'...")
    results = client.search_school("University of Michigan")
    print(f"Found {len(results)} results")
    if results:
        print(f"First match: {results[0].get('school.name')}")
        print(f"IPEDS ID: {results[0].get('id')}")

    # Test full data fetch
    print("\n2. Fetching full data...")
    data = client.get_school_by_name("University of Michigan-Ann Arbor")
    if data:
        print("Successfully fetched data")

        # Extract standardized data
        print("\n3. Extracting standardized data...")
        standardized = client.extract_standardized_data(data)

        print(f"\nSchool: {standardized['school_info']['name']}")
        print(f"Location: {standardized['school_info']['city']}, {standardized['school_info']['state']}")
        print(f"\nAdmissions Data:")
        print(f"  Admission Rate: {standardized['data']['admission_rate']['formatted']}")
        print(f"  SAT Range: {standardized['data']['sat_range']['formatted']}")
        print(f"  ACT Range: {standardized['data']['act_range']['formatted']}")
        print(f"\nCost Data:")
        print(f"  In-State Tuition: {standardized['data']['in_state_tuition']['formatted']}")
        print(f"  Out-of-State Tuition: {standardized['data']['out_state_tuition']['formatted']}")
        print(f"\nEnrollment: {standardized['data']['enrollment_size']['formatted']}")

    print("\n" + "=" * 60)
    print("Test complete!")


if __name__ == "__main__":
    test_ipeds_client()
