/**
 * Playwright Configuration
 * 
 * Configuration for end-to-end testing with Playwright
 * including browser setup, test settings, and CI/CD integration.
 * 
 * @module playwright.config
 * @author PEP Automation Team
 * @version 1.0.0
 */

import { defineConfig, devices } from '@playwright/test';

/**
 * Playwright configuration
 */
export default defineConfig({
  // Test directory
  testDir: './tests',
  
  // Test file patterns
  testMatch: ['**/testDashboardRender.js', '**/test*.e2e.js'],
  
  // Global test timeout
  timeout: 30000,
  
  // Expect timeout for assertions
  expect: {
    timeout: 5000,
  },
  
  // Fail the build on CI if you accidentally left test.only in the source code
  forbidOnly: !!process.env.CI,
  
  // Retry on CI only
  retries: process.env.CI ? 2 : 0,
  
  // Opt out of parallel tests on CI
  workers: process.env.CI ? 1 : undefined,
  
  // Reporter configuration
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results.json' }],
    ['junit', { outputFile: 'test-results.xml' }],
    process.env.CI ? ['github'] : ['list'],
  ],
  
  // Global setup and teardown
  globalSetup: './tests/global-setup.js',
  globalTeardown: './tests/global-teardown.js',
  
  // Shared settings for all tests
  use: {
    // Base URL for tests
    baseURL: process.env.PLAYWRIGHT_BASE_URL || 'http://localhost:3000',
    
    // Browser context options
    viewport: { width: 1280, height: 720 },
    
    // Collect trace when retrying the failed test
    trace: 'on-first-retry',
    
    // Record video on failure
    video: 'retain-on-failure',
    
    // Take screenshot on failure
    screenshot: 'only-on-failure',
    
    // Ignore HTTPS errors
    ignoreHTTPSErrors: true,
    
    // User agent
    userAgent: 'PepWorkday-E2E-Tests/1.0.0',
    
    // Extra HTTP headers
    extraHTTPHeaders: {
      'X-Test-Environment': 'playwright',
    },
  },
  
  // Configure projects for major browsers
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    
    // Mobile browsers
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
    
    {
      name: 'Mobile Safari',
      use: { ...devices['iPhone 12'] },
    },
    
    // Microsoft Edge
    {
      name: 'Microsoft Edge',
      use: { ...devices['Desktop Edge'], channel: 'msedge' },
    },
  ],
  
  // Run your local dev server before starting the tests
  webServer: process.env.CI ? undefined : {
    command: 'npm run dev',
    port: 3000,
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
  
  // Output directory for test artifacts
  outputDir: 'test-results/',
  
  // Directory for test fixtures
  testIgnore: ['**/node_modules/**'],
  
  // Maximum time one test can run for
  globalTimeout: process.env.CI ? 600000 : 0, // 10 minutes on CI
  
  // Configuration for different environments
  ...(process.env.NODE_ENV === 'production' && {
    use: {
      baseURL: process.env.VERCEL_URL || process.env.PLAYWRIGHT_BASE_URL,
    },
    webServer: undefined, // Don't start dev server in production
  }),
});
