/**
 * GCP Credentials Helper for Vercel Integration
 * 
 * This module provides a unified way to handle Google Cloud Platform credentials
 * across different environments:
 * - Vercel: Uses environment variables injected by Vercel's GCP integration
 * - Local development: Falls back to Application Default Credentials (ADC) via gcloud CLI
 * 
 * @module gcpCredentials
 * @author PEP Automation Team
 * @version 1.0.0
 */

/**
 * Retrieves GCP credentials configuration based on the current environment.
 * 
 * For Vercel deployments, this function uses environment variables that are
 * automatically injected by Vercel's GCP integration:
 * - GCP_SERVICE_ACCOUNT_EMAIL: The service account email
 * - GCP_PRIVATE_KEY: The service account private key (base64 encoded)
 * - GCP_PROJECT_ID: The GCP project ID
 * 
 * For local development, it returns an empty object which allows the Google Cloud
 * client libraries to use Application Default Credentials (ADC) via gcloud CLI.
 * 
 * @returns {Object} GCP credentials configuration object
 * @returns {Object} [credentials] - Service account credentials (Vercel only)
 * @returns {string} [credentials.client_email] - Service account email
 * @returns {string} [credentials.private_key] - Service account private key
 * @returns {string} [projectId] - GCP project ID
 * 
 * @example
 * // In Vercel environment with GCP integration
 * const config = getGCPCredentials();
 * // Returns: {
 * //   credentials: {
 * //     client_email: "service-account@project.iam.gserviceaccount.com",
 * //     private_key: "-----BEGIN PRIVATE KEY-----\n..."
 * //   },
 * //   projectId: "my-gcp-project"
 * // }
 * 
 * @example
 * // In local development environment
 * const config = getGCPCredentials();
 * // Returns: {} (empty object, uses ADC)
 */
export const getGCPCredentials = () => {
  // Check if we're in Vercel environment with GCP integration
  // Vercel injects these environment variables when GCP integration is configured
  if (process.env.GCP_PRIVATE_KEY) {
    // Vercel environment: use injected environment variables
    return {
      credentials: {
        // Service account email from Vercel GCP integration
        client_email: process.env.GCP_SERVICE_ACCOUNT_EMAIL,
        // Private key from Vercel GCP integration
        // Note: Vercel may base64 encode the private key, so we decode it if needed
        private_key: process.env.GCP_PRIVATE_KEY.includes('-----BEGIN')
          ? process.env.GCP_PRIVATE_KEY
          : Buffer.from(process.env.GCP_PRIVATE_KEY, 'base64').toString('utf-8'),
      },
      // GCP project ID from Vercel GCP integration
      projectId: process.env.GCP_PROJECT_ID,
    };
  }
  
  // Local development environment: fallback to Application Default Credentials (ADC)
  // This allows developers to use `gcloud auth application-default login`
  // The Google Cloud client libraries will automatically discover and use these credentials
  return {};
};

/**
 * Validates that required GCP environment variables are present in Vercel environment.
 * 
 * @returns {boolean} True if all required environment variables are present
 * @throws {Error} If running in what appears to be Vercel but missing required variables
 */
export const validateGCPEnvironment = () => {
  // Check if we're likely in a Vercel environment
  const isVercel = process.env.VERCEL || process.env.VERCEL_ENV;
  
  if (isVercel) {
    const requiredVars = ['GCP_SERVICE_ACCOUNT_EMAIL', 'GCP_PRIVATE_KEY', 'GCP_PROJECT_ID'];
    const missingVars = requiredVars.filter(varName => !process.env[varName]);
    
    if (missingVars.length > 0) {
      throw new Error(
        `Missing required GCP environment variables in Vercel: ${missingVars.join(', ')}. ` +
        'Please configure Vercel GCP integration or set these variables manually.'
      );
    }
  }
  
  return true;
};

/**
 * Gets the current environment type for logging and debugging purposes.
 * 
 * @returns {string} Environment type: 'vercel', 'local', or 'unknown'
 */
export const getEnvironmentType = () => {
  if (process.env.VERCEL || process.env.VERCEL_ENV) {
    return 'vercel';
  }
  
  if (process.env.GCP_PRIVATE_KEY) {
    return 'vercel'; // Has Vercel-style GCP env vars
  }
  
  return 'local';
};
