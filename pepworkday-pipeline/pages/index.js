/**
 * Home Page - Redirect to Dashboard
 * 
 * Simple home page that redirects users to the main dashboard.
 * This provides a clean entry point for the application.
 * 
 * @module pages/index
 * @author PEP Automation Team
 * @version 1.0.0
 */

import { useEffect } from 'react';
import { useRouter } from 'next/router';
import Head from 'next/head';

/**
 * Home page component with automatic redirect
 * 
 * @returns {JSX.Element} Home page
 */
export default function Home() {
  const router = useRouter();
  
  useEffect(() => {
    // Redirect to dashboard after component mounts
    router.push('/dashboard');
  }, [router]);
  
  return (
    <>
      <Head>
        <title>PepWorkday Pipeline</title>
        <meta name="description" content="PepWorkday Pipeline - Automated dispatch and Samsara data processing" />
        <meta name="viewport" content="width=device-width, initial-scale=1" />
        <link rel="icon" href="/favicon.ico" />
      </Head>
      
      <div style={{
        minHeight: '100vh',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'center',
        backgroundColor: '#f8fafc',
        fontFamily: 'Arial, sans-serif'
      }}>
        <div style={{
          textAlign: 'center',
          padding: '2rem',
          backgroundColor: 'white',
          borderRadius: '0.5rem',
          boxShadow: '0 4px 6px rgba(0,0,0,0.1)',
          border: '1px solid #e5e7eb'
        }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>🚛</div>
          <h1 style={{ 
            margin: '0 0 1rem 0', 
            color: '#1f2937', 
            fontSize: '1.5rem',
            fontWeight: 'bold'
          }}>
            PepWorkday Pipeline
          </h1>
          <p style={{ 
            margin: '0 0 1.5rem 0', 
            color: '#6b7280',
            fontSize: '1rem'
          }}>
            Redirecting to dashboard...
          </p>
          <div style={{
            display: 'inline-block',
            width: '2rem',
            height: '2rem',
            border: '2px solid #e5e7eb',
            borderTop: '2px solid #2563eb',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite'
          }}></div>
        </div>
      </div>
      
      <style jsx>{`
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
      `}</style>
    </>
  );
}
