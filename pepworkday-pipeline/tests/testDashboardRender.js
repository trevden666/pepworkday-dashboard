/**
 * Dashboard Rendering E2E Tests
 * 
 * End-to-end tests for the PepWorkday dashboard using Playwright.
 * Tests cover:
 * - Page loading and rendering
 * - Chart visualization
 * - API integration
 * - User interactions
 * - Responsive design
 * - Performance metrics
 * 
 * @module tests/testDashboardRender
 * @author PEP Automation Team
 * @version 1.0.0
 */

import { test, expect } from '@playwright/test';

/**
 * Test configuration
 */
const TEST_CONFIG = {
  timeout: 30000,
  slowMo: process.env.CI ? 0 : 100,
  retries: process.env.CI ? 2 : 0,
};

/**
 * Dashboard Page Tests
 */
test.describe('Dashboard Page', () => {
  
  test.beforeEach(async ({ page }) => {
    // Set up test environment
    await page.setExtraHTTPHeaders({
      'X-Test-Mode': 'true',
    });
    
    // Navigate to dashboard
    await page.goto('/dashboard');
  });
  
  test('should load dashboard page successfully', async ({ page }) => {
    // Check page title
    await expect(page).toHaveTitle(/PepWorkday Dashboard/);
    
    // Check main heading
    await expect(page.locator('h1')).toContainText('PepWorkday Dashboard');
    
    // Check that the page is not showing an error
    await expect(page.locator('text=Something went wrong')).not.toBeVisible();
    
    // Check for main dashboard elements
    await expect(page.locator('[data-testid="dashboard-header"]')).toBeVisible();
    await expect(page.locator('[data-testid="dashboard-stats"]')).toBeVisible();
    await expect(page.locator('[data-testid="dashboard-chart"]')).toBeVisible();
  });
  
  test('should display API status indicator', async ({ page }) => {
    // Wait for API status to load
    await page.waitForSelector('[data-testid="api-status"]', { timeout: 10000 });
    
    // Check that status indicator is visible
    const statusIndicator = page.locator('[data-testid="api-status"]');
    await expect(statusIndicator).toBeVisible();
    
    // Status should be either healthy, error, or checking
    const statusText = await statusIndicator.textContent();
    expect(['✅ API Healthy', '❌ API Error', '🔄 Checking...']).toContain(statusText);
  });
  
  test('should render chart component', async ({ page }) => {
    // Wait for chart to load
    await page.waitForSelector('canvas', { timeout: 15000 });
    
    // Check that chart canvas is present
    const chartCanvas = page.locator('canvas');
    await expect(chartCanvas).toBeVisible();
    
    // Check chart container
    await expect(page.locator('[data-testid="summary-chart"]')).toBeVisible();
    
    // Verify chart has loaded by checking for Chart.js elements
    const chartContainer = page.locator('.chartjs-render-monitor');
    await expect(chartContainer).toBeVisible();
  });
  
  test('should handle refresh button click', async ({ page }) => {
    // Wait for page to load
    await page.waitForLoadState('networkidle');
    
    // Find and click refresh button
    const refreshButton = page.locator('button:has-text("Refresh")');
    await expect(refreshButton).toBeVisible();
    
    // Click refresh button
    await refreshButton.click();
    
    // Check that API status updates (should show checking state briefly)
    await expect(page.locator('text=🔄 Checking...')).toBeVisible({ timeout: 5000 });
  });
  
  test('should display dashboard statistics', async ({ page }) => {
    // Check for statistics cards
    const statsCards = page.locator('[data-testid="stats-card"]');
    await expect(statsCards).toHaveCount(3);
    
    // Check individual stat cards
    await expect(page.locator('text=DATA SOURCE')).toBeVisible();
    await expect(page.locator('text=Google Sheets')).toBeVisible();
    
    await expect(page.locator('text=LAST REFRESH')).toBeVisible();
    
    await expect(page.locator('text=ORGANIZATION')).toBeVisible();
    await expect(page.locator('text=PEPMove')).toBeVisible();
    await expect(page.locator('text=ID: 5005620')).toBeVisible();
  });
  
  test('should be responsive on mobile devices', async ({ page }) => {
    // Set mobile viewport
    await page.setViewportSize({ width: 375, height: 667 });
    
    // Check that page still loads correctly
    await expect(page.locator('h1')).toContainText('PepWorkday Dashboard');
    
    // Check that chart is still visible and responsive
    await page.waitForSelector('canvas', { timeout: 15000 });
    const chartCanvas = page.locator('canvas');
    await expect(chartCanvas).toBeVisible();
    
    // Check that stats cards stack properly on mobile
    const statsCards = page.locator('[data-testid="stats-card"]');
    await expect(statsCards.first()).toBeVisible();
  });
  
  test('should handle API errors gracefully', async ({ page }) => {
    // Mock API to return error
    await page.route('/api/summary', route => {
      route.fulfill({
        status: 500,
        contentType: 'application/json',
        body: JSON.stringify({
          success: false,
          error: 'Test error',
          timestamp: new Date().toISOString()
        })
      });
    });
    
    // Reload page to trigger API call
    await page.reload();
    
    // Wait for error state
    await page.waitForSelector('text=❌ API Error', { timeout: 10000 });
    
    // Check that error status is displayed
    await expect(page.locator('text=❌ API Error')).toBeVisible();
    
    // Check that chart shows error state
    await expect(page.locator('text=Failed to load chart')).toBeVisible();
  });
  
  test('should load within performance budget', async ({ page }) => {
    const startTime = Date.now();
    
    // Navigate to dashboard
    await page.goto('/dashboard');
    
    // Wait for page to be fully loaded
    await page.waitForLoadState('networkidle');
    
    const loadTime = Date.now() - startTime;
    
    // Page should load within 5 seconds
    expect(loadTime).toBeLessThan(5000);
    
    // Check Core Web Vitals
    const performanceMetrics = await page.evaluate(() => {
      return new Promise((resolve) => {
        new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const metrics = {};
          
          entries.forEach((entry) => {
            if (entry.entryType === 'largest-contentful-paint') {
              metrics.lcp = entry.startTime;
            }
            if (entry.entryType === 'first-input') {
              metrics.fid = entry.processingStart - entry.startTime;
            }
          });
          
          resolve(metrics);
        }).observe({ entryTypes: ['largest-contentful-paint', 'first-input'] });
        
        // Resolve after 3 seconds if no metrics are captured
        setTimeout(() => resolve({}), 3000);
      });
    });
    
    // LCP should be under 2.5 seconds
    if (performanceMetrics.lcp) {
      expect(performanceMetrics.lcp).toBeLessThan(2500);
    }
    
    // FID should be under 100ms
    if (performanceMetrics.fid) {
      expect(performanceMetrics.fid).toBeLessThan(100);
    }
  });
  
  test('should have proper accessibility features', async ({ page }) => {
    // Check for proper heading hierarchy
    const h1 = page.locator('h1');
    await expect(h1).toHaveCount(1);
    
    // Check for alt text on images (if any)
    const images = page.locator('img');
    const imageCount = await images.count();
    
    for (let i = 0; i < imageCount; i++) {
      const img = images.nth(i);
      await expect(img).toHaveAttribute('alt');
    }
    
    // Check for proper button labels
    const buttons = page.locator('button');
    const buttonCount = await buttons.count();
    
    for (let i = 0; i < buttonCount; i++) {
      const button = buttons.nth(i);
      const hasText = await button.textContent();
      const hasAriaLabel = await button.getAttribute('aria-label');
      
      expect(hasText || hasAriaLabel).toBeTruthy();
    }
    
    // Check color contrast (basic check)
    const backgroundColor = await page.evaluate(() => {
      return window.getComputedStyle(document.body).backgroundColor;
    });
    
    expect(backgroundColor).toBeTruthy();
  });
  
  test('should handle network failures', async ({ page }) => {
    // Go offline
    await page.context().setOffline(true);
    
    // Try to refresh the page
    const refreshButton = page.locator('button:has-text("Refresh")');
    await refreshButton.click();
    
    // Should show error state
    await expect(page.locator('text=❌ API Error')).toBeVisible({ timeout: 10000 });
    
    // Go back online
    await page.context().setOffline(false);
    
    // Refresh should work again
    await refreshButton.click();
    
    // Should eventually show healthy or checking state
    await expect(page.locator('text=🔄 Checking...')).toBeVisible({ timeout: 5000 });
  });
});

/**
 * API Integration Tests
 */
test.describe('API Integration', () => {
  
  test('should successfully call summary API', async ({ page }) => {
    // Intercept API call
    let apiResponse;
    
    await page.route('/api/summary', route => {
      route.continue().then(response => {
        apiResponse = response;
      });
    });
    
    // Navigate to dashboard to trigger API call
    await page.goto('/dashboard');
    
    // Wait for API call to complete
    await page.waitForLoadState('networkidle');
    
    // Verify API was called
    expect(apiResponse).toBeTruthy();
  });
  
  test('should handle API rate limiting', async ({ page }) => {
    // Mock rate limit response
    await page.route('/api/summary', route => {
      route.fulfill({
        status: 429,
        contentType: 'application/json',
        body: JSON.stringify({
          success: false,
          error: 'Rate limit exceeded. Please try again later.',
          timestamp: new Date().toISOString()
        })
      });
    });
    
    // Navigate to dashboard
    await page.goto('/dashboard');
    
    // Should show rate limit error
    await expect(page.locator('text=❌ API Error')).toBeVisible({ timeout: 10000 });
  });
});
