/**
 * Next.js API Route - Google Sheets Summary Data
 * 
 * This API route fetches summary data from Google Sheets using the unified
 * GCP credentials helper and googleapis JWT authentication.
 * 
 * Endpoint: GET /api/summary
 * Returns: JSON array of summary data from Summary!A1:Z100 range
 * 
 * Environment Variables Required:
 * - SHEET_ID: Google Sheets spreadsheet ID
 * - GCP_SERVICE_ACCOUNT_EMAIL: Service account email (Vercel)
 * - GCP_PRIVATE_KEY: Service account private key (Vercel)
 * - GCP_PROJECT_ID: GCP project ID (Vercel)
 * 
 * @module api/summary
 * @author PEP Automation Team
 * @version 1.0.0
 */

import { withLogging } from '../../lib/logger.js';
import { SecureDataAccess } from '../../lib/dataAccess.js';
import { withSecurity, getClientIP } from '../../lib/security.js';

/**
 * API configuration
 */
const SUMMARY_RANGE = 'Summary!A1:Z100';

// Removed - functionality moved to SecureDataAccess class

/**
 * Next.js API route handler with security and logging
 *
 * @param {Object} req - Next.js request object
 * @param {Object} res - Next.js response object
 */
async function handler(req, res) {
  const logger = req.logger; // Injected by withLogging wrapper
  // Only allow GET requests
  if (req.method !== 'GET') {
    logger.warn('Method not allowed', { method: req.method });
    return res.status(405).json({
      error: 'Method not allowed',
      message: 'This endpoint only supports GET requests'
    });
  }

  try {
    logger.info('Processing secure summary data request');

    // Validate required environment variables
    const spreadsheetId = process.env.SHEET_ID;
    if (!spreadsheetId) {
      throw new Error('SHEET_ID environment variable is required');
    }

    // Get client IP for rate limiting
    const clientIP = getClientIP(req);

    logger.info('Request details', {
      spreadsheetId: spreadsheetId.substring(0, 10) + '...', // Partial ID for security
      clientIP,
      userAgent: req.headers['user-agent']?.substring(0, 100)
    });

    // Create secure data access instance
    const dataAccess = new SecureDataAccess(logger);

    // Fetch summary data with security controls
    const summaryData = await dataAccess.fetchSummaryData(
      spreadsheetId,
      SUMMARY_RANGE,
      clientIP
    );

    // Return successful response
    const response = {
      success: true,
      data: summaryData,
      metadata: {
        range: SUMMARY_RANGE,
        rowCount: summaryData.length,
        timestamp: new Date().toISOString(),
        spreadsheetId: spreadsheetId,
        cached: true, // Data access layer handles caching
        sanitized: true // Data is sanitized by SecureDataAccess
      }
    };

    logger.info('Secure summary data request completed', {
      rowCount: summaryData.length,
      responseSize: JSON.stringify(response).length,
      clientIP
    });

    res.status(200).json(response);

  } catch (error) {
    logger.error('Secure summary API error', error);

    // Return sanitized error response
    const errorMessage = error.message.includes('Rate limit')
      ? error.message
      : 'An error occurred while fetching data';

    res.status(error.message.includes('Rate limit') ? 429 : 500).json({
      success: false,
      error: errorMessage,
      timestamp: new Date().toISOString()
    });
  }
}

// Export the handler wrapped with security and logging
export default withSecurity(withLogging(handler, 'summary'));
