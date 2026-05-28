# Getting Started with Analytics

## Quick Start

### 1. Ensure sample data is loaded
If you haven't seeded data yet:
```bash
python seed.py
```

### 2. Refresh analytics (populate EmissionsSummary and detect anomalies)
```bash
python manage.py refresh_analytics
```

This command:
- Calculates aggregated emissions by scope and source
- Generates daily/monthly summaries
- Runs anomaly detection
- Creates AnomalyFlag entries for suspicious patterns

### 3. Start the backend
```bash
python manage.py runserver
```

### 4. Start the frontend
In another terminal:
```bash
cd breathe_esg_frontend
npm run dev
```

### 5. Navigate to Analytics
- Go to http://localhost:5173
- Click "Analytics" in the navbar
- You'll see:
  - **KPI Cards**: Total emissions by scope
  - **Breakdown Charts**: Distribution by scope and source
  - **Trend Chart**: Historical emissions over time
  - **Anomalies**: Flagged suspicious records

## Using the Dashboard

### Viewing Metrics
- **Total Emissions**: Sum of all approved records
- **Scope 1, 2, 3**: Emissions by GHG scope classification
- **Approved Records**: Count of records with APPROVED status

### Analyzing Breakdowns
1. Click on a **breakdown chart** to drill down to detailed records
2. This filters the Review page by the selected scope/source
3. You can approve/reject/flag these records

### Tracking Trends
- **Period**: Switch between daily and monthly granularity
- **Lookback**: View 3, 6, 12, or 24 months of history
- **Trend table**: Shows percent change between periods

### Responding to Anomalies
1. **High severity** anomalies require immediate review
2. Click **"Acknowledge"** to mark as reviewed
3. Navigate to the record ID to investigate
4. Approve, reject, or flag the record in the Review page
5. Re-run analytics refresh to recalculate

## Common Workflows

### Scenario 1: Investigate a spike in electricity usage
1. Navigate to Analytics dashboard
2. Look at Trend Chart - notice a spike in month 3
3. Click the chart or filter by `source=UTILITY_ELECTRICITY`
4. Review records from that period
5. Approve valid records or flag suspicious ones

### Scenario 2: Find and fix data quality issues
1. Go to Anomalies section
2. Filter by severity = **High**
3. Review "Potential Duplicate" or "Unusual Increase" anomalies
4. For duplicates: Delete or merge records
5. For outliers: Verify source data or reject invalid entries
6. Click "Acknowledge" when reviewed

### Scenario 3: Generate a monthly summary
1. Ensure all records for the month are loaded
2. Run `python manage.py refresh_analytics`
3. Go to Analytics > Trends
4. Check summary totals (grand_total in the API response)
5. Export data or share KPI cards with stakeholders

## API Examples

### Get dashboard data
```bash
curl http://localhost:8000/api/analytics/summary/
curl http://localhost:8000/api/analytics/breakdown/?group_by=scope
curl http://localhost:8000/api/analytics/trends/?months_back=12
```

### Get anomalies
```bash
# All unacknowledged anomalies
curl http://localhost:8000/api/analytics/anomalies/

# Only high-severity
curl http://localhost:8000/api/analytics/anomalies/?severity=high

# Acknowledged only
curl http://localhost:8000/api/analytics/anomalies/?acknowledged=true
```

### Acknowledge an anomaly
```bash
curl -X PATCH http://localhost:8000/api/analytics/anomalies/1/
```

### Refresh all analytics
```bash
curl -X POST http://localhost:8000/api/analytics/refresh/
```

## Troubleshooting

### No data showing on dashboard
- **Check**: Did you load data with `python seed.py`?
- **Check**: Did you run `python manage.py refresh_analytics`?
- **Fix**: Run both commands, then refresh the browser

### Anomalies disappeared
- Anomalies are cleared when you run `refresh_analytics`
- This is intentional - it re-detects anomalies based on current data
- If you want to preserve acknowledged anomalies, modify the refresh logic in `calculators.py`

### Dashboard is slow
- **Cause**: Large dataset (10,000+ records)
- **Fix 1**: Install and configure Redis for caching
- **Fix 2**: Run `python manage.py refresh_analytics --tenant-id=X` periodically
- **Fix 3**: Add database indexes (see ANALYTICS.md)

### Anomaly detection is too strict/lenient
- Edit `anomaly_detector.py`:
  - `OUTLIER_Z_SCORE_THRESHOLD`: Increase to be less strict
  - `UNUSUAL_CHANGE_THRESHOLD`: Increase to ignore small changes
- Re-run `python manage.py refresh_analytics`

## Next Steps

1. **Add more data**: Upload more CSV files and refresh analytics
2. **Configure thresholds**: Adjust anomaly detection sensitivity
3. **Set up alerts**: Modify views to send webhooks on high-severity anomalies
4. **Generate reports**: Export data to PDF/Excel (future feature)
5. **Track targets**: Set emissions reduction goals and compare against actual
