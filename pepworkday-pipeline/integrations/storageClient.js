/**
 * Google Cloud Storage Client Integration
 * 
 * This module provides a configured Google Cloud Storage client that works
 * seamlessly across Vercel and local development environments using the
 * unified GCP credentials helper.
 * 
 * Features:
 * - Automatic credential management via gcpCredentials utility
 * - Error handling with proper logging
 * - Example usage for common storage operations
 * - PEPMove-specific bucket and file naming conventions
 * 
 * @module storageClient
 * @author PEP Automation Team
 * @version 1.0.0
 */

import { Storage } from '@google-cloud/storage';
import { getGCPCredentials, validateGCPEnvironment, getEnvironmentType } from '../utils/gcpCredentials.js';

/**
 * Initialize Google Cloud Storage client with unified credentials
 * Uses the gcpCredentials utility to handle both Vercel and local environments
 */
let storageClient;

try {
  // Validate environment before initializing
  validateGCPEnvironment();
  
  // Get credentials configuration
  const gcpConfig = getGCPCredentials();
  
  // Initialize Storage client with configuration
  storageClient = new Storage(gcpConfig);
  
  console.log(`✅ Google Cloud Storage client initialized for ${getEnvironmentType()} environment`);
} catch (error) {
  console.error('❌ Failed to initialize Google Cloud Storage client:', error.message);
  throw error;
}

export { storageClient };

/**
 * Example configuration for PEPMove operations
 * These can be overridden via environment variables
 */
const DEFAULT_BUCKET_NAME = process.env.GCP_STORAGE_BUCKET || 'pepworkday-data';
const DEFAULT_FILE_PREFIX = process.env.GCP_FILE_PREFIX || 'pepmove';

/**
 * Upload JSON data to Google Cloud Storage with error handling
 * 
 * @param {Object} data - The JSON data to upload
 * @param {string} [fileName] - Custom file name (optional)
 * @param {string} [bucketName] - Custom bucket name (optional)
 * @returns {Promise<Object>} Upload result with file metadata
 * 
 * @example
 * const result = await uploadJSONData(
 *   { foo: 'bar', timestamp: new Date().toISOString() },
 *   'my-data.json'
 * );
 * console.log(`Uploaded to: ${result.publicUrl}`);
 */
export const uploadJSONData = async (data, fileName = null, bucketName = DEFAULT_BUCKET_NAME) => {
  try {
    // Generate filename if not provided
    const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
    const finalFileName = fileName || `${DEFAULT_FILE_PREFIX}-${timestamp}.json`;
    
    // Get bucket and file references
    const bucket = storageClient.bucket(bucketName);
    const file = bucket.file(finalFileName);
    
    // Convert data to JSON string
    const jsonData = JSON.stringify(data, null, 2);
    
    console.log(`📤 Uploading JSON data to gs://${bucketName}/${finalFileName}`);
    
    // Upload with proper content type and metadata
    await file.save(jsonData, {
      metadata: {
        contentType: 'application/json',
        metadata: {
          uploadedBy: 'pepworkday-pipeline',
          environment: getEnvironmentType(),
          timestamp: new Date().toISOString(),
          dataSize: jsonData.length.toString()
        }
      }
    });
    
    console.log(`✅ Successfully uploaded JSON data (${jsonData.length} bytes)`);
    
    // Return file metadata
    const [metadata] = await file.getMetadata();
    
    return {
      success: true,
      fileName: finalFileName,
      bucketName: bucketName,
      size: metadata.size,
      contentType: metadata.contentType,
      timeCreated: metadata.timeCreated,
      publicUrl: `gs://${bucketName}/${finalFileName}`,
      httpUrl: `https://storage.googleapis.com/${bucketName}/${finalFileName}`
    };
    
  } catch (error) {
    console.error('❌ Failed to upload JSON data:', error.message);
    
    // Return error details for handling
    return {
      success: false,
      error: error.message,
      fileName: fileName,
      bucketName: bucketName
    };
  }
};

/**
 * Download and parse JSON data from Google Cloud Storage
 * 
 * @param {string} fileName - The file name to download
 * @param {string} [bucketName] - Custom bucket name (optional)
 * @returns {Promise<Object>} Parsed JSON data or error details
 * 
 * @example
 * const data = await downloadJSONData('my-file.json');
 * if (data.success) {
 *   console.log('Downloaded data:', data.content);
 * }
 */
export const downloadJSONData = async (fileName, bucketName = DEFAULT_BUCKET_NAME) => {
  try {
    console.log(`📥 Downloading JSON data from gs://${bucketName}/${fileName}`);
    
    const bucket = storageClient.bucket(bucketName);
    const file = bucket.file(fileName);
    
    // Check if file exists
    const [exists] = await file.exists();
    if (!exists) {
      throw new Error(`File not found: gs://${bucketName}/${fileName}`);
    }
    
    // Download file content
    const [content] = await file.download();
    const jsonData = JSON.parse(content.toString());
    
    console.log(`✅ Successfully downloaded and parsed JSON data (${content.length} bytes)`);
    
    return {
      success: true,
      fileName: fileName,
      bucketName: bucketName,
      content: jsonData,
      size: content.length
    };
    
  } catch (error) {
    console.error('❌ Failed to download JSON data:', error.message);
    
    return {
      success: false,
      error: error.message,
      fileName: fileName,
      bucketName: bucketName
    };
  }
};

/**
 * List files in a bucket with optional prefix filtering
 * 
 * @param {string} [bucketName] - Custom bucket name (optional)
 * @param {string} [prefix] - File prefix filter (optional)
 * @returns {Promise<Array>} Array of file metadata objects
 * 
 * @example
 * const files = await listFiles('my-bucket', 'pepmove-');
 * files.forEach(file => console.log(file.name));
 */
export const listFiles = async (bucketName = DEFAULT_BUCKET_NAME, prefix = '') => {
  try {
    console.log(`📋 Listing files in gs://${bucketName}${prefix ? ` with prefix: ${prefix}` : ''}`);
    
    const bucket = storageClient.bucket(bucketName);
    const [files] = await bucket.getFiles({ prefix });
    
    const fileList = files.map(file => ({
      name: file.name,
      size: file.metadata.size,
      contentType: file.metadata.contentType,
      timeCreated: file.metadata.timeCreated,
      updated: file.metadata.updated
    }));
    
    console.log(`✅ Found ${fileList.length} files`);
    
    return fileList;
    
  } catch (error) {
    console.error('❌ Failed to list files:', error.message);
    throw error;
  }
};

/**
 * Example usage function demonstrating common storage operations
 * This function shows how to use the storage client for typical PEPMove workflows
 * 
 * @returns {Promise<void>}
 */
export const demonstrateStorageOperations = async () => {
  try {
    console.log('🚀 Starting Google Cloud Storage demonstration...');
    
    // Example 1: Upload sample PEPMove data
    const sampleData = {
      organization: 'PEPMove',
      organizationId: '5005620',
      groupId: '129031',
      timestamp: new Date().toISOString(),
      vehicles: [
        { id: 'vehicle-001', status: 'active', location: 'depot' },
        { id: 'vehicle-002', status: 'in-transit', location: 'route-a' }
      ],
      summary: {
        totalVehicles: 2,
        activeVehicles: 2,
        generatedBy: 'pepworkday-pipeline'
      }
    };
    
    const uploadResult = await uploadJSONData(sampleData, 'pepmove-demo.json');
    
    if (uploadResult.success) {
      console.log('📤 Upload successful:', uploadResult.publicUrl);
      
      // Example 2: Download the same data
      const downloadResult = await downloadJSONData('pepmove-demo.json');
      
      if (downloadResult.success) {
        console.log('📥 Download successful, data matches:', 
          JSON.stringify(downloadResult.content.summary, null, 2));
      }
      
      // Example 3: List files with PEPMove prefix
      const files = await listFiles(DEFAULT_BUCKET_NAME, 'pepmove-');
      console.log(`📋 Found ${files.length} PEPMove files in bucket`);
    }
    
    console.log('✅ Storage demonstration completed successfully');
    
  } catch (error) {
    console.error('❌ Storage demonstration failed:', error.message);
    throw error;
  }
};
