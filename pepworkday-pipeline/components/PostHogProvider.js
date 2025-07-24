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

  useEffect(() => {
    if (!isAnalyticsEnabled()) return;

    const handleRouteChange = (url) => {
      // Track page view with Google Analytics
      trackPageView(url, document.title);
    };

    // Track initial page view
    handleRouteChange(router.asPath);

    // Listen for route changes
    router.events.on('routeChangeComplete', handleRouteChange);

    return () => {
      router.events.off('routeChangeComplete', handleRouteChange);
    };
  }, [router]);

  return null;
}

/**
 * PostHog Provider Component (Temporarily Disabled)
 *
 * @param {Object} props - Component props
 * @param {React.ReactNode} props.children - Child components
 * @returns {JSX.Element} Simple wrapper without PostHog
 */
export default function PostHogProvider({ children }) {
  return (
    <>
      <PostHogPageViewTracker />
      {children}
    </>
  );
}

// PostHog temporarily disabled - will be re-enabled after build fixes

/**
 * Hook to access PostHog instance (temporarily disabled)
 *
 * @returns {null} Always returns null while PostHog is disabled
 */
export function usePostHogSafe() {
  return null; // PostHog temporarily disabled
}

/**
 * Higher-order component (temporarily disabled)
 *
 * @param {React.Component} WrappedComponent - Component to wrap
 * @param {string} componentName - Name for tracking purposes
 * @returns {React.Component} Wrapped component without tracking
 */
export function withPostHogTracking(WrappedComponent, componentName) {
  return function TrackedComponent(props) {
    return <WrappedComponent {...props} />;
  };
}
