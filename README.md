E-Commerce Customer Segmentation & Retention Analysis (RFM + Cohort Analysis)
--------------------------------------------------------------------------------------
Business Question
Which customers matter most to the business, and how well is the business retaining customers over time? This project answers that using RFM segmentation (who are our best/at-risk/lost customers, today) and Cohort/Retention analysis (are we keeping customers over time, and where exactly are we losing them).
------------------------------------------------------------------------------------
Dataset
Brazilian E-Commerce Public Dataset by Olist — ~100k real orders placed on the Olist marketplace between 2016 and 2018.
--------------------------------------------------------------------------------------
Tools Used
Python (pandas, numpy) — data cleaning, merging, RFM calculation, cohort analysis
Matplotlib / Seaborn — visualization
Google Colab — environment
-----------------------------------------------------------------------------------
## Methodology
- Combined 4 raw data files (orders, order items, payments, customers) into one single table, matching them by order ID and customer ID
- Kept only delivered orders — removed cancelled/unavailable ones since they weren't real sales
- Fixed the date column so it could be used for date calculations
- Removed a few rows with missing key information
- Calculated 3 things for every customer:
  - Recency — days since their last order
  - Frequency — how many times they've ordered
  - Monetary — total amount they've spent
- Converted these into simple 1–5 scores so they could be compared fairly
- Fixed a scoring issue with Frequency — since almost everyone ordered only once, the normal scoring method gave misleading results, so a custom scoring rule was used instead
- Grouped customers into simple labels — Champions, Loyal Customers, New Customers, At-Risk, Lost, Potential Loyalists
- Tracked customers by the month they first purchased (their "cohort"), then checked how many kept buying in the following months
- Turned the results into percentages so different-sized groups could be compared fairly
- Built charts to show the patterns clearly — customer segments, revenue by segment, and a retention heatmap over time

--------------------------------------------------------------------------------

1. Retention collapses almost immediately after the first purchase. Across every single cohort from October 2016 to mid-2018, retention drops from 100% to under 1% within just one month. This is a consistent, structural pattern — not a seasonal dip or a one-off issue with any specific cohort.

<img width="1103" height="855" alt="cohort_retention_heatmap" src="https://github.com/user-attachments/assets/e84d1f5e-9bff-463f-98b9-cf270dff241c" />
--------------------------------------------------------------------------------
2. 97% of customers never make a second purchase. RFM segmentation confirms the same pattern from a different angle: "New Customers" (37,311) and "Lost" (37,146) dominate the customer base, while genuinely loyal repeat customers (Loyal + At-Risk + Champions) total only 228 people — less than 0.3% of the customer base.

<img width="790" height="490" alt="segment_customer_count" src="https://github.com/user-attachments/assets/ac41ee98-41f0-4c47-b5fe-24b61c9c281c" />
----------------------------------------------------------------------------------
3. Revenue by segment is misleading if read at face value. New Customers and Lost segments generate the most total revenue (₹8.0M and ₹7.9M) simply because of their volume.

<img width="790" height="490" alt="segment_revenue" src="https://github.com/user-attachments/assets/a992c25f-9280-49b4-bfd1-7d82319ed336" />
-----------------------------------------------------------------------------------
4. But on a per-customer basis, loyal customers are worth far more. Champions spend ₹1,123 on average per person — over 5x more than New Customers (₹215) or Lost (₹212). Loyal Customers average ₹944 per person. This means the tiny 0.3% of genuinely repeat customers are disproportionately valuable, even though their total revenue looks small next to the high-volume segments
-----------------------------------------------------------------------------------
Reccomendation
1. Most customers buy once and never come back. Try to bring them back quickly — within the first month — with a discount or            reminder.
2. A few customers spend a lot more than others. Take good care of them so they don't leave.
3. Don't just look at total sales. Check how much each customer spends on average — it tells a truer story.
4. Act fast. Most people leave within a month, so any plan to keep them needs to start right away, not later.

--------------------------------------------------------------------------------------
