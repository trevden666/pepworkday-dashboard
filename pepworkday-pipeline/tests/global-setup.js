/**
 * Playwright Global Setup
 * 
 * Global setup script that runs before all tests.
 * Handles environment preparation, test data setup,
 * and service initialization.
 * 
 * @module tests/global-setup
 * @author PEP Automation Team
 * @version 1.0.0
 */

import { chromium } from '@playwright/test';

/**
 * Global setup function
 * 
 * @param {Object} config - Playwright configuration
 */
async function globalSetup(config) {
  console.log('🚀 Starting Playwright global setup...');
  
  try {
    // Set up test environment variables
    process.env.NODE_ENV = 'test';
    process.env.NEXT_PUBLIC_ENABLE_ANALYTICS = 'false';
    
    // Launch browser for setup tasks
    const browser = await chromium.launch();
    const context = await browser.newContext();
    const page = await context.newPage();
    
    // Get base URL from config
    const baseURL = config.use?.baseURL || 'http://localhost:3000';
    
    console.log(`📍 Using base URL: ${baseURL}`);
    
    // Wait for the application to be ready
    await waitForApplication(page, baseURL);
    
    // Perform any additional setup tasks
    await setupTestData(page);
    
    // Clean up
    await browser.close();
    
    console.log('✅ Playwright global setup completed successfully');
    
  } catch (error) {
    console.error('❌ Playwright global setup failed:', error);
    throw error;
  }
}

/**
 * Wait for the application to be ready
 * 
 * @param {Object} page - Playwright page object
 * @param {string} baseURL - Base URL of the application
 */
async function waitForApplication(page, baseURL) {
  console.log('⏳ Waiting for application to be ready...');
  
  const maxRetries = 30;
  const retryDelay = 2000;
  
  for (let i = 0; i < maxRetries; i++) {
    try {
      // Try to navigate to the home page
      const response = await page.goto(baseURL, { 
        waitUntil: 'networkidle',
        timeout: 10000 
      });
      
      if (response && response.ok()) {
        console.log('✅ Application is ready');
        return;
      }
      
      throw new Error(`HTTP ${response?.status()}`);
      
    } catch (error) {
      console.log(`⏳ Attempt ${i + 1}/${maxRetries} failed: ${error.message}`);
      
      if (i === maxRetries - 1) {
        throw new Error(`Application not ready after ${maxRetries} attempts`);
      }
      
      // Wait before retrying
      await new Promise(resolve => setTimeout(resolve, retryDelay));
    }
  }
}

/**
 * Set up test data and mock services
 * 
 * @param {Object} page - Playwright page object
 */
async function setupTestData(page) {
  console.log('📊 Setting up test data...');
  
  try {
    // Mock API responses for consistent testing
    await page.route('/api/summary', route => {
      // Provide mock data for tests
      const mockData = {
        success: true,
        data: [
          {
            _rowIndex: 2,
            Address: '123 Main St',
            'Total Jobs': 15,
            Status: 'Active',
            _sanitized: true,
            _timestamp: new Date().toISOString()
          },
          {
            _rowIndex: 3,
            Address: '456 Oak Ave',
            'Total Jobs': 8,
            Status: 'Active',
            _sanitized: true,
            _timestamp: new Date().toISOString()
          },
          {
            _rowIndex: 4,
            Address: '789 Pine Rd',
            'Total Jobs': 12,
            Status: 'Active',
            _sanitized: true,
            _timestamp: new Date().toISOString()
          }
        ],
        metadata: {
          range: 'Summary!A1:Z100',
          rowCount: 3,
          timestamp: new Date().toISOString(),
          spreadsheetId: 'test-spreadsheet-id',
          cached: true,
          sanitized: true
        }
      };
      
      // Simulate network delay
      setTimeout(() => {
        route.fulfill({
          status: 200,
          contentType: 'application/json',
          body: JSON.stringify(mockData)
        });
      }, 500);
    });
    
    console.log('✅ Test data setup completed');
    
  } catch (error) {
    console.error('❌ Test data setup failed:', error);
    throw error;
  }
}

export default globalSetup;
