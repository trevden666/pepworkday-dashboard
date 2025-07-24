/**
 * Multi-Workbook Google Sheets API Route
 * 
 * Fetches data from multiple Google Sheets workbooks using batchGet
 * for improved performance and reduced API calls.
 * 
 * Query Parameters:
 * - workbook: Index (0-3) for specific workbook, or "all" for all workbooks
 * 
 * @module pages/api/fetchSheets
 * @author PEP Automation Team
 * @version 1.0.0
 */

import { google } from 'googleapis';
import { withLogging, createApiLogger } from '../../lib/logger';
import { validateInput, sanitizeHTML } from '../../lib/security';
import { getGCPCredentials } from '../../utils/gcpCredentials';
import config from '../../config.json';

/**
 * Validate workbook configuration
 * 
 * @param {Array} config - Workbook configuration array
 * @returns {boolean} True if valid
 */
function validateConfig(config) {
  if (!Array.isArray(config)) return false;
  
  return config.every(workbook => 
    workbook.id && 
    workbook.name && 
    Array.isArray(workbook.sheets) &&
    workbook.sheets.every(sheet => sheet.name && sheet.range)
  );
}

/**
 * Fetch data from a single workbook using batchGet
 * 
 * @param {Object} sheets - Google Sheets API client
 * @param {Object} workbook - Workbook configuration
 * @param {Object} logger - Logger instance
 * @returns {Object} Workbook data keyed by sheet name
 */
async function fetchWorkbookData(sheets, workbook, logger) {
  try {
    // Build ranges array for batchGet
    const ranges = workbook.sheets.map(sheet => `${sheet.name}!${sheet.range}`);
    
    logger.info('Fetching workbook data', {
      workbookId: workbook.id,
      workbookName: workbook.name,
      ranges: ranges.length
    });
    
    // Use batchGet for efficient multi-range fetching
    const { data } = await sheets.spreadsheets.values.batchGet({
      spreadsheetId: workbook.id,
      ranges,
      valueRenderOption: 'FORMATTED_VALUE',
      dateTimeRenderOption: 'FORMATTED_STRING'
    });
    
    // Transform response into sheet-keyed object
    const result = {};
    data.valueRanges.forEach((valueRange, index) => {
      const sheet = workbook.sheets[index];
      const sheetData = valueRange.values || [];
      
      // Sanitize data for security
      const sanitizedData = sheetData.map(row => 
        row.map(cell => sanitizeHTML(String(cell || '')))
      );
      
      result[sheet.name] = {
        data: sanitizedData,
        range: sheet.range,
        description: sheet.description,
        lastUpdated: new Date().toISOString(),
        rowCount: sanitizedData.length
      };
    });
    
    logger.info('Successfully fetched workbook data', {
      workbookId: workbook.id,
      sheetsCount: Object.keys(result).length,
      totalRows: Object.values(result).reduce((sum, sheet) => sum + sheet.rowCount, 0)
    });
    
    return result;
    
  } catch (error) {
    logger.error('Failed to fetch workbook data', {
      workbookId: workbook.id,
      workbookName: workbook.name,
      error: error.message
    });
    throw error;
  }
}

/**
 * Main API handler
 * 
 * @param {Object} req - Next.js request object
 * @param {Object} res - Next.js response object
 */
async function handler(req, res) {
  const logger = createApiLogger(req, 'fetchSheets');
  
  // Only allow GET requests
  if (req.method !== 'GET') {
    logger.warn('Method not allowed', { method: req.method });
    return res.status(405).json({ 
      error: 'Method not allowed',
      allowedMethods: ['GET']
    });
  }
  
  try {
    // Validate configuration
    if (!validateConfig(config)) {
      logger.error('Invalid workbook configuration');
      return res.status(500).json({
        error: 'Invalid workbook configuration',
        details: 'config.json format is invalid'
      });
    }
    
    // Validate and sanitize query parameters
    const workbookParam = validateInput(req.query.workbook || 'all', {
      type: 'string',
      maxLength: 10,
      allowedValues: ['all', '0', '1', '2', '3']
    });
    
    if (!workbookParam.isValid) {
      logger.warn('Invalid workbook parameter', { 
        workbook: req.query.workbook,
        error: workbookParam.error 
      });
      return res.status(400).json({
        error: 'Invalid workbook parameter',
        details: 'Must be "all" or index 0-3',
        validValues: ['all', '0', '1', '2', '3']
      });
    }
    
    // Get GCP credentials
    const credentials = await getGCPCredentials();
    if (!credentials) {
      logger.error('GCP credentials not available');
      return res.status(500).json({
        error: 'Authentication failed',
        details: 'GCP credentials not configured'
      });
    }
    
    // Initialize Google Sheets API
    const auth = new google.auth.GoogleAuth({
      credentials,
      scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly']
    });
    
    const sheets = google.sheets({ version: 'v4', auth });
    
    // Determine which workbooks to fetch
    const workbookValue = workbookParam.value;
    let workbooksToFetch = [];
    
    if (workbookValue === 'all') {
      workbooksToFetch = config;
      logger.info('Fetching all workbooks', { count: config.length });
    } else {
      const index = parseInt(workbookValue);
      if (index >= 0 && index < config.length) {
        workbooksToFetch = [config[index]];
        logger.info('Fetching single workbook', { 
          index, 
          workbookName: config[index].name 
        });
      } else {
        logger.warn('Workbook index out of range', { index, maxIndex: config.length - 1 });
        return res.status(400).json({
          error: 'Workbook index out of range',
          details: `Index must be 0-${config.length - 1}`
        });
      }
    }
    
    // Fetch data from selected workbooks
    const results = {};
    const fetchPromises = workbooksToFetch.map(async (workbook, index) => {
      try {
        const workbookData = await fetchWorkbookData(sheets, workbook, logger);
        const key = workbookValue === 'all' ? `workbook_${index}` : 'workbook';
        results[key] = {
          id: workbook.id,
          name: workbook.name,
          description: workbook.description,
          sheets: workbookData,
          fetchedAt: new Date().toISOString()
        };
      } catch (error) {
        logger.error('Failed to fetch workbook', {
          workbookId: workbook.id,
          workbookName: workbook.name,
          error: error.message
        });
        // Include error in results rather than failing entire request
        const key = workbookValue === 'all' ? `workbook_${index}` : 'workbook';
        results[key] = {
          id: workbook.id,
          name: workbook.name,
          error: error.message,
          fetchedAt: new Date().toISOString()
        };
      }
    });
    
    // Wait for all fetches to complete
    await Promise.all(fetchPromises);
    
    // Return successful response
    const response = {
      success: true,
      workbooksRequested: workbookValue,
      workbooksCount: workbooksToFetch.length,
      data: results,
      fetchedAt: new Date().toISOString()
    };
    
    logger.info('Successfully completed multi-workbook fetch', {
      workbooksRequested: workbookValue,
      workbooksCount: workbooksToFetch.length,
      successCount: Object.keys(results).filter(key => !results[key].error).length
    });
    
    // Set cache headers for performance
    res.setHeader('Cache-Control', 's-maxage=300, stale-while-revalidate=60');
    res.status(200).json(response);
    
  } catch (error) {
    logger.error('API request failed', error);
    res.status(500).json({
      error: 'Internal server error',
      details: process.env.NODE_ENV === 'development' ? error.message : 'Please try again later'
    });
  }
}

export default withLogging(handler, 'fetchSheets');
