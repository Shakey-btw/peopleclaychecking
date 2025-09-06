# Lemlist API Reference

Complete API reference for the Lemlist integration.

## 🔐 Authentication

### Basic Authentication
```typescript
const authHeader = Buffer.from(`:${apiKey}`).toString('base64');
const headers = {
  'Authorization': `Basic ${authHeader}`,
  'Content-Type': 'application/json'
};
```

### Environment Variables
```env
LEMLIST_API_KEY=your_api_key_here
```

## 📡 API Endpoints

### 1. Team Information

**Endpoint:** `GET https://api.lemlist.com/api/team`

**Purpose:** Verify authentication and get team details

**Response:**
```typescript
{
  _id: string;
  userIds: string[];
  createdBy: string;
  createdAt: string;
  beta: string[];
  name: string;
  invitedUsers: any[];
  hooks: any[];
  customDomain: string;
}
```

**Usage:**
```typescript
import { authenticateLemlist } from '@/lib/lemlist/auth';

const team = await authenticateLemlist();
console.log('Team:', team.name);
```

### 2. Get Campaigns

**Endpoint:** `GET https://api.lemlist.com/api/campaigns`

**Purpose:** Retrieve all campaigns with pagination

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `version` | string | v2 | API version (v2 recommended) |
| `limit` | number | 10 | Number of campaigns to retrieve |
| `page` | number | 1 | Page number for pagination |
| `sortBy` | string | createdAt | Sort field |
| `sortOrder` | string | desc | Sort direction (asc/desc) |
| `status` | string | - | Filter by status (running, draft, archived, ended, paused, errors) |

**Response:**
```typescript
{
  campaigns: Campaign[];
  pagination: {
    page: number;
    limit: number;
    totalRecords: number;
    currentPage: number;
    nextPage: number;
    totalPage: number;
  };
}
```

**Usage:**
```typescript
import { getCampaigns } from '@/lib/lemlist/auth';

// Get all running campaigns
const campaigns = await getCampaigns({ status: 'running' });

// Get campaigns with pagination
const campaigns = await getCampaigns({ 
  limit: 50, 
  page: 1, 
  sortBy: 'createdAt', 
  sortOrder: 'desc' 
});
```

### 3. Get Campaign Leads

**Endpoint:** `GET https://api.lemlist.com/api/campaigns/{campaignId}/export/leads`

**Purpose:** Export leads from a specific campaign

**Parameters:**
| Parameter | Type | Default | Description |
|-----------|------|---------|-------------|
| `state` | string | all | Lead state filter |
| `format` | string | json | Response format (json/csv) |

**Lead States:**
- `all` - All leads
- `contacted` - Leads that were contacted
- `hooked` - Leads that opened emails or LinkedIn messages
- `interested` - Leads marked as interested
- `emailsOpened` - Leads that opened emails
- `emailsReplied` - Leads that replied to emails
- `emailsUnsubscribed` - Leads that unsubscribed

**Response:**
```typescript
Lead[] // Array of lead objects
```

**Usage:**
```typescript
import { getCampaignLeads } from '@/lib/lemlist/auth';

// Get all leads for a campaign
const leads = await getCampaignLeads('campaign_id', { state: 'all' });

// Get only contacted leads
const contactedLeads = await getCampaignLeads('campaign_id', { 
  state: 'contacted' 
});
```

## 📊 Data Models

### Campaign
```typescript
interface Campaign {
  _id: string;
  name: string;
  status: string;
  createdAt: string;
  createdBy: string;
  labels?: string[];
  archived?: boolean;
  hasError?: boolean;
  errors?: string[];
}
```

### Lead
```typescript
interface Lead {
  _id: string;
  email: string;
  firstName?: string;
  lastName?: string;
  companyName?: string;
  jobTitle?: string;
  linkedinUrl?: string;
  companyDomain?: string;
  state: string;
  stateSystem?: string;
  // Dynamic fields based on campaign
  [key: string]: any;
}
```

### Common Dynamic Fields
| Field | Description | Example |
|-------|-------------|---------|
| `PERSONA` | Lead persona classification | "SCM", "IT", "c-level" |
| `CAMPAIGN ZUWEISUNG` | Campaign assignment | "2ND: Mid-Big companies" |
| `Organization - ID` | Organization identifier | "5880" |
| `RETAILER` | Retailer information | "Edeka", "Rewe" |
| `NORMALIZEDNAME` | Normalized company name | "Teigwaren Riesa" |
| `emailStatus` | Email status | "risky" |

## 🔄 Error Handling

### HTTP Errors
```typescript
if (!response.ok) {
  throw new Error(`HTTP error! status: ${response.status}`);
}
```

### Common Error Codes
| Code | Description | Solution |
|------|-------------|----------|
| 401 | Unauthorized | Check API key |
| 403 | Forbidden | Verify permissions |
| 404 | Not found | Check campaign ID |
| 429 | Rate limited | Wait and retry |
| 500 | Server error | Contact Lemlist support |

### Error Response Format
```typescript
{
  success: false;
  error: string;
}
```

## 📈 Rate Limits

- **Requests per minute:** Varies by plan
- **Campaign retrieval:** 100 campaigns max per request
- **Lead export:** No specific limit mentioned

## 🔍 Field Discovery

### Dynamic Field Detection
```typescript
// Get all available fields for a lead
const firstLead = leads[0];
const fields = Object.keys(firstLead);

console.log('Available fields:', fields);
console.log('Total fields:', fields.length);
```

### Field Type Detection
```typescript
Object.keys(lead).forEach(key => {
  const value = lead[key];
  const type = typeof value;
  console.log(`${key}: ${type}`);
});
```

## 🧪 Testing

### Test Scripts
```bash
# Basic authentication
npm run test-lemlist

# Complete integration test
npm run test-essential

# Specific campaign test
npm run test-specific

# Field discovery
npm run discover-fields
```

### Example Test Output
```
✅ 32 leads retrieved
Total fields in this campaign: 15

Field Name | Value | Type
-----------|-------|------
email      | user@company.com | string
firstName  | John | string
...
```

## 🚀 Best Practices

1. **Always use dynamic field extraction** - Don't hardcode field names
2. **Handle errors gracefully** - Check response status
3. **Use pagination** - For large datasets
4. **Cache results** - When appropriate
5. **Test with different campaigns** - Field structures vary

## 📚 Additional Resources

- [Setup Guide](./setup.md)
- [Data Models](./data-models.md)
- [Testing Guide](./testing.md)
- [Troubleshooting](./troubleshooting.md)
