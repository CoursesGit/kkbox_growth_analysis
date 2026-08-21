# Growth Monitoring chart specification

1. Daily New Users line chart
   - X: registration_date
   - Y: new_users
   - Overlay: moving_avg_7d
   - Reference line: 2015-10-07

2. Daily Registration Source Mix stacked area/column chart
   - X: registration_date
   - Legend: registered_via
   - Y: source_new_users
   - Highlight registered_via=4; do not assign a business channel name.

3. Source Mix 100% stacked column chart
   - X: registration_date
   - Legend: registered_via
   - Y: source_share
   - Reference line: 2015-10-07

4. October anomaly validation combo chart
   - Columns: daily_new_users and source4_new_users
   - Line: source4_share
   - Date range: 2015-10-01 through 2015-10-16

5. Period comparison chart
   - Compare 2015-10-01~06, 2015-10-07, and 2015-10-08~16
   - Metrics: avg_daily_new_users, avg_daily_source4_new_users, source4_share
