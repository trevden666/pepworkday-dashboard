# PepWorkday Pipeline for PEPMove

A production-ready Python data pipeline that automates the daily ingestion of dispatch and Samsara Excel reports, transforms and validates data, enriches with real-world route metrics, and syncs into a centralized Google Sheets workbook.

**PEPMove Configuration:**
- Organization ID: 5005620
- Group ID: 129031
- API Token: [Set via SAMSARA_API_TOKEN environment variable]

## 🚀 Features

### Core Pipeline Features
- **Excel Processing**: Robust Excel parsing with pandas + openpyxl and schema validation
- **PEPMove Samsara Integration**: Full API integration with PEPMove's Samsara organization (5005620) and group (129031)
- **Advanced Fleet Tracking**: Real-time vehicle locations, historical tracking, and fleet summaries
- **Address & Route Management**: Create and manage addresses and routes through Samsara API
- **Google Sheets Sync**: OAuth2/service-account authenticated upserts keyed by `_kp_job_id`
- **Data Enrichment**: Merges Samsara miles, stops, and idle-time calculations with dispatch data
- **Slack Notifications**: Rich notifications summarizing daily KPIs or errors
- **CLI Interface**: Comprehensive command-line tool with PEPMove-specific options and dry-run support

### Advanced Integration Features
- **🔗 Webhook Integration**: Real-time event processing with Flask-based webhook receiver
- **🔄 Advanced Polling**: Intelligent scheduled polling with pagination, rate limiting, and deduplication
- **📊 Enhanced Google Sheets**: Batch operations, idempotent upserts, and real-time synchronization
- **📈 Auto-Refresh Dashboard**: Interactive dashboard with live data updates and filtering
- **🔒 Security & Best Practices**: Secure token management, rate limiting, and audit logging
- **📱 Monitoring & Alerting**: Comprehensive monitoring with intelligent error handling and Slack alerts
- **⚙️ CI/CD Automation**: GitHub Actions workflows with scheduled execution and quality checks
- **🛡️ Production Ready**: Full testing suite, linting, type checking, and security compliance

## 📋 Prerequisites

- Python 3.9+
- Google Sheets API credentials (service account JSON file)
- Samsara API token (optional, for API-based data fetching)
- Slack Bot token or Webhook URL (optional, for notifications)

## 🛠️ Installation

1. **Clone the repository:**
   ```bash
   git clone https://github.com/trevden666/pepworkday.git
   cd pepworkday/pepworkday-pipeline
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Install the package:**
   ```bash
   pip install -e .
   ```

4. **Set up environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your configuration
   ```

## ⚙️ Configuration

### Environment Variables

Create a `.env` file based on `.env.example`:

```bash
# Google Sheets Configuration
GOOGLE_SHEETS_CREDENTIALS_PATH=path/to/service-account-key.json
GOOGLE_SHEETS_SPREADSHEET_ID=your_spreadsheet_id_here
GOOGLE_SHEETS_WORKSHEET_NAME=RawData

# PEPMove Samsara Configuration
SAMSARA_API_TOKEN=samsara_api_7qCpNNFjxM5S4jojGWzO9vxciB8o8I
SAMSARA_BASE_URL=https://api.samsara.com
SAMSARA_ORGANIZATION_ID=5005620
SAMSARA_GROUP_ID=129031

# Samsara API Behavior Settings
SAMSARA_USE_API=true
SAMSARA_API_TIMEOUT=30
SAMSARA_MAX_RETRIES=3

# PEPMove Operational Settings
SAMSARA_DEFAULT_VEHICLE_GROUP=129031
SAMSARA_ENABLE_REAL_TIME_TRACKING=true
SAMSARA_LOCATION_UPDATE_INTERVAL=300

# Slack Configuration
SLACK_BOT_TOKEN=xoxb-your-slack-bot-token-here
SLACK_CHANNEL=#automation-alerts
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/your/webhook/url

# Pipeline Configuration
PIPELINE_LOG_LEVEL=INFO
PIPELINE_DRY_RUN=false
PIPELINE_BATCH_SIZE=1000
```

### Google Sheets Setup

1. Create a Google Cloud Project
2. Enable the Google Sheets API
3. Create a service account and download the JSON credentials file
4. Share your Google Sheets document with the service account email
5. Set `GOOGLE_SHEETS_CREDENTIALS_PATH` to the JSON file path

### Samsara API Setup

The pipeline supports both file-based and API-based Samsara data ingestion:

**API-based (Recommended):**
- Set `SAMSARA_USE_API=true`
- Configure `SAMSARA_API_TOKEN` with your Samsara API token
- The pipeline will automatically fetch trip data for the specified date range

**File-based:**
- Set `SAMSARA_USE_API=false`
- Use the `--samsara-file` CLI option to specify the path to your Samsara CSV/Excel file

## 🔐 Environment & Auth

### Vercel GCP Integration Setup

The pipeline includes JavaScript components designed for Vercel deployment with seamless GCP integration:

#### 1. Configure Vercel GCP Integration

In your Vercel dashboard:
1. Go to your project settings
2. Navigate to "Integrations"
3. Add the "Google Cloud Platform" integration
4. Configure the following environment variables:
   - `GCP_SERVICE_ACCOUNT_EMAIL`: Your service account email
   - `GCP_PRIVATE_KEY`: Your service account private key
   - `GCP_PROJECT_ID`: Your GCP project ID
   - `GCP_STORAGE_BUCKET`: Your Cloud Storage bucket name (optional)

#### 2. Local Development Setup

For local development, use Google Cloud CLI:

```bash
# Install Google Cloud CLI
# https://cloud.google.com/sdk/docs/install

# Authenticate with your Google account
gcloud auth login

# Set up Application Default Credentials
gcloud auth application-default login

# Set your default project
gcloud config set project YOUR_PROJECT_ID
```

#### 3. Using the GCP Credentials Helper

The unified credentials helper automatically detects your environment:

```javascript
import { getGCPCredentials } from './utils/gcpCredentials.js';

// Works in both Vercel and local environments
const gcpConfig = getGCPCredentials();

// In Vercel: Uses environment variables
// In local dev: Uses Application Default Credentials (empty object)
```

#### 4. Google Cloud Storage Integration

Example usage of the storage client:

```javascript
import { storageClient, uploadJSONData } from './integrations/storageClient.js';

// Upload PEPMove data to Cloud Storage
const pepMoveData = {
  organizationId: '5005620',
  groupId: '129031',
  vehicles: await getVehicleData(),
  timestamp: new Date().toISOString()
};

const result = await uploadJSONData(pepMoveData, 'pepmove-daily-report.json');
console.log(`Data uploaded to: ${result.publicUrl}`);
```

#### 5. Environment Variables Reference

**Vercel Environment (automatically injected by GCP integration):**
```bash
GCP_SERVICE_ACCOUNT_EMAIL=pepworkday@my-project.iam.gserviceaccount.com
GCP_PRIVATE_KEY=-----BEGIN PRIVATE KEY-----\n...
GCP_PROJECT_ID=my-gcp-project
GCP_STORAGE_BUCKET=pepworkday-data  # Optional
```

**Local Development (leave empty for ADC):**
```bash
# Leave these empty or unset for local development
# GCP_SERVICE_ACCOUNT_EMAIL=
# GCP_PRIVATE_KEY=
# GCP_PROJECT_ID=
```

## 🚀 Usage

### Command Line Interface

The main pipeline can be run using the CLI:

```bash
# Basic usage with Excel file (uses Samsara API)
pepworkday-pipeline --excel data/dispatch_report.xlsx

# Use a specific Samsara data file instead of API
pepworkday-pipeline --excel data/dispatch_report.xlsx --samsara-file data/samsara_trips.csv

# Dry run mode (no changes made)
pepworkday-pipeline --excel data/dispatch_report.xlsx --dry-run

# Specify date range for Samsara API data
pepworkday-pipeline --excel data/dispatch_report.xlsx --start-date 2024-01-15 --end-date 2024-01-16

# Custom worksheet and Slack channel
pepworkday-pipeline --excel data/dispatch_report.xlsx --worksheet-name "January_Data" --slack-channel "#operations"

# Debug mode with verbose logging
pepworkday-pipeline --excel data/dispatch_report.xlsx --log-level DEBUG

# PEPMove-specific options
pepworkday-pipeline --excel data/dispatch_report.xlsx --include-locations --pepmove-summary

# Generate comprehensive PEPMove fleet report
pepworkday-pipeline --excel data/dispatch_report.xlsx --pepmove-summary --worksheet-name "PEPMove_Fleet_Report"
```

### Advanced Features Usage

#### Webhook Integration
```bash
# Start webhook receiver for real-time events
python -m pepworkday_pipeline.integrations.webhook_receiver

# Webhook endpoint: http://your-server:5000/webhook/samsara
# Health check: http://your-server:5000/webhook/health
```

#### Advanced Polling
```python
from pepworkday_pipeline.core.advanced_polling import create_advanced_poller

# Create and run advanced poller
poller = create_advanced_poller()
results = poller.poll_fleet_data(data_types=['trips', 'locations', 'driver_stats'])

# Run continuous polling
poller.run_continuous_polling(interval_seconds=300)
```

#### Auto-Refresh Dashboard
```bash
# Open the dashboard in your browser
open pepworkday-pipeline/dashboard/auto_refresh_dashboard.html

# Dashboard features:
# - Real-time data updates every 60 seconds
# - Interactive filters for date range, drivers, vehicles
# - Live fleet metrics and charts
# - PEPMove-specific branding and context
```

### Pipeline Flow

1. **Excel Ingestion**: Load and validate dispatch Excel file
2. **Data Normalization**: Standardize column names and data types
3. **Samsara Data Loading**: Fetch trip data from API or file
4. **Data Enrichment**: Merge dispatch and Samsara data, calculate metrics
5. **Google Sheets Upload**: Upsert enriched data to Google Sheets
6. **Slack Notification**: Send success/failure notifications

### Key Metrics Calculated

- **Miles Variance**: Actual vs planned miles (from Samsara vs dispatch)
- **Stops Variance**: Actual vs planned stops
- **Idle Percentage**: Percentage of trip time spent idle
- **Match Rate**: Percentage of dispatch records matched with Samsara data

## 🧪 Testing

Run the test suite:

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pepworkday_pipeline

# Run specific test file
pytest tests/test_samsara_api.py

# Run with verbose output
pytest -v
```

## 🔧 Development

### Code Quality Tools

The project includes comprehensive code quality tools:

```bash
# Linting
flake8 pepworkday-pipeline/

# Type checking
mypy pepworkday-pipeline/

# Code formatting
black pepworkday-pipeline/

# Import sorting
isort pepworkday-pipeline/
```

### VS Code Integration

Use Ctrl+Shift+B to run predefined tasks:
- **Lint**: Run flake8 linting
- **Type Check**: Run mypy type checking
- **Test**: Run pytest test suite
- **Format**: Run black code formatting

## 📊 Monitoring and Logging

The pipeline uses structured logging with configurable levels:

- **DEBUG**: Detailed debugging information
- **INFO**: General operational messages
- **WARNING**: Warning messages for non-critical issues
- **ERROR**: Error messages for failures

Logs include contextual information like processing times, record counts, and error details.

## 🔄 CI/CD

GitHub Actions workflows are configured for:

- **Continuous Integration**: Run tests, linting, and type checking on push/PR
- **Scheduled Execution**: Daily pipeline execution at 7 AM UTC
- **Dependency Updates**: Automated dependency updates with Dependabot

## 📈 PEPMove Samsara API Integration

The pipeline provides comprehensive Samsara API integration specifically configured for PEPMove operations:

### PEPMove Configuration
- **Organization ID**: 5005620
- **Group ID**: 129031
- **API Token**: samsara_api_7qCpNNFjxM5S4jojGWzO9vxciB8o8I

### Core Endpoints

- **Fleet Trips**: `/fleet/trips` - Trip data with miles, idle time, fuel usage
- **Driver Stats**: `/fleet/drivers/stats` - Aggregated driver statistics
- **Vehicle Stats**: `/fleet/vehicles/stats` - Vehicle performance metrics
- **Drivers**: `/fleet/drivers` - Driver information
- **Vehicles**: `/fleet/vehicles` - Vehicle information

### PEPMove-Specific Endpoints

- **Vehicle Locations**: `/fleet/vehicles/locations` - Real-time vehicle positions
- **Location History**: `/fleet/vehicles/locations/history` - Historical location tracking
- **Address Management**: `/addresses` - Create and manage delivery/pickup addresses
- **Route Management**: `/fleet/routes` - Create and manage delivery routes
- **Real-time Stats**: `/fleet/vehicles/stats` - Live vehicle status and metrics

### Advanced Features

- **Automatic PEPMove Context**: All API requests automatically include Organization ID (5005620) and Group ID (129031)
- **Fleet Summary Generation**: Built-in method to generate comprehensive PEPMove fleet summaries
- **Real-time Monitoring**: Support for real-time vehicle tracking and status monitoring
- **Address & Route Creation**: Programmatic creation of addresses and routes for PEPMove operations
- **Historical Analysis**: Access to historical location and trip data for route optimization

### Usage Examples

```python
from pepworkday_pipeline.utils.samsara_api import create_samsara_client

# Create PEPMove-configured client
client = create_samsara_client()

# Get PEPMove fleet summary
summary = client.get_pepmove_fleet_summary()
print(f"PEPMove has {summary['total_vehicles']} vehicles")

# Get current vehicle locations
locations = client.get_vehicle_locations()
print(f"Tracking {len(locations)} vehicles in real-time")

# Get trip data for analysis
from datetime import datetime, timedelta
end_date = datetime.now()
start_date = end_date - timedelta(days=7)
trips = client.get_fleet_trips(start_date, end_date)

# Create a new delivery address
new_address = client.create_address(
    name="Customer Delivery Point",
    formatted_address="123 Main St, City, ST 12345",
    latitude=40.7128,
    longitude=-74.0060,
    notes="Regular delivery location",
    tags=["delivery", "customer"]
)
```

### Data Processing

All PEPMove Samsara data is automatically processed and includes:
- Standardized column names
- PEPMove organization and group context
- Proper data type conversions
- Integration with the main pipeline workflow

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes
4. Run tests and linting (`pytest && flake8`)
5. Commit your changes (`git commit -m 'Add amazing feature'`)
6. Push to the branch (`git push origin feature/amazing-feature`)
7. Open a Pull Request

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

For support and questions:

1. Check the [Issues](https://github.com/trevden666/pepworkday/issues) page
2. Create a new issue with detailed information
3. Contact the development team via Slack

## 🔗 Related Documentation

- [Google Sheets API Documentation](https://developers.google.com/sheets/api)
- [Samsara API Documentation](https://developers.samsara.com/)
- [Slack API Documentation](https://api.slack.com/)
- [Pandas Documentation](https://pandas.pydata.org/docs/)
