#!/usr/bin/env python3
"""
Multi-Source Data Collector

Combines data from multiple sources:
1. IPEDS (federal database) - Most reliable
2. School Website (via AI agent) - Most current
3. Wikipedia - Good for validation

Uses confidence-weighted merging to produce best results.
"""

import argparse
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional
import sys

import pandas as pd
import yaml
from rich.console import Console
from rich.table import Table
from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TaskProgressColumn

from ipeds_client import IPEDSClient
from wikipedia_parser import WikipediaParser

console = Console()


class MultiSourceCollector:
    """Collects and merges data from multiple sources"""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize collector"""
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()

        # Initialize clients
        self.ipeds_client = IPEDSClient()
        self.wikipedia_parser = WikipediaParser()

        # Load Excel files
        self.art_schools_df = None
        self.admission_data_df = None

    def _load_config(self) -> Dict:
        """Load configuration"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            console.print(f"[red]Error: Config file not found: {self.config_path}[/red]")
            sys.exit(1)

    def _setup_logging(self):
        """Setup logging"""
        log_config = self.config.get('logging', {})
        level = getattr(logging, log_config.get('level', 'INFO'))

        logging.basicConfig(
            level=level,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        )
        self.logger = logging.getLogger(__name__)

    def load_excel_files(self):
        """Load Excel files"""
        try:
            art_schools_path = self.config['input']['art_schools_file']
            admission_data_path = self.config['input']['admission_data_file']

            self.art_schools_df = pd.read_excel(art_schools_path)
            self.admission_data_df = pd.read_excel(admission_data_path)

            self.logger.info(f"Loaded {len(self.art_schools_df)} schools from {art_schools_path}")

        except FileNotFoundError as e:
            console.print(f"[red]Error: Excel file not found: {e.filename}[/red]")
            sys.exit(1)

    def collect_from_all_sources(self, school_name: str) -> Dict:
        """
        Collect data from all available sources

        Args:
            school_name: Name of the school

        Returns:
            Dictionary with data from all sources
        """
        results = {
            "school_name": school_name,
            "collected_at": datetime.now().isoformat(),
            "sources": {}
        }

        # Get school info from Excel
        school_info = self._get_school_info(school_name)
        if school_info:
            results["school_url"] = school_info.get('Webpage')
            results["school_location"] = school_info.get('Location')

        console.print(f"\n[bold cyan]Collecting data for: {school_name}[/bold cyan]")

        # Source 1: IPEDS
        console.print("\n[blue]1. Querying IPEDS database...[/blue]")
        try:
            ipeds_data = self.ipeds_client.get_school_by_name(school_name)
            if ipeds_data:
                standardized = self.ipeds_client.extract_standardized_data(ipeds_data)
                results["sources"]["ipeds"] = standardized
                console.print("  [green]✓[/green] IPEDS data collected")
                self._print_source_summary("IPEDS", standardized)
            else:
                console.print("  [yellow]⚠[/yellow] No IPEDS data found")
                results["sources"]["ipeds"] = None
        except Exception as e:
            console.print(f"  [red]✗[/red] IPEDS error: {e}")
            results["sources"]["ipeds"] = None

        # Source 2: Wikipedia
        console.print("\n[blue]2. Checking Wikipedia...[/blue]")
        try:
            wiki_data = self.wikipedia_parser.get_school_data(school_name)
            if wiki_data:
                results["sources"]["wikipedia"] = wiki_data
                console.print("  [green]✓[/green] Wikipedia data collected")
                self._print_source_summary("Wikipedia", wiki_data)
            else:
                console.print("  [yellow]⚠[/yellow] No Wikipedia data found")
                results["sources"]["wikipedia"] = None
        except Exception as e:
            console.print(f"  [red]✗[/red] Wikipedia error: {e}")
            results["sources"]["wikipedia"] = None

        # Source 3: Web scraping (placeholder)
        console.print("\n[blue]3. Web scraping (via AI agent)...[/blue]")
        console.print("  [yellow]⚠[/yellow] Use scraper.py for web scraping")
        results["sources"]["web_scraping"] = None

        return results

    def _get_school_info(self, school_name: str) -> Optional[Dict]:
        """Get school info from Excel"""
        if self.art_schools_df is None:
            self.load_excel_files()

        matches = self.art_schools_df[
            self.art_schools_df['School Name'].str.contains(school_name, case=False, na=False)
        ]

        if not matches.empty:
            return matches.iloc[0].to_dict()

        return None

    def _print_source_summary(self, source_name: str, data: Dict):
        """Print summary of data from a source"""
        if not data or 'data' not in data:
            return

        found_fields = []
        for field, info in data['data'].items():
            if info and info.get('value') is not None:
                confidence = info.get('confidence', 0)
                found_fields.append(f"{field} ({confidence:.0%})")

        if found_fields:
            console.print(f"    Found: {', '.join(found_fields[:3])}{'...' if len(found_fields) > 3 else ''}")

    def merge_data(self, multi_source_data: Dict) -> Dict:
        """
        Merge data from multiple sources using confidence-weighted selection

        Args:
            multi_source_data: Data from collect_from_all_sources()

        Returns:
            Merged data dictionary
        """
        sources = multi_source_data.get("sources", {})

        # Initialize merged data
        merged = {
            "school_name": multi_source_data["school_name"],
            "collected_at": multi_source_data["collected_at"],
            "data": {},
            "sources_used": {}
        }

        # Fields to merge
        fields = [
            "in_state_tuition",
            "out_state_tuition",
            "private_tuition",
            "enrollment_size",
            "admission_rate",
            "yield_rate",
            "sat_range",
            "sat_median",
            "act_range",
            "act_median"
        ]

        # For each field, pick the best source
        for field in fields:
            best_value = None
            best_confidence = 0
            best_source = None

            # Check all sources
            for source_name, source_data in sources.items():
                if not source_data or 'data' not in source_data:
                    continue

                field_data = source_data['data'].get(field)
                if not field_data:
                    continue

                value = field_data.get('value')
                confidence = field_data.get('confidence', 0)

                if value is not None and confidence > best_confidence:
                    best_value = field_data
                    best_confidence = confidence
                    best_source = source_name

            # Store best value
            if best_value:
                merged["data"][field] = best_value
                merged["sources_used"][field] = best_source

        return merged

    def save_results(self, results: Dict, merged: Dict):
        """Save multi-source results"""
        output_dir = Path(self.config['output']['directory'])
        output_dir.mkdir(parents=True, exist_ok=True)

        school_name = results['school_name']
        safe_name = "".join(c for c in school_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_').lower()
        date_str = datetime.now().strftime('%Y-%m-%d')

        # Save raw multi-source data
        raw_path = output_dir / f"{safe_name}_multisource_{date_str}.json"
        with open(raw_path, 'w') as f:
            json.dump(results, f, indent=2)
        console.print(f"\n[green]Raw data saved to:[/green] {raw_path}")

        # Save merged data
        merged_path = output_dir / f"{safe_name}_merged_{date_str}.json"
        with open(merged_path, 'w') as f:
            json.dump(merged, f, indent=2)
        console.print(f"[green]Merged data saved to:[/green] {merged_path}")

        # Print summary
        self._print_merge_summary(merged)

    def _print_merge_summary(self, merged: Dict):
        """Print summary of merged data"""
        console.print("\n[bold]Merged Data Summary:[/bold]")

        table = Table(show_header=True, header_style="bold cyan")
        table.add_column("Field", style="cyan")
        table.add_column("Value", style="green")
        table.add_column("Source", style="yellow")
        table.add_column("Confidence", style="magenta")

        for field, value in merged['data'].items():
            source = merged['sources_used'].get(field, 'unknown')
            confidence = value.get('confidence', 0)
            formatted = value.get('formatted', str(value.get('value')))

            table.add_row(
                field,
                formatted or 'N/A',
                source,
                f"{confidence:.0%}"
            )

        console.print(table)

    def batch_collect(self, school_names: List[str]):
        """Collect data for multiple schools"""
        console.print(f"\n[bold]Collecting data for {len(school_names)} schools...[/bold]")

        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            console=console
        ) as progress:
            task = progress.add_task("[cyan]Processing schools...", total=len(school_names))

            for school in school_names:
                progress.update(task, description=f"[cyan]Processing {school}...")

                # Collect data
                results = self.collect_from_all_sources(school)

                # Merge data
                merged = self.merge_data(results)

                # Save results
                self.save_results(results, merged)

                progress.advance(task)

        console.print("\n[bold green]Batch collection complete![/bold green]")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Multi-Source Data Collector - Collect from IPEDS, Wikipedia, and Web",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--school', type=str, help='School name to collect data for')
    parser.add_argument('--all', action='store_true', help='Collect data for all schools in Excel')
    parser.add_argument('--batch', type=str, help='File with list of school names (one per line)')
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to config file')
    parser.add_argument('--test', action='store_true', help='Test all data sources')

    args = parser.parse_args()

    # Create collector
    collector = MultiSourceCollector(config_path=args.config)

    if args.test:
        # Test each source
        console.print("[bold]Testing data sources...[/bold]")

        console.print("\n1. Testing IPEDS...")
        ipeds_data = collector.ipeds_client.get_school_by_name("University of Michigan")
        if ipeds_data:
            console.print("  [green]✓[/green] IPEDS working")
        else:
            console.print("  [red]✗[/red] IPEDS failed")

        console.print("\n2. Testing Wikipedia...")
        wiki_data = collector.wikipedia_parser.get_school_data("University of Michigan")
        if wiki_data:
            console.print("  [green]✓[/green] Wikipedia working")
        else:
            console.print("  [red]✗[/red] Wikipedia failed")

        console.print("\n[green]Testing complete![/green]")

    elif args.school:
        # Collect for single school
        results = collector.collect_from_all_sources(args.school)
        merged = collector.merge_data(results)
        collector.save_results(results, merged)

    elif args.all:
        # Collect for all schools
        collector.load_excel_files()
        school_names = collector.art_schools_df['School Name'].tolist()
        collector.batch_collect(school_names)

    elif args.batch:
        # Collect from file
        with open(args.batch, 'r') as f:
            school_names = [line.strip() for line in f if line.strip()]
        collector.batch_collect(school_names)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
