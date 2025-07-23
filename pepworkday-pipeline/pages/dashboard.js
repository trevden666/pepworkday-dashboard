/**
 * PepWorkday Dashboard Page
 * 
 * Main dashboard page that demonstrates the integration of:
 * - Google Sheets API data fetching
 * - Chart.js visualization with SummaryChart component
 * - Real-time data updates
 * - PEPMove branding and styling
 * 
 * @module pages/dashboard
 * @author PEP Automation Team
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';
import Head from 'next/head';
import Image from 'next/image';
import SummaryChart from '../components/SummaryChart';
import { dashboardEvents, trackEvent } from '../lib/analytics';
import { usePostHogSafe } from '../components/PostHogProvider';

/**
 * Dashboard page component with ISR and analytics
 *
 * @param {Object} props - Page props from getStaticProps
 * @param {Object} props.initialData - Initial dashboard data
 * @param {string} props.buildTime - Build timestamp
 * @returns {JSX.Element} Dashboard page
 */
export default function Dashboard({ initialData, buildTime }) {
  const [apiStatus, setApiStatus] = useState('checking');
  const [lastRefresh, setLastRefresh] = useState(null);
  const posthog = usePostHogSafe();
  
  /**
   * Check API health status with analytics tracking
   */
  const checkApiStatus = async () => {
    const startTime = performance.now();

    try {
      dashboardEvents.buttonClicked('refresh_api_status', 'header');

      const response = await fetch('/api/summary');
      const result = await response.json();

      const duration = performance.now() - startTime;

      if (response.ok && result.success) {
        setApiStatus('healthy');
        dashboardEvents.dataRefreshed('api_summary', duration);
      } else {
        setApiStatus('error');
        dashboardEvents.apiError('/api/summary', result.error || 'Unknown error');
      }
    } catch (error) {
      setApiStatus('error');
      dashboardEvents.apiError('/api/summary', error.message);
    }

    setLastRefresh(new Date());
  };
  
  // Check API status on component mount and track page view
  useEffect(() => {
    checkApiStatus();

    // Track dashboard page view
    trackEvent('dashboard_viewed', {
      build_time: buildTime,
      has_initial_data: !!initialData,
      user_agent: navigator.userAgent,
    });

    // Track with PostHog if available
    if (posthog) {
      posthog.capture('dashboard_page_viewed', {
        build_time: buildTime,
        initial_data_available: !!initialData,
      });
    }
  }, [buildTime, initialData, posthog]);
  
  /**
   * Get status indicator styling
   */
  const getStatusStyle = () => {
    switch (apiStatus) {
      case 'healthy':
        return { color: '#10b981', backgroundColor: '#d1fae5' };
      case 'error':
        return { color: '#ef4444', backgroundColor: '#fee2e2' };
      default:
        return { color: '#f59e0b', backgroundColor: '#fef3c7' };
    }
  };
  
  /**
   * Get status text
   */
  const getStatusText = () => {
    switch (apiStatus) {
      case 'healthy':
        return '✅ API Healthy';
      case 'error':
        return '❌ API Error';
      default:
        return '🔄 Checking...';
    }
  };
  
  return (
    <>
      <Head>
        <title>PepWorkday Dashboard - Job Summary</title>
        <meta name="description" content="PepWorkday Pipeline Dashboard showing job summary data from Google Sheets" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      
      <div style={{ 
        minHeight: '100vh', 
        backgroundColor: '#f8fafc',
        fontFamily: 'Arial, sans-serif'
      }}>
        {/* Header */}
        <header
          data-testid="dashboard-header"
          style={{
            backgroundColor: '#2563eb',
            color: 'white',
            padding: '1rem 2rem',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)'
          }}>
          <div style={{ 
            maxWidth: '1200px', 
            margin: '0 auto',
            display: 'flex',
            justifyContent: 'space-between',
            alignItems: 'center'
          }}>
            <div>
              <h1 style={{ margin: 0, fontSize: '1.5rem', fontWeight: 'bold' }}>
                🚛 PepWorkday Dashboard
              </h1>
              <p style={{ margin: '0.25rem 0 0 0', opacity: 0.9, fontSize: '0.9rem' }}>
                Real-time job summary and analytics
              </p>
            </div>
            
            <div style={{
              display: 'flex',
              alignItems: 'center',
              gap: '1rem'
            }}>
              {/* API Status Indicator */}
              <div
                data-testid="api-status"
                style={{
                  padding: '0.5rem 1rem',
                  borderRadius: '0.5rem',
                  fontSize: '0.875rem',
                  fontWeight: '500',
                  ...getStatusStyle()
                }}>
                {getStatusText()}
              </div>
              
              {/* Refresh Button */}
              <button
                onClick={checkApiStatus}
                style={{
                  padding: '0.5rem 1rem',
                  backgroundColor: 'rgba(255,255,255,0.2)',
                  color: 'white',
                  border: '1px solid rgba(255,255,255,0.3)',
                  borderRadius: '0.5rem',
                  cursor: 'pointer',
                  fontSize: '0.875rem',
                  transition: 'background-color 0.2s'
                }}
                onMouseOver={(e) => e.target.style.backgroundColor = 'rgba(255,255,255,0.3)'}
                onMouseOut={(e) => e.target.style.backgroundColor = 'rgba(255,255,255,0.2)'}
              >
                🔄 Refresh
              </button>
            </div>
          </div>
        </header>
        
        {/* Main Content */}
        <main style={{ 
          maxWidth: '1200px', 
          margin: '0 auto', 
          padding: '2rem'
        }}>
          {/* Dashboard Stats */}
          <div
            data-testid="dashboard-stats"
            style={{
              display: 'grid',
              gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
              gap: '1rem',
              marginBottom: '2rem'
            }}>
            <div
              data-testid="stats-card"
              style={{
                backgroundColor: 'white',
                padding: '1.5rem',
                borderRadius: '0.5rem',
                boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
                border: '1px solid #e5e7eb'
              }}>
              <h3 style={{ margin: '0 0 0.5rem 0', color: '#374151', fontSize: '0.875rem', fontWeight: '600' }}>
                📊 DATA SOURCE
              </h3>
              <p style={{ margin: 0, fontSize: '1.25rem', fontWeight: 'bold', color: '#1f2937' }}>
                Google Sheets
              </p>
              <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem', color: '#6b7280' }}>
                Summary!A1:Z100 Range
              </p>
            </div>
            
            <div style={{
              backgroundColor: 'white',
              padding: '1.5rem',
              borderRadius: '0.5rem',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              border: '1px solid #e5e7eb'
            }}>
              <h3 style={{ margin: '0 0 0.5rem 0', color: '#374151', fontSize: '0.875rem', fontWeight: '600' }}>
                🔄 LAST REFRESH
              </h3>
              <p style={{ margin: 0, fontSize: '1.25rem', fontWeight: 'bold', color: '#1f2937' }}>
                {lastRefresh ? lastRefresh.toLocaleTimeString() : 'Never'}
              </p>
              <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem', color: '#6b7280' }}>
                Auto-refresh available
              </p>
            </div>
            
            <div style={{
              backgroundColor: 'white',
              padding: '1.5rem',
              borderRadius: '0.5rem',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              border: '1px solid #e5e7eb'
            }}>
              <h3 style={{ margin: '0 0 0.5rem 0', color: '#374151', fontSize: '0.875rem', fontWeight: '600' }}>
                🏢 ORGANIZATION
              </h3>
              <p style={{ margin: 0, fontSize: '1.25rem', fontWeight: 'bold', color: '#1f2937' }}>
                PEPMove
              </p>
              <p style={{ margin: '0.25rem 0 0 0', fontSize: '0.875rem', color: '#6b7280' }}>
                ID: 5005620
              </p>
            </div>
          </div>
          
          {/* Chart Section */}
          <div
            data-testid="dashboard-chart"
            style={{
              backgroundColor: 'white',
              padding: '2rem',
              borderRadius: '0.5rem',
              boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
              border: '1px solid #e5e7eb'
            }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '1.5rem'
            }}>
              <div>
                <h2 style={{ margin: 0, color: '#1f2937', fontSize: '1.25rem', fontWeight: 'bold' }}>
                  📈 Jobs by Address
                </h2>
                <p style={{ margin: '0.25rem 0 0 0', color: '#6b7280', fontSize: '0.875rem' }}>
                  Total job count visualization from Google Sheets data
                </p>
              </div>
              
              <div style={{
                display: 'flex',
                gap: '0.5rem',
                alignItems: 'center'
              }}>
                <label style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.5rem',
                  fontSize: '0.875rem',
                  color: '#374151'
                }}>
                  <input
                    type="checkbox"
                    defaultChecked={false}
                    style={{ margin: 0 }}
                  />
                  Auto-refresh (5min)
                </label>
              </div>
            </div>
            
            {/* Chart Component */}
            <div data-testid="summary-chart">
              <SummaryChart
                height={500}
                autoRefresh={false}
                refreshInterval={300000}
              />
            </div>
          </div>
          
          {/* Footer Info */}
          <div style={{
            marginTop: '2rem',
            padding: '1rem',
            backgroundColor: 'white',
            borderRadius: '0.5rem',
            border: '1px solid #e5e7eb',
            textAlign: 'center'
          }}>
            <p style={{ 
              margin: 0, 
              fontSize: '0.875rem', 
              color: '#6b7280' 
            }}>
              🔧 Powered by Next.js, Chart.js, and Google Sheets API | 
              🚀 Deployed on Vercel | 
              ☁️ GCP Integration
            </p>
          </div>
        </main>
      </div>
    </>
  );
}

/**
 * Get Static Props for ISR (Incremental Static Regeneration)
 * Revalidates every 5 minutes (300 seconds)
 */
export async function getStaticProps() {
  try {
    // In a real implementation, you might fetch some initial data here
    // For now, we'll just provide build-time information
    const buildTime = new Date().toISOString();

    // You could fetch initial dashboard data here if needed
    // const initialData = await fetchDashboardData();

    return {
      props: {
        initialData: null, // Replace with actual data if needed
        buildTime,
      },
      // Revalidate every 5 minutes
      revalidate: 300,
    };
  } catch (error) {
    console.error('❌ Error in getStaticProps:', error);

    return {
      props: {
        initialData: null,
        buildTime: new Date().toISOString(),
      },
      revalidate: 300,
    };
  }
}
