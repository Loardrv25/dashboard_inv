
import streamlit as st
import pandas as pd
import numpy as np
import yfinance as yf
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from datetime import datetime, timedelta

st.set_page_config(layout="wide")
st.title("Dashboard de Análisis Técnico - Criptomonedas e Índices de Mercado")

# --- Configuración de activos ---
cryptos = {
    'BTC-USD': 'Bitcoin',
    'ETH-USD': 'Ethereum',
    'SOL-USD': 'Solana',
    'XRP-USD': 'Ripple',
    'ADA-USD': 'Cardano'
}

indices = {
    "Dow Jones": "^DJI",
    "Nasdaq": "^IXIC",
    "S&P 500": "^GSPC",
    "DAX": "^GDAXI"
}

market_type = st.sidebar.radio("Selecciona tipo de mercado:", ["Criptomonedas", "Índices de Mercado"])

if market_type == "Criptomonedas":
    selected_symbol = st.sidebar.selectbox("Selecciona una criptomoneda:", list(cryptos.keys()), format_func=lambda x: cryptos[x])
else:
    selected_symbol = st.sidebar.selectbox("Selecciona un índice de mercado:", list(indices.keys()), format_func=lambda x: x)

# Fecha de inicio: últimos 3 años
start_date = datetime.now() - timedelta(days=3*365)
start_str = start_date.strftime('%Y-%m-%d')

# Cargar datos de Yahoo Finance
@st.cache_data
def load_data_yf(symbol):
    df = yf.download(symbol, start=start_str)
    df.reset_index(inplace=True)
    return df

df = load_data_yf(selected_symbol)

if df is not None and not df.empty:
    st.subheader(f"Evolución de {selected_symbol}")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], mode='lines', name='Precio', line=dict(color='blue')))
    fig.update_layout(title=f"Curso de {selected_symbol}", xaxis_title="Fecha", yaxis_title="Precio")
    st.plotly_chart(fig, use_container_width=True)

    # Parámetro SMA
    sma_period = st.sidebar.slider("Periodo SMA", 5, 100, 20)
    df['SMA'] = df['Close'].rolling(window=sma_period).mean()

    # RSI
    delta = df['Close'].diff()
    gain = delta.clip(lower=0)
    loss = -delta.clip(upper=0)
    avg_gain = gain.rolling(window=14).mean()
    avg_loss = loss.rolling(window=14).mean()
    rs = avg_gain / avg_loss
    df['RSI'] = 100 - (100 / (1 + rs))

    st.subheader("RSI")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df['Date'], df['RSI'], label='RSI', color='purple')
    ax.axhline(70, linestyle='--', color='red', label='Sobrecompra (70)')
    ax.axhline(30, linestyle='--', color='green', label='Sobreventa (30)')
    ax.legend()
    st.pyplot(fig)

    rsi_signal = "Mantener"
    rsi_color = "gray"
    if not pd.isna(df['RSI'].iloc[-1]):
        if df['RSI'].iloc[-1] < 30:
            rsi_signal = "COMPRA"
            rsi_color = "green"
        elif df['RSI'].iloc[-1] > 70:
            rsi_signal = "VENTA"
            rsi_color = "red"
    st.markdown(f'<div style="background-color:{rsi_color};color:white;padding:10px;border-radius:5px;text-align:center;">{rsi_signal}</div>', unsafe_allow_html=True)

    # MACD
    short_ema = df['Close'].ewm(span=12, adjust=False).mean()
    long_ema = df['Close'].ewm(span=26, adjust=False).mean()
    df['MACD'] = short_ema - long_ema
    df['Signal Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

    st.subheader("MACD")
    fig, ax = plt.subplots(figsize=(10, 4))
    ax.plot(df['Date'], df['MACD'], label='MACD', color='blue')
    ax.plot(df['Date'], df['Signal Line'], label='Línea de Señal', color='red')
    ax.legend()
    st.pyplot(fig)

    macd_signal = "Mantener"
    macd_color = "gray"
    if not pd.isna(df['MACD'].iloc[-1]) and not pd.isna(df['Signal Line'].iloc[-1]):
        if df['MACD'].iloc[-1] > df['Signal Line'].iloc[-1]:
            macd_signal = "COMPRA"
            macd_color = "green"
        elif df['MACD'].iloc[-1] < df['Signal Line'].iloc[-1]:
            macd_signal = "VENTA"
            macd_color = "red"
    st.markdown(f'<div style="background-color:{macd_color};color:white;padding:10px;border-radius:5px;text-align:center;">{macd_signal}</div>', unsafe_allow_html=True)

    # Bandas de Bollinger
    st.subheader("Bandas de Bollinger")
    std_dev = df['Close'].rolling(window=sma_period).std()
    df['Upper Band'] = df['SMA'] + (2 * std_dev)
    df['Lower Band'] = df['SMA'] - (2 * std_dev)

    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Upper Band'], name="Upper Band", line=dict(color='blue', dash='dot')))
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Lower Band'], name="Lower Band", line=dict(color='blue', dash='dot')))
    fig.add_trace(go.Candlestick(x=df['Date'], open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'], name="Candlestick"))
    st.plotly_chart(fig, use_container_width=True)

    boll_signal = "Mantener"
    boll_color = "gray"
    if not pd.isna(df['Close'].iloc[-1]) and not pd.isna(df['Lower Band'].iloc[-1]) and not pd.isna(df['Upper Band'].iloc[-1]):
        if df['Close'].iloc[-1] <= df['Lower Band'].iloc[-1]:
            boll_signal = "COMPRA"
            boll_color = "green"
        elif df['Close'].iloc[-1] >= df['Upper Band'].iloc[-1]:
            boll_signal = "VENTA"
            boll_color = "red"
    st.markdown(f'<div style="background-color:{boll_color};color:white;padding:10px;border-radius:5px;text-align:center;">{boll_signal}</div>', unsafe_allow_html=True)
