# Data Models

TypeScript interfaces and data structures for the Lemlist integration.

## 📋 Core Interfaces

### LemlistApiResponse
```typescript
interface LemlistApiResponse<T> {
  success: boolean;
  data?: T;
  error?: string;
}
```

### Team
```typescript
interface Team {
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

### CampaignsResponse
```typescript
interface CampaignsResponse {
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
  // Dynamic fields - varies by campaign
  [key: string]: any;
}
```

### CampaignLeadsResponse
```typescript
interface CampaignLeadsResponse {
  leads: Lead[];
  total: number;
  campaignId: string;
}
```

## 🔄 Dynamic Fields

### Common Dynamic Fields
These fields appear in most campaigns but with different names/values:

| Field Name | Type | Description | Example Values |
|------------|------|-------------|----------------|
| `PERSONA` | string | Lead persona classification | "SCM", "IT", "c-level" |
| `CAMPAIGN ZUWEISUNG` | string | Campaign assignment | "2ND: Mid-Big companies", "3RD: High Followers" |
| `Organization - ID` | string | Organization identifier | "5880", "6313" |
| `RETAILER` | string | Retailer information | "Edeka", "Rewe", "Kaufland" |
| `NORMALIZEDNAME` | string | Normalized company name | "Teigwaren Riesa", "Marks and Spencer" |
| `emailStatus` | string | Email status (optional) | "risky" |

### Campaign-Specific Fields
Different campaigns may have unique fields:

#### German Campaigns (DE)
```typescript
interface GermanCampaignLead extends Lead {
  "CAMPAIGN ZUWEISUNG": string;
  "RETAILER": string;
  "NORMALIZEDNAME": string;
}
```

#### English Campaigns (EN)
```typescript
interface EnglishCampaignLead extends Lead {
  "Organization - RETAILER _WILL BE DE": string;
  // May not have CAMPAIGN ZUWEISUNG, RETAILER, NORMALIZEDNAME
}
```

## 📊 Lead States

### State Values
| State | Description | System State |
|-------|-------------|--------------|
| `emailsSent` | Email sent, no response yet | `inProgress` |
| `emailsOpened` | Lead opened the email | `inProgress` |
| `emailsReplied` | Lead replied to email | `inProgress` |
| `emailsUnsubscribed` | Lead unsubscribed | `inProgress` |
| `reviewed` | Lead has been reviewed | `reviewed` |
| `contacted` | Lead was contacted | `inProgress` |
| `hooked` | Lead opened email or LinkedIn | `inProgress` |
| `interested` | Lead marked as interested | `inProgress` |

### State System Values
| Value | Description |
|-------|-------------|
| `inProgress` | Lead is actively being processed |
| `reviewed` | Lead has been manually reviewed |
| `completed` | Lead processing is complete |

## 🏢 Company Data

### Company Information
```typescript
interface CompanyData {
  companyName: string;        // Full company name
  companyDomain: string;      // Company domain
  NORMALIZEDNAME?: string;    // Normalized company name
  "Organization - ID"?: string; // Organization identifier
}
```

### Retailer Information
```typescript
interface RetailerData {
  RETAILER?: string;                              // German campaigns
  "Organization - RETAILER _WILL BE DE"?: string; // English campaigns
}
```

## 👤 Persona Classifications

### Persona Types
| Persona | Description | Example Roles |
|---------|-------------|---------------|
| `SCM` | Supply Chain Management | Supply Chain Manager, Logistics |
| `IT` | Information Technology | IT Manager, System Administrator |
| `c-level` | C-Level Executive | CEO, CTO, CMO |
| `sales` | Sales | Sales Manager, Account Manager |
| `marketing` | Marketing | Marketing Manager, Brand Manager |

## 🔍 Field Discovery

### Dynamic Field Detection
```typescript
function discoverFields(leads: Lead[]): string[] {
  if (leads.length === 0) return [];
  
  const firstLead = leads[0];
  return Object.keys(firstLead).sort();
}

function getFieldTypes(lead: Lead): Record<string, string> {
  const types: Record<string, string> = {};
  
  Object.keys(lead).forEach(key => {
    const value = lead[key];
    types[key] = typeof value;
  });
  
  return types;
}
```

### Field Analysis
```typescript
function analyzeFields(leads: Lead[]): {
  totalFields: number;
  commonFields: string[];
  uniqueFields: string[];
  fieldTypes: Record<string, string>;
} {
  const allFields = new Set<string>();
  const fieldTypes: Record<string, string> = {};
  
  leads.forEach(lead => {
    Object.keys(lead).forEach(key => {
      allFields.add(key);
      if (!fieldTypes[key]) {
        fieldTypes[key] = typeof lead[key];
      }
    });
  });
  
  return {
    totalFields: allFields.size,
    commonFields: Array.from(allFields).sort(),
    uniqueFields: [], // Would need comparison logic
    fieldTypes
  };
}
```

## 📈 Data Validation

### Lead Validation
```typescript
function validateLead(lead: Lead): {
  isValid: boolean;
  errors: string[];
} {
  const errors: string[] = [];
  
  if (!lead._id) errors.push('Missing _id');
  if (!lead.email) errors.push('Missing email');
  if (!lead.state) errors.push('Missing state');
  
  return {
    isValid: errors.length === 0,
    errors
  };
}
```

### Campaign Validation
```typescript
function validateCampaign(campaign: Campaign): {
  isValid: boolean;
  errors: string[];
} {
  const errors: string[] = [];
  
  if (!campaign._id) errors.push('Missing _id');
  if (!campaign.name) errors.push('Missing name');
  if (!campaign.status) errors.push('Missing status');
  
  return {
    isValid: errors.length === 0,
    errors
  };
}
```

## 🚀 Usage Examples

### Type-Safe Lead Processing
```typescript
function processLeads(leads: Lead[]): ProcessedLead[] {
  return leads.map(lead => ({
    id: lead._id,
    email: lead.email,
    name: `${lead.firstName || ''} ${lead.lastName || ''}`.trim(),
    company: lead.companyName || 'Unknown',
    jobTitle: lead.jobTitle || 'Unknown',
    state: lead.state,
    linkedin: lead.linkedinUrl,
    // Handle dynamic fields
    persona: lead.PERSONA || 'Unknown',
    retailer: lead.RETAILER || lead['Organization - RETAILER _WILL BE DE'] || 'Unknown'
  }));
}
```

### Campaign Analysis
```typescript
function analyzeCampaign(campaign: Campaign, leads: Lead[]): CampaignAnalysis {
  const fieldAnalysis = analyzeFields(leads);
  const stateCounts = leads.reduce((acc, lead) => {
    acc[lead.state] = (acc[lead.state] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);
  
  return {
    campaignId: campaign._id,
    campaignName: campaign.name,
    totalLeads: leads.length,
    totalFields: fieldAnalysis.totalFields,
    fieldStructure: fieldAnalysis.commonFields,
    stateDistribution: stateCounts
  };
}
```

## 📚 Related Documentation

- [API Reference](./api-reference.md)
- [Setup Guide](./setup.md)
- [Testing Guide](./testing.md)
