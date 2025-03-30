
import pandas as pd

def corregir_bollinger(df: pd.DataFrame, sma_column='SMA', price_column='Close', sma_period=20):
    std_dev = df[price_column].rolling(window=sma_period).std()

    # Asegurar que std_dev sea Serie (1D) y no DataFrame (2D)
    if isinstance(std_dev, pd.DataFrame):
        std_dev = std_dev.iloc[:, 0]

    df['Upper Band'] = df[sma_column] + (2 * std_dev)
    df['Lower Band'] = df[sma_column] - (2 * std_dev)
    return df
