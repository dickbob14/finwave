# Variance UI Components

## Overview

The variance UI provides real-time monitoring and alerting for financial metrics that deviate from expected values.

## Components

### VarianceBadge
A small indicator that shows when a metric has an active variance alert.

**Features:**
- ✅ No indicator when metrics are within thresholds
- ⚠️ Yellow warning icon for non-critical variances
- 🛑 Red pulsing icon for critical variances
- Tooltip on hover showing alert message
- Click to open detailed modal with AI analysis

**Usage:**
```tsx
<VarianceBadge 
  workspaceId="acme-corp"
  metricId="revenue"
/>
```

### KPICardWithVariance
Enhanced KPI card that integrates variance monitoring.

**Usage:**
```tsx
<KPICardWithVariance
  title="Revenue"
  value={1250000}
  metricId="revenue"
  workspaceId="acme-corp"
  format="currency"
  trend="up"
  trendValue="+12.5%"
/>
```

### VarianceAlerts Page
Full alert management interface with filtering, acknowledgment, and resolution.

**Features:**
- Filter by status (active, acknowledged, resolved)
- Filter by severity (critical, warning, info)
- Manual variance check trigger
- Alert acknowledgment with notes
- Bulk alert management

## Integration

1. **Add to existing dashboards:**
```tsx
// Replace existing KPI cards
<KPICardWithVariance ... />
```

2. **Add alerts page to navigation:**
```tsx
<Route path="/alerts" element={<VarianceAlerts workspaceId={workspace} />} />
```

3. **Configure alert polling:**
- Badges poll every 30 seconds
- Dashboard summary polls every 60 seconds
- Manual refresh available

## Alert Lifecycle

1. **Detection**: Variance watcher checks rules hourly
2. **Display**: Red/yellow badges appear on affected metrics
3. **Investigation**: Click badge to see details + AI analysis
4. **Action**: Acknowledge to suppress badge, resolve when fixed
5. **History**: All alerts tracked for audit trail

## Customization

- Adjust polling intervals in component props
- Modify severity colors in component styles
- Add custom alert actions in modal footer
- Extend with notification preferences

## Demo Flow

1. Navigate to dashboard → See normal metrics
2. Trigger test alert via API or wait for scheduled check
3. Red dot appears on affected metric
4. Click red dot → Modal shows variance details + AI insight
5. Acknowledge alert → Badge changes to acknowledged state
6. Resolve issue → Mark resolved → Badge disappears

This creates the "oh wow" moment when stakeholders see proactive monitoring in action.