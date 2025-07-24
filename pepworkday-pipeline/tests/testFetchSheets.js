/**
 * Test Suite for Multi-Workbook Fetch Sheets API
 * 
 * Tests the /api/fetchSheets endpoint with different workbook configurations
 * and validates the batch fetch functionality.
 * 
 * @module tests/testFetchSheets
 * @author PEP Automation Team
 * @version 1.0.0
 */

const { test } = require('node:test');
const assert = require('node:assert');

// Test configuration
const BASE_URL = process.env.TEST_BASE_URL || 'http://localhost:3000';
const API_ENDPOINT = `${BASE_URL}/api/fetchSheets`;

/**
 * Helper function to make API requests
 * 
 * @param {string} workbook - Workbook parameter
 * @returns {Promise<Object>} API response
 */
async function fetchSheetsAPI(workbook = 'all') {
  const url = `${API_ENDPOINT}?workbook=${workbook}`;
  console.log(`🔍 Testing: ${url}`);
  
  const response = await fetch(url);
  const data = await response.json();
  
  return {
    status: response.status,
    ok: response.ok,
    data
  };
}

/**
 * Test: Fetch single workbook (index 0)
 */
test('Fetch single workbook by index', async () => {
  console.log('📋 Testing single workbook fetch...');
  
  const result = await fetchSheetsAPI('0');
  
  // Validate response structure
  assert.strictEqual(result.status, 200, 'Should return 200 status');
  assert.strictEqual(result.ok, true, 'Should be successful');
  assert.strictEqual(result.data.success, true, 'Should have success flag');
  
  // Validate workbook data structure
  assert.ok(result.data.data, 'Should have data object');
  assert.ok(result.data.data.workbook, 'Should have workbook key');
  
  const workbook = result.data.data.workbook;
  assert.ok(workbook.id, 'Workbook should have ID');
  assert.ok(workbook.name, 'Workbook should have name');
  assert.ok(workbook.sheets, 'Workbook should have sheets');
  
  // Validate Summary sheet exists
  assert.ok(workbook.sheets.Summary, 'Should have Summary sheet');
  
  const summarySheet = workbook.sheets.Summary;
  assert.ok(Array.isArray(summarySheet.data), 'Summary data should be array');
  assert.ok(summarySheet.range, 'Summary should have range');
  assert.ok(summarySheet.lastUpdated, 'Summary should have lastUpdated');
  assert.ok(typeof summarySheet.rowCount === 'number', 'Summary should have rowCount');
  
  console.log('✅ Single workbook test passed');
  console.log(`   - Workbook: ${workbook.name}`);
  console.log(`   - Sheets: ${Object.keys(workbook.sheets).length}`);
  console.log(`   - Summary rows: ${summarySheet.rowCount}`);
});

/**
 * Test: Fetch all workbooks
 */
test('Fetch all workbooks', async () => {
  console.log('📋 Testing all workbooks fetch...');
  
  const result = await fetchSheetsAPI('all');
  
  // Validate response structure
  assert.strictEqual(result.status, 200, 'Should return 200 status');
  assert.strictEqual(result.ok, true, 'Should be successful');
  assert.strictEqual(result.data.success, true, 'Should have success flag');
  
  // Validate workbooks data structure
  assert.ok(result.data.data, 'Should have data object');
  assert.strictEqual(result.data.workbooksRequested, 'all', 'Should request all workbooks');
  
  // Should have 4 workbooks (workbook_0, workbook_1, workbook_2, workbook_3)
  const workbookKeys = Object.keys(result.data.data);
  const expectedKeys = ['workbook_0', 'workbook_1', 'workbook_2', 'workbook_3'];
  
  assert.strictEqual(workbookKeys.length, 4, 'Should have 4 workbooks');
  
  expectedKeys.forEach(key => {
    assert.ok(result.data.data[key], `Should have ${key}`);
    
    const workbook = result.data.data[key];
    if (!workbook.error) {
      assert.ok(workbook.id, `${key} should have ID`);
      assert.ok(workbook.name, `${key} should have name`);
      assert.ok(workbook.sheets, `${key} should have sheets`);
    }
  });
  
  console.log('✅ All workbooks test passed');
  console.log(`   - Workbooks returned: ${workbookKeys.length}`);
  console.log(`   - Keys: ${workbookKeys.join(', ')}`);
});

/**
 * Test: Invalid workbook parameter
 */
test('Invalid workbook parameter', async () => {
  console.log('📋 Testing invalid workbook parameter...');
  
  const result = await fetchSheetsAPI('invalid');
  
  // Should return 400 error
  assert.strictEqual(result.status, 400, 'Should return 400 status');
  assert.strictEqual(result.ok, false, 'Should not be successful');
  assert.ok(result.data.error, 'Should have error message');
  
  console.log('✅ Invalid parameter test passed');
  console.log(`   - Error: ${result.data.error}`);
});

/**
 * Test: Out of range workbook index
 */
test('Out of range workbook index', async () => {
  console.log('📋 Testing out of range workbook index...');
  
  const result = await fetchSheetsAPI('99');
  
  // Should return 400 error
  assert.strictEqual(result.status, 400, 'Should return 400 status');
  assert.strictEqual(result.ok, false, 'Should not be successful');
  assert.ok(result.data.error, 'Should have error message');
  assert.ok(result.data.error.includes('out of range'), 'Should mention out of range');
  
  console.log('✅ Out of range test passed');
  console.log(`   - Error: ${result.data.error}`);
});

/**
 * Test: Method not allowed
 */
test('Method not allowed', async () => {
  console.log('📋 Testing method not allowed...');
  
  const response = await fetch(API_ENDPOINT, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ test: 'data' })
  });
  
  const data = await response.json();
  
  // Should return 405 error
  assert.strictEqual(response.status, 405, 'Should return 405 status');
  assert.strictEqual(response.ok, false, 'Should not be successful');
  assert.ok(data.error, 'Should have error message');
  assert.ok(data.error.includes('not allowed'), 'Should mention method not allowed');
  
  console.log('✅ Method not allowed test passed');
  console.log(`   - Error: ${data.error}`);
});

/**
 * Test: Response caching headers
 */
test('Response caching headers', async () => {
  console.log('📋 Testing response caching headers...');
  
  const response = await fetch(`${API_ENDPOINT}?workbook=0`);
  
  // Check for cache control header
  const cacheControl = response.headers.get('cache-control');
  assert.ok(cacheControl, 'Should have cache-control header');
  assert.ok(cacheControl.includes('s-maxage'), 'Should have s-maxage directive');
  
  console.log('✅ Caching headers test passed');
  console.log(`   - Cache-Control: ${cacheControl}`);
});

// Run all tests
console.log('🚀 Starting Multi-Workbook Fetch Sheets API Tests...');
console.log(`📍 Base URL: ${BASE_URL}`);
console.log(`🔗 API Endpoint: ${API_ENDPOINT}`);
console.log('');
