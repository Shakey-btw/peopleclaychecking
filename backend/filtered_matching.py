#!/usr/bin/env python3
"""
Filtered Matching Module
Handles filtered Pipedrive data matching with Lemlist campaigns
"""

import logging
from typing import Dict, Any, Optional, List
from main import DataSyncOrchestrator
from matching import CompanyMatcher

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('filtered_matching.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class FilteredMatchingOrchestrator:
    """Orchestrator for filtered matching operations"""
    
    def __init__(self, lemlist_api_key: str, pipedrive_api_key: str = None):
        self.orchestrator = DataSyncOrchestrator(lemlist_api_key, pipedrive_api_key)
        self.matcher = CompanyMatcher()
        logger.info("Filtered matching orchestrator initialized")
    
    def process_filter_url(self, filter_url: str, status_filter: Optional[str] = None, force_refresh: bool = False) -> Dict[str, Any]:
        """Process a Pipedrive filter URL and perform matching"""
        try:
            logger.info(f"Processing filter URL: {filter_url}")
            
            # Step 1: Extract filter ID to check for existing results
            filter_id = self.orchestrator.pipedrive_puller.client.extract_filter_id_from_url(filter_url)
            
            # Step 2: Check if results already exist for this filter
            if not force_refresh and self.matcher.has_existing_results(filter_id):
                logger.info(f"Found existing results for filter {filter_id}, retrieving from cache...")
                existing_results = self.matcher.get_existing_results(filter_id)
                
                if 'error' not in existing_results:
                    # Get filter info from Pipedrive database
                    try:
                        filter_info = self.orchestrator.pipedrive_puller.database.get_user_filters()
                        filter_name = next((f['filter_name'] for f in filter_info if f['filter_id'] == filter_id), f'Filter {filter_id}')
                        organizations_count = next((f['organizations_count'] for f in filter_info if f['filter_id'] == filter_id), 0)
                    except:
                        filter_name = f'Filter {filter_id}'
                        organizations_count = 0
                    
                    return {
                        'matching_result': existing_results,
                        'filter_id': filter_id,
                        'filter_name': filter_name,
                        'organizations_count': organizations_count,
                        'status': 'retrieved_from_cache',
                        'message': 'Results retrieved from existing cache. Use force_refresh=True to recalculate.'
                    }
            
            # Step 3: Sync filtered data from Pipedrive (only if no existing results or force refresh)
            logger.info(f"Syncing filtered data for filter: {filter_id}")
            sync_result = self.orchestrator.sync_filtered_data(filter_url, status_filter)
            
            if 'error' in sync_result:
                return sync_result
            
            filtered_data = sync_result['filtered_pipedrive_data']
            
            # Step 4: Perform matching with filtered data
            logger.info(f"Starting matching with filter: {filter_id}")
            matching_result = self.matcher.perform_matching(filter_id)
            
            # Step 5: Print summary
            self.matcher.print_summary(filter_id)
            
            return {
                'sync_result': sync_result,
                'matching_result': matching_result,
                'filter_id': filter_id,
                'filter_name': filtered_data['filter_name'],
                'organizations_count': filtered_data['organizations_count'],
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Filter processing failed: {e}")
            raise
    
    def get_user_filters(self) -> list:
        """Get all user filters"""
        try:
            return self.orchestrator.get_user_filters()
        except Exception as e:
            logger.error(f"Failed to get user filters: {e}")
            return []
    
    def delete_user_filter(self, filter_id: str):
        """Delete a user filter"""
        try:
            self.orchestrator.delete_user_filter(filter_id)
            logger.info(f"Deleted user filter: {filter_id}")
        except Exception as e:
            logger.error(f"Failed to delete user filter: {e}")
            raise
    
    def list_filters_with_results(self) -> List[Dict[str, Any]]:
        """List all filters that have matching results"""
        try:
            return self.matcher.list_all_filters_with_results()
        except Exception as e:
            logger.error(f"Failed to list filters with results: {e}")
            return []
    
    def run_matching_with_existing_filter(self, filter_id: str, force_refresh: bool = False) -> Dict[str, Any]:
        """Run matching with an existing filter"""
        try:
            logger.info(f"Running matching with existing filter: {filter_id}")
            
            # Check if results already exist for this filter
            if not force_refresh and self.matcher.has_existing_results(filter_id):
                logger.info(f"Found existing results for filter {filter_id}, retrieving from cache...")
                existing_results = self.matcher.get_existing_results(filter_id)
                
                if 'error' not in existing_results:
                    # Get filter info from Pipedrive database
                    try:
                        filter_info = self.orchestrator.pipedrive_puller.database.get_user_filters()
                        filter_name = next((f['filter_name'] for f in filter_info if f['filter_id'] == filter_id), f'Filter {filter_id}')
                        organizations_count = next((f['organizations_count'] for f in filter_info if f['filter_id'] == filter_id), 0)
                    except:
                        filter_name = f'Filter {filter_id}'
                        organizations_count = 0
                    
                    return {
                        'matching_result': existing_results,
                        'filter_id': filter_id,
                        'filter_name': filter_name,
                        'organizations_count': organizations_count,
                        'status': 'retrieved_from_cache',
                        'message': 'Results retrieved from existing cache. Use force_refresh=True to recalculate.'
                    }
            
            # Perform matching with existing filter
            matching_result = self.matcher.perform_matching(filter_id)
            
            # Print summary
            self.matcher.print_summary(filter_id)
            
            return {
                'matching_result': matching_result,
                'filter_id': filter_id,
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Matching with existing filter failed: {e}")
            raise

def main():
    """Main function for filtered matching operations"""
    import sys
    
    # API Keys
    LEMLIST_API_KEY = "fc8bbfc8a9a884abbb51ecb16c0216f2"
    PIPEDRIVE_API_KEY = "64bb757c7d27fc5be60cc352858bba22bd5ba377"
    
    try:
        # Initialize orchestrator
        orchestrator = FilteredMatchingOrchestrator(
            lemlist_api_key=LEMLIST_API_KEY,
            pipedrive_api_key=PIPEDRIVE_API_KEY
        )
        
        if len(sys.argv) < 2:
            print("Usage:")
            print("  python filtered_matching.py <filter_url>     - Process new filter URL")
            print("  python filtered_matching.py --list           - List existing filters")
            print("  python filtered_matching.py --results        - List filters with results")
            print("  python filtered_matching.py --match <id>     - Run matching with existing filter")
            print("  python filtered_matching.py --match <id> --force - Force refresh existing filter")
            print("  python filtered_matching.py --delete <id>    - Delete a filter")
            return 1
        
        command = sys.argv[1]
        
        if command == "--list":
            # List existing filters
            filters = orchestrator.get_user_filters()
            print("\n" + "="*60)
            print("USER FILTERS")
            print("="*60)
            
            if not filters:
                print("No filters found.")
            else:
                for i, filter_info in enumerate(filters, 1):
                    print(f"{i}. {filter_info['filter_name']}")
                    print(f"   ID: {filter_info['filter_id']}")
                    print(f"   Organizations: {filter_info['organizations_count']}")
                    print(f"   Last Used: {filter_info['last_used']}")
                    print()
        
        elif command == "--results":
            # List filters with results
            results = orchestrator.list_filters_with_results()
            print("\n" + "="*60)
            print("FILTERS WITH MATCHING RESULTS")
            print("="*60)
            
            if not results:
                print("No filters with results found.")
            else:
                for i, result in enumerate(results, 1):
                    print(f"{i}. {result['filter_name']}")
                    print(f"   ID: {result['filter_id']}")
                    print(f"   Matches: {result['matching_companies']}")
                    print(f"   Match Rate: {result['match_percentage']:.2f}%")
                    print(f"   Created: {result['created_at']}")
                    print()
        
        elif command == "--match" and len(sys.argv) > 2:
            # Run matching with existing filter
            filter_id = sys.argv[2]
            force_refresh = "--force" in sys.argv
            
            if force_refresh:
                print(f"🔄 Force refreshing results for filter: {filter_id}")
            else:
                print(f"🔍 Checking for existing results for filter: {filter_id}")
            
            result = orchestrator.run_matching_with_existing_filter(filter_id, force_refresh)
            
            if result['status'] == 'retrieved_from_cache':
                print(f"\n✅ Results retrieved from cache for filter: {filter_id}")
                print(f"📊 {result['message']}")
            else:
                print(f"\n✅ Matching completed with filter: {filter_id}")
        
        elif command == "--delete" and len(sys.argv) > 2:
            # Delete a filter
            filter_id = sys.argv[2]
            orchestrator.delete_user_filter(filter_id)
            print(f"✅ Deleted filter: {filter_id}")
        
        else:
            # Process new filter URL
            filter_url = command
            force_refresh = "--force" in sys.argv
            
            if force_refresh:
                print(f"🔄 Force refreshing results for URL: {filter_url}")
            else:
                print(f"🔍 Processing filter URL: {filter_url}")
            
            result = orchestrator.process_filter_url(filter_url, status_filter='running', force_refresh=force_refresh)
            
            if 'error' in result:
                print(f"❌ Error: {result['error']}")
                return 1
            
            if result['status'] == 'retrieved_from_cache':
                print(f"\n✅ Results retrieved from cache!")
                print(f"📊 Filter: {result['filter_name']} (ID: {result['filter_id']})")
                print(f"📊 Organizations: {result['organizations_count']}")
                print(f"📊 Matches: {result['matching_result']['matching_companies']}")
                print(f"📊 Match Rate: {result['matching_result']['match_percentage']:.2f}%")
                print(f"📊 {result['message']}")
            else:
                print(f"\n✅ Filter processing completed successfully!")
                print(f"📊 Filter: {result['filter_name']} (ID: {result['filter_id']})")
                print(f"📊 Organizations: {result['organizations_count']}")
                print(f"📊 Matches: {result['matching_result']['matching_companies']}")
                print(f"📊 Match Rate: {result['matching_result']['match_percentage']:.2f}%")
        
        return 0
        
    except Exception as e:
        logger.error(f"Application failed: {e}")
        print(f"❌ Error: {e}")
        return 1

if __name__ == "__main__":
    exit(main())
