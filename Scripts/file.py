# ============================================================
# E-Commerce Customer Segmentation & Retention Analysis
# RFM (Recency, Frequency, Monetary) + Cohort Retention Analysis
# Dataset: Olist Brazilian E-Commerce (Kaggle)
#
# GOAL: Find out who our best customers are, and whether the
# business is actually keeping customers over time.
# ============================================================


# ============================================================
# STEP 1: Setup + Load Data
# ============================================================

# Bringing in the tools (libraries) we need.
# Python doesn't know how to handle spreadsheet-style data, math,
# or charts by default - these lines "borrow" that ability.
import pandas as pd            # pandas = works with data tables (like Excel, but in code)
import numpy as np             # numpy = number/math operations
import matplotlib.pyplot as plt  # matplotlib = basic chart drawing
import seaborn as sns          # seaborn = prettier/easier charts, built on top of matplotlib

# Loading each CSV file into a "dataframe" (a table living inside our code).
# We can't do anything with a file until Python actually reads it into memory.
orders = pd.read_csv("olist_orders_dataset.csv")            # who ordered, when, order status
order_items = pd.read_csv("olist_order_items_dataset.csv")  # what was in each order
payments = pd.read_csv("olist_order_payments_dataset.csv")  # how much was paid
customers = pd.read_csv("olist_customers_dataset.csv")      # who the customer actually is

# .info() shows column names, data types, and how many values are missing.
# We check this FIRST so we don't accidentally use a column that doesn't
# exist, or assume a column is a number when it's actually text.
orders.info()

# .head() shows the first 5 rows, so we can SEE real example values,
# not just column names. Together with .info(), this gives us a full
# picture of the data before we touch it.
orders.head()


# ============================================================
# STEP 2: Merge Tables
# ============================================================
# WHY MERGE AT ALL: the answer to "how much did this customer spend,
# and when" doesn't live in ONE table - the customer's identity is in
# `customers`, the date is in `orders`, and the money is in `payments`.
# We need to connect all of them into a single table before we can
# calculate anything.

# Merge #1: connect order_items with payments, matching rows where
# order_id is the same in both tables. Think of it like combining two
# separate lists ("Order #5 has a T-shirt" + "Order #5 was paid ₹500")
# into one row: "Order #5, T-shirt, ₹500".
order_table = pd.merge(order_items, payments, on="order_id", how="left")

# Merge #2: add the order date and order status from `orders`.
order_table = pd.merge(order_table, orders, on="order_id", how="left")

# Merge #3: add customer identity info from `customers`.
# WHY how="left" (used in all 3 merges): this means "keep every row
# from the first table, even if there's no match in the second table -
# just leave it blank instead of deleting the row." This protects us
# from silently losing data. If we used "inner" instead, any row
# without a match would just vanish without warning.
order_table = pd.merge(order_table, customers, on="customer_id", how="left")

# Sanity check: comparing row counts before and after merging.
# If the row count jumped up A LOT unexpectedly, it usually means a
# join key wasn't unique on one side and rows got duplicated - we
# want to catch that now, not later when it quietly wrecks our numbers.
print(order_items.shape)   # (rows, columns) before merging
print(order_table.shape)   # (rows, columns) after merging


# ============================================================
# STEP 3: Clean Data
# ============================================================

# Keep ONLY rows where order_status is "delivered".
# WHY: our business question is about REAL completed purchases.
# A cancelled order was never actually a sale - including it would
# wrongly boost a customer's Frequency/Monetary numbers for something
# that never really happened.
# HOW THE SYNTAX WORKS: order_table["order_status"] == "delivered"
# creates a True/False list (one per row). Wrapping the table in
# order_table[...] keeps only the rows marked True.
order_table = order_table[order_table["order_status"] == "delivered"]

# Converting the purchase date from plain TEXT into an actual DATE type.
# WHY: by default, pandas often loads dates as text. If we don't fix
# this, subtracting dates (which we MUST do to calculate "days since
# last purchase") either breaks or gives wrong, nonsensical results.
order_table["order_purchase_timestamp"] = pd.to_datetime(order_table["order_purchase_timestamp"])

# Checking how many missing (blank) values exist in the 3 columns
# our entire analysis actually depends on. We only check these 3 -
# a missing value in an unrelated column (like a product description)
# wouldn't affect our calculations at all, so there's no need to check it.
print(order_table[["customer_unique_id", "order_purchase_timestamp", "payment_value"]].isnull().sum())

# Removing any row that's missing one of those 3 key values.
# WHY DROP instead of guessing a value: guessing a fake date or amount
# would introduce misleading, made-up data into a business analysis.
# It's safer and more honest to drop a small number of incomplete rows.
order_table = order_table.dropna(subset=["customer_unique_id", "order_purchase_timestamp", "payment_value"])
print(order_table.shape)  # confirms how many rows we have left after cleaning


# ============================================================
# STEP 4: Calculate RFM Values
# ============================================================

# Setting a "reference date" - basically our stand-in for "today".
# WHY WE NEED THIS: Recency means "days since their last purchase" -
# but compared to WHAT date? Since this is old historical data (not
# live data), we use the day AFTER the most recent order in the
# dataset as our "today" for measuring how recent everything else is.
reference_date = order_table["order_purchase_timestamp"].max() + pd.Timedelta(days=1)
print(reference_date)

# This is the core calculation of the whole project - let's break it down:
#
# .groupby("customer_unique_id") bundles every row into groups, one
# group per unique customer. Picture dumping thousands of receipts on
# a table, then sorting them into separate piles - one pile per person.
# Every calculation below happens SEPARATELY within each person's pile.
#
# WHY customer_unique_id and NOT customer_id: this dataset creates a
# brand NEW customer_id for every single order, even from the same
# real person. If we grouped by customer_id instead, every customer
# would look like they only ordered once - completely breaking our
# Frequency numbers without showing any error.
#
# .agg(...) calculates several summary numbers at once, for each group.
rfm = order_table.groupby("customer_unique_id").agg(
    # RECENCY: for each customer, find their LATEST order date (x.max()),
    # then subtract it from our reference date to get "days since last order".
    # We use x.max() (not x.min()) because we want their MOST RECENT
    # order, not their very first one.
    Recency = ("order_purchase_timestamp", lambda x: (reference_date - x.max()).days),

    # FREQUENCY: count how many DISTINCT orders each customer placed.
    # WHY nunique() and not just count(): our table has one row per
    # item (and sometimes per payment installment), so one order can
    # appear as multiple rows. count() would count rows (wrong -
    # inflated). nunique() correctly counts only the DISTINCT order IDs.
    Frequency = ("order_id", "nunique"),

    # MONETARY: simply add up everything this customer has ever paid.
    Monetary = ("payment_value", "sum")
).reset_index()
# .reset_index() turns "customer_unique_id" back into a normal column
# (after groupby, it briefly becomes a special row label instead) -
# this is just housekeeping, not a calculation.

print(rfm.shape)
rfm.head()

# Quick look at the spread of values BEFORE we score anything.
# This matters because it tells us upfront whether our data is evenly
# spread out or heavily lopsided (which affects how we should score it
# in the next step).
rfm[["Recency", "Frequency", "Monetary"]].describe()


# ============================================================
# STEP 5: Score RFM (turn raw numbers into simple 1-5 scores)
# ============================================================
# WHY SCORE AT ALL: raw numbers are hard to compare directly - "12 days"
# and "₹8,500" are totally different scales. Converting each into a
# 1-5 score puts everything on the SAME scale, so we can combine them
# into one simple label later.

# pd.qcut() splits customers into 5 EQUAL-SIZED groups based on rank
# (quintiles), and assigns each group a label. This is different from
# picking your own fixed cutoffs (like "under 30 days = score 5"),
# because qcut automatically balances group sizes no matter how the
# real data is spread out.
#
# WHY labels=[5,4,3,2,1] for Recency (reversed order): for Recency,
# FEWER days since last purchase is BETTER, so it should get a HIGH
# score. Listing the labels in reverse flips the usual low-to-high
# assignment, so "most recent" customers correctly get a 5.
rfm["R_Score"] = pd.qcut(rfm["Recency"], 5, labels=[5,4,3,2,1])

# For Monetary, MORE spending is already "better", so no reversal needed -
# labels go in normal low-to-high order.
rfm["M_Score"] = pd.qcut(rfm["Monetary"], 5, labels=[1,2,3,4,5])

# FREQUENCY IS SPECIAL - we do NOT use qcut here.
# WHY: about 97% of customers have a Frequency of exactly 1 (they only
# ever ordered once). qcut needs enough spread in the data to split
# customers into 5 meaningfully different groups - with almost everyone
# tied at the same value, qcut ends up assigning scores almost randomly
# among those tied customers, which would be misleading (some one-time
# buyers would randomly get labeled as "high frequency").
#
# INSTEAD, we write our OWN simple rule using actual order counts:
def freq_score(f):
    # "def" means we're creating a new, reusable mini-function.
    # "f" stands for whatever Frequency value gets passed in.
    if f == 1:
        return 1          # ordered exactly once -> lowest score
    elif f == 2:
        return 2          # ordered twice
    elif f in [3, 4]:
        return 3          # ordered 3-4 times
    elif f in [5, 6, 7]:
        return 4          # ordered 5-7 times
    else:
        return 5          # ordered 8+ times -> highest score

# .apply(freq_score) runs our custom function on EVERY value in the
# Frequency column, one at a time, and stores the results in a new column.
rfm["F_Score"] = rfm["Frequency"].apply(freq_score)

# Checking how many customers landed in each Frequency score - this
# should show the vast majority sitting at score 1, confirming our
# custom scoring reflects reality accurately (not artificially spread out).
f_score_count = rfm["F_Score"].value_counts()
print(f_score_count)

# Combining all 3 scores into one text label per customer (e.g. "541").
# WHY .astype(str) first: the scores are stored as numbers - if we
# just added them with +, Python would ADD them mathematically
# (5+4+1 = 10) instead of joining them as text. Converting to text
# first makes + glue them together like puzzle pieces ("5"+"4"+"1" = "541"),
# which preserves the full pattern instead of losing information.
rfm["RFM_Score"] = rfm["R_Score"].astype(str) + rfm["F_Score"].astype(str) + rfm["M_Score"].astype(str)
rfm.head()


# ============================================================
# STEP 6: Create Business Segments
# ============================================================
# WHY THIS STEP: a code like "RFM_Score = 541" means nothing to a
# business manager. Translating it into a label like "Champions" makes
# it immediately understandable and actionable - this is the step that
# turns raw numbers into something a real business can use.

def segment_customer(row):
    # Pull out this customer's 3 scores and give them short nicknames
    # (r, f, m) just to make the rest of the function easier to read.
    # int(...) makes sure we're comparing whole numbers.
    r, f, m = int(row["R_Score"]), int(row["F_Score"]), int(row["M_Score"])

    # Checking combinations of scores to decide which label fits best -
    # this mirrors exactly how a human would reason about it manually.
    if r >= 4 and f >= 4 and m >= 4:
        return "Champions"              # recent, frequent, big spenders - the best customers
    elif r >= 3 and f >= 3:
        return "Loyal Customers"        # reliable repeat buyers
    elif r >= 4 and f <= 2:
        return "New Customers"          # just joined recently, haven't ordered much yet
    elif r <= 2 and f >= 3:
        return "At-Risk"                # used to buy often, haven't been back in a while
    elif r <= 2 and f <= 2:
        return "Lost"                   # haven't purchased in a long time
    else:
        return "Potential Loyalists"    # somewhere in between, could go either way

# rfm.apply(segment_customer, axis=1) runs our function on each ROW
# (using all 3 scores together at once). axis=1 is what makes it look
# across a whole row instead of down a single column - this is
# different from the earlier .apply() we used just for Frequency alone.
rfm["Segment"] = rfm.apply(segment_customer, axis=1)

# How many customers fall into each segment - a simple headcount.
segment_counts = rfm["Segment"].value_counts()
print(segment_counts)

# Total money generated by each segment - groups by Segment, then
# sums up Monetary within each group, and sorts biggest to smallest.
segment_revenue = rfm.groupby("Segment")["Monetary"].sum().sort_values(ascending=False)
print(segment_revenue)

# Average revenue PER CUSTOMER within each segment.
# WHY THIS MATTERS: total revenue by segment can be misleading if one
# segment just has way more people in it. Dividing revenue by customer
# count reveals which segments are actually most valuable PER PERSON,
# which is a much fairer, more useful comparison.
segment_avg = (segment_revenue / segment_counts).sort_values(ascending=False)
print(segment_avg)


# ============================================================
# STEP 7-8: Cohort & Retention Analysis
# ============================================================
# WHY A SEPARATE ANALYSIS: RFM tells us where each customer stands
# TODAY - like a single photograph. Cohort analysis instead asks: over
# TIME, are we actually keeping customers, or does everyone leave after
# their first purchase? This is a completely different, time-based
# question that RFM alone can't answer.

# Finding each customer's very FIRST-EVER order date. This becomes
# their "cohort" - the group of people who all joined around the same time.
# WHY .min() here (not .max() like we used for Recency): different
# question. Recency needed their LATEST order. This needs their
# EARLIEST order, since a cohort is defined by when someone first
# became a customer.
customer_first_purchase = order_table.groupby("customer_unique_id")["order_purchase_timestamp"].min().reset_index()

# Renaming columns just for clarity - pure housekeeping, no calculation.
customer_first_purchase.columns = ["customer_unique_id", "cohort_date"]

# Rounding the exact date down to just the MONTH (e.g. "2017-09-13"
# becomes "2017-09"). We don't care about the exact day someone first
# bought - we want to group people by MONTH for this analysis.
customer_first_purchase["cohort_month"] = customer_first_purchase["cohort_date"].dt.to_period("M")

# Attaching each customer's cohort_month back onto EVERY one of their
# order rows, by matching on customer_unique_id (same merge concept as Step 2).
order_table = order_table.merge(customer_first_purchase[["customer_unique_id", "cohort_month"]], on="customer_unique_id")

order_table[["customer_unique_id", "order_purchase_timestamp", "cohort_month"]].head()

# Same month-rounding idea, but applied to EVERY order (not just their
# first one) - so now every row knows which month THAT SPECIFIC order happened in.
order_table["order_month"] = order_table["order_purchase_timestamp"].dt.to_period("M")

# Calculating "cohort_index" = how many months after joining did this
# order happen (0 = their first month, 1 = one month later, etc.)
# WHY WE NEED THIS instead of comparing calendar months directly: we
# want to compare a January cohort's "1 month later" behavior against
# a June cohort's "1 month later" behavior on the SAME shared scale,
# even though their actual calendar months are totally different.
# cohort_index re-aligns every cohort to start counting from 0.
order_table["cohort_index"] = (order_table["order_month"] - order_table["cohort_month"]).apply(lambda x: x.n)

order_table[["customer_unique_id", "cohort_month", "order_month", "cohort_index"]].head()

# Grouping by BOTH cohort_month AND cohort_index together, then
# counting distinct customers in each combination. This answers:
# "of the people who joined in January, how many were still active
# in month 0? Month 1? Month 2?" - calculated separately for every cohort.
cohort_data = order_table.groupby(["cohort_month", "cohort_index"])["customer_unique_id"].nunique().reset_index()

# Reshaping this from a long list into a GRID: cohort months become
# rows, months-since-joining become columns, customer counts fill the grid.
# WHY: a long list of numbers is hard for a human to scan for patterns.
# A grid lets you look down a column or across a row and immediately
# spot whether retention is improving or worsening.
cohort_pivot = cohort_data.pivot(index="cohort_month", columns="cohort_index", values="customer_unique_id")

# Grabbing column "0" - this is each cohort's TOTAL starting size
# (their first purchase month, which is always 100% of that cohort).
cohort_size = cohort_pivot[0]

# Converting raw counts into PERCENTAGES, relative to each cohort's own size.
# WHY: raw counts are misleading - a cohort of 1000 dropping to 200
# looks worse than a cohort of 100 dropping to 30, even though the
# smaller cohort actually retained a HIGHER percentage. Percentages
# let us fairly compare cohorts of very different sizes.
# axis=0 means divide each ROW by its own matching value in cohort_size.
retention_table = cohort_pivot.divide(cohort_size, axis=0) * 100

retention_table.round(1)  # rounding just for a cleaner, more readable display


# ============================================================
# STEP 9: Visualizations
# ============================================================

# --- Cohort retention heatmap ---
# A heatmap lets us see ALL cohorts at once, stacked - so we can spot
# patterns (like "every cohort drops sharply after month 1") just by
# looking at how the colors change across the grid.
plt.figure(figsize=(14,10))   # sets the size of the chart canvas
sns.heatmap(
    retention_table,
    annot=True,      # prints the actual number inside each cell, not just color
    fmt=".1f",        # formats those numbers to show just 1 decimal place
    cmap="Blues"      # sets the color scheme to shades of blue
)
plt.title("Cohort Retention Heatmap (%)")
plt.ylabel("Cohort Month (first purchase)")
plt.xlabel("Months Since First Purchase")
plt.show()   # actually displays the chart

# --- Customer count by RFM segment ---
plt.figure(figsize=(8,5))
segment_counts.plot(kind="bar", color="#4472C4")
plt.title("Number of Customers per RFM Segment")
plt.ylabel("Customer Count")
plt.xticks(rotation=45)      # tilts the segment name labels so long names don't overlap
plt.tight_layout()           # auto-adjusts spacing so nothing gets cut off at the edges
plt.show()

# --- Revenue by RFM segment ---
plt.figure(figsize=(8,5))
segment_revenue.sort_values(ascending=False).plot(kind="bar", color="#2E7D32")
plt.title("Revenue Contribution by RFM Segment")
plt.ylabel("Total Revenue")
plt.xticks(rotation=45)
plt.tight_layout()
plt.show()


# ============================================================
# STEP 10: Export Results
# ============================================================

# Saving our final customer-level table (with RFM scores and segments)
# to a CSV file. index=False means we don't add an extra unnamed
# column for row numbers - just our actual, clean columns.
rfm.to_csv("rfm_output.csv", index=False)

# Triggers a browser download popup in Colab, so we can save this
# file to our computer and later upload it to GitHub.
from google.colab import files
files.download("rfm_output.csv")
