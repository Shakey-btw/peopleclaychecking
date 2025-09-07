# Filtered Matching Functionality

This document explains the new filtered matching functionality that allows users to input Pipedrive filter URLs and perform matching with Lemlist data using only the filtered organizations.

## Overview

The filtered matching system extends the existing backend to support:

1. **Filter URL Processing**: Extract filter IDs from Pipedrive filter URLs
2. **Filtered Data Retrieval**: Pull organizations that match specific filter criteria
3. **Filter Management**: Store and manage user filters for reuse
4. **Filtered Matching**: Perform company matching using only filtered organizations
5. **Results Tracking**: Track matching results per filter

## Architecture

### New Components

#### 1. **Extended PipedriveClient** (`pipedrive.py`)
- `get_filter_details(filter_id)`: Get filter information from Pipedrive API
- `get_organizations_by_filter(filter_id)`: Get organizations matching a filter
- `extract_filter_id_from_url(filter_url)`: Extract filter ID from various URL formats

#### 2. **Extended PipedriveDatabase** (`pipedrive.py`)
- `user_filters` table: Store user filter information
- `filtered_organizations` table: Store organizations for each filter
- Filter management methods: save, get, delete filters

#### 3. **Extended CompanyMatcher** (`matching.py`)
- `perform_matching(filter_id=None)`: Support filtered matching
- Updated results storage with filter information

#### 4. **FilteredMatchingOrchestrator** (`filtered_matching.py`)
- Complete workflow for filtered operations
- Command-line interface for testing

### Database Schema

#### New Tables in `pipedrive.db`:

```sql
-- User filters table
CREATE TABLE user_filters (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filter_id TEXT UNIQUE NOT NULL,
    filter_name TEXT NOT NULL,
    filter_url TEXT,
    filter_conditions TEXT,
    organizations_count INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    last_used TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT 1
);

-- Filtered organizations table
CREATE TABLE filtered_organizations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    filter_id TEXT NOT NULL,
    org_id INTEGER NOT NULL,
    org_name TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (filter_id) REFERENCES user_filters (filter_id),
    FOREIGN KEY (org_id) REFERENCES organizations (id),
    UNIQUE(filter_id, org_id)
);
```

#### Updated `matching_summary` table in `results.db`:

```sql
-- Added filter tracking columns
ALTER TABLE matching_summary ADD COLUMN filter_id TEXT;
ALTER TABLE matching_summary ADD COLUMN filter_name TEXT;
```

## Usage

### 1. **Command Line Interface**

#### Process a new filter URL:
```bash
python filtered_matching.py "https://app.pipedrive.com/filters/12345"
```

#### List existing filters:
```bash
python filtered_matching.py --list
```

#### Run matching with existing filter:
```bash
python filtered_matching.py --match 12345
```

#### Delete a filter:
```bash
python filtered_matching.py --delete 12345
```

### 2. **Programmatic Usage**

```python
from filtered_matching import FilteredMatchingOrchestrator

# Initialize orchestrator
orchestrator = FilteredMatchingOrchestrator(
    lemlist_api_key="your_lemlist_key",
    pipedrive_api_key="your_pipedrive_key"
)

# Process a filter URL
result = orchestrator.process_filter_url("https://app.pipedrive.com/filters/12345")

# Get user filters
filters = orchestrator.get_user_filters()

# Run matching with existing filter
result = orchestrator.run_matching_with_existing_filter("12345")
```

### 3. **Direct API Usage**

```python
from pipedrive import PipedriveDataPuller
from matching import CompanyMatcher

# Initialize components
pipedrive_puller = PipedriveDataPuller("your_api_key")
matcher = CompanyMatcher()

# Pull filtered data
filtered_data = pipedrive_puller.pull_filtered_data("https://app.pipedrive.com/filters/12345")

# Perform matching
matching_result = matcher.perform_matching(filtered_data['filter_id'])
```

## Supported Filter URL Formats

The system can extract filter IDs from various URL formats:

- `https://app.pipedrive.com/filters/12345`
- `https://app.pipedrive.com/organizations?filter_id=67890`
- `https://app.pipedrive.com/filters/11111?view=list`
- Any URL containing a numeric filter ID

## Workflow

### 1. **New Filter Processing**
```
User Input (Filter URL) 
    ↓
Extract Filter ID
    ↓
Get Filter Details from Pipedrive API
    ↓
Pull Filtered Organizations
    ↓
Save Filter & Organizations to Database
    ↓
Perform Matching with Filtered Data
    ↓
Store Results with Filter Information
```

### 2. **Existing Filter Usage**
```
User Selects Existing Filter
    ↓
Retrieve Filtered Organizations from Database
    ↓
Perform Matching with Filtered Data
    ↓
Store Results with Filter Information
```

## API Integration

### Pipedrive API Endpoints Used

1. **Get Filter Details**: `GET /v1/filters/{id}`
2. **Get Filtered Organizations**: `GET /v1/organizations?filter_id={id}`

### Rate Limiting
- Built-in rate limiting protection
- Automatic retry on 429 responses
- 0.5-second delays between requests

## Error Handling

The system includes comprehensive error handling for:

- Invalid filter URLs
- Non-existent filter IDs
- API rate limiting
- Network connectivity issues
- Database operation failures

## Results and Reporting

### Matching Results Include:
- Filter information (ID, name, conditions)
- Organization counts (total, filtered, matching)
- Match percentages
- Detailed match lists
- Non-matching organizations

### Database Tables for Analysis:
- `matching_summary`: High-level statistics per filter
- `detailed_matches`: Individual match records
- `all_matching_companies`: Unique matching companies
- `all_non_matching_*`: Companies without matches

## Testing

Run the test script to verify functionality:

```bash
python test_filtered_matching.py
```

This tests:
- Filter ID extraction from URLs
- Database operations
- Filter management

## Integration with Frontend

The backend is ready for frontend integration. The frontend can:

1. **Send filter URLs** to backend endpoints
2. **Retrieve user filters** for selection
3. **Get matching results** for display
4. **Manage filters** (create, delete, reuse)

## Future Enhancements

Potential improvements:
- Filter condition parsing and display
- Advanced matching algorithms (fuzzy matching)
- Filter sharing between users
- Automated filter refresh
- Filter performance analytics

## Troubleshooting

### Common Issues:

1. **Invalid Filter URL**: Ensure the URL contains a valid filter ID
2. **API Rate Limits**: The system handles this automatically
3. **Missing Organizations**: Check if the filter returns any organizations
4. **Database Errors**: Ensure proper database initialization

### Debug Mode:
Enable debug logging by setting the logging level to DEBUG in the configuration.

## Security Considerations

- API keys are stored in environment variables or configuration files
- Filter URLs are validated before processing
- Database operations use parameterized queries to prevent SQL injection
- User filters are isolated and can be deleted independently
