#!/usr/bin/env python3
"""
Main Orchestrator
Controls Lemlist and Pipedrive integrations
"""

import logging
from typing import Dict, Any, Optional
from lemlist import LemlistDataPuller
from pipedrive import PipedriveDataPuller

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('data_sync.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataSyncOrchestrator:
    """Main orchestrator for data synchronization between Lemlist and Pipedrive"""
    
    def __init__(self, lemlist_api_key: str, pipedrive_api_key: str = None):
        self.lemlist_puller = LemlistDataPuller(lemlist_api_key)
        self.pipedrive_puller = PipedriveDataPuller(pipedrive_api_key) if pipedrive_api_key else None
        logger.info("Data sync orchestrator initialized")
    
    def sync_lemlist_data(self, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """Sync data from Lemlist"""
        try:
            logger.info("Starting Lemlist data sync...")
            
            # Pull data from Lemlist
            lemlist_data = self.lemlist_puller.pull_all_data(status_filter=status_filter)
            
            # Print summary
            self.lemlist_puller.print_summary()
            
            # Save to files
            json_file = self.lemlist_puller.save_to_json()
            csv_dir = self.lemlist_puller.save_to_csv()
            
            print(f"\nLemlist Data saved to:")
            print(f"  JSON: {json_file}")
            print(f"  CSV: {csv_dir}")
            print(f"  SQLite Database: lemlist_campaigns.db")
            print(f"    Each campaign is a separate table in the database")
            print(f"    Use 'campaigns_overview' table to see all campaigns")
            
            return lemlist_data
            
        except Exception as e:
            logger.error(f"Lemlist sync failed: {e}")
            raise
    
    def sync_pipedrive_data(self) -> Dict[str, Any]:
        """Sync data from Pipedrive"""
        try:
            if not self.pipedrive_puller:
                logger.warning("Pipedrive API key not provided, skipping Pipedrive sync")
                return {}
            
            logger.info("Starting Pipedrive data sync...")
            
            # Pull data from Pipedrive
            pipedrive_data = self.pipedrive_puller.pull_all_data()
            
            # Print summary
            self.pipedrive_puller.print_summary()
            
            print(f"\nPipedrive Data saved to:")
            print(f"  SQLite Database: pipedrive.db")
            print(f"    Organizations table: organizations")
            print(f"    Fields table: organization_fields")
            print(f"    Custom fields table: organization_custom_fields")
            
            return pipedrive_data
            
        except Exception as e:
            logger.error(f"Pipedrive sync failed: {e}")
            raise
    
    def full_sync(self, status_filter: Optional[str] = None) -> Dict[str, Any]:
        """Perform full synchronization: Lemlist + Pipedrive"""
        try:
            logger.info("Starting full data synchronization...")
            
            # Step 1: Sync from Lemlist
            lemlist_data = self.sync_lemlist_data(status_filter)
            
            # Step 2: Sync from Pipedrive
            pipedrive_data = self.sync_pipedrive_data()
            
            logger.info("Full synchronization completed!")
            
            return {
                'lemlist_data': lemlist_data,
                'pipedrive_data': pipedrive_data,
                'status': 'completed'
            }
            
        except Exception as e:
            logger.error(f"Full sync failed: {e}")
            raise

def main():
    """Main function"""
    # API Keys
    LEMLIST_API_KEY = "fc8bbfc8a9a884abbb51ecb16c0216f2"
    PIPEDRIVE_API_KEY = "64bb757c7d27fc5be60cc352858bba22bd5ba377"
    
    try:
        # Initialize orchestrator
        orchestrator = DataSyncOrchestrator(
            lemlist_api_key=LEMLIST_API_KEY,
            pipedrive_api_key=PIPEDRIVE_API_KEY
        )
        
        # Perform full sync (both Lemlist and Pipedrive)
        sync_result = orchestrator.full_sync(status_filter='running')
        
        print(f"\n✅ Full sync completed successfully!")
        print(f"📊 Lemlist: {len(sync_result['lemlist_data']['campaigns'])} campaigns")
        print(f"📊 Pipedrive: {len(sync_result['pipedrive_data'].get('organizations', []))} organizations")
        
    except Exception as e:
        logger.error(f"Application failed: {e}")
        print(f"Error: {e}")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main())