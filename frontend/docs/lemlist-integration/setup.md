# Lemlist Integration Setup

Complete setup guide for the Lemlist API integration.

## 📋 Prerequisites

- Node.js 18+ 
- npm or yarn
- Lemlist API key
- Next.js 15 project

## 🔧 Installation

### 1. Install Dependencies

```bash
npm install dotenv tsx
```

### 2. Environment Configuration

Create `.env.local` in project root:

```env
LEMLIST_API_KEY=your_api_key_here
```

**⚠️ Security Note:** Never commit `.env.local` to version control.

### 3. Project Structure

```
src/
├── lib/
│   └── lemlist/
│       ├── auth.ts          # Authentication & API calls
│       └── types.ts         # TypeScript interfaces
├── scripts/
│   ├── test-lemlist.ts      # Basic authentication test
│   ├── test-essential.ts    # Complete integration test
│   ├── test-specific-campaign.ts  # Campaign-specific test
│   └── discover-lead-fields.ts    # Field discovery test
└── app/
    └── api/                 # Future API routes
```

## 🚀 Quick Start

### 1. Test Authentication

```bash
npm run test-lemlist
```

Expected output:
```
✅ Authentication successful!
Team: Your Team Name
```

### 2. Test Campaign Retrieval

```bash
npm run test-essential
```

This will:
- Retrieve all running campaigns
- Get leads for the first campaign
- Show all available fields dynamically

### 3. Test Specific Campaign

```bash
npm run test-specific
```

Tests a specific campaign with detailed field analysis.

## 📊 Available Scripts

| Script | Purpose | Command |
|--------|---------|---------|
| `test-lemlist` | Basic authentication test | `npm run test-lemlist` |
| `test-essential` | Complete integration test | `npm run test-essential` |
| `test-specific` | Specific campaign test | `npm run test-specific` |
| `discover-fields` | Field discovery test | `npm run discover-fields` |

## 🔑 Authentication

The integration uses Basic Authentication:

```typescript
const authHeader = Buffer.from(`:${apiKey}`).toString('base64');
```

Headers:
```typescript
{
  'Authorization': `Basic ${authHeader}`,
  'Content-Type': 'application/json'
}
```

## 📡 API Endpoints

### Campaigns
- **GET** `https://api.lemlist.com/api/campaigns`
- **Parameters**: `limit`, `page`, `sortBy`, `sortOrder`, `status`

### Leads
- **GET** `https://api.lemlist.com/api/campaigns/{campaignId}/export/leads`
- **Parameters**: `state`, `format`

## 🎯 Key Features

### Dynamic Field Extraction
- Automatically discovers all available fields
- Adapts to different campaign structures
- No hardcoded field names

### Campaign Support
- Multiple campaign types (DE, EN, etc.)
- Different field structures per campaign
- Complete data extraction

### Error Handling
- Comprehensive error checking
- Detailed error messages
- Graceful failure handling

## 🔍 Testing

### Field Discovery
```bash
npm run discover-fields
```

Shows all available fields for any campaign.

### Lead Analysis
```bash
npm run test-essential
```

Complete lead analysis with field comparison.

## 📈 Next Steps

1. **Frontend Integration** - Create React components
2. **API Routes** - Build Next.js API endpoints
3. **Data Visualization** - Create dashboards
4. **Real-time Updates** - Add live data refresh

## 🆘 Troubleshooting

See [Troubleshooting Guide](./troubleshooting.md) for common issues.

## 📚 Additional Resources

- [API Reference](./api-reference.md)
- [Data Models](./data-models.md)
- [Testing Guide](./testing.md)
