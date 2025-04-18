import requests
import os
from dotenv import load_dotenv

# Cargar la clave API desde el archivo .env
load_dotenv()
api_key = os.getenv("ALPHA_VANTAGE_API_KEY")

# Ticker de prueba (ETF del S&P 500)
symbol = "SPY"

# Endpoint gratuito
url = "https://www.alphavantage.co/query"
params = {
    "function": "TIME_SERIES_DAILY",
    "symbol": symbol,
    "outputsize": "compact",
    "apikey": api_key
}

# Llamada a la API
response = requests.get(url, params=params)

# Procesar la respuesta
if response.status_code == 200:
    data = response.json()
    if "Time Series (Daily)" in data:
        print("✅ Conexión exitosa. Últimos datos disponibles:")
        latest_date = list(data["Time Series (Daily)"].keys())[0]
        latest_data = data["Time Series (Daily)"][latest_date]
        print(f"{symbol} - {latest_date} - Precio cierre: {latest_data['4. close']}")
    else:
        print("⚠️ Respuesta recibida, pero sin datos de tiempo. Error:")
        print(data)
else:
    print("❌ Error al conectar con Alpha Vantage.")
    print("Código de estado HTTP:", response.status_code)
