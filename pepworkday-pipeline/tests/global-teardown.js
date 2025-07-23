/**
 * Playwright Global Teardown
 * 
 * Global teardown script that runs after all tests.
 * Handles cleanup, report generation, and resource disposal.
 * 
 * @module tests/global-teardown
 * @author PEP Automation Team
 * @version 1.0.0
 */

import fs from 'fs';
import path from 'path';

/**
 * Global teardown function
 * 
 * @param {Object} config - Playwright configuration
 */
async function globalTeardown(config) {
  console.log('🧹 Starting Playwright global teardown...');
  
  try {
    // Clean up test artifacts
    await cleanupTestArtifacts();
    
    // Generate test summary
    await generateTestSummary();
    
    // Clean up environment
    await cleanupEnvironment();
    
    console.log('✅ Playwright global teardown completed successfully');
    
  } catch (error) {
    console.error('❌ Playwright global teardown failed:', error);
    // Don't throw error to avoid masking test failures
  }
}

/**
 * Clean up test artifacts and temporary files
 */
async function cleanupTestArtifacts() {
  console.log('🗑️  Cleaning up test artifacts...');
  
  try {
    const artifactDirs = [
      'test-results',
      'playwright-report',
      '.playwright',
    ];
    
    for (const dir of artifactDirs) {
      const dirPath = path.resolve(dir);
      
      if (fs.existsSync(dirPath)) {
        // Keep artifacts in CI for debugging
        if (!process.env.CI) {
          console.log(`   Cleaning ${dir}/`);
          // In a real implementation, you might want to clean old artifacts
          // fs.rmSync(dirPath, { recursive: true, force: true });
        } else {
          console.log(`   Keeping ${dir}/ for CI analysis`);
        }
      }
    }
    
    console.log('✅ Test artifacts cleanup completed');
    
  } catch (error) {
    console.error('❌ Test artifacts cleanup failed:', error);
  }
}

/**
 * Generate test summary report
 */
async function generateTestSummary() {
  console.log('📊 Generating test summary...');
  
  try {
    const testResultsPath = path.resolve('test-results.json');
    
    if (fs.existsSync(testResultsPath)) {
      const testResults = JSON.parse(fs.readFileSync(testResultsPath, 'utf8'));
      
      const summary = {
        timestamp: new Date().toISOString(),
        environment: process.env.NODE_ENV || 'test',
        ci: !!process.env.CI,
        totalTests: testResults.suites?.reduce((total, suite) => {
          return total + (suite.specs?.length || 0);
        }, 0) || 0,
        passedTests: 0,
        failedTests: 0,
        skippedTests: 0,
        duration: testResults.stats?.duration || 0,
      };
      
      // Calculate test statistics
      testResults.suites?.forEach(suite => {
        suite.specs?.forEach(spec => {
          spec.tests?.forEach(test => {
            switch (test.status) {
              case 'passed':
                summary.passedTests++;
                break;
              case 'failed':
                summary.failedTests++;
                break;
              case 'skipped':
                summary.skippedTests++;
                break;
            }
          });
        });
      });
      
      // Write summary to file
      const summaryPath = path.resolve('test-summary.json');
      fs.writeFileSync(summaryPath, JSON.stringify(summary, null, 2));
      
      // Log summary to console
      console.log('📈 Test Summary:');
      console.log(`   Total Tests: ${summary.totalTests}`);
      console.log(`   Passed: ${summary.passedTests}`);
      console.log(`   Failed: ${summary.failedTests}`);
      console.log(`   Skipped: ${summary.skippedTests}`);
      console.log(`   Duration: ${Math.round(summary.duration / 1000)}s`);
      
      // Set exit code for CI
      if (process.env.CI && summary.failedTests > 0) {
        console.log('❌ Tests failed - setting exit code');
        process.exitCode = 1;
      }
      
    } else {
      console.log('⚠️  No test results file found');
    }
    
    console.log('✅ Test summary generation completed');
    
  } catch (error) {
    console.error('❌ Test summary generation failed:', error);
  }
}

/**
 * Clean up environment and reset state
 */
async function cleanupEnvironment() {
  console.log('🔧 Cleaning up environment...');
  
  try {
    // Reset environment variables
    delete process.env.NEXT_PUBLIC_ENABLE_ANALYTICS;
    
    // Clear any global state
    if (global.testState) {
      delete global.testState;
    }
    
    // Force garbage collection if available
    if (global.gc) {
      global.gc();
    }
    
    console.log('✅ Environment cleanup completed');
    
  } catch (error) {
    console.error('❌ Environment cleanup failed:', error);
  }
}

export default globalTeardown;
