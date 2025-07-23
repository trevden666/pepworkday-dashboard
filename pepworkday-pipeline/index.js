/**
 * PepWorkday Pipeline - JavaScript Entry Point
 * 
 * This is the main entry point for the JavaScript/Node.js components
 * of the PepWorkday pipeline, designed for Vercel deployment.
 * 
 * Features:
 * - Unified GCP credentials management
 * - Google Cloud Storage integration
 * - PEPMove-specific data handling
 * - Environment detection and validation
 * 
 * @module index
 * @author PEP Automation Team
 * @version 1.0.0
 */

import { getGCPCredentials, validateGCPEnvironment, getEnvironmentType } from './utils/gcpCredentials.js';
import { demonstrateStorageOperations } from './integrations/storageClient.js';

/**
 * Main application entry point
 * Demonstrates the GCP integration and storage capabilities
 */
async function main() {
  try {
    console.log('🚀 Starting PepWorkday Pipeline JavaScript Components...');
    console.log(`📍 Environment: ${getEnvironmentType()}`);
    
    // Validate environment configuration
    console.log('🔍 Validating GCP environment...');
    validateGCPEnvironment();
    
    // Display credentials configuration (without sensitive data)
    const gcpConfig = getGCPCredentials();
    if (gcpConfig.credentials) {
      console.log('✅ Using Vercel GCP integration');
      console.log(`   📧 Service Account: ${gcpConfig.credentials.client_email}`);
      console.log(`   🏗️  Project ID: ${gcpConfig.projectId}`);
    } else {
      console.log('✅ Using local Application Default Credentials');
    }
    
    // Demonstrate storage operations
    console.log('\n📦 Demonstrating Google Cloud Storage operations...');
    await demonstrateStorageOperations();
    
    console.log('\n🎉 PepWorkday Pipeline JavaScript components initialized successfully!');
    
  } catch (error) {
    console.error('❌ Failed to initialize PepWorkday Pipeline:', error.message);
    process.exit(1);
  }
}

// Run main function if this file is executed directly
if (import.meta.url === `file://${process.argv[1]}`) {
  main().catch(error => {
    console.error('💥 Unhandled error:', error);
    process.exit(1);
  });
}

export { main };
