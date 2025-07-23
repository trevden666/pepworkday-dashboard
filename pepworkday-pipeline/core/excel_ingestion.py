"""
Excel ingestion module for the PepWorkday pipeline.

Chain of thought:
1. Load Excel files using pandas with openpyxl engine for robust Excel support
2. Validate data against predefined schemas to ensure data quality
3. Normalize column names and data types for consistent processing
4. Handle common Excel issues like merged cells, empty rows, and formatting
5. Provide detailed error reporting and logging for troubleshooting
"""

import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import logging
import re
from datetime import datetime
from pydantic import BaseModel, ValidationError

logger = logging.getLogger(__name__)


class ExcelSchema(BaseModel):
    """Schema definition for Excel data validation."""
    
    required_columns: List[str]
    optional_columns: List[str] = []
    column_types: Dict[str, str] = {}
    date_columns: List[str] = []
    numeric_columns: List[str] = []


class ExcelValidationError(Exception):
    """Custom exception for Excel validation errors."""
    pass


def load_excel(
    file_path: Union[str, Path],
    sheet_name: Optional[str] = None,
    header_row: int = 0,
    skip_rows: Optional[List[int]] = None
) -> pd.DataFrame:
    """
    Load Excel file using pandas with robust error handling.
    
    Args:
        file_path: Path to the Excel file
        sheet_name: Name of the sheet to load (None for first sheet)
        header_row: Row number to use as column headers (0-indexed)
        skip_rows: List of row numbers to skip
        
    Returns:
        pandas.DataFrame: Loaded Excel data
        
    Raises:
        FileNotFoundError: If the Excel file doesn't exist
        ExcelValidationError: If the file cannot be loaded or parsed
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise FileNotFoundError(f"Excel file not found: {file_path}")
    
    logger.info(f"Loading Excel file: {file_path}")
    
    try:
        # Load Excel file with openpyxl engine for better Excel support
        df = pd.read_excel(
            file_path,
            sheet_name=sheet_name,
            header=header_row,
            skiprows=skip_rows,
            engine='openpyxl'
        )
        
        # Remove completely empty rows and columns
        df = df.dropna(how='all').dropna(axis=1, how='all')
        
        logger.info(f"Successfully loaded Excel file with {len(df)} rows and {len(df.columns)} columns")
        return df
        
    except Exception as e:
        error_msg = f"Failed to load Excel file {file_path}: {str(e)}"
        logger.error(error_msg)
        raise ExcelValidationError(error_msg) from e


def validate_schema(df: pd.DataFrame, schema: ExcelSchema) -> Dict[str, Any]:
    """
    Validate DataFrame against a predefined schema.
    
    Args:
        df: DataFrame to validate
        schema: Schema definition to validate against
        
    Returns:
        Dict containing validation results and any issues found
        
    Raises:
        ExcelValidationError: If validation fails and strict mode is enabled
    """
    validation_results = {
        'is_valid': True,
        'errors': [],
        'warnings': [],
        'missing_required_columns': [],
        'unexpected_columns': [],
        'type_mismatches': []
    }
    
    logger.info("Validating DataFrame schema")
    
    # Check for required columns
    missing_required = set(schema.required_columns) - set(df.columns)
    if missing_required:
        validation_results['missing_required_columns'] = list(missing_required)
        validation_results['errors'].append(f"Missing required columns: {missing_required}")
        validation_results['is_valid'] = False
    
    # Check for unexpected columns (optional warning)
    expected_columns = set(schema.required_columns + schema.optional_columns)
    unexpected_columns = set(df.columns) - expected_columns
    if unexpected_columns:
        validation_results['unexpected_columns'] = list(unexpected_columns)
        validation_results['warnings'].append(f"Unexpected columns found: {unexpected_columns}")
    
    # Validate column types
    for column, expected_type in schema.column_types.items():
        if column in df.columns:
            actual_type = str(df[column].dtype)
            if not _is_compatible_type(actual_type, expected_type):
                validation_results['type_mismatches'].append({
                    'column': column,
                    'expected': expected_type,
                    'actual': actual_type
                })
                validation_results['warnings'].append(
                    f"Column '{column}' type mismatch: expected {expected_type}, got {actual_type}"
                )
    
    # Log validation results
    if validation_results['is_valid']:
        logger.info("Schema validation passed")
    else:
        logger.error(f"Schema validation failed: {validation_results['errors']}")
    
    if validation_results['warnings']:
        logger.warning(f"Schema validation warnings: {validation_results['warnings']}")
    
    return validation_results


def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
    """
    Normalize column names and data types for consistent processing.
    
    Args:
        df: DataFrame to normalize
        
    Returns:
        pandas.DataFrame: DataFrame with normalized columns
    """
    logger.info("Normalizing DataFrame columns")
    
    # Create a copy to avoid modifying the original
    normalized_df = df.copy()
    
    # Normalize column names
    normalized_df.columns = [_normalize_column_name(col) for col in normalized_df.columns]
    
    # Remove duplicate columns (keep first occurrence)
    normalized_df = normalized_df.loc[:, ~normalized_df.columns.duplicated()]
    
    # Convert common data types
    normalized_df = _normalize_data_types(normalized_df)
    
    # Add _kp_job_id if not present (required for Google Sheets upserts)
    if '_kp_job_id' not in normalized_df.columns:
        normalized_df['_kp_job_id'] = _generate_job_ids(len(normalized_df))
        logger.info("Added _kp_job_id column for Google Sheets integration")
    
    logger.info(f"Column normalization complete. Final columns: {list(normalized_df.columns)}")
    return normalized_df


def _normalize_column_name(column_name: str) -> str:
    """Normalize a single column name to a consistent format."""
    # Convert to lowercase and replace spaces/special chars with underscores
    normalized = re.sub(r'[^\w\s]', '', str(column_name).lower())
    normalized = re.sub(r'\s+', '_', normalized.strip())
    
    # Remove leading/trailing underscores and collapse multiple underscores
    normalized = re.sub(r'_+', '_', normalized).strip('_')
    
    return normalized or 'unnamed_column'


def _normalize_data_types(df: pd.DataFrame) -> pd.DataFrame:
    """Normalize common data types in the DataFrame."""
    normalized_df = df.copy()
    
    for column in normalized_df.columns:
        # Try to convert date-like columns
        if any(keyword in column.lower() for keyword in ['date', 'time', 'created', 'updated']):
            try:
                normalized_df[column] = pd.to_datetime(normalized_df[column], errors='coerce')
            except Exception:
                pass
        
        # Try to convert numeric columns
        elif any(keyword in column.lower() for keyword in ['amount', 'price', 'cost', 'miles', 'stops']):
            try:
                normalized_df[column] = pd.to_numeric(normalized_df[column], errors='coerce')
            except Exception:
                pass
    
    return normalized_df


def _is_compatible_type(actual_type: str, expected_type: str) -> bool:
    """Check if actual data type is compatible with expected type."""
    type_mappings = {
        'string': ['object', 'string'],
        'integer': ['int64', 'int32', 'int16', 'int8'],
        'float': ['float64', 'float32', 'float16'],
        'datetime': ['datetime64[ns]', 'datetime64'],
        'boolean': ['bool']
    }
    
    expected_variants = type_mappings.get(expected_type.lower(), [expected_type])
    return any(variant in actual_type.lower() for variant in expected_variants)


def _generate_job_ids(count: int) -> List[str]:
    """Generate unique job IDs for rows that don't have them."""
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    return [f"job_{timestamp}_{i:06d}" for i in range(count)]


# Predefined schemas for common Excel formats
DISPATCH_SCHEMA = ExcelSchema(
    required_columns=['driver_name', 'route_id', 'planned_miles', 'planned_stops'],
    optional_columns=['actual_miles', 'actual_stops', 'date', 'notes'],
    column_types={
        'planned_miles': 'float',
        'planned_stops': 'integer',
        'actual_miles': 'float',
        'actual_stops': 'integer'
    },
    date_columns=['date'],
    numeric_columns=['planned_miles', 'planned_stops', 'actual_miles', 'actual_stops']
)

SAMSARA_SCHEMA = ExcelSchema(
    required_columns=['driver_id', 'trip_date', 'total_miles', 'idle_time'],
    optional_columns=['stops_count', 'fuel_used', 'vehicle_id'],
    column_types={
        'total_miles': 'float',
        'idle_time': 'float',
        'stops_count': 'integer',
        'fuel_used': 'float'
    },
    date_columns=['trip_date'],
    numeric_columns=['total_miles', 'idle_time', 'stops_count', 'fuel_used']
)
