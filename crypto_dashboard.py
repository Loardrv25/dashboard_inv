
from dotenv import load_dotenv
load_dotenv()
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from datetime import datetime, timedelta
import requests
import os

# CONFIGURA TU API KEY AQUÍ (o usa variable de entorno)
API_KEY = API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

st.set_page_config(layout="wide")
st.title("Dashboard de Análisis Técnico - Alpha Vantage")

# Configuración de activos
cryptos = {
    'BTC/USD': 'Bitcoin',
    'ETH/USD': 'Ethereum',
    'SOL/USD': 'Solana',
    'XRP/USD': 'Ripple',
    'ADA/USD': 'Cardano'
}

indices = {
    "S&P 500 (SPY ETF)": "SPY",
    "Nasdaq 100 (QQQ ETF)": "QQQ",
    "Dow Jones (DIA ETF)": "DIA",
    "Russell 2000 (IWM ETF)": "IWM",
    "DAX Alemania (EWG ETF)": "EWG"
}

market_type = st.sidebar.radio("Selecciona tipo de mercado:", ["Criptomonedas", "Índices de Mercado"])

if market_type == "Criptomonedas":
    selected_symbol = st.sidebar.selectbox("Selecciona una criptomoneda:", list(cryptos.keys()), format_func=lambda x: cryptos[x])
else:
    selected_symbol = st.sidebar.selectbox("Selecciona un índice de mercado:", list(indices.keys()), format_func=lambda x: x)

# Fecha de inicio
start_date = datetime.now() - timedelta(days=3*365)

@st.cache_data
def fetch_alpha_vantage(symbol, is_crypto=True):
    if is_crypto:
        market = "USD"
        url = f"https://www.alphavantage.co/query?function=DIGITAL_CURRENCY_DAILY&symbol={symbol.split('/')[0]}&market={market}&apikey={API_KEY}"
    else:
        url = f"https://www.alphavantage.co/query?function=TIME_SERIES_DAILY_ADJUSTED&symbol={symbol}&outputsize=full&apikey={API_KEY}"
    
    response = requests.get(url)
    data = response.json()

    if is_crypto:
        ts_key = "Time Series (Digital Currency Daily)"
        price_key = "4a. close (USD)"
    else:
        ts_key = "Time Series (Daily)"
        price_key = "4. close"

    if ts_key not in data:
        return pd.DataFrame()
    if price_key not in next(iter(data[ts_key].values())).keys():
        st.error(f"No se encontró la columna '{price_key}' en los datos recibidos de Alpha Vantage.")
        return pd.DataFrame()

    def fetch_alpha_vantage(symbol, is_crypto=False):
        api_key = os.getenv("ALPHAVANTAGE_API_KEY")
        if not api_key:
            st.error("API key de Alpha Vantage no encontrada.")
            return pd.DataFrame()

        if is_crypto:
            base_url = "https://www.alphavantage.co/query"
            params = {
                "function": "DIGITAL_CURRENCY_DAILY",
                "symbol": symbol,
                "market": "USD",
                "apikey": api_key
            }
            price_key = "4a. close (USD)"
            ts_key = "Time Series (Digital Currency Daily)"
        else:
            base_url = "https://www.alphavantage.co/query"
            params = {
                "function": "TIME_SERIES_DAILY",
                "symbol": symbol,
                "apikey": api_key
            }
            price_key = "4. close"
            ts_key = "Time Series (Daily)"

        response = requests.get(base_url, params=params)
        data = response.json()

        if ts_key not in data:
            return pd.DataFrame()

        first_row = next(iter(data[ts_key].values()))
        if price_key not in first_row:
            st.error(f"No se encontró la columna '{price_key}' en los datos recibidos de Alpha Vantage.")
            return pd.DataFrame()

        df = pd.DataFrame.from_dict(data[ts_key], orient='index')
        df.index = pd.to_datetime(df.index)
        df.sort_index(inplace=True)
        df["Close"] = df[price_key].astype(float)
        df = df[["Close"]]  # Solo dejamos la columna Close
        df.reset_index(inplace=True)
        df.rename(columns={"index": "Date"}, inplace=True)

        return df


df = fetch_alpha_vantage(selected_symbol, is_crypto=(market_type == "Criptomonedas"))

if df is not None and not df.empty:
    st.subheader(f"Evolución de {selected_symbol}")
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=df['Date'], y=df['Close'], mode='lines', name='Precio', line=dict(color='blue')))
    fig.update_layout(title=f"Curso de {selected_symbol}", xaxis_title="Fecha", yaxis_title="Precio")
    st.plotly_chart(fig, use_container_width=True)

    # SMA
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
    ax.axhline(70, linestyle='--', color='red')
    ax.axhline(30, linestyle='--', color='green')
    ax.legend()
    st.pyplot(fig)

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
else:
    st.warning("No se pudieron obtener datos de Alpha Vantage para este activo.")
