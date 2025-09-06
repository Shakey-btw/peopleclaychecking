#!/usr/bin/env python3
"""
Database Explorer for Lemlist Campaigns Database
Helps you explore the single database with multiple campaign tables
"""

import sqlite3
import os
from typing import List, Dict, Any

def get_database_info(db_path: str = "lemlist_campaigns.db") -> Dict[str, Any]:
    """Get information about the database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Get campaigns overview
        cursor.execute('SELECT * FROM campaigns_overview ORDER BY name')
        campaigns = cursor.fetchall()
        
        # Get all campaign table names
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
        return {'error': str(e)}

def query_database(db_path: str, query: str) -> List[tuple]:
    """Execute a query on the database"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(query)
        results = cursor.fetchall()
        conn.close()
        return results
    except Exception as e:
        print(f"Query error: {e}")
        return []

def get_table_schema(db_path: str, table_name: str) -> List[tuple]:
    """Get schema information for a specific table"""
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        cursor.execute(f"PRAGMA table_info({table_name})")
        schema = cursor.fetchall()
        conn.close()
        return schema
    except Exception as e:
        print(f"Schema error: {e}")
        return []

def main():
    """Main function"""
    db_path = "lemlist_campaigns.db"
    
    if not os.path.exists(db_path):
        print(f"Database file {db_path} not found!")
        print("Run main.py first to create the database")
        return
    
    print("🔍 Lemlist Campaigns Database Explorer")
    print("=" * 50)
    
    # Get database info
    info = get_database_info(db_path)
    
    if 'error' in info:
        print(f"Error: {info['error']}")
        return
    
    print(f"Database: {db_path}")
    print(f"Campaigns: {info['campaigns_count']}")
    print(f"Tables: {info['tables_count']}")
    print()
    
    # Show campaigns overview
    print("Campaigns Overview:")
    print("-" * 50)
    print(f"{'#':<3} {'Name':<40} {'Status':<10} {'Table':<30} {'Leads':<8}")
    print("-" * 50)
    
    for i, campaign in enumerate(info['campaigns'], 1):
        campaign_id, name, status, table_name, leads_count, columns_count, created_at, last_updated = campaign
        print(f"{i:<3} {name[:39]:<40} {status:<10} {table_name[:29]:<30} {leads_count:<8}")
    
    print()
    
    # Interactive query mode
    while True:
        print("=" * 50)
        print("Interactive Query Mode")
        print("=" * 50)
        print("Commands:")
        print("  list - List all campaigns")
        print("  info <number> - Show detailed info for campaign")
        print("  schema <number> - Show table schema")
        print("  sample <number> - Show sample leads")
        print("  query <sql> - Execute SQL query")
        print("  tables - List all table names")
        print("  quit - Exit")
        print()
        
        try:
            command = input("Enter command: ").strip().split()
            
            if not command:
                continue
            
            if command[0] == 'quit':
                break
            elif command[0] == 'list':
                print("\nCampaigns:")
                for i, campaign in enumerate(info['campaigns'], 1):
                    campaign_id, name, status, table_name, leads_count, columns_count, created_at, last_updated = campaign
                    print(f"{i}. {name} ({status}) - {leads_count} leads")
            elif command[0] == 'tables':
                print("\nTable Names:")
                for table_name in info['table_names']:
                    print(f"  {table_name}")
            elif command[0] == 'info' and len(command) > 1:
                try:
                    campaign_index = int(command[1]) - 1
                    if 0 <= campaign_index < len(info['campaigns']):
                        campaign = info['campaigns'][campaign_index]
                        campaign_id, name, status, table_name, leads_count, columns_count, created_at, last_updated = campaign
                        
                        print(f"\nCampaign Details:")
                        print(f"  ID: {campaign_id}")
                        print(f"  Name: {name}")
                        print(f"  Status: {status}")
                        print(f"  Table: {table_name}")
                        print(f"  Leads: {leads_count}")
                        print(f"  Columns: {columns_count}")
                        print(f"  Created: {created_at}")
                        print(f"  Updated: {last_updated}")
                    else:
                        print("Invalid campaign number")
                except ValueError:
                    print("Invalid campaign number")
            elif command[0] == 'schema' and len(command) > 1:
                try:
                    campaign_index = int(command[1]) - 1
                    if 0 <= campaign_index < len(info['campaigns']):
                        campaign = info['campaigns'][campaign_index]
                        table_name = campaign[3]  # table_name is at index 3
                        
                        schema = get_table_schema(db_path, table_name)
                        print(f"\nSchema for table '{table_name}':")
                        print("-" * 50)
                        print(f"{'Column':<25} {'Type':<10} {'Null':<5} {'Default':<10}")
                        print("-" * 50)
                        for col in schema:
                            cid, name, col_type, notnull, default_value, pk = col
                            print(f"{name:<25} {col_type:<10} {'No' if notnull else 'Yes':<5} {str(default_value or ''):<10}")
                    else:
                        print("Invalid campaign number")
                except ValueError:
                    print("Invalid campaign number")
            elif command[0] == 'sample' and len(command) > 1:
                try:
                    campaign_index = int(command[1]) - 1
                    if 0 <= campaign_index < len(info['campaigns']):
                        campaign = info['campaigns'][campaign_index]
                        table_name = campaign[3]  # table_name is at index 3
                        
                        results = query_database(db_path, f"SELECT * FROM {table_name} LIMIT 5")
                        
                        print(f"\nSample leads from table '{table_name}':")
                        print("-" * 50)
                        
                        if results:
                            # Get column names
                            schema = get_table_schema(db_path, table_name)
                            columns = [col[1] for col in schema]
                            
                            # Print header
                            print(" | ".join(columns[:5]))  # Show first 5 columns
                            print("-" * 50)
                            
                            # Print sample data
                            for row in results:
                                print(" | ".join(str(cell)[:20] for cell in row[:5]))  # Show first 5 columns
                        else:
                            print("No leads found")
                    else:
                        print("Invalid campaign number")
                except ValueError:
                    print("Invalid campaign number")
            elif command[0] == 'query' and len(command) > 1:
                sql_query = " ".join(command[1:])
                
                print(f"\nExecuting query:")
                print(f"SQL: {sql_query}")
                print("-" * 50)
                
                results = query_database(db_path, sql_query)
                
                if results:
                    for row in results:
                        print(" | ".join(str(cell) for cell in row))
                else:
                    print("No results")
            else:
                print("Unknown command")
                
        except KeyboardInterrupt:
            print("\nExiting...")
            break
        except Exception as e:
            print(f"Error: {e}")

if __name__ == "__main__":
    main()
