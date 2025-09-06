# Testing Guide

Comprehensive testing guide for the Lemlist integration.

## 🧪 Test Scripts Overview

| Script | Purpose | Command | Output |
|--------|---------|---------|--------|
| `test-lemlist` | Basic authentication | `npm run test-lemlist` | Team info |
| `test-essential` | Complete integration | `npm run test-essential` | Campaigns + leads |
| `test-specific` | Specific campaign | `npm run test-specific` | Detailed lead analysis |
| `discover-fields` | Field discovery | `npm run discover-fields` | Field structure |

## 🔐 Authentication Testing

### Basic Test
```bash
npm run test-lemlist
```

**Expected Output:**
```
✅ Authentication successful!
Team: Your Team Name
Team ID: team_123456
```

**What it tests:**
- API key validity
- Basic authentication
- Team data retrieval

### Error Cases
```typescript
// Test with invalid API key
process.env.LEMLIST_API_KEY = 'invalid_key';
// Should throw: "HTTP error! status: 401"

// Test with missing API key
delete process.env.LEMLIST_API_KEY;
// Should throw: "LEMLIST_API_KEY not found in environment"
```

## 📊 Campaign Testing

### Complete Integration Test
```bash
npm run test-essential
```

**What it tests:**
- Campaign retrieval
- Lead extraction
- Field discovery
- Multiple campaign types

**Expected Output:**
```
🎯 ESSENTIAL LEMLIST INTEGRATION TEST

--- Step 1: Retrieve All Running Campaigns ---
✅ Found 10 running campaigns

1. Campaign Name (campaign_id)
2. Campaign Name (campaign_id)
...

--- Step 2: Retrieve ALL Lead Data ---
Campaign: Campaign Name
✅ 32 leads retrieved

--- ALL AVAILABLE FIELDS ---
Field Name | Value | Type
-----------|-------|------
email      | user@company.com | string
firstName  | John | string
...
```

### Field Discovery Test
```bash
npm run discover-fields
```

**Purpose:** Discover all available fields for any campaign

**Expected Output:**
```
🔍 DISCOVERING ALL AVAILABLE LEAD FIELDS

Campaign: Campaign Name
Campaign ID: campaign_id
✅ 32 leads retrieved

--- ALL AVAILABLE FIELDS IN LEAD OBJECT ---
Field Name | Value | Type
-----------|-------|------
email                | user@company.com | string
firstName            | John | string
...
Total fields available: 15
```

## 🎯 Specific Campaign Testing

### Campaign-Specific Test
```bash
npm run test-specific
```

**What it tests:**
- Specific campaign ID
- Field structure analysis
- Lead data extraction
- Field comparison

**Expected Output:**
```
🎯 TESTING SPECIFIC CAMPAIGN

Campaign: 5.1_NON-DACH_Knuspr_EN_08/25
Campaign ID: cam_y7Xc7sPTL4bn7Q46K
✅ 741 leads retrieved

--- ALL AVAILABLE FIELDS FOR THIS CAMPAIGN ---
Field Name | Value | Type
-----------|-------|------
email      | stuart.machin@marksandspencer.com | string
...
Total fields in this campaign: 13
```

## 📈 Test Data Analysis

### Lead State Testing
```typescript
// Test different lead states
const states = ['all', 'contacted', 'hooked', 'interested', 'emailsOpened'];

for (const state of states) {
  const leads = await getCampaignLeads(campaignId, { state });
  console.log(`${state}: ${leads.length} leads`);
}
```

### Field Structure Comparison
```typescript
// Compare field structures across campaigns
const campaigns = await getCampaigns({ status: 'running' });

for (const campaign of campaigns.campaigns.slice(0, 3)) {
  const leads = await getCampaignLeads(campaign._id, { state: 'all' });
  const fields = Object.keys(leads[0] || {});
  console.log(`${campaign.name}: ${fields.length} fields`);
}
```

## 🔍 Field Testing

### Dynamic Field Discovery
```typescript
function testFieldDiscovery(leads: Lead[]) {
  if (leads.length === 0) {
    console.log('No leads to analyze');
    return;
  }
  
  const firstLead = leads[0];
  const fields = Object.keys(firstLead);
  
  console.log('Field Analysis:');
  console.log(`Total fields: ${fields.length}`);
  
  fields.forEach(field => {
    const value = firstLead[field];
    const type = typeof value;
    console.log(`${field}: ${type} = ${value}`);
  });
}
```

### Field Type Validation
```typescript
function validateFieldTypes(leads: Lead[]) {
  const fieldTypes: Record<string, Set<string>> = {};
  
  leads.forEach(lead => {
    Object.keys(lead).forEach(key => {
      if (!fieldTypes[key]) {
        fieldTypes[key] = new Set();
      }
      fieldTypes[key].add(typeof lead[key]);
    });
  });
  
  // Check for inconsistent types
  Object.entries(fieldTypes).forEach(([field, types]) => {
    if (types.size > 1) {
      console.warn(`Field ${field} has multiple types: ${Array.from(types).join(', ')}`);
    }
  });
}
```

## 🚨 Error Testing

### Network Error Testing
```typescript
// Test network failures
const originalFetch = global.fetch;
global.fetch = jest.fn().mockRejectedValue(new Error('Network error'));

try {
  await getCampaigns();
} catch (error) {
  expect(error.message).toBe('Network error');
} finally {
  global.fetch = originalFetch;
}
```

### API Error Testing
```typescript
// Test API errors
const mockResponse = {
  ok: false,
  status: 401,
  statusText: 'Unauthorized'
};

global.fetch = jest.fn().mockResolvedValue(mockResponse);

try {
  await getCampaigns();
} catch (error) {
  expect(error.message).toContain('HTTP error! status: 401');
}
```

## 📊 Performance Testing

### Response Time Testing
```typescript
async function testResponseTimes() {
  const start = Date.now();
  
  // Test campaign retrieval
  const campaignsStart = Date.now();
  const campaigns = await getCampaigns({ status: 'running' });
  const campaignsTime = Date.now() - campaignsStart;
  
  // Test lead retrieval
  const leadsStart = Date.now();
  const leads = await getCampaignLeads(campaigns.campaigns[0]._id, { state: 'all' });
  const leadsTime = Date.now() - leadsStart;
  
  const totalTime = Date.now() - start;
  
  console.log('Performance Metrics:');
  console.log(`Campaigns: ${campaignsTime}ms`);
  console.log(`Leads: ${leadsTime}ms`);
  console.log(`Total: ${totalTime}ms`);
}
```

### Memory Usage Testing
```typescript
function testMemoryUsage(leads: Lead[]) {
  const memBefore = process.memoryUsage();
  
  // Process leads
  const processedLeads = leads.map(lead => ({
    id: lead._id,
    email: lead.email,
    // ... other fields
  }));
  
  const memAfter = process.memoryUsage();
  
  console.log('Memory Usage:');
  console.log(`Before: ${memBefore.heapUsed / 1024 / 1024}MB`);
  console.log(`After: ${memAfter.heapUsed / 1024 / 1024}MB`);
  console.log(`Difference: ${(memAfter.heapUsed - memBefore.heapUsed) / 1024 / 1024}MB`);
}
```

## 🧪 Unit Testing

### Test Setup
```typescript
// jest.config.js
module.exports = {
  testEnvironment: 'node',
  setupFilesAfterEnv: ['<rootDir>/src/tests/setup.ts']
};

// src/tests/setup.ts
import dotenv from 'dotenv';
dotenv.config({ path: '.env.test' });
```

### Authentication Tests
```typescript
// src/tests/auth.test.ts
import { authenticateLemlist } from '@/lib/lemlist/auth';

describe('Authentication', () => {
  test('should authenticate with valid API key', async () => {
    const team = await authenticateLemlist();
    expect(team).toHaveProperty('_id');
    expect(team).toHaveProperty('name');
  });
  
  test('should throw error with invalid API key', async () => {
    process.env.LEMLIST_API_KEY = 'invalid';
    await expect(authenticateLemlist()).rejects.toThrow();
  });
});
```

### Campaign Tests
```typescript
// src/tests/campaigns.test.ts
import { getCampaigns } from '@/lib/lemlist/auth';

describe('Campaigns', () => {
  test('should retrieve running campaigns', async () => {
    const response = await getCampaigns({ status: 'running' });
    expect(response).toHaveProperty('campaigns');
    expect(response).toHaveProperty('pagination');
    expect(Array.isArray(response.campaigns)).toBe(true);
  });
  
  test('should handle pagination', async () => {
    const response = await getCampaigns({ limit: 5, page: 1 });
    expect(response.campaigns.length).toBeLessThanOrEqual(5);
  });
});
```

## 🔄 Integration Testing

### End-to-End Test
```typescript
// src/tests/integration.test.ts
import { getCampaigns, getCampaignLeads } from '@/lib/lemlist/auth';

describe('Integration', () => {
  test('should complete full workflow', async () => {
    // 1. Get campaigns
    const campaigns = await getCampaigns({ status: 'running' });
    expect(campaigns.campaigns.length).toBeGreaterThan(0);
    
    // 2. Get leads for first campaign
    const campaign = campaigns.campaigns[0];
    const leads = await getCampaignLeads(campaign._id, { state: 'all' });
    expect(leads.length).toBeGreaterThan(0);
    
    // 3. Verify lead structure
    const lead = leads[0];
    expect(lead).toHaveProperty('_id');
    expect(lead).toHaveProperty('email');
    expect(lead).toHaveProperty('state');
  });
});
```

## 📋 Test Checklist

### Pre-Test Setup
- [ ] API key is valid and set in `.env.local`
- [ ] Dependencies are installed
- [ ] Test scripts are available in `package.json`

### Authentication Tests
- [ ] Valid API key works
- [ ] Invalid API key fails
- [ ] Missing API key fails
- [ ] Team data is retrieved correctly

### Campaign Tests
- [ ] Running campaigns are retrieved
- [ ] Pagination works
- [ ] Different status filters work
- [ ] Campaign data structure is correct

### Lead Tests
- [ ] Leads are retrieved for campaigns
- [ ] Different state filters work
- [ ] Field structure is discovered
- [ ] Dynamic fields are handled

### Error Handling Tests
- [ ] Network errors are handled
- [ ] API errors are handled
- [ ] Invalid campaign IDs fail gracefully
- [ ] Rate limiting is handled

## 🚀 Running Tests

### Manual Testing
```bash
# Run all test scripts
npm run test-lemlist
npm run test-essential
npm run test-specific
npm run discover-fields
```

### Automated Testing
```bash
# Run unit tests
npm test

# Run with coverage
npm run test:coverage

# Run specific test file
npm test -- auth.test.ts
```

## 📚 Related Documentation

- [Setup Guide](./setup.md)
- [API Reference](./api-reference.md)
- [Data Models](./data-models.md)
- [Troubleshooting](./troubleshooting.md)
