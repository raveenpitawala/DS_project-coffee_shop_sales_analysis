import streamlit as st
import pandas as pd
import plotly.express as px

# Load cleaned dataset
df = pd.read_csv("../../data/processed/cleaned_coffee_sales.csv", parse_dates=['transaction_date'])

# Preprocessing
df['transaction_date'] = pd.to_datetime(df['transaction_date'])
df['month_year'] = df['transaction_date'].dt.to_period('M').astype(str)
df['profit'] = (df['unit_price'] - df['unit_cost']) * df['transaction_qty']

# Monthly sales summary
monthly_summary = df.groupby('month_year').agg({
    'total_price': 'sum',
    'profit': 'sum'
}).reset_index()

# Sidebar filters
st.sidebar.header("Filters")
store = st.sidebar.selectbox("Select Store", df['store_location'].unique())
category = st.sidebar.selectbox("Select Product Category", df['product_category'].unique())
analysis_level = st.sidebar.radio("Select Analysis Level", ['Product Level', 'Category Level'])

# Segment filter in main area
segment_options = df['Segment'].dropna().unique().tolist()
selected_segments = st.multiselect("Filter by Customer Segment", segment_options, default=segment_options)

# Apply all filters
filtered_df = df[
    (df['store_location'] == store) &
    (df['product_category'] == category) &
    (df['Segment'].isin(selected_segments))
]

# -------------------
# UI Starts
# -------------------
st.title("Coffee Shop Sales Dashboard")

# Download filtered data
st.subheader("⬇ Download Filtered Data")
export_df = filtered_df[['transaction_date', 'store_location', 'product_category', 'product_type',
                         'transaction_qty', 'unit_price', 'total_price', 'profit']]
csv = export_df.to_csv(index=False).encode('utf-8')
st.download_button("Download CSV", csv, "filtered_sales_data.csv", "text/csv")

# 1. Daily Sales Trend
st.subheader("Daily Sales Trend")
sales_trend = filtered_df.groupby('transaction_date')['total_price'].sum().reset_index()
fig_trend = px.line(sales_trend, x='transaction_date', y='total_price', title='Daily Sales')
st.plotly_chart(fig_trend)

# 2. Top Products/Categories
st.subheader("Top Selling Items")
if analysis_level == 'Product Level':
    top_items = filtered_df.groupby('product_type')['total_price'].sum().nlargest(10).reset_index()
    fig_top = px.bar(top_items, x='product_type', y='total_price', title='Top Selling Product Types')
else:
    top_items = filtered_df.groupby('product_category')['total_price'].sum().nlargest(10).reset_index()
    fig_top = px.bar(top_items, x='product_category', y='total_price', title='Top Selling Categories')
st.plotly_chart(fig_top)

# 3. Monthly Sales and Profit
st.subheader("Monthly Sales and Profit Summary")
fig_month = px.bar(
    monthly_summary.melt(id_vars='month_year'),
    x='month_year', y='value', color='variable',
    title='Monthly Sales vs Profit',
    barmode='group',
    labels={'value': 'Amount (Rs)', 'month_year': 'Month'}
)
st.plotly_chart(fig_month)

# 4. RFM Segment Pie Chart (if available)
if 'Segment' in df.columns:
    st.subheader("Customer Segments (RFM)")
    unique_customers = df[['customer_id', 'Segment']].drop_duplicates()
    segment_counts = unique_customers['Segment'].value_counts().reset_index()
    segment_counts.columns = ['Segment', 'Count']
    fig_rfm = px.pie(segment_counts, names='Segment', values='Count', title='Distribution of Customer Segments')
    st.plotly_chart(fig_rfm)

# 5. Forecast Chart
st.subheader("30-Day Sales Forecast")
try:
    forecast_df = pd.read_csv("../../data/processed/forecast_30days.csv", parse_dates=['Date'])

    # Forecast chart
    fig_forecast = px.line(forecast_df, x='Date', y='Forecasted_Sales', title='Projected Sales for Next 30 Days')
    st.plotly_chart(fig_forecast)

    # Combine actual + forecast
    actual_sales = df.groupby('transaction_date')['total_price'].sum().reset_index()
    actual_sales.columns = ['Date', 'Sales']
    actual_sales['Type'] = 'Actual'

    forecast_df = forecast_df.rename(columns={'Forecasted_Sales': 'Sales'})
    forecast_df['Type'] = 'Forecast'

    combined = pd.concat([actual_sales, forecast_df], ignore_index=True)
    fig_combined = px.line(combined, x='Date', y='Sales', color='Type', title='Actual vs Forecasted Sales')
    st.plotly_chart(fig_combined)
except FileNotFoundError:
    st.warning("Forecast file not found. Skipping forecast section.")

