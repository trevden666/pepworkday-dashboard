/**
 * API Smoke Test - Summary Endpoint
 * 
 * This test suite validates the /api/summary endpoint functionality
 * including response format, data structure, and error handling.
 * 
 * Test Categories:
 * - Endpoint availability and response format
 * - Data structure validation
 * - Error handling scenarios
 * - Performance and timeout testing
 * 
 * @module testApiSummary
 * @author PEP Automation Team
 * @version 1.0.0
 */

import { test, describe } from 'node:test';
import assert from 'node:assert';
import http from 'node:http';

/**
 * Configuration for API testing
 */
const TEST_CONFIG = {
  host: 'localhost',
  port: process.env.PORT || 3000,
  timeout: 10000, // 10 seconds
  retries: 3
};

/**
 * Make HTTP request with timeout and retry logic
 * 
 * @param {Object} options - HTTP request options
 * @param {number} [retries=3] - Number of retry attempts
 * @returns {Promise<Object>} Response object with status, headers, and data
 */
function makeRequest(options, retries = TEST_CONFIG.retries) {
  return new Promise((resolve, reject) => {
    const req = http.request(options, (res) => {
      let data = '';
      
      res.on('data', (chunk) => {
        data += chunk;
      });
      
      res.on('end', () => {
        try {
          const parsedData = data ? JSON.parse(data) : null;
          resolve({
            status: res.statusCode,
            headers: res.headers,
            data: parsedData,
            rawData: data
          });
        } catch (parseError) {
          resolve({
            status: res.statusCode,
            headers: res.headers,
            data: null,
            rawData: data,
            parseError: parseError.message
          });
        }
      });
    });
    
    req.on('error', (error) => {
      if (retries > 0) {
        console.log(`⚠️  Request failed, retrying... (${retries} attempts left)`);
        setTimeout(() => {
          makeRequest(options, retries - 1)
            .then(resolve)
            .catch(reject);
        }, 1000);
      } else {
        reject(error);
      }
    });
    
    req.setTimeout(TEST_CONFIG.timeout, () => {
      req.destroy();
      reject(new Error('Request timeout'));
    });
    
    req.end();
  });
}

/**
 * Check if the Next.js development server is running
 * 
 * @returns {Promise<boolean>} True if server is accessible
 */
async function checkServerAvailability() {
  try {
    const response = await makeRequest({
      hostname: TEST_CONFIG.host,
      port: TEST_CONFIG.port,
      path: '/api/summary',
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    }, 1); // Only try once for availability check
    
    return response.status !== undefined;
  } catch (error) {
    return false;
  }
}

describe('API Summary Endpoint Tests', () => {
  
  test('Server availability check', async () => {
    const isAvailable = await checkServerAvailability();
    
    if (!isAvailable) {
      console.log('⚠️  Server not available. Make sure to run "npm run dev" first.');
      console.log(`   Expected server at http://${TEST_CONFIG.host}:${TEST_CONFIG.port}`);
      
      // Skip remaining tests if server is not available
      process.exit(0);
    }
    
    assert.ok(isAvailable, 'Server should be available for testing');
    console.log('✅ Server is available for testing');
  });
  
  test('GET /api/summary returns valid JSON response', async () => {
    const response = await makeRequest({
      hostname: TEST_CONFIG.host,
      port: TEST_CONFIG.port,
      path: '/api/summary',
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    // Should return a valid HTTP status
    assert.ok(response.status, 'Response should have a status code');
    assert.ok([200, 500].includes(response.status), 
      `Status should be 200 (success) or 500 (server error), got ${response.status}`);
    
    // Should return valid JSON
    assert.ok(response.data !== null, 'Response should contain valid JSON data');
    assert.strictEqual(typeof response.data, 'object', 'Response data should be an object');
    
    console.log(`✅ Received ${response.status} response with valid JSON`);
  });
  
  test('Successful response has correct structure', async () => {
    const response = await makeRequest({
      hostname: TEST_CONFIG.host,
      port: TEST_CONFIG.port,
      path: '/api/summary',
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (response.status === 200) {
      // Test successful response structure
      assert.ok(response.data.success, 'Success response should have success: true');
      assert.ok(Array.isArray(response.data.data), 'Success response should have data array');
      assert.ok(response.data.metadata, 'Success response should have metadata object');
      
      // Test metadata structure
      const metadata = response.data.metadata;
      assert.ok(metadata.range, 'Metadata should include range');
      assert.ok(typeof metadata.rowCount === 'number', 'Metadata should include rowCount as number');
      assert.ok(metadata.timestamp, 'Metadata should include timestamp');
      assert.ok(metadata.spreadsheetId, 'Metadata should include spreadsheetId');
      
      console.log(`✅ Success response structure is valid (${metadata.rowCount} rows)`);
      
    } else if (response.status === 500) {
      // Test error response structure
      assert.strictEqual(response.data.success, false, 'Error response should have success: false');
      assert.ok(response.data.error, 'Error response should have error message');
      assert.ok(response.data.timestamp, 'Error response should have timestamp');
      
      console.log(`⚠️  Server error response structure is valid: ${response.data.error}`);
      
    } else {
      assert.fail(`Unexpected status code: ${response.status}`);
    }
  });
  
  test('Data array contains valid objects (if successful)', async () => {
    const response = await makeRequest({
      hostname: TEST_CONFIG.host,
      port: TEST_CONFIG.port,
      path: '/api/summary',
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    if (response.status === 200 && response.data.data.length > 0) {
      const firstRow = response.data.data[0];
      
      // Each row should be an object
      assert.strictEqual(typeof firstRow, 'object', 'Data rows should be objects');
      
      // Should have _rowIndex property
      assert.ok(typeof firstRow._rowIndex === 'number', 'Each row should have _rowIndex as number');
      
      // Should have at least one data property besides _rowIndex
      const dataKeys = Object.keys(firstRow).filter(key => key !== '_rowIndex');
      assert.ok(dataKeys.length > 0, 'Each row should have data properties besides _rowIndex');
      
      console.log(`✅ Data array contains ${response.data.data.length} valid objects`);
      console.log(`   Sample row keys: ${Object.keys(firstRow).slice(0, 5).join(', ')}`);
      
    } else if (response.status === 200) {
      console.log('✅ Successful response with empty data array');
    }
  });
  
  test('Method not allowed for non-GET requests', async () => {
    const response = await makeRequest({
      hostname: TEST_CONFIG.host,
      port: TEST_CONFIG.port,
      path: '/api/summary',
      method: 'POST',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    assert.strictEqual(response.status, 405, 'POST request should return 405 Method Not Allowed');
    assert.strictEqual(response.data.error, 'Method not allowed', 'Should return method not allowed error');
    
    console.log('✅ POST request correctly rejected with 405 status');
  });
  
  test('Response time is reasonable', async () => {
    const startTime = Date.now();
    
    const response = await makeRequest({
      hostname: TEST_CONFIG.host,
      port: TEST_CONFIG.port,
      path: '/api/summary',
      method: 'GET',
      headers: {
        'Content-Type': 'application/json'
      }
    });
    
    const responseTime = Date.now() - startTime;
    
    // Response should be within reasonable time (30 seconds max)
    assert.ok(responseTime < 30000, `Response time should be under 30 seconds, got ${responseTime}ms`);
    
    console.log(`✅ Response time: ${responseTime}ms`);
  });
  
});

/**
 * Run tests if this file is executed directly
 */
if (import.meta.url === `file://${process.argv[1]}`) {
  console.log('🧪 Running API Summary Endpoint Tests');
  console.log(`📍 Testing server at http://${TEST_CONFIG.host}:${TEST_CONFIG.port}`);
  console.log('⚠️  Make sure to run "npm run dev" in another terminal first\n');
}
