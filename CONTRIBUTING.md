# Contributing to PepWorkday Pipeline

Thank you for your interest in contributing to the PepWorkday Pipeline for PEPMove! This document provides guidelines and information for contributors.

## 🏢 PEPMove Context

This pipeline is specifically configured for PEPMove operations with the following Samsara integration:

- **Organization ID**: 5005620
- **Group ID**: 129031
- **API Token**: [Set via SAMSARA_API_TOKEN environment variable]

When developing features, ensure they work within this PEPMove context and respect the organization's operational requirements.

## 🚀 Getting Started

### Prerequisites

- Python 3.9+
- Git
- Access to PEPMove's Google Sheets and Slack workspace (for testing integrations)
- Basic understanding of Samsara API structure

### Development Setup

1. **Fork and clone the repository:**
   ```bash
   git clone https://github.com/your-username/pepworkday.git
   cd pepworkday/pepworkday-pipeline
   ```

2. **Create a virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install development dependencies:**
   ```bash
   pip install -r requirements.txt
   pip install -e .
   ```

4. **Set up pre-commit hooks:**
   ```bash
   pre-commit install
   ```

5. **Copy and configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env with your development configuration
   ```

## 🧪 Testing

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=pepworkday_pipeline --cov-report=html

# Run specific test categories
pytest tests/test_samsara_api.py  # Samsara API tests
pytest tests/test_excel_ingestion.py  # Excel processing tests

# Run PEPMove-specific tests
pytest tests/test_samsara_api.py::TestPEPMoveSpecificEndpoints
```

### Test Guidelines

- **Mock External APIs**: Always mock Samsara API calls in tests
- **PEPMove Context**: Include PEPMove organization and group IDs in test data
- **Data Validation**: Test both successful and error scenarios
- **Integration Tests**: Test the full pipeline flow with sample data

### Writing New Tests

When adding new features, include tests that cover:

1. **Unit Tests**: Individual function/method behavior
2. **Integration Tests**: Component interaction
3. **PEPMove-Specific Tests**: Organization/group context validation
4. **Error Handling**: Exception scenarios and edge cases

## 🔧 Code Quality

### Code Style

We use several tools to maintain code quality:

```bash
# Format code
black pepworkday-pipeline/

# Sort imports
isort pepworkday-pipeline/

# Lint code
flake8 pepworkday-pipeline/

# Type checking
mypy pepworkday-pipeline/
```

### Code Standards

- **Type Hints**: Use type hints for all function parameters and return values
- **Docstrings**: Include comprehensive docstrings for all public functions
- **Error Handling**: Implement proper exception handling with meaningful messages
- **Logging**: Use structured logging with appropriate levels
- **PEPMove Context**: Always include organization/group context in API calls

### Example Code Structure

```python
def pepmove_specific_function(
    vehicle_ids: List[str],
    start_date: datetime,
    end_date: datetime
) -> pd.DataFrame:
    """
    Process PEPMove vehicle data for the specified date range.
    
    Args:
        vehicle_ids: List of PEPMove vehicle IDs
        start_date: Start date for data processing
        end_date: End date for data processing
        
    Returns:
        DataFrame with processed vehicle data including PEPMove context
        
    Raises:
        SamsaraAPIError: If API request fails
        ValueError: If date range is invalid
    """
    logger.info(f"Processing PEPMove vehicle data for {len(vehicle_ids)} vehicles")
    
    try:
        # Implementation with proper error handling
        result_df = process_data(vehicle_ids, start_date, end_date)
        
        # Add PEPMove context
        result_df['organization_id'] = '5005620'
        result_df['group_id'] = '129031'
        
        return result_df
        
    except Exception as e:
        logger.error(f"Failed to process PEPMove vehicle data: {str(e)}")
        raise
```

## 📝 Documentation

### Updating Documentation

- **README.md**: Update usage examples and feature descriptions
- **Docstrings**: Keep inline documentation current
- **API Documentation**: Document new Samsara API endpoints
- **Configuration**: Update environment variable documentation

### Documentation Standards

- **Clear Examples**: Provide working code examples
- **PEPMove Context**: Include organization/group information where relevant
- **Error Scenarios**: Document common error conditions and solutions
- **Configuration**: Explain all configuration options

## 🔄 Development Workflow

### Branch Naming

Use descriptive branch names:
- `feature/pepmove-route-optimization`
- `bugfix/samsara-api-timeout`
- `enhancement/fleet-summary-metrics`

### Commit Messages

Follow conventional commit format:
```
feat(samsara): add PEPMove fleet summary endpoint
fix(excel): handle missing columns in dispatch data
docs(readme): update PEPMove configuration examples
test(api): add tests for vehicle location tracking
```

### Pull Request Process

1. **Create Feature Branch**: Branch from `main`
2. **Implement Changes**: Follow code standards and include tests
3. **Update Documentation**: Update relevant documentation
4. **Run Tests**: Ensure all tests pass
5. **Submit PR**: Include clear description and link to issues

### PR Checklist

- [ ] Tests pass locally
- [ ] Code follows style guidelines
- [ ] Documentation updated
- [ ] PEPMove context preserved
- [ ] No sensitive data exposed
- [ ] Backward compatibility maintained

## 🐛 Bug Reports

When reporting bugs, include:

1. **Environment**: Python version, OS, dependencies
2. **PEPMove Context**: Organization/group IDs if relevant
3. **Steps to Reproduce**: Clear reproduction steps
4. **Expected vs Actual**: What should happen vs what happens
5. **Logs**: Relevant log output (sanitize sensitive data)
6. **Sample Data**: Anonymized sample data if applicable

## 💡 Feature Requests

For new features, provide:

1. **Use Case**: Why is this feature needed for PEPMove?
2. **Requirements**: Detailed functional requirements
3. **Samsara Integration**: How it relates to Samsara API
4. **Impact**: Effect on existing functionality
5. **Examples**: Usage examples or mockups

## 🔒 Security Considerations

### Sensitive Data

- **API Tokens**: Never commit API tokens to version control
- **Credentials**: Use environment variables for all credentials
- **PII**: Sanitize personally identifiable information in logs/tests
- **Organization Data**: Respect PEPMove's data privacy requirements

### Best Practices

- Use `.env` files for local development
- Implement proper input validation
- Log security-relevant events
- Follow principle of least privilege

## 📞 Getting Help

### Resources

- **Samsara API Documentation**: https://developers.samsara.com/
- **Google Sheets API**: https://developers.google.com/sheets/api
- **Slack API**: https://api.slack.com/
- **Pandas Documentation**: https://pandas.pydata.org/docs/

### Contact

- **Issues**: Use GitHub Issues for bug reports and feature requests
- **Discussions**: Use GitHub Discussions for questions and ideas
- **Security**: Contact maintainers directly for security issues

## 🎯 Contribution Areas

We welcome contributions in these areas:

### High Priority
- **Performance Optimization**: Improve API request efficiency
- **Error Handling**: Enhanced error recovery and reporting
- **Data Validation**: More robust data quality checks
- **Monitoring**: Better observability and alerting

### Medium Priority
- **New Samsara Endpoints**: Additional API integrations
- **Data Enrichment**: New calculated metrics and insights
- **Reporting**: Enhanced summary and analytics features
- **Documentation**: Improved examples and guides

### Low Priority
- **UI/UX**: Command-line interface improvements
- **Integrations**: Additional third-party service integrations
- **Automation**: Enhanced CI/CD and deployment features

Thank you for contributing to the PepWorkday Pipeline! Your efforts help improve PEPMove's operational efficiency and data insights.
