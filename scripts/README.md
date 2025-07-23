# Google Sheets API Client with Application Default Credentials

This module provides a simplified interface to Google Sheets API using service account authentication via Application Default Credentials for the PepWorkday project.

## Features

- **Application Default Credentials**: Uses service account authentication via `GOOGLE_APPLICATION_CREDENTIALS` environment variable
- **Comprehensive API Coverage**: Supports read, write, append, and clear operations
- **Error Handling**: Robust error handling with detailed logging
- **Type Hints**: Full type annotations for better IDE support
- **Testing**: Comprehensive unit tests and integration tests
- **Documentation**: Inline comments and docstrings

## Configuration

### PepWorkday Settings
- **Spreadsheet ID**: `1e5lulkbbwk6F9Xu97K38f40PUGVdp_f7W9qh31UglcU`
- **Service Account**: `pepmove@pepworkday.iam.gserviceaccount.com`
- **Project ID**: `pepworkday`

### Required Scopes
- `https://www.googleapis.com/auth/spreadsheets` - Full access to Google Sheets
- `https://www.googleapis.com/auth/drive` - Access to Google Drive (for spreadsheet metadata)

## Setup

### 1. Install Dependencies

```bash
pip install google-api-python-client google-auth google-auth-oauthlib google-auth-httplib2
```

### 2. Set Environment Variable

Set the `GOOGLE_APPLICATION_CREDENTIALS` environment variable to point to your service account JSON file:

**Linux/macOS:**
```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/pepmove-service-account.json"
```

**Windows (PowerShell):**
```powershell
$env:GOOGLE_APPLICATION_CREDENTIALS="C:\path\to\pepmove-service-account.json"
```

**Windows (Command Prompt):**
```cmd
set GOOGLE_APPLICATION_CREDENTIALS=C:\path\to\pepmove-service-account.json
```

### 3. Service Account Permissions

Ensure the service account (`pepmove@pepworkday.iam.gserviceaccount.com`) has been granted access to the target spreadsheet:

1. Open the Google Sheets document
2. Click "Share" 
3. Add `pepmove@pepworkday.iam.gserviceaccount.com` with "Editor" permissions

## Usage

### Basic Usage

```python
from sheets import create_sheets_client

# Create client (uses default spreadsheet ID)
client = create_sheets_client()

# Read data
values = client.get_values('RawData!A1:Z10')
print(f"Read {len(values)} rows")

# Write data
data = [['Header1', 'Header2'], ['Value1', 'Value2']]
result = client.update_values('RawData!A1:B2', data)
print(f"Updated {result.get('updatedCells', 0)} cells")

# Append data
new_data = [['New Row', 'New Value']]
result = client.append_values('RawData!A:B', new_data)
print(f"Appended {result.get('updates', {}).get('updatedCells', 0)} cells")
```

### Advanced Usage

```python
from sheets import SheetsClient

# Create client with custom spreadsheet ID
client = SheetsClient('your_custom_spreadsheet_id')

# Get spreadsheet information
info = client.get_spreadsheet_info()
print(f"Spreadsheet: {info.get('properties', {}).get('title')}")

# List all worksheets
worksheets = client.list_worksheets()
print(f"Worksheets: {worksheets}")

# Clear a range
client.clear_values('RawData!A1:Z100')
```

### Error Handling

```python
from sheets import create_sheets_client
from googleapiclient.errors import HttpError

try:
    client = create_sheets_client()
    values = client.get_values('NonExistentSheet!A1:B2')
except HttpError as e:
    print(f"API Error: {e}")
except FileNotFoundError as e:
    print(f"Credentials file not found: {e}")
except ValueError as e:
    print(f"Configuration error: {e}")
```

## API Reference

### SheetsClient Class

#### Constructor
```python
SheetsClient(spreadsheet_id: str = SPREADSHEET_ID)
```

#### Methods

**`get_values(range_name: str) -> List[List[str]]`**
- Get values from a specific range
- Returns 2D list of cell values

**`update_values(range_name: str, values: List[List[Any]], value_input_option: str = 'RAW') -> Dict[str, Any]`**
- Update values in a specific range
- Returns API response with update information

**`append_values(range_name: str, values: List[List[Any]], value_input_option: str = 'RAW') -> Dict[str, Any]`**
- Append values to the end of a range
- Returns API response with append information

**`clear_values(range_name: str) -> Dict[str, Any]`**
- Clear values in a specific range
- Returns API response

**`get_spreadsheet_info() -> Dict[str, Any]`**
- Get spreadsheet metadata
- Returns full spreadsheet information

**`list_worksheets() -> List[str]`**
- Get list of worksheet names
- Returns list of worksheet titles

### Factory Function

**`create_sheets_client(spreadsheet_id: str = SPREADSHEET_ID) -> SheetsClient`**
- Create a SheetsClient instance
- Uses default spreadsheet ID if not provided

## Testing

### Run Unit Tests

```bash
# Run all tests
python -m pytest tests/test_sheets.py -v

# Run with coverage
python -m pytest tests/test_sheets.py --cov=sheets --cov-report=html

# Run specific test class
python -m pytest tests/test_sheets.py::TestSheetsClient -v

# Run integration tests (requires valid credentials)
python -m pytest tests/test_sheets.py::TestSheetsIntegration -v
```

### Test the `test_auth()` Function

The `test_auth()` function in `tests/test_sheets.py` performs a simple read operation on `RawData!A1` and asserts that it returns a list:

```python
def test_auth(self):
    """Test authentication and basic read operation on RawData!A1."""
    client = create_sheets_client()
    values = client.get_values('RawData!A1')
    self.assertIsInstance(values, list)
```

### Run Example Script

```bash
# Set credentials and run example
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/pepmove-service-account.json"
python examples/sheets_example.py
```

## Logging

The module uses Python's built-in logging module. Configure logging level as needed:

```python
import logging
logging.basicConfig(level=logging.INFO)
```

Log levels used:
- `INFO`: Successful operations, initialization
- `ERROR`: API errors, authentication failures
- `DEBUG`: Detailed operation information

## Security Considerations

1. **Credentials Security**: Never commit service account JSON files to version control
2. **Environment Variables**: Use environment variables for credential paths
3. **Least Privilege**: Grant minimum necessary permissions to the service account
4. **Audit Logging**: Monitor API usage through Google Cloud Console

## Troubleshooting

### Common Issues

**1. `GOOGLE_APPLICATION_CREDENTIALS` not set**
```
ValueError: GOOGLE_APPLICATION_CREDENTIALS environment variable not set
```
**Solution**: Set the environment variable to point to your service account JSON file

**2. Credentials file not found**
```
FileNotFoundError: Service account file not found: /path/to/file.json
```
**Solution**: Verify the file path and ensure the file exists

**3. Permission denied**
```
HttpError 403: The caller does not have permission
```
**Solution**: Share the spreadsheet with the service account email address

**4. Invalid range**
```
HttpError 400: Unable to parse range
```
**Solution**: Use valid A1 notation (e.g., 'Sheet1!A1:B10')

### Debug Steps

1. Verify environment variable: `echo $GOOGLE_APPLICATION_CREDENTIALS`
2. Check file exists: `ls -la $GOOGLE_APPLICATION_CREDENTIALS`
3. Validate JSON format: `python -m json.tool $GOOGLE_APPLICATION_CREDENTIALS`
4. Test authentication: `python scripts/sheets.py`
5. Run integration tests: `python -m pytest tests/test_sheets.py::TestSheetsIntegration -v`

## License

This module is part of the PepWorkday project and follows the project's licensing terms.
