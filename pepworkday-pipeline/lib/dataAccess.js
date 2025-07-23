/**
 * Data Access Layer
 * 
 * Secure data access layer that provides:
 * - Input sanitization and validation
 * - Rate limiting and access control
 * - Structured error handling
 * - Audit logging
 * - Data transformation and caching
 * 
 * @module lib/dataAccess
 * @author PEP Automation Team
 * @version 1.0.0
 */

import { google } from 'googleapis';
import DOMPurify from 'isomorphic-dompurify';
import { getGCPCredentials, validateGCPEnvironment } from '../utils/gcpCredentials.js';
import { PerformanceTimer } from './logger.js';

/**
 * Input validation schemas
 */
const VALIDATION_SCHEMAS = {
  spreadsheetId: {
    pattern: /^[a-zA-Z0-9-_]{44}$/,
    maxLength: 44,
    minLength: 44,
  },
  range: {
    pattern: /^[A-Z]+[0-9]+:[A-Z]+[0-9]+$/,
    maxLength: 50,
  },
  sheetName: {
    pattern: /^[a-zA-Z0-9_\s-]+$/,
    maxLength: 100,
  },
};

/**
 * Rate limiting configuration
 */
const RATE_LIMITS = {
  perMinute: 60,
  perHour: 1000,
  perDay: 10000,
};

/**
 * Cache configuration
 */
const CACHE_TTL = {
  summary: 300, // 5 minutes
  metadata: 3600, // 1 hour
};

/**
 * In-memory cache (in production, use Redis or similar)
 */
const cache = new Map();

/**
 * Rate limiting store (in production, use Redis or similar)
 */
const rateLimitStore = new Map();

/**
 * Sanitize and validate input
 * 
 * @param {string} input - Input to sanitize
 * @param {string} type - Validation type
 * @returns {string} Sanitized input
 * @throws {Error} If validation fails
 */
function sanitizeInput(input, type) {
  if (!input || typeof input !== 'string') {
    throw new Error(`Invalid input: ${type} must be a non-empty string`);
  }
  
  // Sanitize HTML/XSS
  const sanitized = DOMPurify.sanitize(input.trim());
  
  // Validate against schema
  const schema = VALIDATION_SCHEMAS[type];
  if (schema) {
    if (sanitized.length > schema.maxLength) {
      throw new Error(`Invalid ${type}: exceeds maximum length of ${schema.maxLength}`);
    }
    
    if (schema.minLength && sanitized.length < schema.minLength) {
      throw new Error(`Invalid ${type}: below minimum length of ${schema.minLength}`);
    }
    
    if (schema.pattern && !schema.pattern.test(sanitized)) {
      throw new Error(`Invalid ${type}: does not match required pattern`);
    }
  }
  
  return sanitized;
}

/**
 * Check rate limits for a client
 * 
 * @param {string} clientId - Client identifier (IP, user ID, etc.)
 * @param {Object} logger - Logger instance
 * @returns {boolean} True if within limits
 */
function checkRateLimit(clientId, logger) {
  const now = Date.now();
  const clientLimits = rateLimitStore.get(clientId) || {
    minute: { count: 0, resetTime: now + 60000 },
    hour: { count: 0, resetTime: now + 3600000 },
    day: { count: 0, resetTime: now + 86400000 },
  };
  
  // Reset counters if time windows have passed
  if (now > clientLimits.minute.resetTime) {
    clientLimits.minute = { count: 0, resetTime: now + 60000 };
  }
  if (now > clientLimits.hour.resetTime) {
    clientLimits.hour = { count: 0, resetTime: now + 3600000 };
  }
  if (now > clientLimits.day.resetTime) {
    clientLimits.day = { count: 0, resetTime: now + 86400000 };
  }
  
  // Check limits
  if (clientLimits.minute.count >= RATE_LIMITS.perMinute) {
    logger.warn('Rate limit exceeded', { clientId, limit: 'perMinute' });
    return false;
  }
  if (clientLimits.hour.count >= RATE_LIMITS.perHour) {
    logger.warn('Rate limit exceeded', { clientId, limit: 'perHour' });
    return false;
  }
  if (clientLimits.day.count >= RATE_LIMITS.perDay) {
    logger.warn('Rate limit exceeded', { clientId, limit: 'perDay' });
    return false;
  }
  
  // Increment counters
  clientLimits.minute.count++;
  clientLimits.hour.count++;
  clientLimits.day.count++;
  
  rateLimitStore.set(clientId, clientLimits);
  return true;
}

/**
 * Get cached data
 * 
 * @param {string} key - Cache key
 * @returns {Object|null} Cached data or null
 */
function getCachedData(key) {
  const cached = cache.get(key);
  if (cached && cached.expiresAt > Date.now()) {
    return cached.data;
  }
  
  // Remove expired cache entry
  if (cached) {
    cache.delete(key);
  }
  
  return null;
}

/**
 * Set cached data
 * 
 * @param {string} key - Cache key
 * @param {Object} data - Data to cache
 * @param {number} ttl - Time to live in seconds
 */
function setCachedData(key, data, ttl) {
  cache.set(key, {
    data,
    expiresAt: Date.now() + (ttl * 1000),
  });
}

/**
 * Create authenticated Google Sheets client
 * 
 * @param {Object} logger - Logger instance
 * @returns {Promise<Object>} Authenticated Google Sheets API client
 */
async function createSheetsClient(logger) {
  const timer = new PerformanceTimer('sheets_auth', logger);
  
  try {
    validateGCPEnvironment();
    timer.mark('environment_validated');
    
    const gcpConfig = getGCPCredentials();
    timer.mark('credentials_retrieved');
    
    let auth;
    
    if (gcpConfig.credentials) {
      auth = new google.auth.JWT(
        gcpConfig.credentials.client_email,
        null,
        gcpConfig.credentials.private_key,
        ['https://www.googleapis.com/auth/spreadsheets.readonly']
      );
      
      await auth.authorize();
      timer.mark('jwt_authorized');
    } else {
      auth = new google.auth.GoogleAuth({
        scopes: ['https://www.googleapis.com/auth/spreadsheets.readonly']
      });
      timer.mark('adc_configured');
    }
    
    const sheets = google.sheets({ version: 'v4', auth });
    
    timer.end({ auth_type: gcpConfig.credentials ? 'service_account' : 'adc' });
    logger.info('Google Sheets client authenticated');
    
    return sheets;
    
  } catch (error) {
    timer.end({ success: false, error: error.message });
    logger.error('Failed to create Google Sheets client', error);
    throw new Error(`Authentication failed: ${error.message}`);
  }
}

/**
 * Secure data access class
 */
export class SecureDataAccess {
  constructor(logger) {
    this.logger = logger;
    this.sheetsClient = null;
  }
  
  /**
   * Initialize the data access layer
   */
  async initialize() {
    if (!this.sheetsClient) {
      this.sheetsClient = await createSheetsClient(this.logger);
    }
  }
  
  /**
   * Fetch summary data with security controls
   * 
   * @param {string} spreadsheetId - Spreadsheet ID
   * @param {string} range - Data range
   * @param {string} clientId - Client identifier for rate limiting
   * @returns {Promise<Object>} Sanitized summary data
   */
  async fetchSummaryData(spreadsheetId, range, clientId) {
    const timer = new PerformanceTimer('secure_fetch_summary', this.logger);
    
    try {
      // Input validation and sanitization
      const sanitizedSpreadsheetId = sanitizeInput(spreadsheetId, 'spreadsheetId');
      const sanitizedRange = sanitizeInput(range, 'range');
      
      timer.mark('input_validated');
      
      // Rate limiting
      if (!checkRateLimit(clientId, this.logger)) {
        throw new Error('Rate limit exceeded. Please try again later.');
      }
      
      timer.mark('rate_limit_checked');
      
      // Check cache first
      const cacheKey = `summary:${sanitizedSpreadsheetId}:${sanitizedRange}`;
      const cachedData = getCachedData(cacheKey);
      
      if (cachedData) {
        timer.end({ cache_hit: true });
        this.logger.info('Returning cached summary data', { cacheKey });
        return cachedData;
      }
      
      timer.mark('cache_checked');
      
      // Initialize client if needed
      await this.initialize();
      
      // Fetch data from Google Sheets
      this.logger.info('Fetching data from Google Sheets', { 
        spreadsheetId: sanitizedSpreadsheetId,
        range: sanitizedRange 
      });
      
      const response = await this.sheetsClient.spreadsheets.values.get({
        spreadsheetId: sanitizedSpreadsheetId,
        range: sanitizedRange,
        valueRenderOption: 'UNFORMATTED_VALUE',
        dateTimeRenderOption: 'FORMATTED_STRING'
      });
      
      timer.mark('sheets_api_response');
      
      const rows = response.data.values || [];
      
      // Transform and sanitize data
      const summaryData = this.transformSummaryData(rows);
      
      timer.mark('data_transformed');
      
      // Cache the result
      setCachedData(cacheKey, summaryData, CACHE_TTL.summary);
      
      timer.end({ 
        cache_hit: false,
        rowCount: rows.length,
        dataRows: summaryData.length
      });
      
      this.logger.info('Summary data fetched successfully', {
        rowCount: rows.length,
        dataRows: summaryData.length,
        cached: true
      });
      
      return summaryData;
      
    } catch (error) {
      timer.end({ success: false, error: error.message });
      this.logger.error('Failed to fetch summary data', error);
      throw error;
    }
  }
  
  /**
   * Transform and sanitize raw sheet data
   * 
   * @param {Array} rows - Raw sheet rows
   * @returns {Array} Transformed and sanitized data
   */
  transformSummaryData(rows) {
    if (!rows || rows.length === 0) {
      return [];
    }
    
    // First row contains headers
    const headers = rows[0].map(header => 
      DOMPurify.sanitize(String(header || '').trim())
    );
    
    const dataRows = rows.slice(1);
    
    // Convert to array of objects with sanitized data
    return dataRows.map((row, index) => {
      const rowData = { 
        _rowIndex: index + 2, // +2 for header and 1-based indexing
        _sanitized: true,
        _timestamp: new Date().toISOString()
      };
      
      headers.forEach((header, colIndex) => {
        const value = row[colIndex];
        const sanitizedHeader = header || `Column_${colIndex + 1}`;
        
        // Sanitize cell values
        if (value !== null && value !== undefined) {
          if (typeof value === 'string') {
            rowData[sanitizedHeader] = DOMPurify.sanitize(value);
          } else {
            rowData[sanitizedHeader] = value;
          }
        } else {
          rowData[sanitizedHeader] = null;
        }
      });
      
      return rowData;
    });
  }
  
  /**
   * Get cache statistics
   * 
   * @returns {Object} Cache statistics
   */
  getCacheStats() {
    return {
      size: cache.size,
      entries: Array.from(cache.keys()),
    };
  }
  
  /**
   * Clear cache
   */
  clearCache() {
    cache.clear();
    this.logger.info('Cache cleared');
  }
}
