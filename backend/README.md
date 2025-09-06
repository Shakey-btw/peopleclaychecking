# Lemlist Data Puller

A Python script to pull running campaigns and their leads from the Lemlist API with dynamic field handling.

## Features

- ✅ **Running Campaigns Only**: Pulls only campaigns with "running" status
- ✅ **Complete Lead Data**: Retrieves all leads for running campaigns
- ✅ **Dynamic Lead Fields**: Handles different field structures per campaign
- ✅ **Comprehensive Export**: Saves data in both JSON and CSV formats
- ✅ **Field Analysis**: Analyzes field types and null percentages
- ✅ **Rate Limiting**: Built-in protection against API rate limits
- ✅ **Error Handling**: Robust error handling and logging
- ✅ **Progress Tracking**: Detailed logging and progress updates

## Quick Start

1. **Setup** (run once):
   ```bash
   python setup.py
   ```

2. **Run the data puller**:
   ```bash
   python main.py
   ```

## What It Does

1. **Authenticates** with your Lemlist API key
2. **Fetches all campaigns** with their names and status
3. **Pulls all leads** for each campaign with all available fields
4. **Analyzes field structures** to understand data variations
5. **Exports data** in multiple formats:
   - JSON file with complete data structure
   - CSV files for each campaign's leads
   - Summary CSV with campaign overview

## Output Files

- `lemlist_data_YYYYMMDD_HHMMSS.json` - Complete data in JSON format
- `lemlist_export/campaigns_summary.csv` - Campaign overview
- `lemlist_export/leads_[CampaignName]_[ID].csv` - Individual campaign leads
- `lemlist_data_pull.log` - Detailed execution log

## Configuration

The script uses your API key: `fc8bbfc8a9a884abbb51ecb16c0216f2`

To change the API key, edit the `API_KEY` variable in `main.py`.

## Field Analysis

The script automatically analyzes each campaign's lead fields:

- **Field Types**: Detects string, number, boolean, etc.
- **Null Percentages**: Shows how often fields are empty
- **Sample Values**: Provides examples of field content
- **Dynamic Discovery**: Adapts to different campaign structures

## Example Output

```
LEMLIST DATA PULL SUMMARY
============================================================
Total Campaigns: 5
Pull Timestamp: 2024-01-15T10:30:00
Total Leads: 1,247

Campaign Details:
------------------------------------------------------------
• (new) 4.1_2ND:Mid-Big companies_DE_08/25
  ID: cam_xJYxjrC63rhDpJSHt
  Status: running
  Leads: 324
  Fields: 15

• English Campaign 2024
  ID: cam_abc123def456
  Status: running
  Leads: 156
  Fields: 13
```

## Error Handling

- **Rate Limiting**: Automatically waits when rate limited
- **Network Issues**: Retries failed requests
- **Data Validation**: Handles malformed responses
- **Logging**: Comprehensive error logging

## Requirements

- Python 3.7+
- requests library
- Internet connection
- Valid Lemlist API key

## Troubleshooting

1. **API Key Issues**: Verify your API key is correct
2. **Rate Limiting**: The script handles this automatically
3. **Network Issues**: Check your internet connection
4. **Permission Issues**: Ensure write permissions for output directories

## Support

Check the log file `lemlist_data_pull.log` for detailed error information.
