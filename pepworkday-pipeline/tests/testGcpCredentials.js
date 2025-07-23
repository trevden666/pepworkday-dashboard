/**
 * Test Suite for GCP Credentials Helper
 * 
 * This test suite validates the getGCPCredentials() function behavior
 * across different environment configurations:
 * - Vercel environment with GCP integration
 * - Local development environment
 * - Error conditions and edge cases
 * 
 * @module testGcpCredentials
 * @author PEP Automation Team
 * @version 1.0.0
 */

import { test, describe, beforeEach, afterEach } from 'node:test';
import assert from 'node:assert';
import { getGCPCredentials, validateGCPEnvironment, getEnvironmentType } from '../utils/gcpCredentials.js';

/**
 * Helper function to backup and restore environment variables
 */
class EnvironmentManager {
  constructor() {
    this.backup = {};
  }
  
  /**
   * Backup current environment variables
   * @param {string[]} vars - Array of environment variable names to backup
   */
  backup(vars) {
    vars.forEach(varName => {
      this.backup[varName] = process.env[varName];
    });
  }
  
  /**
   * Set environment variables for testing
   * @param {Object} vars - Object with variable names and values
   */
  set(vars) {
    Object.entries(vars).forEach(([name, value]) => {
      if (value === undefined) {
        delete process.env[name];
      } else {
        process.env[name] = value;
      }
    });
  }
  
  /**
   * Restore backed up environment variables
   */
  restore() {
    Object.entries(this.backup).forEach(([name, value]) => {
      if (value === undefined) {
        delete process.env[name];
      } else {
        process.env[name] = value;
      }
    });
    this.backup = {};
  }
}

describe('GCP Credentials Helper Tests', () => {
  let envManager;
  
  beforeEach(() => {
    envManager = new EnvironmentManager();
    // Backup relevant environment variables
    envManager.backup([
      'GCP_PRIVATE_KEY',
      'GCP_SERVICE_ACCOUNT_EMAIL', 
      'GCP_PROJECT_ID',
      'VERCEL',
      'VERCEL_ENV'
    ]);
  });
  
  afterEach(() => {
    // Restore original environment
    envManager.restore();
  });
  
  describe('getGCPCredentials() - Vercel Environment', () => {
    test('should return credentials object when GCP_PRIVATE_KEY is set', () => {
      // Arrange: Set up Vercel-style environment variables
      envManager.set({
        GCP_PRIVATE_KEY: '-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----',
        GCP_SERVICE_ACCOUNT_EMAIL: 'pepworkday@my-project.iam.gserviceaccount.com',
        GCP_PROJECT_ID: 'my-gcp-project'
      });
      
      // Act: Get credentials
      const result = getGCPCredentials();
      
      // Assert: Verify structure and content
      assert.strictEqual(typeof result, 'object', 'Should return an object');
      assert.ok(result.credentials, 'Should have credentials property');
      assert.ok(result.projectId, 'Should have projectId property');
      
      assert.strictEqual(
        result.credentials.client_email, 
        'pepworkday@my-project.iam.gserviceaccount.com',
        'Should have correct client_email'
      );
      
      assert.ok(
        result.credentials.private_key.includes('-----BEGIN PRIVATE KEY-----'),
        'Should have properly formatted private_key'
      );
      
      assert.strictEqual(
        result.projectId,
        'my-gcp-project',
        'Should have correct projectId'
      );
    });
    
    test('should decode base64 encoded private key', () => {
      // Arrange: Set up base64 encoded private key (as Vercel might do)
      const originalKey = '-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----';
      const base64Key = Buffer.from(originalKey).toString('base64');
      
      envManager.set({
        GCP_PRIVATE_KEY: base64Key,
        GCP_SERVICE_ACCOUNT_EMAIL: 'test@project.iam.gserviceaccount.com',
        GCP_PROJECT_ID: 'test-project'
      });
      
      // Act: Get credentials
      const result = getGCPCredentials();
      
      // Assert: Verify key was decoded properly
      assert.strictEqual(
        result.credentials.private_key,
        originalKey,
        'Should decode base64 private key correctly'
      );
    });
    
    test('should handle already formatted private key', () => {
      // Arrange: Set up already formatted private key
      const formattedKey = '-----BEGIN PRIVATE KEY-----\nMIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC...\n-----END PRIVATE KEY-----';
      
      envManager.set({
        GCP_PRIVATE_KEY: formattedKey,
        GCP_SERVICE_ACCOUNT_EMAIL: 'test@project.iam.gserviceaccount.com',
        GCP_PROJECT_ID: 'test-project'
      });
      
      // Act: Get credentials
      const result = getGCPCredentials();
      
      // Assert: Verify key remains unchanged
      assert.strictEqual(
        result.credentials.private_key,
        formattedKey,
        'Should not modify already formatted private key'
      );
    });
  });
  
  describe('getGCPCredentials() - Local Environment', () => {
    test('should return empty object when GCP_PRIVATE_KEY is not set', () => {
      // Arrange: Clear all GCP environment variables
      envManager.set({
        GCP_PRIVATE_KEY: undefined,
        GCP_SERVICE_ACCOUNT_EMAIL: undefined,
        GCP_PROJECT_ID: undefined
      });
      
      // Act: Get credentials
      const result = getGCPCredentials();
      
      // Assert: Should return empty object for ADC fallback
      assert.deepStrictEqual(result, {}, 'Should return empty object for local development');
    });
  });
  
  describe('validateGCPEnvironment()', () => {
    test('should pass validation when all required vars are present in Vercel', () => {
      // Arrange: Set up complete Vercel environment
      envManager.set({
        VERCEL: '1',
        GCP_PRIVATE_KEY: 'test-key',
        GCP_SERVICE_ACCOUNT_EMAIL: 'test@project.iam.gserviceaccount.com',
        GCP_PROJECT_ID: 'test-project'
      });
      
      // Act & Assert: Should not throw
      assert.doesNotThrow(() => {
        const result = validateGCPEnvironment();
        assert.strictEqual(result, true, 'Should return true for valid environment');
      });
    });
    
    test('should throw error when required vars are missing in Vercel', () => {
      // Arrange: Set up incomplete Vercel environment
      envManager.set({
        VERCEL: '1',
        GCP_PRIVATE_KEY: undefined,
        GCP_SERVICE_ACCOUNT_EMAIL: 'test@project.iam.gserviceaccount.com',
        GCP_PROJECT_ID: undefined
      });
      
      // Act & Assert: Should throw with specific error message
      assert.throws(() => {
        validateGCPEnvironment();
      }, {
        name: 'Error',
        message: /Missing required GCP environment variables in Vercel: GCP_PRIVATE_KEY, GCP_PROJECT_ID/
      });
    });
    
    test('should pass validation in non-Vercel environment', () => {
      // Arrange: Set up non-Vercel environment
      envManager.set({
        VERCEL: undefined,
        VERCEL_ENV: undefined,
        GCP_PRIVATE_KEY: undefined,
        GCP_SERVICE_ACCOUNT_EMAIL: undefined,
        GCP_PROJECT_ID: undefined
      });
      
      // Act & Assert: Should not throw
      assert.doesNotThrow(() => {
        const result = validateGCPEnvironment();
        assert.strictEqual(result, true, 'Should return true for non-Vercel environment');
      });
    });
  });
  
  describe('getEnvironmentType()', () => {
    test('should return "vercel" when VERCEL env var is set', () => {
      // Arrange
      envManager.set({ VERCEL: '1' });
      
      // Act & Assert
      assert.strictEqual(getEnvironmentType(), 'vercel');
    });
    
    test('should return "vercel" when VERCEL_ENV is set', () => {
      // Arrange
      envManager.set({ VERCEL_ENV: 'production' });
      
      // Act & Assert
      assert.strictEqual(getEnvironmentType(), 'vercel');
    });
    
    test('should return "vercel" when GCP_PRIVATE_KEY is set (Vercel-style)', () => {
      // Arrange
      envManager.set({ 
        VERCEL: undefined,
        VERCEL_ENV: undefined,
        GCP_PRIVATE_KEY: 'test-key' 
      });
      
      // Act & Assert
      assert.strictEqual(getEnvironmentType(), 'vercel');
    });
    
    test('should return "local" when no Vercel indicators are present', () => {
      // Arrange
      envManager.set({
        VERCEL: undefined,
        VERCEL_ENV: undefined,
        GCP_PRIVATE_KEY: undefined
      });
      
      // Act & Assert
      assert.strictEqual(getEnvironmentType(), 'local');
    });
  });
});
