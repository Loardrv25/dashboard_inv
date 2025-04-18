
import streamlit as st
import pandas as pd
import numpy as np
import requests
from datetime import datetime, timedelta
import plotly.graph_objects as go

st.set_page_config(layout="wide", page_title="Dashboard Análisis Técnico", page_icon="📈")

# --- CONFIGURACIÓN DE ACTIVOS ---
cryptos = {
    'BTC-USD': 'Bitcoin',
    'ETH-USD': 'Ethereum',
    'SOL-USD': 'Solana',
    'XRP-USD': 'Ripple',
    'ADA-USD': 'Cardano'
}

# ETFs como alternativa a índices reales
market_indices = {
    'S&P 500 (SPY)': 'SPY',
    'Nasdaq 100 (QQQ)': 'QQQ',
    'Dow Jones (DIA)': 'DIA',
    'DAX (EWG)': 'EWG'
}

# --- INTERFAZ ---
st.sidebar.title("Selecciona tipo de mercado:")
market_type = st.sidebar.radio("", ["Criptomonedas", "Índices de Mercado"])

if market_type == "Criptomonedas":
    selected_symbol = st.sidebar.selectbox("Selecciona una criptomoneda:", list(cryptos.keys()), format_func=lambda x: cryptos[x])
else:
    selected_symbol = st.sidebar.selectbox("Selecciona un índice de mercado (ETF):", list(market_indices.values()))

st.title("📈 Dashboard de Análisis Técnico - Alpha Vantage")

# --- FUNCIÓN PARA CARGAR DATOS ---
@st.cache_data(ttl=3600)
def fetch_alpha_vantage(symbol):
    api_key = st.secrets["ALPHA_VANTAGE_API_KEY"]
    function = "DIGITAL_CURRENCY_DAILY" if symbol.endswith("-USD") else "TIME_SERIES_DAILY_ADJUSTED"
    market_param = "&market=USD" if function == "DIGITAL_CURRENCY_DAILY" else ""
    url = f"https://www.alphavantage.co/query?function={function}&symbol={symbol}{market_param}&apikey={api_key}"

    response = requests.get(url)
    data = response.json()

    if function == "DIGITAL_CURRENCY_DAILY":
        timeseries = data.get("Time Series (Digital Currency Daily)", {})
        price_key = "4a. close (USD)"
    else:
        timeseries = data.get("Time Series (Daily)", {})
        price_key = "5. adjusted close"

    if not timeseries:
        return None

    df = pd.DataFrame.from_dict(timeseries, orient="index")
    df.index = pd.to_datetime(df.index)
    df.sort_index(inplace=True)
    df["Close"] = df[price_key].astype(float)
    df = df[df.index > datetime.now() - timedelta(days=3 * 365)]  # 3 años
    df.reset_index(inplace=True)
    df.rename(columns={"index": "Date"}, inplace=True)
    return df

# --- CARGA DE DATOS ---
df = fetch_alpha_vantage(selected_symbol)

if df is None or df.empty:
    st.warning("⚠️ No se pudieron obtener datos válidos para este activo desde Alpha Vantage.")
    st.stop()

# --- GRÁFICO DE PRECIO ---
st.subheader(f"Evolución de {selected_symbol}")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], mode='lines', name="Precio", line=dict(color="blue")))
fig.update_layout(xaxis_title="Fecha", yaxis_title="Precio", title=f"Precio de {selected_symbol}")
st.plotly_chart(fig, use_container_width=True)

# --- CÁLCULO DE INDICADORES ---
sma_period = st.sidebar.slider("Periodo SMA", 5, 100, 20)
df['SMA'] = df['Close'].rolling(window=sma_period).mean()

# RSI
delta = df['Close'].diff()
gain = np.where(delta > 0, delta, 0)
loss = np.where(delta < 0, -delta, 0)
avg_gain = pd.Series(gain).rolling(window=14).mean()
avg_loss = pd.Series(loss).rolling(window=14).mean()
rs = avg_gain / avg_loss
df['RSI'] = 100 - (100 / (1 + rs))

# MACD
short_ema = df['Close'].ewm(span=12, adjust=False).mean()
long_ema = df['Close'].ewm(span=26, adjust=False).mean()
df['MACD'] = short_ema - long_ema
df['Signal Line'] = df['MACD'].ewm(span=9, adjust=False).mean()

# Bandas de Bollinger
df['STD'] = df['Close'].rolling(window=sma_period).std()
df['Upper Band'] = df['SMA'] + (2 * df['STD'])
df['Lower Band'] = df['SMA'] - (2 * df['STD'])

# --- VISUALIZACIÓN DE INDICADORES ---
st.subheader("RSI")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["Date"], y=df["RSI"], name="RSI", line=dict(color="purple")))
fig.add_hline(y=70, line=dict(dash="dash", color="red"))
fig.add_hline(y=30, line=dict(dash="dash", color="green"))
st.plotly_chart(fig, use_container_width=True)

rsi_color = "gray"
rsi_text = "Mantener"
if df['RSI'].iloc[-1] < 30:
    rsi_color = "green"
    rsi_text = "COMPRA"
elif df['RSI'].iloc[-1] > 70:
    rsi_color = "red"
    rsi_text = "VENTA"
st.markdown(f"<div style='background-color:{rsi_color};color:white;padding:10px;text-align:center;border-radius:5px'>{rsi_text}</div>", unsafe_allow_html=True)

# MACD
st.subheader("MACD")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["Date"], y=df["MACD"], name="MACD", line=dict(color="blue")))
fig.add_trace(go.Scatter(x=df["Date"], y=df["Signal Line"], name="Signal", line=dict(color="red")))
st.plotly_chart(fig, use_container_width=True)

macd_color = "gray"
macd_text = "Mantener"
if df['MACD'].iloc[-1] > df['Signal Line'].iloc[-1]:
    macd_color = "green"
    macd_text = "COMPRA"
elif df['MACD'].iloc[-1] < df['Signal Line'].iloc[-1]:
    macd_color = "red"
    macd_text = "VENTA"
st.markdown(f"<div style='background-color:{macd_color};color:white;padding:10px;text-align:center;border-radius:5px'>{macd_text}</div>", unsafe_allow_html=True)

# Bandas de Bollinger
st.subheader("Bandas de Bollinger")
fig = go.Figure()
fig.add_trace(go.Scatter(x=df["Date"], y=df["Upper Band"], name="Upper Band", line=dict(color="lightblue", dash="dot")))
fig.add_trace(go.Scatter(x=df["Date"], y=df["Lower Band"], name="Lower Band", line=dict(color="lightblue", dash="dot")))
fig.add_trace(go.Scatter(x=df["Date"], y=df["Close"], name="Precio", line=dict(color="black")))
st.plotly_chart(fig, use_container_width=True)

boll_color = "gray"
boll_text = "Mantener"
if df['Close'].iloc[-1] >= df['Upper Band'].iloc[-1]:
    boll_color = "red"
    boll_text = "VENTA"
elif df['Close'].iloc[-1] <= df['Lower Band'].iloc[-1]:
    boll_color = "green"
    boll_text = "COMPRA"
st.markdown(f"<div style='background-color:{boll_color};color:white;padding:10px;text-align:center;border-radius:5px'>{boll_text}</div>", unsafe_allow_html=True)
