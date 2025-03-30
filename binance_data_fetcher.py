
import ccxt
import pandas as pd


# Configuración de la API de Binance
api_key = 'URd6TYDCROAcY3VLpyywWev6yR9SIKhWfLgit0z4J3DlU3lIjAOo3uXRVwfV3nI2'  # Reemplaza con tu clave API
api_secret = '4fxu5oqv10kZ4h4taLH1RO4pIo8fikcnQq7iBKqJxQFcybU2reDUUdKhhmlaPHWb'  # Reemplaza con tu clave secreta

# Conexión a Binance con ajuste de tiempo
exchange = ccxt.binance({
    'apiKey': api_key,
    'secret': api_secret,
})
exchange.options['adjustForTimeDifference'] = True  # Ajusta automáticamente la diferencia de tiempo

# Parámetros
symbol = 'BTC/USDT'
timeframe = '1d'
start_date = '2020-01-01T00:00:00Z'
since = exchange.parse8601(start_date)

# Descargar datos históricos
print(f"Descargando datos de {symbol} desde {start_date}...")
ohlcv = exchange.fetch_ohlcv(symbol, timeframe, since)

# Procesar y guardar datos
columns = ['timestamp', 'open', 'high', 'low', 'close', 'volume']
df = pd.DataFrame(ohlcv, columns=columns)
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
df.to_csv(f'{symbol.replace("/", "_")}_historical_data.csv', index=False)

print(f"Datos guardados en {symbol.replace('/', '_')}_historical_data.csv")