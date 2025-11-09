#!/usr/bin/env python3
"""
Art School Web Scraper
Uses Ollama (local AI) and MCP Server (Playwright) to intelligently extract data from university websites.
"""

import argparse
import json
import logging
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
import requests
import yaml
from rich.console import Console
from rich.logging import RichHandler
from rich.progress import Progress, SpinnerColumn, TextColumn
from rich.table import Table

from mcp_client import MCPClient

console = Console()

# MCP Tools Definition
MCP_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "browser_navigate",
            "description": "Navigate the browser to a specific URL and wait for page load",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {
                        "type": "string",
                        "description": "The URL to navigate to (must be absolute)"
                    }
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_snapshot",
            "description": "Get the page accessibility tree (structured text representation of the page). This is the BEST tool for extracting data from web pages.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_click",
            "description": "Click an element on the page",
            "parameters": {
                "type": "object",
                "properties": {
                    "selector": {
                        "type": "string",
                        "description": "CSS selector for the element to click"
                    }
                },
                "required": ["selector"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_evaluate",
            "description": "Execute JavaScript in the browser context",
            "parameters": {
                "type": "object",
                "properties": {
                    "script": {
                        "type": "string",
                        "description": "JavaScript code to execute"
                    }
                },
                "required": ["script"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "browser_wait_for",
            "description": "Wait for a specific condition or time",
            "parameters": {
                "type": "object",
                "properties": {
                    "text": {
                        "type": "string",
                        "description": "Text to wait for (optional)"
                    },
                    "timeout": {
                        "type": "number",
                        "description": "Timeout in milliseconds (default 3000)"
                    }
                }
            }
        }
    }
]


class ArtSchoolScraper:
    """Main scraper application"""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize the scraper with configuration"""
        self.config_path = config_path
        self.config = self._load_config()
        self._setup_logging()
        self.art_schools_df = None
        self.admission_data_df = None
        self.session = requests.Session()
        self.mcp_client = None  # Will be initialized when needed

    def _load_config(self) -> Dict:
        """Load configuration from YAML file"""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except FileNotFoundError:
            console.print(f"[red]Error: Config file not found: {self.config_path}[/red]")
            sys.exit(1)
        except yaml.YAMLError as e:
            console.print(f"[red]Error parsing config file: {e}[/red]")
            sys.exit(1)

    def _setup_logging(self):
        """Setup logging configuration"""
        log_config = self.config.get('logging', {})
        level = getattr(logging, log_config.get('level', 'INFO'))

        handlers = []
        if log_config.get('console_output', True):
            handlers.append(RichHandler(rich_tracebacks=True, console=console))

        if log_config.get('save_logs', True):
            log_file = log_config.get('log_file', 'logs/scraper.log')
            Path(log_file).parent.mkdir(parents=True, exist_ok=True)
            handlers.append(logging.FileHandler(log_file))

        logging.basicConfig(
            level=level,
            format="%(message)s",
            handlers=handlers
        )
        self.logger = logging.getLogger(__name__)

    def load_excel_files(self) -> Tuple[bool, str]:
        """Load both Excel files into DataFrames"""
        try:
            art_schools_path = self.config['input']['art_schools_file']
            admission_data_path = self.config['input']['admission_data_file']

            self.art_schools_df = pd.read_excel(art_schools_path)
            self.admission_data_df = pd.read_excel(admission_data_path)

            self.logger.info(f"Loaded {len(self.art_schools_df)} schools from {art_schools_path}")
            self.logger.info(f"Loaded {len(self.admission_data_df)} schools from {admission_data_path}")

            return True, "Excel files loaded successfully"
        except FileNotFoundError as e:
            return False, f"Excel file not found: {e.filename}"
        except Exception as e:
            return False, f"Error loading Excel files: {str(e)}"

    def test_connections(self) -> bool:
        """Test connections to Ollama and MCP server"""
        all_ok = True

        # Test Ollama
        console.print("\n[bold]Testing Ollama connection...[/bold]")
        try:
            ollama_url = f"{self.config['ollama']['base_url']}/api/tags"
            response = self.session.get(ollama_url, timeout=10)
            if response.status_code == 200:
                models = response.json().get('models', [])
                console.print(f"  [green]✓[/green] Ollama connected")
                console.print(f"  Available models: {', '.join([m['name'] for m in models])}")

                # Check if configured model exists
                target_model = self.config['ollama']['model']
                if not any(m['name'] == target_model for m in models):
                    console.print(f"  [yellow]⚠[/yellow] Model '{target_model}' not found")
                    console.print(f"  Run: docker exec -it art-scraper-ollama ollama pull {target_model}")
                    all_ok = False
            else:
                console.print(f"  [red]✗[/red] Ollama responded with status {response.status_code}")
                all_ok = False
        except Exception as e:
            console.print(f"  [red]✗[/red] Cannot connect to Ollama: {e}")
            console.print(f"  Make sure Docker is running: docker-compose up -d")
            all_ok = False

        # Test MCP Server
        console.print("\n[bold]Testing MCP Server connection...[/bold]")
        try:
            mcp_config = self.config.get('mcp', {})
            base_url = mcp_config.get('base_url', 'http://localhost:8931/sse')

            # Try to initialize MCP client
            test_client = MCPClient(base_url=base_url, timeout=10)
            result = test_client.initialize()

            console.print(f"  [green]✓[/green] MCP Server connected")
            server_info = result.get('result', {}).get('serverInfo', {})
            if server_info:
                console.print(f"  Server: {server_info.get('name', 'Unknown')} v{server_info.get('version', '?')}")

            # List tools
            tools = test_client.list_tools()
            console.print(f"  Available tools: {len(tools)}")

            test_client.close()

        except Exception as e:
            console.print(f"  [red]✗[/red] Cannot connect to MCP Server: {e}")
            console.print(f"  Make sure MCP server is running: docker-compose up -d mcp-server")
            console.print(f"  Check logs: docker-compose logs mcp-server")
            all_ok = False

        return all_ok

    def list_schools(self):
        """Display list of all available schools"""
        if self.art_schools_df is None:
            success, message = self.load_excel_files()
            if not success:
                console.print(f"[red]Error: {message}[/red]")
                return

        table = Table(title="Available Schools", show_lines=True)
        table.add_column("School Name", style="cyan")
        table.add_column("Location", style="green")
        table.add_column("Type", style="yellow")
        table.add_column("URL", style="blue", overflow="fold")

        for _, row in self.art_schools_df.iterrows():
            table.add_row(
                str(row.get('School Name', 'N/A')),
                str(row.get('Location', 'N/A')),
                str(row.get('Type', 'N/A')),
                str(row.get('Webpage', 'N/A'))
            )

        console.print(table)

    def show_fields(self):
        """Display fields that will be extracted"""
        fields = self.config['fields_to_extract']

        table = Table(title="Data Fields to Extract", show_lines=True)
        table.add_column("Field Name", style="cyan")
        table.add_column("Excel Column", style="green")
        table.add_column("Data Type", style="yellow")
        table.add_column("Keywords", style="blue", overflow="fold")

        for field in fields:
            keywords = ", ".join(field['keywords'][:3]) + "..."
            table.add_row(
                field['name'],
                field['column'],
                field['data_type'],
                keywords
            )

        console.print(table)

    def find_school(self, school_name: str) -> Optional[Dict]:
        """Find school information by name"""
        if self.art_schools_df is None:
            success, message = self.load_excel_files()
            if not success:
                return None

        # Try exact match first
        matches = self.art_schools_df[
            self.art_schools_df['School Name'].str.lower() == school_name.lower()
        ]

        # Try partial match if no exact match
        if matches.empty:
            matches = self.art_schools_df[
                self.art_schools_df['School Name'].str.contains(school_name, case=False, na=False)
            ]

        if matches.empty:
            return None

        if len(matches) > 1:
            console.print(f"[yellow]Multiple matches found. Using first match.[/yellow]")

        school_data = matches.iloc[0].to_dict()

        # Also get admission data if available
        admission_matches = self.admission_data_df[
            self.admission_data_df['School Name'].str.lower() == school_data['School Name'].lower()
        ]

        if not admission_matches.empty:
            admission_data = admission_matches.iloc[0].to_dict()
            school_data['admission_data'] = admission_data

        return school_data

    def create_system_prompt(self, school_info: Dict) -> str:
        """Create the system prompt for Ollama"""
        school_name = school_info['School Name']
        url = school_info['Webpage']
        fields = self.config['fields_to_extract']

        fields_description = "\n".join([
            f"- {field['name']} ({field['data_type']}): Look for {', '.join(field['keywords'][:3])}"
            for field in fields
        ])

        prompt = f"""You are an intelligent web scraping agent. Your task is to extract specific information from university websites using browser automation tools.

TARGET: {school_name}
STARTING URL: {url}

MISSION: Extract the following information:
{fields_description}

PRIORITY STRATEGY - COMMON DATA SET (CDS) FIRST:
1. Start by navigating to the school's homepage
2. Use browser_snapshot to see the page structure
3. **HIGHEST PRIORITY**: Look for "Common Data Set" link/page:
   - Search for links containing: "Common Data Set", "CDS", "Institutional Research", "Fast Facts"
   - Common patterns: /common-data-set, /institutional-research, /ir, /about/facts
   - CDS is a standardized report with ALL the data you need in consistent format
   - Section C of CDS has admissions data, Section H has tuition
   - If you find CDS (PDF or Excel), prioritize extracting from there

SECONDARY STRATEGY - DEDICATED PAGES:
4. If no CDS found, look for dedicated sections:
   - Admissions Statistics, Facts, Profile
   - Tuition & Fees, Cost of Attendance
   - About, Facts & Figures, At a Glance
5. Navigate to promising pages using browser_click or browser_navigate
6. Extract the requested data from each page

FALLBACK STRATEGY:
7. If you can't find something, try:
   - Search functionality (search for "tuition" or "admission rate")
   - Site map or footer links
   - Institutional Research office pages
   - About/Facts pages
8. Return all findings in structured JSON format

AVAILABLE TOOLS:
- browser_navigate(url): Go to a URL
- browser_snapshot(): Get page structure as text (BEST for data extraction)
- browser_click(selector): Click an element
- browser_evaluate(script): Run JavaScript
- browser_wait_for(text, timeout): Wait for content

IMPORTANT GUIDELINES:
- Use browser_snapshot extensively - it's perfect for extracting data
- Always provide confidence scores (0.0 to 1.0):
  * 0.95+: Found on official page with clear labels
  * 0.85-0.94: Found with good context but some ambiguity
  * 0.70-0.84: Inferred from related information
  * 0.50-0.69: Uncertain, needs verification
  * <0.50: Don't include
- Include source URLs for all data
- Note if data appears outdated
- Be thorough but efficient - you have 5 minutes max
- Wait 2-3 seconds between page navigations

FINAL RESPONSE FORMAT:
Return ONLY valid JSON in this exact structure:
{{
  "data": {{
    "field_name": {{
      "value": <extracted_value>,
      "formatted": "<human_readable>",
      "confidence": 0.95,
      "source_url": "https://...",
      "notes": "any relevant notes"
    }}
  }},
  "summary": "Brief summary of what you found and any challenges",
  "navigation_path": ["url1", "url2", ...],
  "tool_calls_made": <number>
}}

Begin by navigating to the school's homepage and exploring."""

        return prompt

    def call_ollama(self, messages: List[Dict], tools: List[Dict]) -> Dict:
        """Call Ollama API with tool support"""
        url = f"{self.config['ollama']['base_url']}/v1/chat/completions"

        payload = {
            "model": self.config['ollama']['model'],
            "messages": messages,
            "tools": tools,
            "temperature": self.config['ollama']['temperature'],
            "max_tokens": self.config['ollama']['max_tokens']
        }

        try:
            response = self.session.post(
                url,
                json=payload,
                timeout=self.config['ollama']['timeout']
            )
            response.raise_for_status()
            return response.json()
        except Exception as e:
            self.logger.error(f"Ollama API error: {e}")
            raise

    def _init_mcp_client(self):
        """Initialize MCP client if not already done"""
        if self.mcp_client is None:
            try:
                mcp_config = self.config.get('mcp', {})
                base_url = mcp_config.get('base_url', 'http://localhost:8931/sse')
                timeout = mcp_config.get('timeout', 60)

                self.logger.info(f"Initializing MCP client at {base_url}")
                self.mcp_client = MCPClient(base_url=base_url, timeout=timeout)
                self.mcp_client.initialize()
                self.logger.info("MCP client initialized successfully")

            except Exception as e:
                self.logger.error(f"Failed to initialize MCP client: {e}")
                raise

    def execute_mcp_tool(self, tool_name: str, arguments: Dict) -> str:
        """Execute an MCP tool call"""
        try:
            # Initialize MCP client if needed
            if self.mcp_client is None:
                self._init_mcp_client()

            self.logger.info(f"  └─ Tool: {tool_name}({json.dumps(arguments)})")

            # Add delay before tool execution
            time.sleep(self.config['scraping']['page_load_delay'])

            # Call actual MCP tool
            result = self.mcp_client.call_tool(tool_name, arguments)

            # Return result as JSON string
            return json.dumps(result)

        except Exception as e:
            self.logger.error(f"MCP tool execution error: {e}")
            # Return error as JSON
            return json.dumps({
                "error": str(e),
                "success": False
            })

    def scrape_school(self, school_name: str) -> Optional[Dict]:
        """Scrape a single school"""
        start_time = time.time()

        # Find school
        school_info = self.find_school(school_name)
        if not school_info:
            console.print(f"[red]School not found: {school_name}[/red]")
            console.print("\nUse --list to see available schools")
            return None

        console.print(f"\n[bold cyan]Starting scrape: {school_info['School Name']}[/bold cyan]")
        console.print(f"URL: {school_info['Webpage']}")
        console.print(f"Fields to extract: {len(self.config['fields_to_extract'])}\n")

        # Create system prompt
        system_prompt = self.create_system_prompt(school_info)

        # Initialize conversation
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": "Begin the data extraction process."}
        ]

        tool_calls_count = 0
        max_iterations = 20
        navigation_path = []

        # Agent loop
        for iteration in range(max_iterations):
            if self.config['scraping']['verbose']:
                console.print(f"[dim]Iteration {iteration + 1}/{max_iterations}[/dim]")

            try:
                # Call Ollama
                response = self.call_ollama(messages, MCP_TOOLS)
                choice = response['choices'][0]
                message = choice['message']

                # Check if done (no tool calls)
                if choice['finish_reason'] == 'stop' and 'tool_calls' not in message:
                    console.print("[green]Agent completed data extraction[/green]")

                    # Parse final response
                    content = message.get('content', '')
                    try:
                        # Try to extract JSON from response
                        if '{' in content:
                            json_start = content.index('{')
                            json_end = content.rindex('}') + 1
                            json_str = content[json_start:json_end]
                            result = json.loads(json_str)
                        else:
                            result = {"error": "No JSON found in response"}
                    except Exception as e:
                        result = {"error": f"Failed to parse response: {e}"}

                    break

                # Handle tool calls
                if 'tool_calls' in message:
                    messages.append(message)

                    for tool_call in message['tool_calls']:
                        function = tool_call['function']
                        tool_name = function['name']
                        arguments = json.loads(function['arguments'])

                        tool_calls_count += 1

                        if self.config['scraping']['verbose']:
                            console.print(f"[blue]Tool call: {tool_name}[/blue]")

                        # Execute tool
                        result = self.execute_mcp_tool(tool_name, arguments)

                        # Track navigation
                        if tool_name == "browser_navigate":
                            navigation_path.append(arguments.get('url', ''))

                        # Add tool result to messages
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tool_call['id'],
                            "name": tool_name,
                            "content": result
                        })
                else:
                    # No tool calls but not finished
                    console.print("[yellow]Agent stopped without tool calls[/yellow]")
                    result = {"error": "Agent stopped unexpectedly"}
                    break

            except Exception as e:
                console.print(f"[red]Error during scraping: {e}[/red]")
                result = {"error": str(e)}
                break

        duration = time.time() - start_time

        # Prepare final result
        final_result = {
            "school_name": school_info['School Name'],
            "url": school_info['Webpage'],
            "scraped_at": datetime.now().isoformat(),
            "scrape_duration_seconds": int(duration),
            "model_used": self.config['ollama']['model'],
            "data": result.get('data', {}),
            "agent_summary": result.get('summary', ''),
            "navigation_path": navigation_path or result.get('navigation_path', []),
            "tool_calls_made": tool_calls_count,
            "errors": []
        }

        console.print(f"\n[green]Scraping complete![/green] Duration: {int(duration)}s")
        console.print(f"Tool calls made: {tool_calls_count}")

        return final_result

    def save_results(self, result: Dict):
        """Save scraping results"""
        output_dir = Path(self.config['output']['directory'])
        output_dir.mkdir(parents=True, exist_ok=True)

        # Generate filename
        school_name = result['school_name']
        safe_name = "".join(c for c in school_name if c.isalnum() or c in (' ', '-', '_')).strip()
        safe_name = safe_name.replace(' ', '_').lower()
        date_str = datetime.now().strftime('%Y-%m-%d')

        # Save individual JSON
        if self.config['output']['save_individual_files']:
            json_path = output_dir / f"{safe_name}_{date_str}.json"
            with open(json_path, 'w') as f:
                json.dump(result, f, indent=2)
            console.print(f"Results saved to: {json_path}")

        # TODO: Update Excel if configured
        if self.config['output']['update_excel']:
            console.print("[yellow]Excel update not yet implemented[/yellow]")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(
        description="Art School Web Scraper - Extract data from university websites using AI",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('--school', type=str, help='School name to scrape')
    parser.add_argument('--list', action='store_true', help='List all available schools')
    parser.add_argument('--show-fields', action='store_true', help='Show fields that will be extracted')
    parser.add_argument('--test-connection', action='store_true', help='Test Ollama and MCP connections')
    parser.add_argument('--model', type=str, help='Override Ollama model from config')
    parser.add_argument('--config', type=str, default='config.yaml', help='Path to config file')
    parser.add_argument('--quiet', action='store_true', help='Reduce output verbosity')
    parser.add_argument('--interactive', action='store_true', help='Interactive mode')

    args = parser.parse_args()

    # Create scraper instance
    scraper = ArtSchoolScraper(config_path=args.config)

    # Override model if specified
    if args.model:
        scraper.config['ollama']['model'] = args.model

    # Override verbosity if quiet
    if args.quiet:
        scraper.config['scraping']['verbose'] = False

    # Handle different modes
    if args.test_connection:
        success = scraper.test_connections()
        sys.exit(0 if success else 1)

    elif args.list:
        scraper.list_schools()

    elif args.show_fields:
        scraper.show_fields()

    elif args.interactive:
        console.print("[yellow]Interactive mode not yet implemented[/yellow]")
        sys.exit(1)

    elif args.school:
        # Test connections first
        console.print("[bold]Checking connections...[/bold]")
        if not scraper.test_connections():
            console.print("\n[red]Connection test failed. Please fix issues before scraping.[/red]")
            sys.exit(1)

        # Perform scraping
        result = scraper.scrape_school(args.school)
        if result:
            scraper.save_results(result)

    else:
        parser.print_help()


if __name__ == "__main__":
    main()
