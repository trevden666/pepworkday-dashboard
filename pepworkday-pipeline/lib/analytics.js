/**
 * Analytics Configuration and Utilities
 * 
 * This module provides unified analytics tracking using:
 * - Google Analytics 4 for web analytics
 * - PostHog for product analytics and event tracking
 * 
 * Features:
 * - Environment-aware initialization
 * - Custom event tracking
 * - User identification
 * - Performance monitoring
 * - Privacy-compliant configuration
 * 
 * @module lib/analytics
 * @author PEP Automation Team
 * @version 1.0.0
 */

/**
 * Google Analytics 4 Configuration
 */
export const GA_MEASUREMENT_ID = process.env.NEXT_PUBLIC_GA_MEASUREMENT_ID;

/**
 * PostHog Configuration
 */
export const POSTHOG_KEY = process.env.NEXT_PUBLIC_POSTHOG_KEY;
export const POSTHOG_HOST = process.env.NEXT_PUBLIC_POSTHOG_HOST || 'https://app.posthog.com';

/**
 * Check if analytics should be enabled
 * Only enable in production or when explicitly configured
 */
export const isAnalyticsEnabled = () => {
  return process.env.NODE_ENV === 'production' || 
         process.env.NEXT_PUBLIC_ENABLE_ANALYTICS === 'true';
};

/**
 * Google Analytics 4 Event Tracking
 * 
 * @param {string} action - The action being tracked
 * @param {Object} parameters - Additional event parameters
 */
export const trackGAEvent = (action, parameters = {}) => {
  if (!isAnalyticsEnabled() || !GA_MEASUREMENT_ID) return;
  
  try {
    if (typeof window !== 'undefined' && window.gtag) {
      window.gtag('event', action, {
        ...parameters,
        // Add default parameters
        app_name: 'pepworkday-pipeline',
        app_version: '1.0.0',
        timestamp: new Date().toISOString()
      });
      
      console.log('📊 GA4 Event:', action, parameters);
    }
  } catch (error) {
    console.error('❌ GA4 tracking error:', error);
  }
};

/**
 * PostHog Event Tracking
 * 
 * @param {string} event - The event name
 * @param {Object} properties - Event properties
 */
export const trackPostHogEvent = (event, properties = {}) => {
  if (!isAnalyticsEnabled() || !POSTHOG_KEY) return;
  
  try {
    if (typeof window !== 'undefined' && window.posthog) {
      window.posthog.capture(event, {
        ...properties,
        // Add default properties
        $app_name: 'pepworkday-pipeline',
        $app_version: '1.0.0',
        $timestamp: new Date().toISOString(),
        $current_url: window.location.href
      });
      
      console.log('📈 PostHog Event:', event, properties);
    }
  } catch (error) {
    console.error('❌ PostHog tracking error:', error);
  }
};

/**
 * Combined event tracking (both GA4 and PostHog)
 * 
 * @param {string} eventName - The event name
 * @param {Object} data - Event data
 */
export const trackEvent = (eventName, data = {}) => {
  // Track in Google Analytics
  trackGAEvent(eventName, data);
  
  // Track in PostHog
  trackPostHogEvent(eventName, data);
};

/**
 * Track page views
 * 
 * @param {string} url - The page URL
 * @param {string} title - The page title
 */
export const trackPageView = (url, title) => {
  // Google Analytics page view
  if (isAnalyticsEnabled() && GA_MEASUREMENT_ID && typeof window !== 'undefined' && window.gtag) {
    window.gtag('config', GA_MEASUREMENT_ID, {
      page_location: url,
      page_title: title
    });
  }
  
  // PostHog page view
  if (isAnalyticsEnabled() && POSTHOG_KEY && typeof window !== 'undefined' && window.posthog) {
    window.posthog.capture('$pageview', {
      $current_url: url,
      $title: title
    });
  }
  
  console.log('📄 Page view tracked:', url, title);
};

/**
 * Identify user for analytics
 * 
 * @param {string} userId - Unique user identifier
 * @param {Object} traits - User traits/properties
 */
export const identifyUser = (userId, traits = {}) => {
  if (!isAnalyticsEnabled()) return;
  
  try {
    // PostHog user identification
    if (POSTHOG_KEY && typeof window !== 'undefined' && window.posthog) {
      window.posthog.identify(userId, {
        ...traits,
        $app_name: 'pepworkday-pipeline'
      });
    }
    
    // Google Analytics user ID
    if (GA_MEASUREMENT_ID && typeof window !== 'undefined' && window.gtag) {
      window.gtag('config', GA_MEASUREMENT_ID, {
        user_id: userId
      });
    }
    
    console.log('👤 User identified:', userId, traits);
  } catch (error) {
    console.error('❌ User identification error:', error);
  }
};

/**
 * Track dashboard-specific events
 */
export const dashboardEvents = {
  /**
   * Track chart interactions
   */
  chartViewed: (chartType, dataPoints) => {
    trackEvent('chart_viewed', {
      chart_type: chartType,
      data_points: dataPoints,
      category: 'dashboard'
    });
  },
  
  /**
   * Track data refresh events
   */
  dataRefreshed: (source, duration) => {
    trackEvent('data_refreshed', {
      data_source: source,
      refresh_duration_ms: duration,
      category: 'dashboard'
    });
  },
  
  /**
   * Track API errors
   */
  apiError: (endpoint, errorMessage) => {
    trackEvent('api_error', {
      endpoint: endpoint,
      error_message: errorMessage,
      category: 'error'
    });
  },
  
  /**
   * Track user interactions
   */
  buttonClicked: (buttonName, location) => {
    trackEvent('button_clicked', {
      button_name: buttonName,
      button_location: location,
      category: 'interaction'
    });
  },
  
  /**
   * Track performance metrics
   */
  performanceMetric: (metricName, value, unit) => {
    trackEvent('performance_metric', {
      metric_name: metricName,
      metric_value: value,
      metric_unit: unit,
      category: 'performance'
    });
  }
};

/**
 * Initialize analytics on app start
 */
export const initializeAnalytics = () => {
  if (!isAnalyticsEnabled()) {
    console.log('📊 Analytics disabled in development mode');
    return;
  }
  
  console.log('📊 Initializing analytics...');
  console.log(`   GA4: ${GA_MEASUREMENT_ID ? '✅ Configured' : '❌ Missing'}`);
  console.log(`   PostHog: ${POSTHOG_KEY ? '✅ Configured' : '❌ Missing'}`);
};
