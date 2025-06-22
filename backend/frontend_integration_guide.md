# Frontend Integration Guide

## 🎨 **Easy Frontend Integration**

Block D APIs are designed for seamless Next.js integration with minimal setup.

## **Chart Integration (Super Easy)**

```tsx
// components/FinWaveChart.tsx
import { useEffect, useState } from 'react';
import Plot from 'react-plotly.js';

interface ChartProps {
  type: 'revenue-trend' | 'expense-breakdown' | 'profit-margin' | 'kpi-dashboard';
  startDate: string;
  endDate: string;
  className?: string;
}

export function FinWaveChart({ type, startDate, endDate, className }: ChartProps) {
  const [chartData, setChartData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/api/charts/${type}?start_date=${startDate}&end_date=${endDate}`)
      .then(res => res.json())
      .then(data => {
        setChartData(data.plotly_data);
        setLoading(false);
      })
      .catch(() => setLoading(false));
  }, [type, startDate, endDate]);

  if (loading) return <div className="animate-pulse bg-gray-200 h-64 rounded"></div>;
  if (!chartData) return <div className="text-red-500">Chart failed to load</div>;

  return (
    <div className={className}>
      <Plot
        data={chartData.data}
        layout={{
          ...chartData.layout,
          autosize: true,
          margin: { t: 40, r: 20, b: 40, l: 60 }
        }}
        useResizeHandler
        style={{ width: "100%", height: "400px" }}
      />
    </div>
  );
}

// Usage - Drop anywhere in your app:
// <FinWaveChart type="revenue-trend" startDate="2024-01-01" endDate="2024-12-31" />
```

## **Dashboard Page Example**

```tsx
// pages/dashboard.tsx
import { FinWaveChart } from '../components/FinWaveChart';

export default function Dashboard() {
  const currentMonth = new Date().toISOString().slice(0, 7); // "2024-12"
  const startDate = `${currentMonth}-01`;
  const endDate = new Date().toISOString().slice(0, 10);

  return (
    <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 p-6">
      <FinWaveChart 
        type="revenue-trend" 
        startDate="2024-01-01" 
        endDate={endDate}
        className="bg-white p-4 rounded-lg shadow"
      />
      
      <FinWaveChart 
        type="expense-breakdown" 
        startDate={startDate} 
        endDate={endDate}
        className="bg-white p-4 rounded-lg shadow"
      />
      
      <div className="lg:col-span-2">
        <FinWaveChart 
          type="kpi-dashboard" 
          startDate={startDate} 
          endDate={endDate}
          className="bg-white p-4 rounded-lg shadow"
        />
      </div>
    </div>
  );
}
```

## **Financial Insights Widget**

```tsx
// components/InsightsWidget.tsx
import { useState } from 'react';

export function InsightsWidget({ startDate, endDate }: { startDate: string, endDate: string }) {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);

  const askQuestion = async () => {
    setLoading(true);
    try {
      const response = await fetch('/api/insight/analyze', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ question, start_date: startDate, end_date: endDate })
      });
      const data = await response.json();
      setAnswer(data);
    } catch (error) {
      console.error('Failed to get insights:', error);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="bg-white p-6 rounded-lg shadow">
      <h3 className="text-lg font-semibold mb-4">Ask About Your Finances</h3>
      
      <div className="flex gap-2 mb-4">
        <input
          type="text"
          value={question}
          onChange={(e) => setQuestion(e.target.value)}
          placeholder="Why are expenses higher this month?"
          className="flex-1 border rounded px-3 py-2"
        />
        <button
          onClick={askQuestion}
          disabled={loading || !question}
          className="bg-blue-500 text-white px-4 py-2 rounded disabled:opacity-50"
        >
          {loading ? 'Analyzing...' : 'Ask'}
        </button>
      </div>

      {answer && (
        <div className="border-t pt-4">
          <p className="font-medium mb-2">Analysis:</p>
          <p className="text-gray-700 mb-3">{answer.analysis.explanation}</p>
          
          {answer.recommendations?.length > 0 && (
            <div>
              <p className="font-medium mb-2">Recommendations:</p>
              <ul className="list-disc list-inside text-sm text-gray-600">
                {answer.recommendations.map((rec, i) => (
                  <li key={i}>{rec}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
}
```

## **Report Download Buttons**

```tsx
// components/ReportDownloads.tsx
export function ReportDownloads({ startDate, endDate }: { startDate: string, endDate: string }) {
  const downloadReport = (type: string, format: string = 'pdf') => {
    const url = format === 'pdf' 
      ? `/api/report/${type}?start_date=${startDate}&end_date=${endDate}`
      : `/api/export/${format}?start_date=${startDate}&end_date=${endDate}`;
    
    window.open(url, '_blank');
  };

  return (
    <div className="bg-white p-4 rounded-lg shadow">
      <h3 className="font-semibold mb-3">Download Reports</h3>
      
      <div className="grid grid-cols-2 gap-2">
        <button
          onClick={() => downloadReport('executive')}
          className="bg-blue-500 text-white px-3 py-2 rounded text-sm"
        >
          Executive Summary
        </button>
        
        <button
          onClick={() => downloadReport('detailed')}
          className="bg-green-500 text-white px-3 py-2 rounded text-sm"
        >
          Detailed Report
        </button>
        
        <button
          onClick={() => downloadReport('excel', 'excel')}
          className="bg-emerald-500 text-white px-3 py-2 rounded text-sm"
        >
          Excel Export
        </button>
        
        <button
          onClick={() => downloadReport('board-pack')}
          className="bg-purple-500 text-white px-3 py-2 rounded text-sm"
        >
          Board Pack
        </button>
      </div>
    </div>
  );
}
```

## **Complete Page Example**

```tsx
// pages/financial-analytics.tsx
import { FinWaveChart } from '../components/FinWaveChart';
import { InsightsWidget } from '../components/InsightsWidget';
import { ReportDownloads } from '../components/ReportDownloads';

export default function FinancialAnalytics() {
  const endDate = new Date().toISOString().slice(0, 10);
  const startDate = new Date(Date.now() - 90 * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);

  return (
    <div className="min-h-screen bg-gray-50 p-6">
      <div className="max-w-7xl mx-auto">
        <h1 className="text-3xl font-bold mb-8">Financial Analytics</h1>
        
        {/* Top row - KPI Dashboard */}
        <div className="mb-8">
          <FinWaveChart 
            type="kpi-dashboard" 
            startDate={startDate} 
            endDate={endDate}
            className="bg-white rounded-lg shadow-lg p-6"
          />
        </div>

        {/* Main content grid */}
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-6 mb-8">
          <div className="lg:col-span-2 space-y-6">
            <FinWaveChart 
              type="revenue-trend" 
              startDate={startDate} 
              endDate={endDate}
              className="bg-white rounded-lg shadow p-4"
            />
            
            <FinWaveChart 
              type="expense-breakdown" 
              startDate={startDate} 
              endDate={endDate}
              className="bg-white rounded-lg shadow p-4"
            />
          </div>
          
          <div className="space-y-6">
            <InsightsWidget startDate={startDate} endDate={endDate} />
            <ReportDownloads startDate={startDate} endDate={endDate} />
          </div>
        </div>
      </div>
    </div>
  );
}
```

## **Next.js API Route Setup**

```typescript
// pages/api/[...path].ts - Proxy to FinWave backend
import { NextApiRequest, NextApiResponse } from 'next';

export default async function handler(req: NextApiRequest, res: NextApiResponse) {
  const { path } = req.query;
  const apiPath = Array.isArray(path) ? path.join('/') : path;
  
  const backendUrl = `http://localhost:8000/${apiPath}`;
  const queryString = new URLSearchParams(req.query as any).toString();
  const fullUrl = queryString ? `${backendUrl}?${queryString}` : backendUrl;

  try {
    const response = await fetch(fullUrl, {
      method: req.method,
      headers: {
        'Content-Type': 'application/json',
        ...req.headers
      },
      body: req.method !== 'GET' ? JSON.stringify(req.body) : undefined
    });

    const data = await response.json();
    res.status(response.status).json(data);
  } catch (error) {
    res.status(500).json({ error: 'Backend request failed' });
  }
}
```

## **Required Dependencies**

```bash
npm install react-plotly.js plotly.js
npm install @types/plotly.js  # If using TypeScript
```

## **Why This Is Easy**

1. **📊 Drop-in Charts**: Just import `<FinWaveChart>` - no configuration needed
2. **🔌 Auto-formatting**: All chart data pre-formatted for Plotly
3. **📱 Responsive**: Charts automatically resize and adapt
4. **⚡ Fast**: Data served as JSON, renders instantly
5. **🎨 Customizable**: Full Plotly customization available
6. **📥 One-click Downloads**: PDF/Excel reports download directly
7. **🤖 AI Integration**: Ask questions in plain English
8. **📊 Real-time**: Data updates automatically from QuickBooks

## **Testing Frontend Integration**

```bash
# 1. Start FinWave backend
cd backend && uvicorn app.main:app --reload

# 2. In your Next.js project, test the API proxy:
curl "http://localhost:3000/api/charts/revenue-trend?start_date=2024-01-01&end_date=2024-12-31"

# 3. View in browser - charts should render immediately
```

The frontend integration is **plug-and-play** - just drop the components in and they work! 🚀