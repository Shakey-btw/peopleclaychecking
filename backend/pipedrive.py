#!/usr/bin/env python3
"""
Pipedrive Integration Module
Handles all Pipedrive API operations and database management
"""

import requests
import json
import time
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import sqlite3
import re

# Configure logging
logger = logging.getLogger(__name__)

class PipedriveClient:
    """Client for interacting with Pipedrive API"""
    
    def __init__(self, api_key: str):
        self.api_key = api_key
        self.base_url = "https://api.pipedrive.com/v1"
        self.session = requests.Session()
        
        # Set up authentication
        self.session.params = {'api_token': self.api_key}
        
        logger.info("Pipedrive client initialized")
    
    def _make_request(self, method: str, endpoint: str, params: Optional[Dict] = None) -> Dict[str, Any]:
        """Make authenticated request to Pipedrive API"""
        url = f"{self.base_url}/{endpoint}"
        
        # Merge with default API token
        request_params = {'api_token': self.api_key}
        if params:
            request_params.update(params)
        
        try:
            logger.debug(f"Making {method} request to {url}")
            response = self.session.request(method, url, params=request_params)
            
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
    
    def get_organization_fields(self) -> List[Dict[str, Any]]:
        """Get all organization field definitions"""
        try:
            logger.info("Fetching organization fields...")
            response = self._make_request('GET', 'organizationFields')
            fields = response.get('data', [])
            logger.info(f"Retrieved {len(fields)} organization fields")
            return fields
        except Exception as e:
            logger.error(f"Failed to get organization fields: {e}")
            raise
    
    def get_all_organizations(self, start: int = 0, limit: int = 500) -> List[Dict[str, Any]]:
        """Get all organizations with pagination"""
        try:
            logger.info("Fetching all organizations...")
            all_organizations = []
            start_index = start
            
            while True:
                params = {
                    'start': start_index,
                    'limit': limit
                }
                
                response = self._make_request('GET', 'organizations', params=params)
                organizations = response.get('data', [])
                
                if not organizations:
                    break
                
                all_organizations.extend(organizations)
                logger.info(f"Fetched {len(organizations)} organizations (total: {len(all_organizations)})")
                
                # Check if there are more pages
                additional_data = response.get('additional_data', {})
                pagination = additional_data.get('pagination', {})
                
                if not pagination.get('more_items_in_collection', False):
                    break
                
                start_index += limit
                time.sleep(0.5)  # Rate limiting protection
            
            logger.info(f"Total organizations retrieved: {len(all_organizations)}")
            return all_organizations
            
        except Exception as e:
            logger.error(f"Failed to get organizations: {e}")
            raise
    
    def get_filter_details(self, filter_id: str) -> Dict[str, Any]:
        """Get details of a specific filter"""
        try:
            logger.info(f"Fetching filter details for ID: {filter_id}")
            response = self._make_request('GET', f'filters/{filter_id}')
            filter_data = response.get('data', {})
            logger.info(f"Retrieved filter: {filter_data.get('name', 'Unknown')}")
            return filter_data
        except Exception as e:
            logger.error(f"Failed to get filter details for ID {filter_id}: {e}")
            raise
    
    def get_organizations_by_filter(self, filter_id: str, start: int = 0, limit: int = 500) -> List[Dict[str, Any]]:
        """Get organizations filtered by a specific filter ID"""
        try:
            logger.info(f"Fetching organizations with filter ID: {filter_id}")
            all_organizations = []
            start_index = start
            
            while True:
                params = {
                    'filter_id': filter_id,
                    'start': start_index,
                    'limit': limit
                }
                
                response = self._make_request('GET', 'organizations', params=params)
                organizations = response.get('data', [])
                
                if not organizations:
                    break
                
                all_organizations.extend(organizations)
                logger.info(f"Fetched {len(organizations)} filtered organizations (total: {len(all_organizations)})")
                
                # Check if there are more pages
                additional_data = response.get('additional_data', {})
                pagination = additional_data.get('pagination', {})
                
                if not pagination.get('more_items_in_collection', False):
                    break
                
                start_index += limit
                time.sleep(0.5)  # Rate limiting protection
            
            logger.info(f"Total filtered organizations retrieved: {len(all_organizations)}")
            return all_organizations
            
        except Exception as e:
            logger.error(f"Failed to get organizations with filter {filter_id}: {e}")
            raise
    
    def extract_filter_id_from_url(self, filter_url: str) -> str:
        """Extract filter ID from Pipedrive filter URL"""
        try:
            # Pipedrive filter URLs typically look like:
            # https://app.pipedrive.com/filters/12345
            # or similar patterns
            import re
            
            # Try to extract ID from various URL patterns
            patterns = [
                r'/filters/(\d+)',
                r'filter_id=(\d+)',
                r'filter=(\d+)',
                r'id=(\d+)'
            ]
            
            for pattern in patterns:
                match = re.search(pattern, filter_url)
                if match:
                    filter_id = match.group(1)
                    logger.info(f"Extracted filter ID: {filter_id} from URL: {filter_url}")
                    return filter_id
            
            # If no pattern matches, try to extract any number from the URL
            numbers = re.findall(r'\d+', filter_url)
            if numbers:
                # Take the last number found (most likely to be the filter ID)
                filter_id = numbers[-1]
                logger.info(f"Extracted filter ID (fallback): {filter_id} from URL: {filter_url}")
                return filter_id
            
            raise ValueError(f"Could not extract filter ID from URL: {filter_url}")
            
        except Exception as e:
            logger.error(f"Failed to extract filter ID from URL {filter_url}: {e}")
            raise

class PipedriveDatabase:
    """Handles SQLite database operations for Pipedrive data"""
    
    def __init__(self, db_path: str = "pipedrive.db"):
        self.db_path = db_path
        self._init_database()
    
    def _init_database(self):
        """Initialize the database with organizations table"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Create organizations table with all standard fields
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS organizations (
                    id INTEGER PRIMARY KEY,
                    name TEXT,
                    owner_name TEXT,
                    cc_email TEXT,
                    address TEXT,
                    address_subpremise TEXT,
                    address_street_number TEXT,
                    address_route TEXT,
                    address_sublocality TEXT,
                    address_locality TEXT,
                    address_admin_area_level_1 TEXT,
                    address_admin_area_level_2 TEXT,
                    address_country TEXT,
                    address_postal_code TEXT,
                    address_formatted_address TEXT,
                    open_deals_count INTEGER,
                    related_open_deals_count INTEGER,
                    closed_deals_count INTEGER,
                    related_closed_deals_count INTEGER,
                    participant_open_deals_count INTEGER,
                    participant_closed_deals_count INTEGER,
                    email_messages_count INTEGER,
                    activities_count INTEGER,
                    done_activities_count INTEGER,
                    undone_activities_count INTEGER,
                    files_count INTEGER,
                    notes_count INTEGER,
                    followers_count INTEGER,
                    won_deals_count INTEGER,
                    related_won_deals_count INTEGER,
                    related_lost_deals_count INTEGER,
                    visible_to TEXT,
                    picture_id TEXT,
                    next_activity_date DATE,
                    next_activity_time TEXT,
                    next_activity_id INTEGER,
                    last_activity_id INTEGER,
                    last_activity_date DATE,
                    last_incoming_mail_time DATETIME,
                    last_outgoing_mail_time DATETIME,
                    label INTEGER,
                    country_code TEXT,
                    first_char TEXT,
                    update_time DATETIME,
                    add_time DATETIME,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create organization fields table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS organization_fields (
                    id INTEGER PRIMARY KEY,
                    key TEXT UNIQUE,
                    name TEXT,
                    field_type TEXT,
                    options TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create organization custom fields table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS organization_custom_fields (
                    org_id INTEGER,
                    field_key TEXT,
                    field_value TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (org_id) REFERENCES organizations (id),
                    PRIMARY KEY (org_id, field_key)
                )
            ''')
            
            # Create user filters table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_filters (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filter_id TEXT UNIQUE NOT NULL,
                    filter_name TEXT NOT NULL,
                    filter_url TEXT,
                    filter_conditions TEXT,
                    organizations_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    is_active BOOLEAN DEFAULT 1
                )
            ''')
            
            # Create filtered organizations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS filtered_organizations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filter_id TEXT NOT NULL,
                    org_id INTEGER NOT NULL,
                    org_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (filter_id) REFERENCES user_filters (filter_id),
                    FOREIGN KEY (org_id) REFERENCES organizations (id),
                    UNIQUE(filter_id, org_id)
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info(f"Pipedrive database initialized: {self.db_path}")
            
        except Exception as e:
            logger.error(f"Failed to initialize Pipedrive database: {e}")
            raise
    
    def save_organization_fields(self, fields: List[Dict[str, Any]]):
        """Save organization field definitions"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for field in fields:
                cursor.execute('''
                    INSERT OR REPLACE INTO organization_fields 
                    (id, key, name, field_type, options)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    field.get('id'),
                    field.get('key'),
                    field.get('name'),
                    field.get('field_type'),
                    json.dumps(field.get('options', []))
                ))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {len(fields)} organization fields")
            
        except Exception as e:
            logger.error(f"Failed to save organization fields: {e}")
            raise
    
    def save_organizations(self, organizations: List[Dict[str, Any]]):
        """Save organizations to database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            for org in organizations:
                # Skip if org is not a dictionary
                if not isinstance(org, dict):
                    logger.warning(f"Skipping non-dict organization: {type(org)} - {org}")
                    continue
                
                # Extract basic fields with safe access
                basic_fields = {
                    'id': org.get('id'),
                    'name': org.get('name'),
                    'owner_name': org.get('owner_name'),
                    'cc_email': org.get('cc_email'),
                    'open_deals_count': org.get('open_deals_count'),
                    'related_open_deals_count': org.get('related_open_deals_count'),
                    'closed_deals_count': org.get('closed_deals_count'),
                    'related_closed_deals_count': org.get('related_closed_deals_count'),
                    'participant_open_deals_count': org.get('participant_open_deals_count'),
                    'participant_closed_deals_count': org.get('participant_closed_deals_count'),
                    'email_messages_count': org.get('email_messages_count'),
                    'activities_count': org.get('activities_count'),
                    'done_activities_count': org.get('done_activities_count'),
                    'undone_activities_count': org.get('undone_activities_count'),
                    'files_count': org.get('files_count'),
                    'notes_count': org.get('notes_count'),
                    'followers_count': org.get('followers_count'),
                    'won_deals_count': org.get('won_deals_count'),
                    'related_won_deals_count': org.get('related_won_deals_count'),
                    'related_lost_deals_count': org.get('related_lost_deals_count'),
                    'visible_to': org.get('visible_to'),
                    'picture_id': org.get('picture_id'),
                    'next_activity_date': org.get('next_activity_date'),
                    'next_activity_time': org.get('next_activity_time'),
                    'next_activity_id': org.get('next_activity_id'),
                    'last_activity_id': org.get('last_activity_id'),
                    'last_activity_date': org.get('last_activity_date'),
                    'last_incoming_mail_time': org.get('last_incoming_mail_time'),
                    'last_outgoing_mail_time': org.get('last_outgoing_mail_time'),
                    'label': org.get('label'),
                    'country_code': org.get('country_code'),
                    'first_char': org.get('first_char'),
                    'update_time': org.get('update_time'),
                    'add_time': org.get('add_time'),
                    'created_at': datetime.now().isoformat(),
                    'last_updated': datetime.now().isoformat()
                }
                
                # Initialize address fields with None values
                basic_fields.update({
                    'address': None,
                    'address_subpremise': None,
                    'address_street_number': None,
                    'address_route': None,
                    'address_sublocality': None,
                    'address_locality': None,
                    'address_admin_area_level_1': None,
                    'address_admin_area_level_2': None,
                    'address_country': None,
                    'address_postal_code': None,
                    'address_formatted_address': None
                })
                
                # Handle address fields safely
                address = org.get('address', {})
                if isinstance(address, dict):
                    basic_fields.update({
                        'address': address.get('address'),
                        'address_subpremise': address.get('subpremise'),
                        'address_street_number': address.get('street_number'),
                        'address_route': address.get('route'),
                        'address_sublocality': address.get('sublocality'),
                        'address_locality': address.get('locality'),
                        'address_admin_area_level_1': address.get('admin_area_level_1'),
                        'address_admin_area_level_2': address.get('admin_area_level_2'),
                        'address_country': address.get('country'),
                        'address_postal_code': address.get('postal_code'),
                        'address_formatted_address': address.get('formatted_address')
                    })
                
                # Insert organization
                cursor.execute('''
                    INSERT OR REPLACE INTO organizations 
                    (id, name, owner_name, cc_email, address, address_subpremise, 
                     address_street_number, address_route, address_sublocality, 
                     address_locality, address_admin_area_level_1, address_admin_area_level_2, 
                     address_country, address_postal_code, address_formatted_address,
                     open_deals_count, related_open_deals_count, closed_deals_count, 
                     related_closed_deals_count, participant_open_deals_count, 
                     participant_closed_deals_count, email_messages_count, activities_count, 
                     done_activities_count, undone_activities_count, files_count, 
                     notes_count, followers_count, won_deals_count, related_won_deals_count, 
                     related_lost_deals_count, visible_to, picture_id, next_activity_date, 
                     next_activity_time, next_activity_id, last_activity_id, 
                     last_activity_date, last_incoming_mail_time, last_outgoing_mail_time, 
                     label, country_code, first_char, update_time, add_time, created_at, last_updated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', tuple(basic_fields.values()))
                
                # Save custom fields safely
                for key, value in org.items():
                    if key not in basic_fields and value is not None:
                        try:
                            cursor.execute('''
                                INSERT OR REPLACE INTO organization_custom_fields 
                                (org_id, field_key, field_value)
                                VALUES (?, ?, ?)
                            ''', (org.get('id'), key, str(value)))
                        except Exception as e:
                            logger.warning(f"Failed to save custom field {key} for org {org.get('id')}: {e}")
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {len(organizations)} organizations to database")
            
        except Exception as e:
            logger.error(f"Failed to save organizations: {e}")
            raise
    
    def clear_organization_custom_fields(self):
        """Clear all organization custom fields from the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear all custom fields
            cursor.execute('DELETE FROM organization_custom_fields')
            
            conn.commit()
            conn.close()
            
            logger.info("Cleared all organization custom fields")
            
        except Exception as e:
            logger.error(f"Failed to clear organization custom fields: {e}")
            raise
    
    def save_user_filter(self, filter_id: str, filter_name: str, filter_url: str = None, 
                        filter_conditions: str = None, organizations_count: int = 0):
        """Save or update a user filter"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT OR REPLACE INTO user_filters 
                (filter_id, filter_name, filter_url, filter_conditions, organizations_count, last_used)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (filter_id, filter_name, filter_url, filter_conditions, organizations_count, datetime.now().isoformat()))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved user filter: {filter_name} (ID: {filter_id})")
            
        except Exception as e:
            logger.error(f"Failed to save user filter: {e}")
            raise
    
    def get_user_filters(self) -> List[Dict[str, Any]]:
        """Get all user filters"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT filter_id, filter_name, filter_url, filter_conditions, 
                       organizations_count, created_at, last_used, is_active
                FROM user_filters 
                WHERE is_active = 1
                ORDER BY last_used DESC
            ''')
            
            filters = []
            for row in cursor.fetchall():
                filters.append({
                    'filter_id': row[0],
                    'filter_name': row[1],
                    'filter_url': row[2],
                    'filter_conditions': row[3],
                    'organizations_count': row[4],
                    'created_at': row[5],
                    'last_used': row[6],
                    'is_active': row[7]
                })
            
            conn.close()
            
            logger.info(f"Retrieved {len(filters)} user filters")
            return filters
            
        except Exception as e:
            logger.error(f"Failed to get user filters: {e}")
            raise
    
    def save_filtered_organizations(self, filter_id: str, organizations: List[Dict[str, Any]]):
        """Save filtered organizations for a specific filter"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Clear existing filtered organizations for this filter
            cursor.execute('DELETE FROM filtered_organizations WHERE filter_id = ?', (filter_id,))
            
            # Insert new filtered organizations
            for org in organizations:
                cursor.execute('''
                    INSERT INTO filtered_organizations (filter_id, org_id, org_name)
                    VALUES (?, ?, ?)
                ''', (filter_id, org.get('id'), org.get('name')))
            
            # Update organizations count in user_filters table
            cursor.execute('''
                UPDATE user_filters 
                SET organizations_count = ?, last_used = ?
                WHERE filter_id = ?
            ''', (len(organizations), datetime.now().isoformat(), filter_id))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Saved {len(organizations)} filtered organizations for filter {filter_id}")
            
        except Exception as e:
            logger.error(f"Failed to save filtered organizations: {e}")
            raise
    
    def get_filtered_organizations(self, filter_id: str) -> List[Dict[str, Any]]:
        """Get organizations for a specific filter"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT fo.org_id, fo.org_name, o.name, o.owner_name, o.open_deals_count
                FROM filtered_organizations fo
                LEFT JOIN organizations o ON fo.org_id = o.id
                WHERE fo.filter_id = ?
                ORDER BY fo.org_name
            ''', (filter_id,))
            
            organizations = []
            for row in cursor.fetchall():
                organizations.append({
                    'id': row[0],
                    'name': row[1] or row[2],  # Use filtered name or fallback to org name
                    'owner_name': row[3],
                    'open_deals_count': row[4]
                })
            
            conn.close()
            
            logger.info(f"Retrieved {len(organizations)} organizations for filter {filter_id}")
            return organizations
            
        except Exception as e:
            logger.error(f"Failed to get filtered organizations: {e}")
            raise
    
    def delete_user_filter(self, filter_id: str):
        """Delete a user filter and its associated data"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Delete filtered organizations
            cursor.execute('DELETE FROM filtered_organizations WHERE filter_id = ?', (filter_id,))
            
            # Mark filter as inactive instead of deleting
            cursor.execute('UPDATE user_filters SET is_active = 0 WHERE filter_id = ?', (filter_id,))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Deleted user filter: {filter_id}")
            
        except Exception as e:
            logger.error(f"Failed to delete user filter: {e}")
            raise
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get information about the database"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get organizations count
            cursor.execute('SELECT COUNT(*) FROM organizations')
            org_count = cursor.fetchone()[0]
            
            # Get fields count
            cursor.execute('SELECT COUNT(*) FROM organization_fields')
            fields_count = cursor.fetchone()[0]
            
            # Get custom fields count
            cursor.execute('SELECT COUNT(*) FROM organization_custom_fields')
            custom_fields_count = cursor.fetchone()[0]
            
            # Get user filters count
            cursor.execute('SELECT COUNT(*) FROM user_filters WHERE is_active = 1')
            filters_count = cursor.fetchone()[0]
            
            # Get filtered organizations count
            cursor.execute('SELECT COUNT(*) FROM filtered_organizations')
            filtered_orgs_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'organizations_count': org_count,
                'fields_count': fields_count,
                'custom_fields_count': custom_fields_count,
                'user_filters_count': filters_count,
                'filtered_organizations_count': filtered_orgs_count
            }
            
        except Exception as e:
            logger.error(f"Failed to get database info: {e}")
            return {}

class PipedriveDataPuller:
    """Main class for pulling and processing Pipedrive data"""
    
    def __init__(self, api_key: str):
        self.client = PipedriveClient(api_key)
        self.database = PipedriveDatabase()
        self.data = {
            'organizations': [],
            'fields': [],
            'pull_timestamp': datetime.now().isoformat()
        }
    
    def pull_all_data(self) -> Dict[str, Any]:
        """Pull all organizations and their data"""
        try:
            logger.info("Starting data pull from Pipedrive...")
            
            # Clear existing custom fields to prevent duplicates
            logger.info("Clearing existing organization custom fields...")
            self.database.clear_organization_custom_fields()
            
            # Get organization fields
            logger.info("Fetching organization fields...")
            fields = self.client.get_organization_fields()
            self.data['fields'] = fields
            self.database.save_organization_fields(fields)
            
            # Get all organizations
            logger.info("Fetching all organizations...")
            organizations = self.client.get_all_organizations()
            self.data['organizations'] = organizations
            
            # Save organizations to database
            self.database.save_organizations(organizations)
            
            logger.info("Pipedrive data pull completed successfully!")
            return self.data
            
        except Exception as e:
            logger.error(f"Pipedrive data pull failed: {e}")
            raise
    
    def pull_filtered_data(self, filter_url: str) -> Dict[str, Any]:
        """Pull filtered organizations from Pipedrive using a filter URL"""
        try:
            logger.info(f"Starting filtered data pull from Pipedrive with URL: {filter_url}")
            
            # Extract filter ID from URL
            filter_id = self.client.extract_filter_id_from_url(filter_url)
            logger.info(f"Extracted filter ID: {filter_id}")
            
            # Get filter details
            filter_details = self.client.get_filter_details(filter_id)
            filter_name = filter_details.get('name', f'Filter {filter_id}')
            filter_conditions = json.dumps(filter_details.get('conditions', {}))
            
            # Get filtered organizations
            logger.info(f"Fetching organizations with filter: {filter_name}")
            organizations = self.client.get_organizations_by_filter(filter_id)
            
            # Save filter information
            self.database.save_user_filter(
                filter_id=filter_id,
                filter_name=filter_name,
                filter_url=filter_url,
                filter_conditions=filter_conditions,
                organizations_count=len(organizations)
            )
            
            # Save filtered organizations
            self.database.save_filtered_organizations(filter_id, organizations)
            
            # Prepare response data
            filtered_data = {
                'filter_id': filter_id,
                'filter_name': filter_name,
                'filter_url': filter_url,
                'filter_conditions': filter_details.get('conditions', {}),
                'organizations': organizations,
                'organizations_count': len(organizations),
                'pull_timestamp': datetime.now().isoformat()
            }
            
            logger.info(f"Filtered data pull completed successfully! Found {len(organizations)} organizations")
            return filtered_data
            
        except Exception as e:
            logger.error(f"Filtered data pull failed: {e}")
            raise
    
    def get_user_filters(self) -> List[Dict[str, Any]]:
        """Get all user filters"""
        try:
            return self.database.get_user_filters()
        except Exception as e:
            logger.error(f"Failed to get user filters: {e}")
            raise
    
    def get_filtered_organizations(self, filter_id: str) -> List[Dict[str, Any]]:
        """Get organizations for a specific filter"""
        try:
            return self.database.get_filtered_organizations(filter_id)
        except Exception as e:
            logger.error(f"Failed to get filtered organizations: {e}")
            raise
    
    def delete_user_filter(self, filter_id: str):
        """Delete a user filter"""
        try:
            self.database.delete_user_filter(filter_id)
            logger.info(f"Deleted user filter: {filter_id}")
        except Exception as e:
            logger.error(f"Failed to delete user filter: {e}")
            raise
    
    def print_summary(self):
        """Print a summary of the pulled data"""
        print("\n" + "="*60)
        print("PIPEDRIVE DATA PULL SUMMARY")
        print("="*60)
        
        print(f"Total Organizations: {len(self.data['organizations'])}")
        print(f"Total Fields: {len(self.data['fields'])}")
        print(f"Pull Timestamp: {self.data['pull_timestamp']}")
        
        # Get database info
        db_info = self.database.get_database_info()
        print(f"Database: pipedrive.db")
        print(f"Organizations in DB: {db_info.get('organizations_count', 0)}")
        print(f"Fields in DB: {db_info.get('fields_count', 0)}")
        print(f"Custom Fields in DB: {db_info.get('custom_fields_count', 0)}")
        
        # Show sample organizations
        if self.data['organizations']:
            print("\nSample Organizations:")
            print("-" * 60)
            for i, org in enumerate(self.data['organizations'][:5], 1):
                print(f"{i}. {org.get('name', 'N/A')} (ID: {org.get('id', 'N/A')})")
                print(f"   Owner: {org.get('owner_name', 'N/A')}")
                print(f"   Open Deals: {org.get('open_deals_count', 0)}")
                print(f"   Activities: {org.get('activities_count', 0)}")
                print()
        
        # Show field types
        if self.data['fields']:
            print("Field Types:")
            print("-" * 60)
            field_types = {}
            for field in self.data['fields']:
                field_type = field.get('field_type', 'unknown')
                field_types[field_type] = field_types.get(field_type, 0) + 1
            
            for field_type, count in field_types.items():
                print(f"  {field_type}: {count} fields")
