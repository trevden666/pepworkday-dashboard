/**
 * PostHog Analytics Provider
 * 
 * React component that initializes and provides PostHog analytics
 * throughout the application with proper error handling and
 * environment-aware configuration.
 * 
 * @module components/PostHogProvider
 * @author PEP Automation Team
 * @version 1.0.0
 */

import { useEffect } from 'react';
import { useRouter } from 'next/router';
import { PostHogProvider as PHProvider, usePostHog } from '@posthog/react';
import { POSTHOG_KEY, POSTHOG_HOST, isAnalyticsEnabled, trackPageView } from '../lib/analytics';

/**
 * PostHog configuration options
 */
const postHogConfig = {
  api_host: POSTHOG_HOST,
  // Privacy and compliance settings
  opt_out_capturing_by_default: false,
  capture_pageview: false, // We'll handle this manually
  capture_pageleave: true,
  
  // Performance settings
  loaded: (posthog) => {
    if (process.env.NODE_ENV === 'development') {
      posthog.debug(false); // Disable debug in development
    }
  },
  
  // Feature flags and experiments
  bootstrap: {
    distinctID: 'anonymous',
  },
  
  // Session recording (disabled by default for privacy)
  disable_session_recording: process.env.NEXT_PUBLIC_POSTHOG_DISABLE_SESSION_RECORDING !== 'false',
  
  // Autocapture settings
  autocapture: {
    // Capture clicks on buttons, links, and form elements
    dom_event_allowlist: ['click', 'change', 'submit'],
    // Don't capture sensitive form fields
    mask_all_element_attributes: false,
    mask_all_text: false,
  },
  
  // Cross-domain tracking
  cross_subdomain_cookie: false,
  
  // Persistence settings
  persistence: 'localStorage+cookie',
  
  // Custom properties to include with all events
  property_blacklist: ['$initial_referrer', '$initial_referring_domain'],
};

/**
 * PostHog Page View Tracker
 * Handles automatic page view tracking with Next.js router
 */
function PostHogPageViewTracker() {
  const router = useRouter();
  const posthog = usePostHog();
  
  useEffect(() => {
    if (!isAnalyticsEnabled() || !posthog) return;
    
    const handleRouteChange = (url) => {
      // Track page view with PostHog
      trackPageView(url, document.title);
    };
    
    // Track initial page view
    handleRouteChange(router.asPath);
    
    // Listen for route changes
    router.events.on('routeChangeComplete', handleRouteChange);
    
    return () => {
      router.events.off('routeChangeComplete', handleRouteChange);
    };
  }, [router, posthog]);
  
  return null;
}

/**
 * PostHog Provider Component
 * 
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child components
 * @returns {JSX.Element} PostHog provider wrapper
 */
export default function PostHogProvider({ children }) {
  // Don't initialize PostHog if analytics is disabled or key is missing
  if (!isAnalyticsEnabled() || !POSTHOG_KEY) {
    console.log('📈 PostHog disabled: Analytics not enabled or key missing');
    return (
      <>
        {children}
      </>
    );
  }
  
  return (
    <PHProvider 
      apiKey={POSTHOG_KEY} 
      options={postHogConfig}
    >
      <PostHogPageViewTracker />
      <PostHogInitializer />
      {children}
    </PHProvider>
  );
}

/**
 * PostHog Initializer Component
 * Handles initial setup and configuration
 */
function PostHogInitializer() {
  const posthog = usePostHog();
  
  useEffect(() => {
    if (!posthog) return;
    
    try {
      // Set up custom properties
      posthog.register({
        app_name: 'pepworkday-pipeline',
        app_version: '1.0.0',
        environment: process.env.NODE_ENV,
        deployment_url: process.env.NEXT_PUBLIC_VERCEL_URL || 'localhost',
      });
      
      // Identify organization context
      posthog.group('organization', 'pepmove', {
        name: 'PEPMove',
        organization_id: '5005620',
        group_id: '129031',
      });
      
      console.log('📈 PostHog initialized successfully');
      
      // Track initialization event
      posthog.capture('app_initialized', {
        initialization_time: new Date().toISOString(),
        user_agent: navigator.userAgent,
        screen_resolution: `${screen.width}x${screen.height}`,
        timezone: Intl.DateTimeFormat().resolvedOptions().timeZone,
      });
      
    } catch (error) {
      console.error('❌ PostHog initialization error:', error);
    }
  }, [posthog]);
  
  return null;
}

/**
 * Hook to access PostHog instance with error handling
 * 
 * @returns {Object|null} PostHog instance or null if not available
 */
export function usePostHogSafe() {
  try {
    const posthog = usePostHog();
    return isAnalyticsEnabled() ? posthog : null;
  } catch (error) {
    console.error('❌ PostHog hook error:', error);
    return null;
  }
}

/**
 * Higher-order component to wrap components with PostHog tracking
 * 
 * @param {React.Component} WrappedComponent - Component to wrap
 * @param {string} componentName - Name for tracking purposes
 * @returns {React.Component} Wrapped component with tracking
 */
export function withPostHogTracking(WrappedComponent, componentName) {
  return function TrackedComponent(props) {
    const posthog = usePostHogSafe();
    
    useEffect(() => {
      if (posthog) {
        posthog.capture('component_mounted', {
          component_name: componentName,
          props: Object.keys(props),
        });
      }
    }, [posthog, props]);
    
    return <WrappedComponent {...props} />;
  };
}
