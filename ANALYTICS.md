# Analytics & Intelligence Module

## Overview

The **Analytics** module provides real-time insights into emissions data with automatic anomaly detection, trend analysis, and interactive dashboards. It transforms raw emission records into actionable intelligence.

## Key Features

### 📊 **Real-time Dashboard**
- **KPI Cards**: Total emissions by scope (1, 2, 3), record counts, and targets
- **Breakdown Charts**: Visualize emissions by source type or scope with percentages
- **Trend Charts**: Track emissions over time with daily/monthly aggregations
- **Drill-down**: Click charts to filter detailed records for deeper analysis

### 🚨 **Anomaly Detection**
Automatically detects suspicious patterns:
- **Statistical Outliers**: Z-score based detection (>2.5σ flagged as anomalies)
- **Unusual Changes**: Flags records with >20% increase/decrease from historical average
- **Duplicate Detection**: Identifies identical or near-duplicate records
- **Unit Mismatches**: Warns when activity units don't match source type expectations
- **Zero Values**: Flags records with missing or zero normalized values

Each anomaly includes:
- Severity level (High/Medium/Low)
- Detailed description with expected vs. actual values
- Metadata for investigation
- Acknowledgment workflow for reviewer sign-off

### 📈 **Trend Analysis**
- Monthly/yearly aggregations
- Percent change calculations
- Historical comparisons
- Support for filtering by source type and scope

### ⚡ **Performance Optimized**
- Cached aggregations (EmissionsSummary model)
- Bulk calculation of daily/monthly summaries
- Efficient anomaly detection with batch processing
- Optional Redis caching (TTL: 5 minutes)

## API Endpoints

### Summary & Breakdowns
```bash
# Get total emissions by scope
GET /api/analytics/summary/
# Response: { grand_total, scope_1_total, scope_2_total, scope_3_total, record_count }

# Get breakdown by scope or source
GET /api/analytics/breakdown/?group_by=scope|source
# Response: { breakdown: { "Scope 1": { value, code }, ... }, group_by }
```

### Trends
```bash
# Get emissions trends
GET /api/analytics/trends/?period=monthly&months_back=12&source_type=SAP_FUEL&scope=SCOPE_1
# Response: { trends: [ { date, total, average, count }, ... ], period }
```

### Anomalies
```bash
# List anomalies
GET /api/analytics/anomalies/?severity=high&type=OUTLIER&acknowledged=false&limit=50
# Response: [ { id, record_id, anomaly_type, severity, description, ... } ]

# Get anomaly details
GET /api/analytics/anomalies/{id}/
# Response: { id, record_id, ... }

# Acknowledge anomaly
PATCH /api/analytics/anomalies/{id}/
# Response: Updated anomaly object
```

### Refresh
```bash
# Manually refresh analytics data
POST /api/analytics/refresh/
# Recalculates all summaries and runs anomaly detection
```

## Data Models

### EmissionsSummary
Cached aggregated emissions data for fast dashboard queries.
- **period**: total, daily, monthly, yearly
- **date**: For period-based aggregations (null for total)
- **scope_X_total**: Emissions by scope
- **grand_total**: Sum of all scopes
- **source_breakdown**: JSON breakdown by source type
- **record_count**: Number of records in aggregation

### AnomalyFlag
Stores detected anomalies with metadata and reviewer acknowledgment.
- **anomaly_type**: OUTLIER, DUPLICATE, UNUSUAL_INCREASE/DECREASE, ZERO_VALUE, UNIT_MISMATCH
- **severity**: high, medium, low
- **description**: Human-readable explanation
- **metadata**: JSON with threshold, actual value, expected range
- **is_acknowledged**: Whether reviewer has seen this anomaly

### TrendAnalysis
Pre-calculated trend data for performance.
- **period_start/end**: Date range
- **total_emissions**, **avg_emissions**: Calculated statistics
- **percent_change**: % change from previous period

## Backend Implementation

### Calculators (`calculators.py`)
`EmissionsCalculator` handles all aggregation logic:
```python
from analytics.calculators import EmissionsCalculator
from core.models import Tenant

tenant = Tenant.objects.first()
calc = EmissionsCalculator(tenant)

# Calculate summaries
calc.calculate_total_summary()
calc.calculate_monthly_summary(year=2024, month=5)

# Get breakdowns
scopes = calc.calculate_breakdown_by_scope()
sources = calc.calculate_breakdown_by_source()

# Refresh all (called by management command)
calc.refresh_all_summaries()
```

### Anomaly Detector (`anomaly_detector.py`)
`AnomalyDetector` identifies suspicious patterns:
```python
from analytics.anomaly_detector import AnomalyDetector

detector = AnomalyDetector(tenant)

# Run specific checks
detector.detect_outliers_by_source_scope("SAP_FUEL", "SCOPE_1")
detector.detect_zero_values()
detector.detect_duplicates()

# Run all checks
detector.run_full_scan()

# Acknowledge anomalies
detector.acknowledge_anomaly(anomaly_id, acknowledged_by="user123")
```

## Frontend Implementation

### Components
- **KPICard**: Metric display with trend indicators
- **BreakdownChart**: Stacked bar chart with percentages
- **TrendChart**: Line chart with SVG rendering (no external charting library)
- **AnomaliesAlert**: Grouped anomalies by severity with drill-down

### Pages
- **AnalyticsPage**: Main dashboard with all visualizations and controls

### Client (`analyticsClient.js`)
```javascript
import { analyticsClient } from "./analyticsClient";

// All analytics API calls
await analyticsClient.getSummary();
await analyticsClient.getBreakdown("scope");
await analyticsClient.getTrends("monthly", 12);
await analyticsClient.getAnomalies();
await analyticsClient.acknowledgeAnomaly(id);
await analyticsClient.refreshAnalytics();
```

## Management Commands

### Refresh Analytics
```bash
# Refresh all tenants
python manage.py refresh_analytics

# Refresh specific tenant
python manage.py refresh_analytics --tenant-id=1
```

Recalculates EmissionsSummary objects and runs anomaly detection for all records.

## Configuration

### Anomaly Detection Thresholds
Edit in `anomaly_detector.py`:
```python
OUTLIER_Z_SCORE_THRESHOLD = 2.5  # 2.5 standard deviations
UNUSUAL_CHANGE_THRESHOLD = 0.20  # 20% change
```

### Caching (Optional)
Add to `settings.py` for Redis caching:
```python
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.redis.RedisCache',
        'LOCATION': 'redis://127.0.0.1:6379/1',
        'TIMEOUT': 300,  # 5 minutes
    }
}
```

## Performance Notes

- Dashboard queries typically complete in <500ms with caching
- Anomaly detection on 10,000+ records takes ~2-5 seconds
- EmissionsSummary provides O(1) access to common queries
- Consider running `refresh_analytics` as a background task (Celery) for large datasets
- Index recommendations:
  ```python
  class Meta:
      indexes = [
          models.Index(fields=['tenant', 'status']),
          models.Index(fields=['tenant', 'created_at']),
          models.Index(fields=['source_type', 'scope']),
      ]
  ```

## Future Enhancements

- **Machine Learning**: Replace Z-score with LSTM/Isolation Forest for better anomaly detection
- **Forecasting**: Predict next month's emissions based on trends
- **Benchmarking**: Compare against industry standards or peer organizations
- **Alerts**: Webhook notifications for high-severity anomalies
- **Exports**: PDF/Excel report generation aligned with GRI/CSRD frameworks
- **Real-time Updates**: WebSocket support for live dashboard updates
