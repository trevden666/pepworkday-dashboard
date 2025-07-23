/**
 * Summary Chart Component
 * 
 * React component that renders a Bar chart showing total jobs by address
 * using data from the Google Sheets Summary API endpoint.
 * 
 * Features:
 * - Fetches data from /api/summary endpoint
 * - Renders interactive Bar chart using Chart.js
 * - Handles loading states and errors
 * - Responsive design with PEPMove branding
 * - Automatic data refresh capability
 * 
 * @module SummaryChart
 * @author PEP Automation Team
 * @version 1.0.0
 */

import React, { useState, useEffect } from 'react';
import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend,
} from 'chart.js';
import { Bar } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  BarElement,
  Title,
  Tooltip,
  Legend
);

/**
 * Default chart configuration options
 */
const DEFAULT_CHART_OPTIONS = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'top',
      labels: {
        font: {
          family: 'Arial, sans-serif',
          size: 12
        }
      }
    },
    title: {
      display: true,
      text: 'PEPMove Jobs Summary by Address',
      font: {
        family: 'Arial, sans-serif',
        size: 16,
        weight: 'bold'
      },
      color: '#2563eb'
    },
    tooltip: {
      backgroundColor: 'rgba(0, 0, 0, 0.8)',
      titleColor: '#ffffff',
      bodyColor: '#ffffff',
      borderColor: '#2563eb',
      borderWidth: 1,
      callbacks: {
        label: function(context) {
          return `Total Jobs: ${context.parsed.y}`;
        }
      }
    }
  },
  scales: {
    x: {
      title: {
        display: true,
        text: 'Address',
        font: {
          family: 'Arial, sans-serif',
          size: 14,
          weight: 'bold'
        }
      },
      ticks: {
        maxRotation: 45,
        minRotation: 0,
        font: {
          size: 11
        }
      }
    },
    y: {
      title: {
        display: true,
        text: 'Total Jobs',
        font: {
          family: 'Arial, sans-serif',
          size: 14,
          weight: 'bold'
        }
      },
      beginAtZero: true,
      ticks: {
        precision: 0,
        font: {
          size: 11
        }
      }
    }
  }
};

/**
 * Generate chart colors based on data length
 * 
 * @param {number} count - Number of data points
 * @returns {Object} Object with backgroundColor and borderColor arrays
 */
function generateChartColors(count) {
  const colors = [
    { bg: 'rgba(37, 99, 235, 0.6)', border: 'rgba(37, 99, 235, 1)' },
    { bg: 'rgba(16, 185, 129, 0.6)', border: 'rgba(16, 185, 129, 1)' },
    { bg: 'rgba(245, 158, 11, 0.6)', border: 'rgba(245, 158, 11, 1)' },
    { bg: 'rgba(239, 68, 68, 0.6)', border: 'rgba(239, 68, 68, 1)' },
    { bg: 'rgba(139, 92, 246, 0.6)', border: 'rgba(139, 92, 246, 1)' },
    { bg: 'rgba(236, 72, 153, 0.6)', border: 'rgba(236, 72, 153, 1)' },
    { bg: 'rgba(14, 165, 233, 0.6)', border: 'rgba(14, 165, 233, 1)' },
    { bg: 'rgba(34, 197, 94, 0.6)', border: 'rgba(34, 197, 94, 1)' }
  ];
  
  const backgroundColor = [];
  const borderColor = [];
  
  for (let i = 0; i < count; i++) {
    const color = colors[i % colors.length];
    backgroundColor.push(color.bg);
    borderColor.push(color.border);
  }
  
  return { backgroundColor, borderColor };
}

/**
 * Process raw summary data into chart format
 * 
 * @param {Array} rawData - Raw data from API
 * @returns {Object} Chart.js compatible data object
 */
function processChartData(rawData) {
  if (!rawData || rawData.length === 0) {
    return {
      labels: [],
      datasets: [{
        label: 'Total Jobs',
        data: [],
        backgroundColor: [],
        borderColor: [],
        borderWidth: 2
      }]
    };
  }
  
  // Extract addresses (Column A) and job counts (Column B)
  // Assuming first column is address and second column is job count
  const chartData = rawData
    .filter(row => {
      // Filter out rows with empty address or invalid job count
      const address = Object.values(row)[0];
      const jobCount = Object.values(row)[1];
      return address && jobCount !== null && jobCount !== undefined && !isNaN(Number(jobCount));
    })
    .map(row => {
      const values = Object.values(row);
      return {
        address: String(values[0] || 'Unknown'),
        jobCount: Number(values[1] || 0)
      };
    })
    .sort((a, b) => b.jobCount - a.jobCount); // Sort by job count descending
  
  const labels = chartData.map(item => item.address);
  const data = chartData.map(item => item.jobCount);
  const colors = generateChartColors(data.length);
  
  return {
    labels,
    datasets: [{
      label: 'Total Jobs',
      data,
      backgroundColor: colors.backgroundColor,
      borderColor: colors.borderColor,
      borderWidth: 2,
      borderRadius: 4,
      borderSkipped: false,
    }]
  };
}

/**
 * SummaryChart React Component
 * 
 * @param {Object} props - Component props
 * @param {number} [props.height=400] - Chart height in pixels
 * @param {Object} [props.options] - Additional Chart.js options
 * @param {boolean} [props.autoRefresh=false] - Enable automatic data refresh
 * @param {number} [props.refreshInterval=300000] - Refresh interval in milliseconds (default: 5 minutes)
 * @returns {JSX.Element} SummaryChart component
 */
export default function SummaryChart({ 
  height = 400, 
  options = {}, 
  autoRefresh = false, 
  refreshInterval = 300000 
}) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [lastUpdated, setLastUpdated] = useState(null);
  
  /**
   * Fetch summary data from API
   */
  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      
      console.log('📊 Fetching summary data for chart...');
      
      const response = await fetch('/api/summary');
      const result = await response.json();
      
      if (!response.ok) {
        throw new Error(result.error || `HTTP ${response.status}`);
      }
      
      if (!result.success) {
        throw new Error(result.error || 'API request failed');
      }
      
      console.log(`✅ Received ${result.data.length} rows for chart`);
      
      const chartData = processChartData(result.data);
      setData(chartData);
      setLastUpdated(new Date());
      
    } catch (err) {
      console.error('❌ Failed to fetch chart data:', err.message);
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };
  
  // Initial data fetch
  useEffect(() => {
    fetchData();
  }, []);
  
  // Auto-refresh setup
  useEffect(() => {
    if (!autoRefresh) return;
    
    const interval = setInterval(fetchData, refreshInterval);
    return () => clearInterval(interval);
  }, [autoRefresh, refreshInterval]);
  
  // Merge default options with custom options
  const chartOptions = {
    ...DEFAULT_CHART_OPTIONS,
    ...options
  };
  
  // Loading state
  if (loading) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '18px', marginBottom: '10px' }}>📊</div>
          <div>Loading chart data...</div>
        </div>
      </div>
    );
  }
  
  // Error state
  if (error) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center', color: '#dc2626' }}>
          <div style={{ fontSize: '18px', marginBottom: '10px' }}>❌</div>
          <div style={{ fontWeight: 'bold', marginBottom: '5px' }}>Failed to load chart</div>
          <div style={{ fontSize: '14px', marginBottom: '10px' }}>{error}</div>
          <button 
            onClick={fetchData}
            style={{
              padding: '8px 16px',
              backgroundColor: '#2563eb',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer'
            }}
          >
            Retry
          </button>
        </div>
      </div>
    );
  }
  
  // No data state
  if (!data || data.labels.length === 0) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        <div style={{ textAlign: 'center' }}>
          <div style={{ fontSize: '18px', marginBottom: '10px' }}>📈</div>
          <div>No data available</div>
          <button 
            onClick={fetchData}
            style={{
              padding: '8px 16px',
              backgroundColor: '#2563eb',
              color: 'white',
              border: 'none',
              borderRadius: '4px',
              cursor: 'pointer',
              marginTop: '10px'
            }}
          >
            Refresh
          </button>
        </div>
      </div>
    );
  }
  
  // Render chart
  return (
    <div style={{ height }}>
      <div style={{ height: '100%', position: 'relative' }}>
        <Bar data={data} options={chartOptions} />
        {lastUpdated && (
          <div style={{ 
            position: 'absolute', 
            bottom: '5px', 
            right: '10px', 
            fontSize: '12px', 
            color: '#6b7280',
            backgroundColor: 'rgba(255, 255, 255, 0.8)',
            padding: '2px 6px',
            borderRadius: '3px'
          }}>
            Updated: {lastUpdated.toLocaleTimeString()}
          </div>
        )}
      </div>
    </div>
  );
}
