#!/usr/bin/env python3
"""
Lemlist Integration Module
Handles all Lemlist API operations and database management
"""

import requests
import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import csv
import os
import sqlite3
import re

# Configure logging
logger = logging.getLogger(__name__)

class LemlistClient:
    """Client for interacting with Lemlist API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.lemlist.com/api"
        self.session = requests.Session()
        
        # Set up authentication headers
        # Lemlist uses Basic Auth with empty username and API key as password
        import base64
        credentials = f":{api_key}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()
        self.session.headers.update({
            'Authorization': f'Basic {encoded_credentials}',
            'Content-Type': 'application/json',
            'User-Agent': 'LemlistDataPuller/1.0'
        })
        
        logger.info("Lemlist client initialized")
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Lemlist API"""
        url = f"{self.base_url}/{endpoint}"
        
        try:
            logger.debug(f"Making {method} request to {url}")
            response = self.session.request(method, url, params=params)
            
            # Handle rate limiting
            if response.status_code == 429:
                logger.warning("Rate limited. Waiting 60 seconds...")
                time.sleep(60)
                return self._make_request(method, endpoint, params)
            
            response.raise_for_status()
            return response.json()
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed: {e}")
            raise
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse JSON response: {e}")
            raise
    
    def get_team_info(self) -> Dict[str, Any]:
        """Get team information to verify API key"""
        try:
            logger.info("Fetching team information...")
            team_info = self._make_request('GET', 'team')
            logger.info(f"Team info retrieved: {team_info.get('name', 'Unknown')}")
            return team_info
        except Exception as e:
            logger.error(f"Failed to get team info: {e}")
            raise
    
    def get_all_campaigns(self, status: Optional[str] = None) -> List[Dict[str, Any]]:
        """Get all campaigns with optional status filter"""
        try:
            logger.info("Fetching all campaigns...")
            params = {
                'version': 'v2',
                'limit': 100,  # Maximum per page
                'page': 1,
                'sortBy': 'createdAt',
                'sortOrder': 'desc'
            }
            
            if status:
                params['status'] = status
            
            all_campaigns = []
            page = 1
            
            while True:
                params['page'] = page
                response = self._make_request('GET', 'campaigns', params=params)
                
                campaigns = response.get('campaigns', [])
                if not campaigns:
                    break
                
                all_campaigns.extend(campaigns)
                logger.info(f"Fetched page {page}: {len(campaigns)} campaigns")
                
                # Check if there are more pages
                pagination = response.get('pagination', {})
                if page >= pagination.get('totalPages', 1):
                    break
                
                page += 1
                time.sleep(0.5)  # Rate limiting protection
            
            logger.info(f"Total campaigns retrieved: {len(all_campaigns)}")
            return all_campaigns
            
        except Exception as e:
            logger.error(f"Failed to get campaigns: {e}")
            raise
    
    def get_campaign_leads(self, campaign_id: str, state: str = 'all') -> List[Dict[str, Any]]:
        """Get all leads for a specific campaign"""
        try:
            logger.info(f"Fetching leads for campaign {campaign_id}...")
            
            params = {
                'state': state,
                'format': 'json'
            }
            
            response = self._make_request('GET', f'campaigns/{campaign_id}/export/leads', params=params)
            
            # Handle different response formats
            if isinstance(response, list):
                leads = response
            elif isinstance(response, dict) and 'leads' in response:
                leads = response['leads']
            else:
                leads = [response] if response else []
            
            logger.info(f"Retrieved {len(leads)} leads for campaign {campaign_id}")
            return leads
            
        except Exception as e:
            logger.error(f"Failed to get leads for campaign {campaign_id}: {e}")
            return []
    
    def analyze_lead_fields(self, leads: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze lead fields to understand the structure"""
        if not leads:
            return {}
        
        field_analysis = {}
        
        for lead in leads:
            for field_name, field_value in lead.items():
                if field_name not in field_analysis:
                    field_analysis[field_name] = {
                        'type': type(field_value).__name__,
                        'sample_values': [],
                        'null_count': 0,
                        'total_count': 0
                    }
                
                field_analysis[field_name]['total_count'] += 1
                
                if field_value is None:
                    field_analysis[field_name]['null_count'] += 1
                elif len(field_analysis[field_name]['sample_values']) < 3:
                    field_analysis[field_name]['sample_values'].append(str(field_value)[:100])
        
        return field_analysis

class CampaignDatabase:
    """Handles SQLite database operations for all campaigns in one database"""
    
    def __init__(self, db_path: str = "lemlist_campaigns.db"):
        self.db_path = db_path
        
        # Initialize database
        self._init_database()
    
    def _sanitize_filename(self, filename: str) -> str:
        """Sanitize filename for safe file system usage"""
        # Remove or replace invalid characters
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', filename)
        # Remove extra spaces and dots
        sanitized = re.sub(r'\s+', '_', sanitized.strip())
        # Remove leading/trailing dots and underscores
        sanitized = sanitized.strip('._')
        # Limit length
        return sanitized[:50] if len(sanitized) > 50 else sanitized
    
    def _init_database(self):
        """Initialize the database with campaigns overview table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create campaigns overview table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS campaigns_overview (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    status TEXT NOT NULL,
                    table_name TEXT NOT NULL,
                    leads_count INTEGER DEFAULT 0,
                    columns_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info(f"Database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize database {self.db_path}: {e}")
            raise
    
    def create_campaign_table(self, campaign_id: str, campaign_name: str, campaign_status: str, leads: List[Dict[str, Any]]):
        """Create a table for a specific campaign with dynamic columns based on lead data"""
        if not leads:
            logger.warning(f"No leads to create table for campaign {campaign_name}")
            return None
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create safe table name
            table_name = self._sanitize_table_name(campaign_id, campaign_name)
            
            # Get all unique field names from leads
            all_fields = set()
            for lead in leads:
                all_fields.update(lead.keys())
            
            # Create campaign table with dynamic columns
            columns = []
            for field in sorted(all_fields):
                # Determine column type based on sample data
                column_type = self._determine_column_type(field, leads)
                safe_field = self._sanitize_column_name(field)
                columns.append(f'"{safe_field}" {column_type}')
            
            create_table_sql = f'''
                CREATE TABLE IF NOT EXISTS "{table_name}" (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    {', '.join(columns)}
                )
            '''
            
            cursor.execute(create_table_sql)
            
            # Add campaign to overview table
            cursor.execute('''
                INSERT OR REPLACE INTO campaigns_overview 
                (id, name, status, table_name, leads_count, columns_count, last_updated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (campaign_id, campaign_name, campaign_status, table_name, len(leads), len(all_fields), datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Campaign table '{table_name}' created with {len(all_fields)} columns for {campaign_name}")
            return table_name
            
        except Exception as e:
            logger.error(f"Failed to create table for campaign {campaign_name}: {e}")
            raise
    
    def _determine_column_type(self, field_name: str, leads: List[Dict[str, Any]]) -> str:
        """Determine SQLite column type based on sample data"""
        sample_values = [lead.get(field_name) for lead in leads[:10] if lead.get(field_name) is not None]
        
        if not sample_values:
            return 'TEXT'
        
        # Check if all values are numbers
        try:
            for value in sample_values:
                float(str(value))
            return 'REAL'
        except (ValueError, TypeError):
            pass
        
        # Check if all values are integers
        try:
            for value in sample_values:
                int(str(value))
            return 'INTEGER'
        except (ValueError, TypeError):
            pass
        
        # Check for boolean values
        bool_values = {'true', 'false', '1', '0', 'yes', 'no', 'on', 'off'}
        if all(str(value).lower() in bool_values for value in sample_values):
            return 'INTEGER'  # Store as 0/1
        
        # Default to TEXT
        return 'TEXT'
    
    def _sanitize_table_name(self, campaign_id: str, campaign_name: str) -> str:
        """Sanitize table name for SQLite"""
        # Use campaign_id as base and add campaign name for readability
        safe_name = self._sanitize_filename(campaign_name)
        table_name = f"campaign_{campaign_id}_{safe_name}"
        
        # Ensure it's valid SQLite table name
        table_name = re.sub(r'[^a-zA-Z0-9_]', '_', table_name)
        # Ensure it doesn't start with a number
        if table_name and table_name[0].isdigit():
            table_name = f"t_{table_name}"
        # Limit length
        return table_name[:63] if len(table_name) > 63 else table_name
    
    def _sanitize_column_name(self, column_name: str) -> str:
        """Sanitize column name for SQLite"""
        # Remove or replace invalid characters
        sanitized = re.sub(r'[^a-zA-Z0-9_]', '_', column_name)
        # Ensure it doesn't start with a number
        if sanitized and sanitized[0].isdigit():
            sanitized = f"col_{sanitized}"
        # Ensure it's not empty
        if not sanitized:
            sanitized = "unknown_field"
        return sanitized
    
    def insert_campaign_leads(self, table_name: str, leads: List[Dict[str, Any]]):
        """Insert leads into a specific campaign table"""
        if not leads:
            logger.warning(f"No leads to insert for table {table_name}")
            return
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all unique field names
            all_fields = set()
            for lead in leads:
                all_fields.update(lead.keys())
            
            # Prepare data for insertion
            sanitized_fields = [self._sanitize_column_name(field) for field in sorted(all_fields)]
            placeholders = ', '.join(['?' for _ in sanitized_fields])
            field_names = ', '.join([f'"{field}"' for field in sanitized_fields])
            
            insert_sql = f'INSERT INTO "{table_name}" ({field_names}) VALUES ({placeholders})'
            
            # Insert each lead
            for lead in leads:
                values = []
                for field in sorted(all_fields):
                    value = lead.get(field)
                    # Convert None to empty string for TEXT fields
                    if value is None:
                        values.append('')
                    else:
                        values.append(str(value))
                
                cursor.execute(insert_sql, values)
            
            conn.commit()
            conn.close()
            
            logger.info(f"Inserted {len(leads)} leads into table {table_name}")
            
        except Exception as e:
            logger.error(f"Failed to insert leads for table {table_name}: {e}")
            raise
    
    def clear_all_campaign_data(self):
        """Delete all campaign tables from the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get all campaign table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'campaign_%'")
            table_names = [row[0] for row in cursor.fetchall()]
            
            # Drop all campaign tables
            for table_name in table_names:
                cursor.execute(f'DROP TABLE IF EXISTS "{table_name}"')
                logger.info(f"Dropped table {table_name}")
            
            # Recreate the campaigns_overview table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS campaigns_overview (
                    id TEXT PRIMARY KEY,
                    name TEXT NOT NULL,
                    status TEXT,
                    table_name TEXT,
                    leads_count INTEGER DEFAULT 0,
                    columns_count INTEGER DEFAULT 0,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            logger.info("Recreated campaigns_overview table")
            
            conn.commit()
            conn.close()
            
            logger.info(f"Dropped {len(table_names)} campaign tables and recreated campaigns_overview")
            
        except Exception as e:
            logger.error(f"Failed to clear campaign data: {e}")
            raise
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get information about the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get campaigns overview
            cursor.execute('SELECT * FROM campaigns_overview')
            campaigns = cursor.fetchall()
            
            # Get all table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'campaign_%'")
            table_names = [row[0] for row in cursor.fetchall()]
            
            conn.close()
            
            return {
                'campaigns_count': len(campaigns),
                'tables_count': len(table_names),
                'campaigns': campaigns,
                'table_names': table_names
            }
            
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {}

class LemlistDataPuller:
    """Main class for pulling and processing Lemlist data"""
    
    def __init__(self, api_key: str):
        self.client = LemlistClient(api_key)
        self.database = CampaignDatabase()
        self.data = {
            'campaigns': [],
            'leads': {},
            'field_analysis': {},
            'tables': {},
            'pull_timestamp': datetime.now().isoformat()
        }
    
    def pull_all_data(self, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """Pull all campaigns and their leads"""
        try:
            logger.info("Starting data pull from Lemlist...")
            
            # Clear existing data to prevent duplicates
            logger.info("Clearing existing campaign data...")
            self.database.clear_all_campaign_data()
            
            # Verify API connection
            team_info = self.client.get_team_info()
            logger.info(f"Connected to team: {team_info.get('name', 'Unknown')}")
            
            # Get all campaigns
            campaigns = self.client.get_all_campaigns(status=status_filter)
            self.data['campaigns'] = campaigns
            
            logger.info(f"Found {len(campaigns)} campaigns")
            
            # Process each campaign
            for i, campaign in enumerate(campaigns, 1):
                campaign_id = campaign['_id']
                campaign_name = campaign['name']
                campaign_status = campaign['status']
                
                logger.info(f"Processing campaign {i}/{len(campaigns)}: {campaign_name}")
                
                # Get leads for this campaign
                leads = self.client.get_campaign_leads(campaign_id)
                
                # Create table for this campaign
                try:
                    if leads:
                        # Create campaign table and insert data
                        table_name = self.database.create_campaign_table(campaign_id, campaign_name, campaign_status, leads)
                        
                        if table_name:
                            self.database.insert_campaign_leads(table_name, leads)
                            
                            self.data['tables'][campaign_id] = {
                                'table_name': table_name,
                                'campaign_name': campaign_name,
                                'leads_count': len(leads),
                                'columns_count': len(set().union(*[lead.keys() for lead in leads]))
                            }
                            
                            logger.info(f"✅ Table created: {table_name} ({len(leads)} leads)")
                        else:
                            logger.warning(f"Failed to create table for campaign {campaign_name}")
                    else:
                        logger.info(f"Campaign {campaign_name}: No leads found - no table created")
                        self.data['tables'][campaign_id] = {
                            'table_name': None,
                            'campaign_name': campaign_name,
                            'leads_count': 0,
                            'columns_count': 0
                        }
                    
                except Exception as e:
                    logger.error(f"Failed to create table for campaign {campaign_name}: {e}")
                    self.data['tables'][campaign_id] = {
                        'table_name': None,
                        'campaign_name': campaign_name,
                        'leads_count': 0,
                        'columns_count': 0,
                        'error': str(e)
                    }
                
                # Store leads data (for backward compatibility)
                self.data['leads'][campaign_id] = {
                    'campaign_info': {
                        'id': campaign_id,
                        'name': campaign_name,
                        'status': campaign_status
                    },
                    'leads': leads,
                    'lead_count': len(leads)
                }
                
                # Analyze fields for this campaign
                if leads:
                    field_analysis = self.client.analyze_lead_fields(leads)
                    self.data['field_analysis'][campaign_id] = field_analysis
                    
                    logger.info(f"Campaign {campaign_name}: {len(leads)} leads, {len(field_analysis)} unique fields")
                else:
                    logger.info(f"Campaign {campaign_name}: No leads found")
                
                # Rate limiting protection
                time.sleep(1)
            
            logger.info("Data pull completed successfully!")
            return self.data
            
        except Exception as e:
            logger.error(f"Data pull failed: {e}")
            raise
    
    def save_to_json(self, filename: str = None) -> str:
        """Save data to JSON file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"lemlist_data_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"Data saved to {filename}")
            return filename
        except Exception as e:
            logger.error(f"Failed to save JSON file: {e}")
            raise
    
    def save_to_csv(self, output_dir: str = "lemlist_export") -> str:
        """Save data to CSV files"""
        try:
            os.makedirs(output_dir, exist_ok=True)
            
            # Save campaigns summary
            campaigns_file = os.path.join(output_dir, "campaigns_summary.csv")
            with open(campaigns_file, 'w', newline='', encoding='utf-8') as f:
                writer = csv.writer(f)
                writer.writerow(['Campaign ID', 'Name', 'Status', 'Lead Count'])
                
                for campaign in self.data['campaigns']:
                    campaign_id = campaign['_id']
                    lead_count = self.data['leads'].get(campaign_id, {}).get('lead_count', 0)
                    writer.writerow([
                        campaign_id,
                        campaign['name'],
                        campaign['status'],
                        lead_count
                    ])
            
            # Save leads for each campaign
            for campaign_id, campaign_data in self.data['leads'].items():
                if not campaign_data['leads']:
                    continue
                
                campaign_name = campaign_data['campaign_info']['name']
                # Clean filename
                safe_name = "".join(c for c in campaign_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
                safe_name = safe_name.replace(' ', '_')
                
                leads_file = os.path.join(output_dir, f"leads_{safe_name}_{campaign_id}.csv")
                
                # Get all unique field names across all leads
                all_fields = set()
                for lead in campaign_data['leads']:
                    all_fields.update(lead.keys())
                
                with open(leads_file, 'w', newline='', encoding='utf-8') as f:
                    writer = csv.DictWriter(f, fieldnames=sorted(all_fields))
                    writer.writeheader()
                    writer.writerows(campaign_data['leads'])
                
                logger.info(f"Saved {len(campaign_data['leads'])} leads to {leads_file}")
            
            logger.info(f"CSV files saved to {output_dir}")
            return output_dir
            
        except Exception as e:
            logger.error(f"Failed to save CSV files: {e}")
            raise
    
    def print_summary(self):
        """Print a summary of the pulled data"""
        print("\n" + "="*60)
        print("LEMLIST DATA PULL SUMMARY")
        print("="*60)
        
        print(f"Total Campaigns: {len(self.data['campaigns'])}")
        print(f"Pull Timestamp: {self.data['pull_timestamp']}")
        
        total_leads = sum(campaign_data['lead_count'] for campaign_data in self.data['leads'].values())
        print(f"Total Leads: {total_leads}")
        
        print("\nCampaign Details:")
        print("-" * 60)
        for campaign in self.data['campaigns']:
            campaign_id = campaign['_id']
            lead_count = self.data['leads'].get(campaign_id, {}).get('lead_count', 0)
            field_count = len(self.data['field_analysis'].get(campaign_id, {}))
            table_info = self.data['tables'].get(campaign_id, {})
            
            print(f"• {campaign['name']}")
            print(f"  ID: {campaign_id}")
            print(f"  Status: {campaign['status']}")
            print(f"  Leads: {lead_count}")
            print(f"  Fields: {field_count}")
            print(f"  Table: {table_info.get('table_name', 'N/A')}")
            print()
        
        # Show table summary
        print("Table Summary:")
        print("-" * 60)
        for campaign_id, table_info in self.data['tables'].items():
            print(f"• {table_info['campaign_name']}")
            print(f"  Table: {table_info['table_name'] or 'No table'}")
            print(f"  Leads: {table_info['leads_count']}")
            print(f"  Columns: {table_info['columns_count']}")
            if 'error' in table_info:
                print(f"  Error: {table_info['error']}")
            print()
        
        # Show field analysis for campaigns with leads
        print("Field Analysis:")
        print("-" * 60)
        for campaign_id, field_analysis in self.data['field_analysis'].items():
            campaign_name = self.data['leads'][campaign_id]['campaign_info']['name']
            print(f"\n{campaign_name} ({campaign_id}):")
            
            for field_name, analysis in field_analysis.items():
                null_percentage = (analysis['null_count'] / analysis['total_count']) * 100
                print(f"  • {field_name} ({analysis['type']}) - {null_percentage:.1f}% null")
                if analysis['sample_values']:
                    print(f"    Samples: {', '.join(analysis['sample_values'])}")
