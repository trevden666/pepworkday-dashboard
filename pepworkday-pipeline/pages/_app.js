/**
 * Next.js App Component
 * 
 * Root application component that provides:
 * - Analytics integration (Google Analytics 4 + PostHog)
 * - Global styles and providers
 * - Error boundaries
 * - Performance monitoring
 * 
 * @module pages/_app
 * @author PEP Automation Team
 * @version 1.0.0
 */

import React, { useEffect } from 'react';
import { useRouter } from 'next/router';
import Script from 'next/script';
import PostHogProvider from '../components/PostHogProvider';
import { 
  GA_MEASUREMENT_ID, 
  isAnalyticsEnabled, 
  initializeAnalytics,
  trackPageView,
  dashboardEvents
} from '../lib/analytics';

/**
 * Global CSS styles
 */
const globalStyles = `
  * {
    box-sizing: border-box;
    margin: 0;
    padding: 0;
  }
  
  html, body {
    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif;
    line-height: 1.6;
    color: #333;
    background-color: #f8fafc;
  }
  
  a {
    color: #2563eb;
    text-decoration: none;
  }
  
  a:hover {
    text-decoration: underline;
  }
  
  button {
    cursor: pointer;
    border: none;
    border-radius: 4px;
    font-family: inherit;
    font-size: 14px;
    transition: all 0.2s ease;
  }
  
  button:disabled {
    cursor: not-allowed;
    opacity: 0.6;
  }
  
  input, textarea, select {
    font-family: inherit;
    font-size: 14px;
    border: 1px solid #d1d5db;
    border-radius: 4px;
    padding: 8px 12px;
  }
  
  input:focus, textarea:focus, select:focus {
    outline: none;
    border-color: #2563eb;
    box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
  }
  
  .sr-only {
    position: absolute;
    width: 1px;
    height: 1px;
    padding: 0;
    margin: -1px;
    overflow: hidden;
    clip: rect(0, 0, 0, 0);
    white-space: nowrap;
    border: 0;
  }
`;

/**
 * Google Analytics Page View Tracker
 */
function GAPageViewTracker() {
  const router = useRouter();
  
  useEffect(() => {
    if (!isAnalyticsEnabled() || !GA_MEASUREMENT_ID) return;
    
    const handleRouteChange = (url) => {
      // Track page view with Google Analytics
      if (typeof window !== 'undefined' && window.gtag) {
        window.gtag('config', GA_MEASUREMENT_ID, {
          page_location: url,
          page_title: document.title,
        });
      }
      
      // Also track with our unified function
      trackPageView(url, document.title);
    };
    
    // Track initial page view
    handleRouteChange(window.location.href);
    
    // Listen for route changes
    router.events.on('routeChangeComplete', handleRouteChange);
    
    return () => {
      router.events.off('routeChangeComplete', handleRouteChange);
    };
  }, [router]);
  
  return null;
}

/**
 * Performance Monitor Component
 */
function PerformanceMonitor() {
  useEffect(() => {
    if (!isAnalyticsEnabled()) return;
    
    // Monitor Core Web Vitals
    if (typeof window !== 'undefined' && 'PerformanceObserver' in window) {
      try {
        // Largest Contentful Paint (LCP)
        const lcpObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          const lastEntry = entries[entries.length - 1];
          dashboardEvents.performanceMetric('LCP', Math.round(lastEntry.startTime), 'ms');
        });
        lcpObserver.observe({ entryTypes: ['largest-contentful-paint'] });
        
        // First Input Delay (FID)
        const fidObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry) => {
            dashboardEvents.performanceMetric('FID', Math.round(entry.processingStart - entry.startTime), 'ms');
          });
        });
        fidObserver.observe({ entryTypes: ['first-input'] });
        
        // Cumulative Layout Shift (CLS)
        let clsValue = 0;
        const clsObserver = new PerformanceObserver((list) => {
          const entries = list.getEntries();
          entries.forEach((entry) => {
            if (!entry.hadRecentInput) {
              clsValue += entry.value;
            }
          });
          dashboardEvents.performanceMetric('CLS', Math.round(clsValue * 1000) / 1000, 'score');
        });
        clsObserver.observe({ entryTypes: ['layout-shift'] });
        
      } catch (error) {
        console.error('❌ Performance monitoring error:', error);
      }
    }
  }, []);
  
  return null;
}

/**
 * Error Boundary Component
 */
class ErrorBoundary extends React.Component {
  constructor(props) {
    super(props);
    this.state = { hasError: false, error: null };
  }
  
  static getDerivedStateFromError(error) {
    return { hasError: true, error };
  }
  
  componentDidCatch(error, errorInfo) {
    console.error('❌ Application error:', error, errorInfo);
    
    // Track error with analytics
    if (isAnalyticsEnabled()) {
      dashboardEvents.apiError('app_error', error.message);
    }
  }
  
  render() {
    if (this.state.hasError) {
      return (
        <div style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          padding: '2rem',
          textAlign: 'center'
        }}>
          <div>
            <h1 style={{ fontSize: '2rem', marginBottom: '1rem', color: '#dc2626' }}>
              ⚠️ Something went wrong
            </h1>
            <p style={{ marginBottom: '1rem', color: '#6b7280' }}>
              We're sorry, but something unexpected happened.
            </p>
            <button
              onClick={() => window.location.reload()}
              style={{
                padding: '0.75rem 1.5rem',
                backgroundColor: '#2563eb',
                color: 'white',
                borderRadius: '0.5rem',
                fontSize: '1rem'
              }}
            >
              Reload Page
            </button>
          </div>
        </div>
      );
    }
    
    return this.props.children;
  }
}

/**
 * Main App Component
 * 
 * @param {Object} props - App props
 * @param {React.Component} props.Component - Page component
 * @param {Object} props.pageProps - Page props
 * @returns {JSX.Element} App component
 */
export default function App({ Component, pageProps }) {
  useEffect(() => {
    // Initialize analytics
    initializeAnalytics();
    
    // Track app initialization
    if (isAnalyticsEnabled()) {
      dashboardEvents.performanceMetric('app_load_time', performance.now(), 'ms');
    }
  }, []);
  
  return (
    <>
      {/* Global Styles */}
      <style jsx global>{globalStyles}</style>
      
      {/* Google Analytics 4 */}
      {isAnalyticsEnabled() && GA_MEASUREMENT_ID && (
        <>
          <Script
            src={`https://www.googletagmanager.com/gtag/js?id=${GA_MEASUREMENT_ID}`}
            strategy="afterInteractive"
          />
          <Script
            id="google-analytics"
            strategy="afterInteractive"
            dangerouslySetInnerHTML={{
              __html: `
                window.dataLayer = window.dataLayer || [];
                function gtag(){dataLayer.push(arguments);}
                gtag('js', new Date());
                gtag('config', '${GA_MEASUREMENT_ID}', {
                  page_location: window.location.href,
                  page_title: document.title,
                  // Privacy settings
                  anonymize_ip: true,
                  allow_google_signals: false,
                  allow_ad_personalization_signals: false
                });
              `,
            }}
          />
        </>
      )}
      
      {/* Error Boundary */}
      <ErrorBoundary>
        {/* PostHog Provider */}
        <PostHogProvider>
          {/* Performance Monitoring */}
          <PerformanceMonitor />
          
          {/* Google Analytics Page Tracking */}
          <GAPageViewTracker />
          
          {/* Main App Content */}
          <Component {...pageProps} />
        </PostHogProvider>
      </ErrorBoundary>
    </>
  );
}
