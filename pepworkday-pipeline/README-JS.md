# PepWorkday Pipeline - JavaScript Components

This directory contains the JavaScript/Node.js components of the PepWorkday pipeline, designed for Vercel deployment with seamless GCP integration. Features a complete Next.js dashboard with Google Sheets integration, Chart.js visualization, analytics tracking, security enhancements, and comprehensive testing.

## 🏗️ Architecture

```
pepworkday-pipeline/
├── components/
│   ├── SummaryChart.js        # React Chart.js component for data visualization
│   └── PostHogProvider.js     # PostHog analytics provider
├── pages/
│   ├── api/
│   │   ├── summary.js         # Legacy single-sheet API route
│   │   └── fetchSheets.js     # Multi-workbook batch fetch API route
│   ├── _app.js                # Next.js app with analytics and error boundaries
│   ├── dashboard.js           # Main dashboard page with multi-workbook support
│   └── index.js               # Home page with redirect
├── config.json                # Multi-workbook configuration file
├── lib/
│   ├── analytics.js           # Unified analytics (GA4 + PostHog)
│   ├── dataAccess.js          # Secure data access layer
│   ├── logger.js              # Structured logging with Vercel integration
│   └── security.js            # Security utilities and middleware
├── utils/
│   └── gcpCredentials.js      # Unified GCP credentials helper
├── integrations/
│   └── storageClient.js       # Google Cloud Storage client
├── tests/
│   ├── testGcpCredentials.js  # Test suite for credentials helper
│   ├── testApiSummary.js      # API endpoint smoke tests
│   ├── testFetchSheets.js     # Multi-workbook API tests
│   ├── testDashboardRender.js # E2E tests with Playwright
│   ├── global-setup.js        # Playwright global setup
│   └── global-teardown.js     # Playwright global teardown
├── .github/workflows/
│   └── e2e-tests.yml          # GitHub Actions E2E testing workflow
├── package.json               # Node.js dependencies and scripts
├── next.config.js             # Next.js configuration
├── playwright.config.js       # Playwright testing configuration
├── vercel.json                # Vercel deployment configuration
├── .env.local.example         # Environment variables template
├── index.js                   # Main entry point (legacy)
└── README-JS.md              # This file
```

## 🚀 Quick Start

### 1. Install Dependencies

```bash
npm install
```

### 2. Set Up Environment Variables

Create a `.env.local` file with required variables:

```bash
# Google Sheets Configuration
SHEET_ID=your_google_sheets_spreadsheet_id

# GCP Credentials (for local development, leave empty to use ADC)
# GCP_SERVICE_ACCOUNT_EMAIL=
# GCP_PRIVATE_KEY=
# GCP_PROJECT_ID=

# Analytics Configuration (optional)
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
NEXT_PUBLIC_POSTHOG_KEY=phc_xxxxxxxxxx
NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com
NEXT_PUBLIC_ENABLE_ANALYTICS=false

# Security Configuration
NODE_ENV=development
```

### 3. Run Development Server

```bash
npm run dev
```

Open [http://localhost:3000](http://localhost:3000) to view the dashboard.

### 4. Run Tests

```bash
# Run all tests
npm test

# Run API-specific tests
npm run test:api

# Run E2E tests with Playwright
npm run test:e2e

# Run E2E tests with UI mode
npm run test:e2e:ui

# Install Playwright browsers (first time only)
npm run playwright:install
```

### 5. Build for Production

```bash
npm run build
npm start
```

## 📊 Multi-Workbook Configuration

The dashboard supports fetching data from multiple Google Sheets workbooks using a configuration-driven approach.

### Configuration File (`config.json`)

Edit `config.json` to add, remove, or modify workbooks:

```json
[
  {
    "id": "YOUR_SPREADSHEET_ID_1",
    "name": "Primary Dispatch",
    "description": "Main dispatch workbook for daily operations",
    "sheets": [
      {
        "name": "Summary",
        "range": "A1:Z100",
        "description": "Daily dispatch summary data"
      }
    ]
  },
  {
    "id": "YOUR_SPREADSHEET_ID_2",
    "name": "Secondary Dispatch",
    "description": "Secondary dispatch workbook for overflow operations",
    "sheets": [
      {
        "name": "Summary",
        "range": "A1:Z100",
        "description": "Secondary dispatch summary data"
      }
    ]
  }
]
```

### API Usage

The `/api/fetchSheets` endpoint supports the following query parameters:

```javascript
// Fetch all workbooks
const response = await fetch('/api/fetchSheets?workbook=all');

// Fetch specific workbook by index (0-3)
const response = await fetch('/api/fetchSheets?workbook=0');

// Response format
{
  "success": true,
  "workbooksRequested": "all",
  "workbooksCount": 4,
  "data": {
    "workbook_0": {
      "id": "SPREADSHEET_ID",
      "name": "Primary Dispatch",
      "description": "Main dispatch workbook",
      "sheets": {
        "Summary": {
          "data": [["Header1", "Header2"], ["Row1Col1", "Row1Col2"]],
          "range": "A1:Z100",
          "rowCount": 50,
          "lastUpdated": "2024-01-15T10:30:00.000Z"
        }
      },
      "fetchedAt": "2024-01-15T10:30:00.000Z"
    }
  }
}
```

### Dashboard UI

The dashboard includes:

- **Workbook Selector**: Dropdown to choose between individual workbooks or "All Workbooks"
- **Dynamic Charts**: Each workbook's data is displayed in separate chart sections
- **Real-time Updates**: Refresh button updates data for the selected workbook(s)
- **Error Handling**: Individual workbook errors don't affect other workbooks

### Testing Multi-Workbook API

```bash
# Test single workbook
npm run test:api -- --grep "single workbook"

# Test all workbooks
npm run test:api -- --grep "all workbooks"

# Run full multi-workbook test suite
node tests/testFetchSheets.js
```

## 🔧 Components

### Analytics Integration

The application includes comprehensive analytics tracking:

#### Google Analytics 4
```javascript
// Automatic page view tracking
// Custom event tracking
import { trackEvent } from '../lib/analytics';

trackEvent('button_clicked', {
  button_name: 'refresh',
  location: 'dashboard'
});
```

#### PostHog Analytics
```javascript
// Product analytics and feature flags
import { usePostHogSafe } from '../components/PostHogProvider';

const posthog = usePostHogSafe();
posthog?.capture('dashboard_viewed', { user_type: 'admin' });
```

### Security Features

#### Secure Data Access Layer
```javascript
import { SecureDataAccess } from '../lib/dataAccess';

const dataAccess = new SecureDataAccess(logger);
const data = await dataAccess.fetchSummaryData(spreadsheetId, range, clientIP);
```

#### Input Sanitization and Validation
```javascript
import { validateInput, sanitizeHTML } from '../lib/security';

const result = validateInput(userInput, {
  type: 'string',
  maxLength: 100,
  sanitizeHTML: true
});
```

### Monitoring and Logging

#### Structured Logging
```javascript
import { withLogging, createApiLogger } from '../lib/logger';

// Wrap API routes with logging
export default withLogging(handler, 'api-name');

// Create contextual loggers
const logger = createApiLogger(req, 'endpoint-name');
logger.info('Processing request', { userId: 123 });
```

### Next.js API Route (`pages/api/summary.js`)

Fetches data from Google Sheets using the unified GCP credentials helper:

```javascript
// GET /api/summary
// Returns: JSON array of summary data from Summary!A1:Z100 range

// Example response:
{
  "success": true,
  "data": [
    {
      "_rowIndex": 2,
      "Address": "123 Main St",
      "Total Jobs": 15,
      "Status": "Active"
    }
  ],
  "metadata": {
    "range": "Summary!A1:Z100",
    "rowCount": 25,
    "timestamp": "2024-01-15T10:30:00.000Z",
    "spreadsheetId": "your-sheet-id"
  }
}
```

### React Chart Component (`components/SummaryChart.js`)

Interactive Bar chart using Chart.js and react-chartjs-2:

```javascript
import SummaryChart from '../components/SummaryChart';

// Basic usage
<SummaryChart height={400} />

// With auto-refresh
<SummaryChart
  height={500}
  autoRefresh={true}
  refreshInterval={300000}
/>

// With custom options
<SummaryChart
  height={600}
  options={{
    plugins: {
      title: {
        text: 'Custom Chart Title'
      }
    }
  }}
/>
```

### GCP Credentials Helper (`utils/gcpCredentials.js`)

Provides unified credential management across environments:

- **Vercel**: Uses environment variables from GCP integration
- **Local**: Falls back to Application Default Credentials

```javascript
import { getGCPCredentials } from './utils/gcpCredentials.js';

const config = getGCPCredentials();
// Vercel: { credentials: {...}, projectId: "..." }
// Local: {} (uses ADC)
```

### Storage Client (`integrations/storageClient.js`)

Google Cloud Storage integration with error handling:

```javascript
import { uploadJSONData, downloadJSONData } from './integrations/storageClient.js';

// Upload data
const result = await uploadJSONData({ foo: 'bar' }, 'my-file.json');

// Download data
const data = await downloadJSONData('my-file.json');
```

## 🧪 Testing

The test suite includes comprehensive testing for both credentials and API endpoints:

### Credential Tests

```bash
# Run credential tests
node --test tests/testGcpCredentials.js
```

### API Smoke Tests

```bash
# Start development server first
npm run dev

# In another terminal, run API tests
npm run test:api
# or
node tests/testApiSummary.js
```

The API tests validate:
- Endpoint availability and response format
- Data structure validation
- Error handling scenarios
- Response time performance
- Method restrictions (GET only)

### End-to-End Tests with Playwright

```bash
# Install Playwright browsers (first time)
npm run playwright:install

# Run E2E tests
npm run test:e2e

# Run with UI mode for debugging
npm run test:e2e:ui

# Run specific browser
npx playwright test --project=chromium
```

E2E tests cover:
- Dashboard page rendering and functionality
- Chart visualization and interactions
- API integration and error handling
- Responsive design across devices
- Performance metrics and Core Web Vitals
- Accessibility compliance
- Network failure scenarios

### All Tests

```bash
# Run all tests
npm test
```

## 🌐 Vercel Deployment

### Environment Variables

Configure these in your Vercel dashboard:

```bash
# Required for Google Sheets API
SHEET_ID=your_google_sheets_spreadsheet_id

# GCP Integration (automatically injected by Vercel GCP integration)
GCP_SERVICE_ACCOUNT_EMAIL=your-service-account@project.iam.gserviceaccount.com
GCP_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...\n-----END PRIVATE KEY-----
GCP_PROJECT_ID=your-gcp-project-id

# Analytics (optional)
NEXT_PUBLIC_GA_MEASUREMENT_ID=G-XXXXXXXXXX
NEXT_PUBLIC_POSTHOG_KEY=phc_xxxxxxxxxx
NEXT_PUBLIC_POSTHOG_HOST=https://app.posthog.com

# Optional
GCP_STORAGE_BUCKET=pepworkday-data
GCP_FILE_PREFIX=pepmove
```

### Vercel Configuration

The `vercel.json` file is already configured with:

- Next.js framework detection
- API route optimization
- Environment variable mapping
- CORS headers for API routes
- Caching configuration

Key configuration features:
- API routes run with 30-second timeout
- Automatic redirects from `/` to `/dashboard`
- Proper CORS headers for API endpoints
- Environment variable references using `@` syntax
- Vercel Analytics and Speed Insights enabled
- Enhanced observability and monitoring

## 🚀 CI/CD Pipeline

### GitHub Actions Workflow

The project includes a comprehensive CI/CD pipeline (`.github/workflows/e2e-tests.yml`):

#### Quality Checks
- ESLint code linting
- TypeScript type checking
- Security vulnerability scanning

#### E2E Testing
- Multi-browser testing (Chromium, Firefox, WebKit)
- Mobile device testing
- Performance testing with Lighthouse
- Accessibility compliance testing

#### Deployment
- Automatic preview deployments for PRs
- Production deployment on main branch
- Test result reporting and artifacts

### Running CI/CD Locally

```bash
# Run quality checks
npm run lint

# Run all tests (unit + E2E)
npm test && npm run test:e2e

# Run security audit
npm audit

# Build for production
npm run build
```

### Test Coverage and Reporting

The pipeline generates:
- HTML test reports (Playwright)
- JUnit XML reports for CI integration
- Performance metrics and Core Web Vitals
- Security audit reports
- Test coverage summaries

## 📊 Dashboard Usage

### Accessing the Dashboard

1. **Local Development**: http://localhost:3000
2. **Production**: Your Vercel deployment URL

### Dashboard Features

- **Real-time Data**: Fetches latest data from Google Sheets
- **Interactive Charts**: Bar chart showing jobs by address
- **API Status**: Live status indicator for the Google Sheets API
- **Auto-refresh**: Optional automatic data updates every 5 minutes
- **Responsive Design**: Works on desktop and mobile devices

### API Endpoints

#### GET /api/summary

Fetches summary data from Google Sheets `Summary!A1:Z100` range.

**Response Format:**
```json
{
  "success": true,
  "data": [
    {
      "_rowIndex": 2,
      "Address": "123 Main St",
      "Total Jobs": 15,
      "Status": "Active"
    }
  ],
  "metadata": {
    "range": "Summary!A1:Z100",
    "rowCount": 25,
    "timestamp": "2024-01-15T10:30:00.000Z",
    "spreadsheetId": "your-sheet-id"
  }
}
```

**Error Response:**
```json
{
  "success": false,
  "error": "Authentication failed: Invalid credentials",
  "timestamp": "2024-01-15T10:30:00.000Z"
}
```

### Chart Component Usage

The `SummaryChart` component automatically:
1. Fetches data from `/api/summary`
2. Processes data to extract addresses (Column A) and job counts (Column B)
3. Renders an interactive Bar chart
4. Handles loading states and errors
5. Provides optional auto-refresh functionality

## 🔗 Integration with Python Pipeline

The JavaScript components complement the existing Python pipeline:

- **Python**: Core data processing, Excel ingestion, Samsara API
- **JavaScript**: Next.js dashboard, Google Sheets visualization, web interfaces
- **Shared Resources**: Same GCP project, Google Sheets, and storage buckets

### Data Flow

1. **Python Pipeline**: Processes dispatch data and updates Google Sheets
2. **JavaScript Dashboard**: Reads from Google Sheets and visualizes data
3. **Real-time Updates**: Dashboard reflects changes made by Python pipeline

## 📝 Development

### Code Style

- Use ES modules (`import`/`export`)
- Include JSDoc comments for all functions
- Handle errors gracefully with try/catch
- Log operations with appropriate emoji prefixes

### Adding New Features

1. Create feature in appropriate directory (`utils/`, `integrations/`)
2. Add comprehensive JSDoc documentation
3. Include error handling and logging
4. Write tests in `tests/` directory
5. Update this README

## 🤝 Contributing

Follow the same contribution guidelines as the main Python pipeline:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## 📚 Related Documentation

- [Main README](../README.md) - Python pipeline documentation
- [Vercel Documentation](https://vercel.com/docs)
- [Google Cloud Storage Node.js Client](https://googleapis.dev/nodejs/storage/latest/)
- [Node.js Test Runner](https://nodejs.org/api/test.html)
