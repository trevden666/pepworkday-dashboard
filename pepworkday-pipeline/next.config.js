/**
 * Next.js Configuration
 * 
 * Configuration for the PepWorkday Pipeline Next.js application
 * with optimizations for Vercel deployment and GCP integration.
 * 
 * @module next.config
 * @author PEP Automation Team
 * @version 1.0.0
 */

/** @type {import('next').NextConfig} */
const nextConfig = {
  // Enable React strict mode for better development experience
  reactStrictMode: true,
  
  // Enable SWC minification for better performance
  swcMinify: true,
  
  // Optimize images
  images: {
    domains: ['storage.googleapis.com'],
    formats: ['image/webp', 'image/avif'],
  },
  
  // Environment variables to expose to the browser
  env: {
    CUSTOM_KEY: 'pepworkday-pipeline',
  },
  
  // API routes configuration
  async rewrites() {
    return [
      {
        source: '/dashboard',
        destination: '/pages/dashboard',
      },
    ];
  },
  
  // Headers for security and caching
  async headers() {
    return [
      {
        source: '/api/:path*',
        headers: [
          {
            key: 'Access-Control-Allow-Origin',
            value: '*',
          },
          {
            key: 'Access-Control-Allow-Methods',
            value: 'GET, POST, PUT, DELETE, OPTIONS',
          },
          {
            key: 'Access-Control-Allow-Headers',
            value: 'Content-Type, Authorization',
          },
          {
            key: 'Cache-Control',
            value: 's-maxage=300, stale-while-revalidate=60',
          },
        ],
      },
    ];
  },
  
  // Webpack configuration for ES modules compatibility
  webpack: (config, { isServer }) => {
    // Handle ES modules in Node.js environment
    if (isServer) {
      config.externals = [...config.externals, 'googleapis'];
    }
    
    return config;
  },
  
  // Experimental features
  experimental: {
    // Enable server components (if using Next.js 13+)
    appDir: false,
  },
  
  // Output configuration for Vercel
  output: 'standalone',
  
  // Disable x-powered-by header
  poweredByHeader: false,
  
  // Compression
  compress: true,
  
  // Trailing slash handling
  trailingSlash: false,
};

module.exports = nextConfig;
