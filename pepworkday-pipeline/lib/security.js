/**
 * Security Utilities
 * 
 * Provides security utilities for:
 * - Cookie management with HttpOnly flags
 * - CSRF protection
 * - Input validation and sanitization
 * - Security headers
 * - Session management
 * 
 * @module lib/security
 * @author PEP Automation Team
 * @version 1.0.0
 */

import { serialize, parse } from 'cookie';
import DOMPurify from 'isomorphic-dompurify';

/**
 * Security configuration
 */
const SECURITY_CONFIG = {
  // Cookie settings
  cookie: {
    httpOnly: true,
    secure: process.env.NODE_ENV === 'production',
    sameSite: 'strict',
    maxAge: 24 * 60 * 60 * 1000, // 24 hours
    path: '/',
  },
  
  // CSRF settings
  csrf: {
    tokenLength: 32,
    headerName: 'x-csrf-token',
    cookieName: 'csrf-token',
  },
  
  // Rate limiting
  rateLimit: {
    windowMs: 15 * 60 * 1000, // 15 minutes
    maxRequests: 100,
  },
  
  // Content Security Policy
  csp: {
    defaultSrc: ["'self'"],
    scriptSrc: ["'self'", "'unsafe-inline'", "https://www.googletagmanager.com"],
    styleSrc: ["'self'", "'unsafe-inline'"],
    imgSrc: ["'self'", "data:", "https:"],
    connectSrc: ["'self'", "https://api.posthog.com", "https://www.google-analytics.com"],
    fontSrc: ["'self'"],
    objectSrc: ["'none'"],
    mediaSrc: ["'self'"],
    frameSrc: ["'none'"],
  },
};

/**
 * Generate cryptographically secure random string
 * 
 * @param {number} length - Length of the random string
 * @returns {string} Random string
 */
function generateSecureRandom(length = 32) {
  const chars = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
  let result = '';
  
  // Use crypto.getRandomValues if available (browser/Node.js 15+)
  if (typeof crypto !== 'undefined' && crypto.getRandomValues) {
    const array = new Uint8Array(length);
    crypto.getRandomValues(array);
    
    for (let i = 0; i < length; i++) {
      result += chars[array[i] % chars.length];
    }
  } else {
    // Fallback for older Node.js versions
    const crypto = require('crypto');
    const bytes = crypto.randomBytes(length);
    
    for (let i = 0; i < length; i++) {
      result += chars[bytes[i] % chars.length];
    }
  }
  
  return result;
}

/**
 * Set secure HTTP-only cookie
 * 
 * @param {Object} res - Response object
 * @param {string} name - Cookie name
 * @param {string} value - Cookie value
 * @param {Object} options - Additional cookie options
 */
export function setSecureCookie(res, name, value, options = {}) {
  const cookieOptions = {
    ...SECURITY_CONFIG.cookie,
    ...options,
  };
  
  const serialized = serialize(name, value, cookieOptions);
  
  // Handle multiple cookies
  const existingCookies = res.getHeader('Set-Cookie') || [];
  const cookies = Array.isArray(existingCookies) ? existingCookies : [existingCookies];
  
  res.setHeader('Set-Cookie', [...cookies, serialized]);
}

/**
 * Get cookie value safely
 * 
 * @param {Object} req - Request object
 * @param {string} name - Cookie name
 * @returns {string|null} Cookie value or null
 */
export function getSecureCookie(req, name) {
  try {
    const cookies = parse(req.headers.cookie || '');
    return cookies[name] || null;
  } catch (error) {
    console.error('Error parsing cookies:', error);
    return null;
  }
}

/**
 * Clear cookie
 * 
 * @param {Object} res - Response object
 * @param {string} name - Cookie name
 */
export function clearCookie(res, name) {
  setSecureCookie(res, name, '', { maxAge: 0 });
}

/**
 * Generate CSRF token
 * 
 * @returns {string} CSRF token
 */
export function generateCSRFToken() {
  return generateSecureRandom(SECURITY_CONFIG.csrf.tokenLength);
}

/**
 * Validate CSRF token
 * 
 * @param {Object} req - Request object
 * @param {string} token - Token to validate
 * @returns {boolean} True if valid
 */
export function validateCSRFToken(req, token) {
  const cookieToken = getSecureCookie(req, SECURITY_CONFIG.csrf.cookieName);
  const headerToken = req.headers[SECURITY_CONFIG.csrf.headerName];
  
  return token && (token === cookieToken || token === headerToken);
}

/**
 * Sanitize HTML input
 * 
 * @param {string} input - Input to sanitize
 * @param {Object} options - DOMPurify options
 * @returns {string} Sanitized input
 */
export function sanitizeHTML(input, options = {}) {
  if (typeof input !== 'string') {
    return '';
  }
  
  return DOMPurify.sanitize(input, {
    ALLOWED_TAGS: ['b', 'i', 'em', 'strong', 'p', 'br'],
    ALLOWED_ATTR: [],
    ...options,
  });
}

/**
 * Validate and sanitize input
 * 
 * @param {string} input - Input to validate
 * @param {Object} rules - Validation rules
 * @returns {Object} Validation result
 */
export function validateInput(input, rules = {}) {
  const result = {
    isValid: true,
    sanitized: input,
    errors: [],
  };
  
  // Type check
  if (rules.type && typeof input !== rules.type) {
    result.isValid = false;
    result.errors.push(`Expected ${rules.type}, got ${typeof input}`);
    return result;
  }
  
  // Required check
  if (rules.required && (!input || input.toString().trim() === '')) {
    result.isValid = false;
    result.errors.push('Field is required');
    return result;
  }
  
  // String validations
  if (typeof input === 'string') {
    // Length checks
    if (rules.minLength && input.length < rules.minLength) {
      result.isValid = false;
      result.errors.push(`Minimum length is ${rules.minLength}`);
    }
    
    if (rules.maxLength && input.length > rules.maxLength) {
      result.isValid = false;
      result.errors.push(`Maximum length is ${rules.maxLength}`);
    }
    
    // Pattern check
    if (rules.pattern && !rules.pattern.test(input)) {
      result.isValid = false;
      result.errors.push('Invalid format');
    }
    
    // Sanitize HTML if requested
    if (rules.sanitizeHTML) {
      result.sanitized = sanitizeHTML(input, rules.sanitizeOptions);
    }
  }
  
  // Number validations
  if (typeof input === 'number') {
    if (rules.min !== undefined && input < rules.min) {
      result.isValid = false;
      result.errors.push(`Minimum value is ${rules.min}`);
    }
    
    if (rules.max !== undefined && input > rules.max) {
      result.isValid = false;
      result.errors.push(`Maximum value is ${rules.max}`);
    }
  }
  
  return result;
}

/**
 * Set security headers
 * 
 * @param {Object} res - Response object
 */
export function setSecurityHeaders(res) {
  // Content Security Policy
  const cspDirectives = Object.entries(SECURITY_CONFIG.csp)
    .map(([directive, sources]) => `${directive.replace(/([A-Z])/g, '-$1').toLowerCase()} ${sources.join(' ')}`)
    .join('; ');
  
  res.setHeader('Content-Security-Policy', cspDirectives);
  
  // Other security headers
  res.setHeader('X-Content-Type-Options', 'nosniff');
  res.setHeader('X-Frame-Options', 'DENY');
  res.setHeader('X-XSS-Protection', '1; mode=block');
  res.setHeader('Referrer-Policy', 'strict-origin-when-cross-origin');
  res.setHeader('Permissions-Policy', 'camera=(), microphone=(), geolocation=()');
  
  // HSTS (only in production with HTTPS)
  if (process.env.NODE_ENV === 'production') {
    res.setHeader('Strict-Transport-Security', 'max-age=31536000; includeSubDomains; preload');
  }
}

/**
 * Middleware to add security headers and CSRF protection
 * 
 * @param {Function} handler - API route handler
 * @returns {Function} Wrapped handler with security
 */
export function withSecurity(handler) {
  return async (req, res) => {
    // Set security headers
    setSecurityHeaders(res);
    
    // Generate and set CSRF token for GET requests
    if (req.method === 'GET') {
      const csrfToken = generateCSRFToken();
      setSecureCookie(res, SECURITY_CONFIG.csrf.cookieName, csrfToken);
      res.setHeader('X-CSRF-Token', csrfToken);
    }
    
    // Validate CSRF token for state-changing requests
    if (['POST', 'PUT', 'DELETE', 'PATCH'].includes(req.method)) {
      const token = req.headers[SECURITY_CONFIG.csrf.headerName] || req.body?.csrfToken;
      
      if (!validateCSRFToken(req, token)) {
        return res.status(403).json({
          error: 'CSRF token validation failed',
          message: 'Invalid or missing CSRF token',
        });
      }
    }
    
    // Call the original handler
    return handler(req, res);
  };
}

/**
 * Get client IP address
 * 
 * @param {Object} req - Request object
 * @returns {string} Client IP address
 */
export function getClientIP(req) {
  return (
    req.headers['x-forwarded-for']?.split(',')[0]?.trim() ||
    req.headers['x-real-ip'] ||
    req.connection?.remoteAddress ||
    req.socket?.remoteAddress ||
    'unknown'
  );
}

/**
 * Create session token
 * 
 * @param {Object} payload - Session payload
 * @returns {string} Session token
 */
export function createSessionToken(payload = {}) {
  const sessionData = {
    ...payload,
    createdAt: Date.now(),
    id: generateSecureRandom(16),
  };
  
  // In production, you would encrypt this or use JWT
  return Buffer.from(JSON.stringify(sessionData)).toString('base64');
}

/**
 * Validate session token
 * 
 * @param {string} token - Session token
 * @returns {Object|null} Session data or null if invalid
 */
export function validateSessionToken(token) {
  try {
    const sessionData = JSON.parse(Buffer.from(token, 'base64').toString());
    
    // Check if session is expired (24 hours)
    if (Date.now() - sessionData.createdAt > 24 * 60 * 60 * 1000) {
      return null;
    }
    
    return sessionData;
  } catch (error) {
    return null;
  }
}
