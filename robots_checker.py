#!/usr/bin/env python3
"""
robots.txt Checker

Verifies if scraping is allowed per robots.txt before accessing sites.
Use this to be respectful and compliant with site policies.
"""

import logging
from urllib.parse import urlparse, urljoin
from urllib.robotparser import RobotFileParser
import requests

logger = logging.getLogger(__name__)


class RobotsChecker:
    """Check robots.txt compliance before scraping"""

    def __init__(self, user_agent: str = "CollegeScraper/1.0"):
        """
        Initialize robots checker

        Args:
            user_agent: User agent to identify as
        """
        self.user_agent = user_agent
        self.parsers = {}  # Cache robots.txt parsers by domain

    def can_fetch(self, url: str) -> tuple[bool, str]:
        """
        Check if URL can be fetched according to robots.txt

        Args:
            url: URL to check

        Returns:
            Tuple of (allowed: bool, reason: str)
        """
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        # Get or create parser for this domain
        if domain not in self.parsers:
            parser = RobotFileParser()
            robots_url = urljoin(domain, '/robots.txt')

            try:
                # Fetch robots.txt
                response = requests.get(robots_url, timeout=10)
                if response.status_code == 200:
                    parser.parse(response.text.splitlines())
                    self.parsers[domain] = parser
                    logger.info(f"Loaded robots.txt from {robots_url}")
                else:
                    # No robots.txt or error - assume allowed
                    logger.info(f"No robots.txt found at {robots_url} (status {response.status_code})")
                    self.parsers[domain] = None
            except Exception as e:
                logger.warning(f"Error fetching robots.txt from {robots_url}: {e}")
                self.parsers[domain] = None

        parser = self.parsers[domain]

        # If no robots.txt, allow
        if parser is None:
            return True, "No robots.txt found (allowed by default)"

        # Check if allowed
        allowed = parser.can_fetch(self.user_agent, url)

        if allowed:
            return True, "Allowed by robots.txt"
        else:
            return False, f"Disallowed by robots.txt for user-agent '{self.user_agent}'"

    def get_crawl_delay(self, url: str) -> float:
        """
        Get recommended crawl delay from robots.txt

        Args:
            url: URL to check

        Returns:
            Crawl delay in seconds (0 if not specified)
        """
        parsed = urlparse(url)
        domain = f"{parsed.scheme}://{parsed.netloc}"

        parser = self.parsers.get(domain)
        if parser is None:
            return 0.0

        try:
            delay = parser.crawl_delay(self.user_agent)
            return float(delay) if delay else 0.0
        except:
            return 0.0


def test_robots_checker():
    """Test the robots checker with some URLs"""
    checker = RobotsChecker(user_agent="CollegeScraper/1.0")

    test_urls = [
        "https://stamps.umich.edu/",
        "https://en.wikipedia.org/wiki/University_of_Michigan",
        "https://www.risd.edu/",
    ]

    print("Testing robots.txt compliance:")
    print("=" * 60)

    for url in test_urls:
        print(f"\nURL: {url}")
        allowed, reason = checker.can_fetch(url)
        delay = checker.get_crawl_delay(url)

        print(f"  Allowed: {'✓' if allowed else '✗'}")
        print(f"  Reason: {reason}")
        if delay > 0:
            print(f"  Recommended delay: {delay}s")

    print("\n" + "=" * 60)


if __name__ == "__main__":
    test_robots_checker()
