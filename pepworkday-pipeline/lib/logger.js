/**
 * Structured Logging Utility
 * 
 * Provides structured logging with Vercel integration and
 * environment-aware configuration for better observability.
 * 
 * Features:
 * - Structured JSON logging
 * - Request correlation IDs
 * - Performance metrics
 * - Error tracking
 * - Vercel observability integration
 * 
 * @module lib/logger
 * @author PEP Automation Team
 * @version 1.0.0
 */

// Using console.log instead of @vercel/log (which doesn't exist)

/**
 * Log levels
 */
export const LOG_LEVELS = {
  ERROR: 'error',
  WARN: 'warn',
  INFO: 'info',
  DEBUG: 'debug',
};

/**
 * Generate correlation ID for request tracking
 * 
 * @returns {string} Unique correlation ID
 */
function generateCorrelationId() {
  return `req_${Date.now()}_${Math.random().toString(36).substr(2, 9)}`;
}

/**
 * Get request metadata for logging
 * 
 * @param {Object} req - Next.js request object
 * @returns {Object} Request metadata
 */
function getRequestMetadata(req) {
  if (!req) return {};
  
  return {
    method: req.method,
    url: req.url,
    userAgent: req.headers['user-agent'],
    ip: req.headers['x-forwarded-for'] || req.connection?.remoteAddress,
    referer: req.headers.referer,
    correlationId: req.correlationId || generateCorrelationId(),
  };
}

/**
 * Base logger class with structured logging
 */
class Logger {
  constructor(context = {}) {
    this.context = context;
    this.isProduction = process.env.NODE_ENV === 'production';
    this.isVercel = !!process.env.VERCEL;
  }
  
  /**
   * Format log entry with context and metadata
   * 
   * @param {string} level - Log level
   * @param {string} message - Log message
   * @param {Object} data - Additional data
   * @param {Object} req - Request object (optional)
   * @returns {Object} Formatted log entry
   */
  formatLogEntry(level, message, data = {}, req = null) {
    const timestamp = new Date().toISOString();
    const requestMeta = getRequestMetadata(req);
    
    return {
      timestamp,
      level,
      message,
      service: 'pepworkday-pipeline',
      version: '1.0.0',
      environment: process.env.NODE_ENV,
      ...this.context,
      ...requestMeta,
      ...data,
    };
  }
  
  /**
   * Log error with stack trace and context
   * 
   * @param {string} message - Error message
   * @param {Error|Object} error - Error object or additional data
   * @param {Object} req - Request object (optional)
   */
  error(message, error = {}, req = null) {
    const logEntry = this.formatLogEntry(LOG_LEVELS.ERROR, message, {
      error: error instanceof Error ? {
        name: error.name,
        message: error.message,
        stack: error.stack,
      } : error,
    }, req);
    
    // Log to console (works in both local and Vercel environments)
    console.error('❌', JSON.stringify(logEntry, null, 2));
  }
  
  /**
   * Log warning message
   * 
   * @param {string} message - Warning message
   * @param {Object} data - Additional data
   * @param {Object} req - Request object (optional)
   */
  warn(message, data = {}, req = null) {
    const logEntry = this.formatLogEntry(LOG_LEVELS.WARN, message, data, req);
    
    // Log to console (works in both local and Vercel environments)
    console.warn('⚠️', JSON.stringify(logEntry, null, 2));
  }
  
  /**
   * Log info message
   * 
   * @param {string} message - Info message
   * @param {Object} data - Additional data
   * @param {Object} req - Request object (optional)
   */
  info(message, data = {}, req = null) {
    const logEntry = this.formatLogEntry(LOG_LEVELS.INFO, message, data, req);
    
    // Log to console (works in both local and Vercel environments)
    console.log('ℹ️', JSON.stringify(logEntry, null, 2));
  }
  
  /**
   * Log debug message (only in development)
   * 
   * @param {string} message - Debug message
   * @param {Object} data - Additional data
   * @param {Object} req - Request object (optional)
   */
  debug(message, data = {}, req = null) {
    if (this.isProduction) return;
    
    const logEntry = this.formatLogEntry(LOG_LEVELS.DEBUG, message, data, req);
    
    console.debug('🐛', JSON.stringify(logEntry, null, 2));
  }
  
  /**
   * Create child logger with additional context
   * 
   * @param {Object} additionalContext - Additional context to merge
   * @returns {Logger} New logger instance with merged context
   */
  child(additionalContext) {
    return new Logger({
      ...this.context,
      ...additionalContext,
    });
  }
}

/**
 * Default logger instance
 */
export const logger = new Logger();

/**
 * Create API logger with request context
 * 
 * @param {Object} req - Next.js request object
 * @param {string} endpoint - API endpoint name
 * @returns {Logger} Logger with request context
 */
export function createApiLogger(req, endpoint) {
  const correlationId = generateCorrelationId();
  req.correlationId = correlationId;
  
  return logger.child({
    endpoint,
    correlationId,
    requestId: correlationId,
  });
}

/**
 * Performance timer utility
 */
export class PerformanceTimer {
  constructor(name, logger) {
    this.name = name;
    this.logger = logger;
    this.startTime = performance.now();
    this.markers = [];
  }
  
  /**
   * Add a performance marker
   * 
   * @param {string} name - Marker name
   */
  mark(name) {
    const time = performance.now();
    this.markers.push({
      name,
      time: time - this.startTime,
      timestamp: new Date().toISOString(),
    });
  }
  
  /**
   * End timer and log performance metrics
   * 
   * @param {Object} additionalData - Additional data to log
   */
  end(additionalData = {}) {
    const endTime = performance.now();
    const duration = endTime - this.startTime;
    
    this.logger.info(`Performance: ${this.name}`, {
      duration_ms: Math.round(duration),
      markers: this.markers,
      ...additionalData,
    });
    
    return duration;
  }
}

/**
 * Higher-order function to wrap API routes with logging
 * 
 * @param {Function} handler - API route handler
 * @param {string} routeName - Route name for logging
 * @returns {Function} Wrapped handler with logging
 */
export function withLogging(handler, routeName) {
  return async (req, res) => {
    const apiLogger = createApiLogger(req, routeName);
    const timer = new PerformanceTimer(`API ${routeName}`, apiLogger);
    
    // Add logger to request object
    req.logger = apiLogger;
    
    try {
      apiLogger.info(`API request started`, {
        method: req.method,
        query: req.query,
        body: req.method === 'POST' ? req.body : undefined,
      });
      
      timer.mark('handler_start');
      
      // Call the original handler
      const result = await handler(req, res);
      
      timer.mark('handler_end');
      timer.end({
        status: res.statusCode,
        success: res.statusCode < 400,
      });
      
      apiLogger.info(`API request completed`, {
        status: res.statusCode,
        success: res.statusCode < 400,
      });
      
      return result;
      
    } catch (error) {
      timer.mark('error');
      timer.end({
        status: 500,
        success: false,
        error: error.message,
      });
      
      apiLogger.error(`API request failed`, error);
      
      // Re-throw the error to be handled by Next.js
      throw error;
    }
  };
}

/**
 * Middleware to add correlation ID to requests
 * 
 * @param {Object} req - Request object
 * @param {Object} res - Response object
 * @param {Function} next - Next function
 */
export function correlationMiddleware(req, res, next) {
  req.correlationId = req.headers['x-correlation-id'] || generateCorrelationId();
  res.setHeader('x-correlation-id', req.correlationId);
  
  if (next) next();
}
