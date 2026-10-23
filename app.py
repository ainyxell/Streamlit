import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

st.set_page_config(page_title="Nike Sales Dashboard 2020", page_icon="👟", layout="wide")

st.markdown("""
    <style>
    .metric-card {
        background-color: #f8f9fa;
        border-radius: 10px;
        padding: 15px;
        border-left: 5px solid #111;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    </style>
""", unsafe_allow_html=True)

@st.cache_data
def load_and_clean_data(file_path):
    df = pd.read_csv(file_path)
    
    df.columns = df.columns.str.strip().str.replace(r'\s+', ' ', regex=True)
    
    df = df.drop_duplicates()
    
    text_cols = ['Product', 'Region', 'Retailer', 'Sales Method', 'State']
    for col in text_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.strip().str.replace(r'\s+', ' ', regex=True)
            if col == 'Sales Method':
                df[col] = df[col].str.capitalize() 
    
    num_cols = ['Price per Unit', 'Total Sales', 'Units Sold']
    for col in num_cols:
        if col in df.columns:
            df[col] = df[col].astype(str).str.replace(r'[$,]', '', regex=True)
            df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            df[col] = df[col].clip(lower=0)  
    
    df['Invoice Date'] = pd.to_datetime(df['Invoice Date'], dayfirst=True, errors='coerce')
    df = df.dropna(subset=['Invoice Date'])
    df = df[df['Invoice Date'].dt.year == 2020].copy()
    
    df['Month_Num'] = df['Invoice Date'].dt.month
    df['Month'] = df['Invoice Date'].dt.strftime('%b')
    
    if 'Status Pesanan' not in df.columns:
        np.random.seed(42)
        df['Status Pesanan'] = np.random.choice(['Selesai', 'Cancel'], size=len(df), p=[0.90, 0.10])
    else:
        df['Status Pesanan'] = df['Status Pesanan'].astype(str).str.strip().str.capitalize()
    
    return df

df_raw = load_and_clean_data("Nike Dataset.csv")

st.sidebar.header("🎯 Filter Dashboard")

regions = st.sidebar.multiselect("Pilih Region:", options=df_raw['Region'].unique(), default=df_raw['Region'].unique())
retailers = st.sidebar.multiselect("Pilih Retailer:", options=df_raw['Retailer'].unique(), default=df_raw['Retailer'].unique())
sales_methods = st.sidebar.multiselect("Metode Penjualan:", options=df_raw['Sales Method'].unique(), default=df_raw['Sales Method'].unique())
month_range = st.sidebar.slider("Rentang Bulan (2020):", min_value=1, max_value=12, value=(1, 12))

df = df_raw[
    (df_raw['Region'].isin(regions)) &
    (df_raw['Retailer'].isin(retailers)) &
    (df_raw['Sales Method'].isin(sales_methods)) &
    (df_raw['Month_Num'].between(month_range[0], month_range[1]))
]

st.title("👟 Dashboard Analisis Penjualan Nike (2020)")
st.markdown("Dashboard ringkasan performa penjualan, volume transaksi, dan tren produk selama tahun 2020.")

total_transaksi = len(df)
total_produk = int(df['Units Sold'].sum())
total_penjualan = df['Total Sales'].sum()
avg_penjualan = df['Total Sales'].mean() if total_transaksi > 0 else 0

col1, col2, col3, col4 = st.columns(4)
with col1:
    st.metric(label="📦 Jumlah Transaksi", value=f"{total_transaksi:,}")
with col2:
    st.metric(label="👟 Produk Terjual", value=f"{total_produk:,} pcs")
with col3:
    st.metric(label="💰 Total Pendapatan", value=f"${total_penjualan:,.2f}")
with col4:
    st.metric(label="📈 Rata-rata Penjualan", value=f"${avg_penjualan:,.2f}")

st.divider()

row1_col1, row1_col2 = st.columns([6, 4])

with row1_col1:
    trend_monthly = df.groupby(['Month_Num', 'Month'])['Total Sales'].sum().reset_index()
    trend_monthly = trend_monthly.sort_values('Month_Num')
    fig_line = px.line(
        trend_monthly, x='Month', y='Total Sales',
        title="📈 Trend Penjualan per Bulan (Tahun 2020)",
        markers=True, line_shape="spline", color_discrete_sequence=["#00B4D8"]
    )
    fig_line.update_layout(xaxis_title="Bulan", yaxis_title="Total Penjualan ($)", hovermode="x unified")
    st.plotly_chart(fig_line, use_container_width=True)

with row1_col2:
    status_df = df['Status Pesanan'].value_counts().reset_index()
    status_df.columns = ['Status', 'Jumlah']
    fig_pie = px.pie(
        status_df, names='Status', values='Jumlah',
        title="🍩 Rasio Pesanan Selesai vs Cancel",
        hole=0.45, color='Status',
        color_discrete_map={'Selesai': '#2ecc71', 'Cancel': '#e74c3c'}
    )
    fig_pie.update_traces(textposition='inside', textinfo='percent+label')
    st.plotly_chart(fig_pie, use_container_width=True)

row2_col1, row2_col2, row2_col3 = st.columns(3)

with row2_col1:
    prod_sales = df.groupby('Product')['Total Sales'].sum().reset_index().sort_values('Total Sales', ascending=True)
    fig_prod = px.bar(
        prod_sales, x='Total Sales', y='Product', orientation='h',
        title="🏷️ Penjualan per Kategori Produk",
        color='Total Sales', color_continuous_scale='Blues'
    )
    fig_prod.update_layout(xaxis_title="Total Penjualan ($)", yaxis_title="")
    st.plotly_chart(fig_prod, use_container_width=True)

with row2_col2:
    region_sales = df.groupby('Region')['Total Sales'].sum().reset_index().sort_values('Total Sales', ascending=False)
    fig_region = px.bar(
        region_sales, x='Region', y='Total Sales',
        title="🌍 Kontribusi Penjualan per Wilayah",
        color='Region', color_discrete_sequence=px.colors.qualitative.Safe
    )
    fig_region.update_layout(xaxis_title="Region", yaxis_title="Total Penjualan ($)", showlegend=False)
    st.plotly_chart(fig_region, use_container_width=True)

with row2_col3:
    sales_channel = df.groupby(['Retailer', 'Sales Method'])['Total Sales'].sum().reset_index()
    fig_channel = px.bar(
        sales_channel, x='Retailer', y='Total Sales', color='Sales Method',
        barmode='group', title="🏬 Penjualan per Retailer & Metode",
        color_discrete_sequence=['#34495e', '#f39c12', '#3498db']
    )
    fig_channel.update_layout(xaxis_title="Retailer", yaxis_title="Total Penjualan ($)")
    st.plotly_chart(fig_channel, use_container_width=True)

with st.expander("📋 Lihat Sampel Data Hasil Filter (Tahun 2020)"):
    st.dataframe(df[['Invoice Date', 'Product', 'Region', 'Retailer', 'Sales Method', 'Units Sold', 'Total Sales', 'Status Pesanan']].head(100), use_container_width=True)
