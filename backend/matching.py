#!/usr/bin/env python3
"""
Company Matching Module
Matches organization names from Pipedrive with company names from Lemlist campaigns
"""

import sqlite3
import logging
from typing import Dict, List, Set, Tuple, Any
from datetime import datetime
import os

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('matching.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class CompanyMatcher:
    """Matches companies between Pipedrive and Lemlist databases"""
    
    def __init__(self, pipedrive_db: str = "pipedrive.db", lemlist_db: str = "lemlist_campaigns.db", results_db: str = "results.db"):
        self.pipedrive_db = pipedrive_db
        self.lemlist_db = lemlist_db
        self.results_db = results_db
        
        # Initialize results database
        self._init_results_database()
        
        logger.info("Company matcher initialized")
    
    def _init_results_database(self):
        """Initialize the results database with tables for matching results"""
        try:
            conn = sqlite3.connect(self.results_db)
            cursor = conn.cursor()
            
            # Check if we need to migrate existing database
            self._migrate_database_if_needed(cursor)
            
            # Create matching summary table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS matching_summary (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filter_id TEXT,
                    filter_name TEXT,
                    total_pipedrive_orgs INTEGER,
                    total_lemlist_companies INTEGER,
                    total_lemlist_companies_unique INTEGER,
                    matching_companies INTEGER,
                    non_matching_pipedrive INTEGER,
                    non_matching_lemlist INTEGER,
                    match_percentage REAL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(filter_id)
                )
            ''')
            
            # Create detailed matches table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS detailed_matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filter_id TEXT,
                    pipedrive_org_name TEXT,
                    lemlist_company_name TEXT,
                    campaign_name TEXT,
                    campaign_id TEXT,
                    match_type TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create non-matching Pipedrive organizations table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS non_matching_pipedrive (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filter_id TEXT,
                    org_name TEXT,
                    org_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create non-matching Lemlist companies table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS non_matching_lemlist (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filter_id TEXT,
                    company_name TEXT,
                    campaign_name TEXT,
                    campaign_id TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create table for all unique Lemlist companies (after duplicate removal)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS all_unique_lemlist_companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filter_id TEXT,
                    company_name TEXT,
                    first_seen_campaign TEXT,
                    first_seen_campaign_id TEXT,
                    total_occurrences INTEGER,
                    campaigns_list TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(filter_id, company_name)
                )
            ''')
            
            # Create table for all Lemlist companies before duplicate removal
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS all_lemlist_companies_with_duplicates (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filter_id TEXT,
                    company_name TEXT,
                    campaign_name TEXT,
                    campaign_id TEXT,
                    table_name TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Create table for all matching companies (unique list)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS all_matching_companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filter_id TEXT,
                    company_name TEXT,
                    pipedrive_org_name TEXT,
                    first_seen_campaign TEXT,
                    first_seen_campaign_id TEXT,
                    total_occurrences INTEGER,
                    campaigns_list TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(filter_id, company_name)
                )
            ''')
            
            # Create table for all non-matching Pipedrive organizations (unique list)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS all_non_matching_pipedrive_orgs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filter_id TEXT,
                    org_name TEXT,
                    org_id INTEGER,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(filter_id, org_name)
                )
            ''')
            
            # Create table for all non-matching Lemlist companies (unique list)
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS all_non_matching_lemlist_companies (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    filter_id TEXT,
                    company_name TEXT,
                    first_seen_campaign TEXT,
                    first_seen_campaign_id TEXT,
                    total_occurrences INTEGER,
                    campaigns_list TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(filter_id, company_name)
                )
            ''')
            
            conn.commit()
            conn.close()
            
            logger.info(f"Results database initialized: {self.results_db}")
            
        except Exception as e:
            logger.error(f"Failed to initialize results database: {e}")
            raise
    
    def _migrate_database_if_needed(self, cursor):
        """Migrate existing database to support per-filter results"""
        try:
            # Check if matching_summary table exists and has filter_id column
            cursor.execute("PRAGMA table_info(matching_summary)")
            columns = [column[1] for column in cursor.fetchall()]
            
            if 'matching_summary' in [table[0] for table in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
                if 'filter_id' not in columns:
                    logger.info("Migrating database to support per-filter results...")
                    
                    # Add filter_id column to existing tables
                    try:
                        cursor.execute('ALTER TABLE matching_summary ADD COLUMN filter_id TEXT')
                        logger.info("Added filter_id column to matching_summary")
                    except:
                        pass  # Column might already exist
                    
                    try:
                        cursor.execute('ALTER TABLE detailed_matches ADD COLUMN filter_id TEXT')
                        logger.info("Added filter_id column to detailed_matches")
                    except:
                        pass
                    
                    try:
                        cursor.execute('ALTER TABLE non_matching_pipedrive ADD COLUMN filter_id TEXT')
                        logger.info("Added filter_id column to non_matching_pipedrive")
                    except:
                        pass
                    
                    try:
                        cursor.execute('ALTER TABLE non_matching_lemlist ADD COLUMN filter_id TEXT')
                        logger.info("Added filter_id column to non_matching_lemlist")
                    except:
                        pass
                    
                    try:
                        cursor.execute('ALTER TABLE all_unique_lemlist_companies ADD COLUMN filter_id TEXT')
                        logger.info("Added filter_id column to all_unique_lemlist_companies")
                    except:
                        pass
                    
                    try:
                        cursor.execute('ALTER TABLE all_lemlist_companies_with_duplicates ADD COLUMN filter_id TEXT')
                        logger.info("Added filter_id column to all_lemlist_companies_with_duplicates")
                    except:
                        pass
                    
                    try:
                        cursor.execute('ALTER TABLE all_matching_companies ADD COLUMN filter_id TEXT')
                        logger.info("Added filter_id column to all_matching_companies")
                    except:
                        pass
                    
                    try:
                        cursor.execute('ALTER TABLE all_non_matching_pipedrive_orgs ADD COLUMN filter_id TEXT')
                        logger.info("Added filter_id column to all_non_matching_pipedrive_orgs")
                    except:
                        pass
                    
                    try:
                        cursor.execute('ALTER TABLE all_non_matching_lemlist_companies ADD COLUMN filter_id TEXT')
                        logger.info("Added filter_id column to all_non_matching_lemlist_companies")
                    except:
                        pass
                    
                    logger.info("Database migration completed")
                    
        except Exception as e:
            logger.warning(f"Database migration failed (this is normal for new databases): {e}")
    
    def get_pipedrive_organizations(self, filter_id: str = None) -> List[Dict[str, Any]]:
        """Get organization names from Pipedrive database, optionally filtered"""
        try:
            conn = sqlite3.connect(self.pipedrive_db)
            cursor = conn.cursor()
            
            if filter_id:
                # Get filtered organizations
                cursor.execute('''
                    SELECT fo.org_id, fo.org_name 
                    FROM filtered_organizations fo
                    WHERE fo.filter_id = ? AND fo.org_name IS NOT NULL AND fo.org_name != ""
                ''', (filter_id,))
                logger.info(f"Retrieved filtered organizations for filter: {filter_id}")
            else:
                # Get all organizations
                cursor.execute('SELECT id, name FROM organizations WHERE name IS NOT NULL AND name != ""')
                logger.info("Retrieved all organizations from Pipedrive")
            
            organizations = cursor.fetchall()
            conn.close()
            
            logger.info(f"Retrieved {len(organizations)} organizations from Pipedrive")
            return [{'id': org[0], 'name': org[1]} for org in organizations]
            
        except Exception as e:
            logger.error(f"Failed to get Pipedrive organizations: {e}")
            raise
    
    def get_lemlist_company_names(self) -> List[Dict[str, Any]]:
        """Get all company names from all Lemlist campaigns"""
        try:
            conn = sqlite3.connect(self.lemlist_db)
            cursor = conn.cursor()
            
            # Get all campaign table names
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'campaign_%'")
            table_names = [row[0] for row in cursor.fetchall()]
            
            all_companies = []
            
            for table_name in table_names:
                try:
                    # Get campaign info from campaigns_overview
                    cursor.execute('''
                        SELECT id, name FROM campaigns_overview 
                        WHERE table_name = ?
                    ''', (table_name,))
                    campaign_info = cursor.fetchone()
                    
                    if campaign_info:
                        campaign_id, campaign_name = campaign_info
                        
                        # Get company names from this campaign table
                        cursor.execute(f'SELECT companyName FROM "{table_name}" WHERE companyName IS NOT NULL AND companyName != ""')
                        companies = cursor.fetchall()
                        
                        for company in companies:
                            all_companies.append({
                                'company_name': company[0],
                                'campaign_id': campaign_id,
                                'campaign_name': campaign_name,
                                'table_name': table_name
                            })
                            
                except Exception as e:
                    logger.warning(f"Failed to process table {table_name}: {e}")
                    continue
            
            conn.close()
            
            logger.info(f"Retrieved {len(all_companies)} company names from Lemlist campaigns")
            return all_companies
            
        except Exception as e:
            logger.error(f"Failed to get Lemlist company names: {e}")
            raise
    
    def perform_matching(self, filter_id: str = None) -> Dict[str, Any]:
        """Perform the matching between Pipedrive and Lemlist companies"""
        try:
            if filter_id:
                logger.info(f"Starting filtered company matching process with filter: {filter_id}")
            else:
                logger.info("Starting company matching process with all organizations...")
            
            # Get data from both databases
            pipedrive_orgs = self.get_pipedrive_organizations(filter_id)
            lemlist_companies = self.get_lemlist_company_names()
            
            # Create sets for matching
            pipedrive_names = {org['name'].strip().lower() for org in pipedrive_orgs}
            lemlist_names = {company['company_name'].strip().lower() for company in lemlist_companies}
            
            # Find matches
            matching_names = pipedrive_names.intersection(lemlist_names)
            
            # Calculate statistics
            total_pipedrive = len(pipedrive_orgs)
            total_lemlist = len(lemlist_companies)
            total_lemlist_unique = len(lemlist_names)
            matching_count = len(matching_names)
            non_matching_pipedrive = total_pipedrive - matching_count
            non_matching_lemlist = total_lemlist_unique - matching_count
            match_percentage = (matching_count / total_pipedrive * 100) if total_pipedrive > 0 else 0
            
            # Create detailed matches
            detailed_matches = []
            non_matching_pipedrive_list = []
            non_matching_lemlist_list = []
            
            # Process matches
            for pipedrive_org in pipedrive_orgs:
                org_name_lower = pipedrive_org['name'].strip().lower()
                if org_name_lower in matching_names:
                    # Find all Lemlist companies that match this org
                    matching_lemlist = [comp for comp in lemlist_companies 
                                     if comp['company_name'].strip().lower() == org_name_lower]
                    
                    for lemlist_comp in matching_lemlist:
                        detailed_matches.append({
                            'pipedrive_org_name': pipedrive_org['name'],
                            'lemlist_company_name': lemlist_comp['company_name'],
                            'campaign_name': lemlist_comp['campaign_name'],
                            'campaign_id': lemlist_comp['campaign_id'],
                            'match_type': 'exact'
                        })
                else:
                    non_matching_pipedrive_list.append({
                        'org_name': pipedrive_org['name'],
                        'org_id': pipedrive_org['id']
                    })
            
            # Process non-matching Lemlist companies
            for lemlist_comp in lemlist_companies:
                company_name_lower = lemlist_comp['company_name'].strip().lower()
                if company_name_lower not in matching_names:
                    non_matching_lemlist_list.append({
                        'company_name': lemlist_comp['company_name'],
                        'campaign_name': lemlist_comp['campaign_name'],
                        'campaign_id': lemlist_comp['campaign_id']
                    })
            
            # Create unique lists for detailed analysis
            unique_lemlist_companies = {}
            matching_companies = {}
            non_matching_pipedrive_unique = []
            non_matching_lemlist_unique = {}
            
            # Process unique Lemlist companies
            for lemlist_comp in lemlist_companies:
                company_name_lower = lemlist_comp['company_name'].strip().lower()
                company_name_original = lemlist_comp['company_name'].strip()
                
                if company_name_lower not in unique_lemlist_companies:
                    unique_lemlist_companies[company_name_lower] = {
                        'first_seen_campaign': lemlist_comp['campaign_name'],
                        'first_seen_campaign_id': lemlist_comp['campaign_id'],
                        'total_occurrences': 1,
                        'campaigns_list': lemlist_comp['campaign_name']
                    }
                else:
                    unique_lemlist_companies[company_name_lower]['total_occurrences'] += 1
                    if lemlist_comp['campaign_name'] not in unique_lemlist_companies[company_name_lower]['campaigns_list']:
                        unique_lemlist_companies[company_name_lower]['campaigns_list'] += f", {lemlist_comp['campaign_name']}"
            
            # Process matching companies
            for company_name_lower in matching_names:
                # Find original case version
                original_company = next((comp for comp in lemlist_companies 
                                       if comp['company_name'].strip().lower() == company_name_lower), None)
                if original_company:
                    matching_companies[company_name_lower] = {
                        'pipedrive_org_name': next((org['name'] for org in pipedrive_orgs 
                                                   if org['name'].strip().lower() == company_name_lower), ''),
                        'first_seen_campaign': original_company['campaign_name'],
                        'first_seen_campaign_id': original_company['campaign_id'],
                        'total_occurrences': unique_lemlist_companies[company_name_lower]['total_occurrences'],
                        'campaigns_list': unique_lemlist_companies[company_name_lower]['campaigns_list']
                    }
            
            # Process non-matching Pipedrive organizations (unique)
            seen_orgs = set()
            for org in non_matching_pipedrive_list:
                org_name_lower = org['org_name'].strip().lower()
                if org_name_lower not in seen_orgs:
                    non_matching_pipedrive_unique.append(org)
                    seen_orgs.add(org_name_lower)
            
            # Process non-matching Lemlist companies (unique)
            for company_name_lower, comp_info in unique_lemlist_companies.items():
                if company_name_lower not in matching_names:
                    non_matching_lemlist_unique[company_name_lower] = comp_info
            
            # Store results in database
            self._store_results(
                total_pipedrive, total_lemlist, total_lemlist_unique,
                matching_count, non_matching_pipedrive, non_matching_lemlist,
                match_percentage, detailed_matches, non_matching_pipedrive_list,
                non_matching_lemlist_list, lemlist_companies, unique_lemlist_companies,
                matching_companies, non_matching_pipedrive_unique, non_matching_lemlist_unique,
                filter_id
            )
            
            results = {
                'total_pipedrive_orgs': total_pipedrive,
                'total_lemlist_companies': total_lemlist,
                'total_lemlist_companies_unique': total_lemlist_unique,
                'matching_companies': matching_count,
                'non_matching_pipedrive': non_matching_pipedrive,
                'non_matching_lemlist': non_matching_lemlist,
                'match_percentage': match_percentage,
                'detailed_matches_count': len(detailed_matches),
                'non_matching_pipedrive_count': len(non_matching_pipedrive_list),
                'non_matching_lemlist_count': len(non_matching_lemlist_list)
            }
            
            logger.info("Company matching completed successfully!")
            return results
            
        except Exception as e:
            logger.error(f"Company matching failed: {e}")
            raise
    
    def _store_results(self, total_pipedrive: int, total_lemlist: int, total_lemlist_unique: int,
                      matching_count: int, non_matching_pipedrive: int, non_matching_lemlist: int,
                      match_percentage: float, detailed_matches: List[Dict], 
                      non_matching_pipedrive_list: List[Dict], non_matching_lemlist_list: List[Dict],
                      all_lemlist_companies: List[Dict], unique_lemlist_companies: Dict[str, Dict],
                      matching_companies: Dict[str, Dict], non_matching_pipedrive_unique: List[Dict],
                      non_matching_lemlist_unique: List[Dict], filter_id: str = None):
        """Store matching results in the results database"""
        try:
            conn = sqlite3.connect(self.results_db)
            cursor = conn.cursor()
            
            # Clear existing data for this specific filter (or all data if no filter)
            if filter_id:
                cursor.execute('DELETE FROM matching_summary WHERE filter_id = ?', (filter_id,))
                cursor.execute('DELETE FROM detailed_matches WHERE filter_id = ?', (filter_id,))
                cursor.execute('DELETE FROM non_matching_pipedrive WHERE filter_id = ?', (filter_id,))
                cursor.execute('DELETE FROM non_matching_lemlist WHERE filter_id = ?', (filter_id,))
                cursor.execute('DELETE FROM all_unique_lemlist_companies WHERE filter_id = ?', (filter_id,))
                cursor.execute('DELETE FROM all_lemlist_companies_with_duplicates WHERE filter_id = ?', (filter_id,))
                cursor.execute('DELETE FROM all_matching_companies WHERE filter_id = ?', (filter_id,))
                cursor.execute('DELETE FROM all_non_matching_pipedrive_orgs WHERE filter_id = ?', (filter_id,))
                cursor.execute('DELETE FROM all_non_matching_lemlist_companies WHERE filter_id = ?', (filter_id,))
            else:
                # For "all organizations" matching, clear all data
                cursor.execute('DELETE FROM matching_summary WHERE filter_id IS NULL')
                cursor.execute('DELETE FROM detailed_matches WHERE filter_id IS NULL')
                cursor.execute('DELETE FROM non_matching_pipedrive WHERE filter_id IS NULL')
                cursor.execute('DELETE FROM non_matching_lemlist WHERE filter_id IS NULL')
                cursor.execute('DELETE FROM all_unique_lemlist_companies WHERE filter_id IS NULL')
                cursor.execute('DELETE FROM all_lemlist_companies_with_duplicates WHERE filter_id IS NULL')
                cursor.execute('DELETE FROM all_matching_companies WHERE filter_id IS NULL')
                cursor.execute('DELETE FROM all_non_matching_pipedrive_orgs WHERE filter_id IS NULL')
                cursor.execute('DELETE FROM all_non_matching_lemlist_companies WHERE filter_id IS NULL')
            
            # Get filter name if filter_id is provided
            filter_name = None
            if filter_id:
                try:
                    pipedrive_conn = sqlite3.connect(self.pipedrive_db)
                    pipedrive_cursor = pipedrive_conn.cursor()
                    pipedrive_cursor.execute('SELECT filter_name FROM user_filters WHERE filter_id = ?', (filter_id,))
                    filter_result = pipedrive_cursor.fetchone()
                    if filter_result:
                        filter_name = filter_result[0]
                    pipedrive_conn.close()
                except Exception as e:
                    logger.warning(f"Could not get filter name for {filter_id}: {e}")
            
            # Insert summary
            cursor.execute('''
                INSERT INTO matching_summary 
                (filter_id, filter_name, total_pipedrive_orgs, total_lemlist_companies, total_lemlist_companies_unique,
                 matching_companies, non_matching_pipedrive, non_matching_lemlist, match_percentage)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (filter_id, filter_name, total_pipedrive, total_lemlist, total_lemlist_unique, matching_count,
                  non_matching_pipedrive, non_matching_lemlist, match_percentage))
            
            # Insert detailed matches
            for match in detailed_matches:
                cursor.execute('''
                    INSERT INTO detailed_matches 
                    (filter_id, pipedrive_org_name, lemlist_company_name, campaign_name, campaign_id, match_type)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (filter_id, match['pipedrive_org_name'], match['lemlist_company_name'],
                      match['campaign_name'], match['campaign_id'], match['match_type']))
            
            # Insert non-matching Pipedrive organizations
            for org in non_matching_pipedrive_list:
                cursor.execute('''
                    INSERT INTO non_matching_pipedrive (filter_id, org_name, org_id)
                    VALUES (?, ?, ?)
                ''', (filter_id, org['org_name'], org['org_id']))
            
            # Insert non-matching Lemlist companies
            for comp in non_matching_lemlist_list:
                cursor.execute('''
                    INSERT INTO non_matching_lemlist (filter_id, company_name, campaign_name, campaign_id)
                    VALUES (?, ?, ?, ?)
                ''', (filter_id, comp['company_name'], comp['campaign_name'], comp['campaign_id']))
            
            # Insert all Lemlist companies with duplicates (before removal)
            for comp in all_lemlist_companies:
                cursor.execute('''
                    INSERT INTO all_lemlist_companies_with_duplicates 
                    (filter_id, company_name, campaign_name, campaign_id, table_name)
                    VALUES (?, ?, ?, ?, ?)
                ''', (filter_id, comp['company_name'], comp['campaign_name'], comp['campaign_id'], comp['table_name']))
            
            # Insert unique Lemlist companies (after duplicate removal)
            for company_name, comp_info in unique_lemlist_companies.items():
                cursor.execute('''
                    INSERT INTO all_unique_lemlist_companies 
                    (filter_id, company_name, first_seen_campaign, first_seen_campaign_id, total_occurrences, campaigns_list)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (filter_id, company_name, comp_info['first_seen_campaign'], comp_info['first_seen_campaign_id'], 
                      comp_info['total_occurrences'], comp_info['campaigns_list']))
            
            # Insert matching companies (unique list)
            for company_name, match_info in matching_companies.items():
                cursor.execute('''
                    INSERT INTO all_matching_companies 
                    (filter_id, company_name, pipedrive_org_name, first_seen_campaign, first_seen_campaign_id, 
                     total_occurrences, campaigns_list)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''', (filter_id, company_name, match_info['pipedrive_org_name'], match_info['first_seen_campaign'], 
                      match_info['first_seen_campaign_id'], match_info['total_occurrences'], match_info['campaigns_list']))
            
            # Insert non-matching Pipedrive organizations (unique list)
            for org in non_matching_pipedrive_unique:
                cursor.execute('''
                    INSERT INTO all_non_matching_pipedrive_orgs (filter_id, org_name, org_id)
                    VALUES (?, ?, ?)
                ''', (filter_id, org['org_name'], org['org_id']))
            
            # Insert non-matching Lemlist companies (unique list)
            for company_name, comp_info in non_matching_lemlist_unique.items():
                cursor.execute('''
                    INSERT INTO all_non_matching_lemlist_companies 
                    (filter_id, company_name, first_seen_campaign, first_seen_campaign_id, total_occurrences, campaigns_list)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (filter_id, company_name, comp_info['first_seen_campaign'], comp_info['first_seen_campaign_id'], 
                      comp_info['total_occurrences'], comp_info['campaigns_list']))
            
            conn.commit()
            conn.close()
            
            logger.info("Results stored in database successfully")
            
        except Exception as e:
            logger.error(f"Failed to store results: {e}")
            raise
    
    def print_summary(self, filter_id: str = None):
        """Print a summary of the matching results"""
        try:
            conn = sqlite3.connect(self.results_db)
            cursor = conn.cursor()
            
            # Get summary data for specific filter or latest
            if filter_id:
                cursor.execute('SELECT * FROM matching_summary WHERE filter_id = ? ORDER BY created_at DESC LIMIT 1', (filter_id,))
            else:
                cursor.execute('SELECT * FROM matching_summary WHERE filter_id IS NULL OR filter_id = "" ORDER BY created_at DESC LIMIT 1')
            
            summary = cursor.fetchone()
            
            if not summary:
                if filter_id:
                    print(f"No matching results found for filter {filter_id}. Run perform_matching() first.")
                else:
                    print("No matching results found. Run perform_matching() first.")
                return
            
            # Handle different column orders based on database schema
            if len(summary) == 11:  # New schema with filter_id and filter_name
                (_, total_pipedrive, total_lemlist, total_lemlist_unique, matching_count,
                 non_matching_pipedrive, non_matching_lemlist, match_percentage, created_at, filter_id_result, filter_name) = summary
            else:  # Old schema without filter_id and filter_name
                (_, total_pipedrive, total_lemlist, total_lemlist_unique, matching_count,
                 non_matching_pipedrive, non_matching_lemlist, match_percentage, created_at) = summary
                filter_id_result = None
                filter_name = None
            
            print("\n" + "="*70)
            print("COMPANY MATCHING RESULTS SUMMARY")
            print("="*70)
            print(f"Analysis Date: {created_at}")
            if filter_name:
                print(f"Filter: {filter_name} (ID: {filter_id_result})")
            else:
                print("All Organizations (No Filter)")
            print()
            print("DATABASE STATISTICS:")
            print("-" * 40)
            print(f"Total Pipedrive Organizations: {total_pipedrive:,}")
            print(f"Total Lemlist Companies: {total_lemlist:,}")
            print(f"Unique Lemlist Companies: {total_lemlist_unique:,}")
            print()
            print("MATCHING RESULTS:")
            print("-" * 40)
            print(f"Matching Companies: {matching_count:,}")
            print(f"Non-matching Pipedrive: {non_matching_pipedrive:,}")
            print(f"Non-matching Lemlist: {non_matching_lemlist:,}")
            print(f"Match Percentage: {match_percentage:.2f}%")
            print()
            print("DETAILED BREAKDOWN:")
            print("-" * 40)
            print(f"Pipedrive Coverage: {matching_count}/{total_pipedrive} ({(matching_count/total_pipedrive*100):.2f}%)")
            print(f"Lemlist Coverage: {matching_count}/{total_lemlist_unique} ({(matching_count/total_lemlist_unique*100):.2f}%)")
            
            # Show sample matches
            if filter_id_result:
                cursor.execute('SELECT pipedrive_org_name, lemlist_company_name, campaign_name FROM detailed_matches WHERE filter_id = ? LIMIT 10', (filter_id_result,))
            else:
                cursor.execute('SELECT pipedrive_org_name, lemlist_company_name, campaign_name FROM detailed_matches WHERE filter_id IS NULL OR filter_id = "" LIMIT 10')
            sample_matches = cursor.fetchall()
            
            if sample_matches:
                print("\nSAMPLE MATCHES:")
                print("-" * 40)
                for i, (pipedrive_name, lemlist_name, campaign_name) in enumerate(sample_matches, 1):
                    print(f"{i:2d}. {pipedrive_name} ↔ {lemlist_name} ({campaign_name})")
            
            # Show detailed table counts
            print("\nDETAILED TABLES:")
            print("-" * 40)
            
            # Count records in each detailed table for this filter
            if filter_id_result:
                cursor.execute('SELECT COUNT(*) FROM all_lemlist_companies_with_duplicates WHERE filter_id = ?', (filter_id_result,))
                total_with_duplicates = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM all_unique_lemlist_companies WHERE filter_id = ?', (filter_id_result,))
                unique_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM all_matching_companies WHERE filter_id = ?', (filter_id_result,))
                matching_unique_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM all_non_matching_pipedrive_orgs WHERE filter_id = ?', (filter_id_result,))
                non_matching_pipedrive_unique_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM all_non_matching_lemlist_companies WHERE filter_id = ?', (filter_id_result,))
                non_matching_lemlist_unique_count = cursor.fetchone()[0]
            else:
                cursor.execute('SELECT COUNT(*) FROM all_lemlist_companies_with_duplicates WHERE filter_id IS NULL OR filter_id = ""')
                total_with_duplicates = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM all_unique_lemlist_companies WHERE filter_id IS NULL OR filter_id = ""')
                unique_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM all_matching_companies WHERE filter_id IS NULL OR filter_id = ""')
                matching_unique_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM all_non_matching_pipedrive_orgs WHERE filter_id IS NULL OR filter_id = ""')
                non_matching_pipedrive_unique_count = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM all_non_matching_lemlist_companies WHERE filter_id IS NULL OR filter_id = ""')
                non_matching_lemlist_unique_count = cursor.fetchone()[0]
            
            print(f"All Lemlist Companies (with duplicates): {total_with_duplicates:,}")
            print(f"Unique Lemlist Companies: {unique_count:,}")
            print(f"Matching Companies (unique): {matching_unique_count:,}")
            print(f"Non-matching Pipedrive (unique): {non_matching_pipedrive_unique_count:,}")
            print(f"Non-matching Lemlist (unique): {non_matching_lemlist_unique_count:,}")
            
            print(f"\n📊 Detailed company lists are available in the following tables:")
            print(f"   • all_lemlist_companies_with_duplicates - All companies before duplicate removal")
            print(f"   • all_unique_lemlist_companies - Unique companies after duplicate removal")
            print(f"   • all_matching_companies - Companies that have matches")
            print(f"   • all_non_matching_pipedrive_orgs - Pipedrive orgs without matches")
            print(f"   • all_non_matching_lemlist_companies - Lemlist companies without matches")
            
            conn.close()
            
        except Exception as e:
            logger.error(f"Failed to print summary: {e}")
            print(f"Error printing summary: {e}")
    
    def has_existing_results(self, filter_id: str = None) -> bool:
        """Check if results already exist for a filter"""
        try:
            conn = sqlite3.connect(self.results_db)
            cursor = conn.cursor()
            
            if filter_id:
                cursor.execute('SELECT COUNT(*) FROM matching_summary WHERE filter_id = ?', (filter_id,))
            else:
                # For "all organizations", check for NULL filter_id or empty string
                cursor.execute('SELECT COUNT(*) FROM matching_summary WHERE filter_id IS NULL OR filter_id = ""')
            
            count = cursor.fetchone()[0]
            conn.close()
            
            return count > 0
            
        except Exception as e:
            logger.error(f"Failed to check existing results: {e}")
            return False
    
    def get_existing_results(self, filter_id: str = None) -> Dict[str, Any]:
        """Get existing results for a filter without running matching again"""
        try:
            conn = sqlite3.connect(self.results_db)
            cursor = conn.cursor()
            
            # Get summary data
            if filter_id:
                cursor.execute('SELECT * FROM matching_summary WHERE filter_id = ? ORDER BY created_at DESC LIMIT 1', (filter_id,))
            else:
                # For "all organizations", check for NULL filter_id or empty string
                cursor.execute('SELECT * FROM matching_summary WHERE filter_id IS NULL OR filter_id = "" ORDER BY created_at DESC LIMIT 1')
            
            summary = cursor.fetchone()
            
            if not summary:
                return {'error': f'No results found for filter {filter_id}' if filter_id else 'No results found'}
            
            # Handle different column orders based on database schema
            if len(summary) == 11:  # New schema with filter_id and filter_name
                (_, total_pipedrive, total_lemlist, total_lemlist_unique, matching_count,
                 non_matching_pipedrive, non_matching_lemlist, match_percentage, created_at, filter_id_result, filter_name) = summary
            else:  # Old schema without filter_id and filter_name
                (_, total_pipedrive, total_lemlist, total_lemlist_unique, matching_count,
                 non_matching_pipedrive, non_matching_lemlist, match_percentage, created_at) = summary
                filter_id_result = None
                filter_name = None
            
            # Get detailed matches count
            if filter_id_result:
                cursor.execute('SELECT COUNT(*) FROM detailed_matches WHERE filter_id = ?', (filter_id_result,))
            else:
                cursor.execute('SELECT COUNT(*) FROM detailed_matches WHERE filter_id IS NULL OR filter_id = ""')
            detailed_matches_count = cursor.fetchone()[0]
            
            conn.close()
            
            return {
                'filter_id': filter_id_result,
                'filter_name': filter_name,
                'total_pipedrive_orgs': total_pipedrive,
                'total_lemlist_companies': total_lemlist,
                'total_lemlist_companies_unique': total_lemlist_unique,
                'matching_companies': matching_count,
                'non_matching_pipedrive': non_matching_pipedrive,
                'non_matching_lemlist': non_matching_lemlist,
                'match_percentage': match_percentage,
                'detailed_matches_count': detailed_matches_count,
                'created_at': created_at,
                'status': 'retrieved_from_cache'
            }
            
        except Exception as e:
            logger.error(f"Failed to get existing results: {e}")
            return {'error': str(e)}
    
    def list_all_filters_with_results(self) -> List[Dict[str, Any]]:
        """List all filters that have matching results"""
        try:
            conn = sqlite3.connect(self.results_db)
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT filter_id, filter_name, matching_companies, match_percentage, created_at
                FROM matching_summary 
                ORDER BY created_at DESC
            ''')
            
            results = []
            for row in cursor.fetchall():
                filter_id, filter_name, matching_companies, match_percentage, created_at = row
                results.append({
                    'filter_id': filter_id,
                    'filter_name': filter_name or 'All Organizations',
                    'matching_companies': matching_companies,
                    'match_percentage': match_percentage,
                    'created_at': created_at
                })
            
            conn.close()
            return results
            
        except Exception as e:
            logger.error(f"Failed to list filters with results: {e}")
            return []

def main():
    """Main function to run the matching process"""
    try:
        # Check if databases exist
        if not os.path.exists("pipedrive.db"):
            print("❌ pipedrive.db not found!")
            return 1
        
        if not os.path.exists("lemlist_campaigns.db"):
            print("❌ lemlist_campaigns.db not found!")
            return 1
        
        # Initialize matcher
        matcher = CompanyMatcher()
        
        # Check if results already exist for "All Organizations" (filter_id = None)
        if matcher.has_existing_results(filter_id=None):
            print("✅ Found existing results for All Organizations, retrieving from cache...")
            matcher.print_summary(filter_id=None)
            print(f"\n✅ Results retrieved from cache!")
            print(f"📊 Results loaded from: results.db")
        else:
            # Perform matching
            print("🔄 Starting company matching process...")
            results = matcher.perform_matching()
            
            # Print summary
            matcher.print_summary()
            
            print(f"\n✅ Matching completed successfully!")
            print(f"📊 Results saved to: results.db")
        
        return 0
        
    except Exception as e:
        logger.error(f"Application failed: {e}")
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
