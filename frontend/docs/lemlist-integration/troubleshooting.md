# Troubleshooting Guide

Common issues and solutions for the Lemlist integration.

## 🚨 Common Issues

### 1. Authentication Errors

#### Error: `LEMLIST_API_KEY not found in environment`
**Cause:** API key not set in environment variables

**Solution:**
```bash
# Create .env.local file
echo "LEMLIST_API_KEY=your_api_key_here" > .env.local

# Verify file exists
cat .env.local
```

**Prevention:** Always check `.env.local` exists before running tests

#### Error: `HTTP error! status: 401`
**Cause:** Invalid API key

**Solution:**
1. Verify API key is correct
2. Check for extra spaces or characters
3. Regenerate API key in Lemlist dashboard

```bash
# Test API key
curl -u ":your_api_key" https://api.lemlist.com/api/team
```

#### Error: `HTTP error! status: 403`
**Cause:** Insufficient permissions

**Solution:**
1. Check API key permissions in Lemlist
2. Verify account has access to campaigns/leads
3. Contact Lemlist support if needed

### 2. Network Errors

#### Error: `fetch failed` or `ECONNREFUSED`
**Cause:** Network connectivity issues

**Solution:**
```typescript
// Add retry logic
async function fetchWithRetry(url: string, options: RequestInit, retries = 3) {
  for (let i = 0; i < retries; i++) {
    try {
      const response = await fetch(url, options);
      return response;
    } catch (error) {
      if (i === retries - 1) throw error;
      await new Promise(resolve => setTimeout(resolve, 1000 * (i + 1)));
    }
  }
}
```

#### Error: `timeout`
**Cause:** Request taking too long

**Solution:**
```typescript
// Add timeout
const controller = new AbortController();
const timeoutId = setTimeout(() => controller.abort(), 30000); // 30s timeout

const response = await fetch(url, {
  ...options,
  signal: controller.signal
});

clearTimeout(timeoutId);
```

### 3. Data Issues

#### Error: `leads is not iterable`
**Cause:** API returning unexpected data format

**Solution:**
```typescript
// Add data validation
function validateLeadsResponse(data: any): Lead[] {
  if (Array.isArray(data)) {
    return data;
  }
  
  if (data && Array.isArray(data.leads)) {
    return data.leads;
  }
  
  throw new Error('Invalid leads response format');
}

// Usage
const leads = validateLeadsResponse(await response.json());
```

#### Error: `Cannot read property 'length' of undefined`
**Cause:** Campaigns response missing pagination

**Solution:**
```typescript
// Add safe property access
const leadCount = leads?.length || leads?.leads?.length || 0;
const campaignCount = campaigns?.campaigns?.length || 0;
```

### 4. Field Discovery Issues

#### Error: `Cannot read property 'keys' of undefined`
**Cause:** No leads returned or empty response

**Solution:**
```typescript
// Add safety checks
if (leads && leads.length > 0) {
  const fields = Object.keys(leads[0]);
  console.log('Available fields:', fields);
} else {
  console.log('No leads available for field discovery');
}
```

#### Issue: Fields missing from some campaigns
**Cause:** Different campaigns have different field structures

**Solution:**
```typescript
// Always use dynamic field discovery
function getAvailableFields(leads: Lead[]): string[] {
  if (!leads || leads.length === 0) return [];
  
  const allFields = new Set<string>();
  leads.forEach(lead => {
    Object.keys(lead).forEach(key => allFields.add(key));
  });
  
  return Array.from(allFields).sort();
}
```

## 🔧 Debugging

### Enable Debug Logging
```typescript
// Add debug logging
const DEBUG = process.env.NODE_ENV === 'development';

function debugLog(message: string, data?: any) {
  if (DEBUG) {
    console.log(`[DEBUG] ${message}`, data);
  }
}

// Usage
debugLog('Fetching campaigns', { status: 'running' });
const campaigns = await getCampaigns({ status: 'running' });
debugLog('Campaigns retrieved', { count: campaigns.campaigns.length });
```

### API Response Logging
```typescript
// Log full API responses
const response = await fetch(url, options);
const data = await response.json();

console.log('API Response:', {
  status: response.status,
  headers: Object.fromEntries(response.headers.entries()),
  data: data
});
```

### Field Analysis
```typescript
// Analyze field differences between campaigns
function analyzeFieldDifferences(campaigns: Campaign[], leadsByCampaign: Record<string, Lead[]>) {
  const fieldSets = Object.entries(leadsByCampaign).map(([campaignId, leads]) => {
    const campaign = campaigns.find(c => c._id === campaignId);
    const fields = leads.length > 0 ? Object.keys(leads[0]) : [];
    return {
      campaignId,
      campaignName: campaign?.name || 'Unknown',
      fields: fields.sort()
    };
  });
  
  console.log('Field Analysis:');
  fieldSets.forEach(({ campaignName, fields }) => {
    console.log(`${campaignName}: ${fields.length} fields`);
    console.log(`  Fields: ${fields.join(', ')}`);
  });
}
```

## 🐛 Error Handling Best Practices

### Comprehensive Error Handling
```typescript
async function safeApiCall<T>(
  apiCall: () => Promise<T>,
  errorContext: string
): Promise<T | null> {
  try {
    return await apiCall();
  } catch (error) {
    console.error(`Error in ${errorContext}:`, {
      message: error.message,
      stack: error.stack,
      timestamp: new Date().toISOString()
    });
    return null;
  }
}

// Usage
const campaigns = await safeApiCall(
  () => getCampaigns({ status: 'running' }),
  'campaign retrieval'
);

if (!campaigns) {
  console.log('Failed to retrieve campaigns');
  return;
}
```

### Retry Logic
```typescript
async function withRetry<T>(
  operation: () => Promise<T>,
  maxRetries = 3,
  delay = 1000
): Promise<T> {
  let lastError: Error;
  
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await operation();
    } catch (error) {
      lastError = error;
      
      if (attempt === maxRetries) {
        throw lastError;
      }
      
      console.log(`Attempt ${attempt} failed, retrying in ${delay}ms...`);
      await new Promise(resolve => setTimeout(resolve, delay));
      delay *= 2; // Exponential backoff
    }
  }
  
  throw lastError!;
}
```

## 📊 Performance Issues

### Large Dataset Handling
```typescript
// Process leads in batches
async function processLeadsInBatches(leads: Lead[], batchSize = 100) {
  const batches = [];
  
  for (let i = 0; i < leads.length; i += batchSize) {
    const batch = leads.slice(i, i + batchSize);
    batches.push(batch);
  }
  
  console.log(`Processing ${leads.length} leads in ${batches.length} batches`);
  
  for (let i = 0; i < batches.length; i++) {
    console.log(`Processing batch ${i + 1}/${batches.length}`);
    await processBatch(batches[i]);
  }
}
```

### Memory Management
```typescript
// Clear large objects when done
function processLargeDataset(leads: Lead[]) {
  try {
    // Process leads
    const processed = leads.map(lead => ({
      id: lead._id,
      email: lead.email,
      // ... minimal data
    }));
    
    return processed;
  } finally {
    // Clear references
    leads.length = 0;
  }
}
```

## 🔍 Monitoring

### Health Check
```typescript
async function healthCheck(): Promise<{
  status: 'healthy' | 'unhealthy';
  issues: string[];
}> {
  const issues: string[] = [];
  
  try {
    // Test authentication
    await authenticateLemlist();
  } catch (error) {
    issues.push(`Authentication failed: ${error.message}`);
  }
  
  try {
    // Test campaign retrieval
    const campaigns = await getCampaigns({ limit: 1 });
    if (campaigns.campaigns.length === 0) {
      issues.push('No campaigns found');
    }
  } catch (error) {
    issues.push(`Campaign retrieval failed: ${error.message}`);
  }
  
  return {
    status: issues.length === 0 ? 'healthy' : 'unhealthy',
    issues
  };
}
```

### Rate Limit Monitoring
```typescript
class RateLimiter {
  private requests: number[] = [];
  private maxRequests = 100;
  private windowMs = 60000; // 1 minute
  
  canMakeRequest(): boolean {
    const now = Date.now();
    this.requests = this.requests.filter(time => now - time < this.windowMs);
    
    return this.requests.length < this.maxRequests;
  }
  
  recordRequest(): void {
    this.requests.push(Date.now());
  }
}

const rateLimiter = new RateLimiter();

async function rateLimitedFetch(url: string, options: RequestInit) {
  if (!rateLimiter.canMakeRequest()) {
    throw new Error('Rate limit exceeded');
  }
  
  rateLimiter.recordRequest();
  return fetch(url, options);
}
```

## 📞 Support

### Lemlist Support
- **Documentation:** [Lemlist API Docs](https://help.lemlist.com/en/articles/9727997-contacts-section)
- **Support:** Contact through Lemlist dashboard
- **Status:** Check [Lemlist Status Page](https://status.lemlist.com)

### Debug Information to Include
When reporting issues, include:
1. Error message and stack trace
2. API key (masked: `abc...xyz`)
3. Campaign ID that failed
4. Number of leads being processed
5. Node.js version
6. Package versions

### Log Collection
```typescript
// Collect debug information
function collectDebugInfo(error: Error, context: any) {
  return {
    timestamp: new Date().toISOString(),
    error: {
      message: error.message,
      stack: error.stack,
      name: error.name
    },
    context,
    environment: {
      nodeVersion: process.version,
      platform: process.platform,
      arch: process.arch
    }
  };
}
```

## 📚 Related Documentation

- [Setup Guide](./setup.md)
- [API Reference](./api-reference.md)
- [Data Models](./data-models.md)
- [Testing Guide](./testing.md)
