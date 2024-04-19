import pandas as pd
import ta
import ccxt 
import schedule


pd.set_option('display.max_rows', None)

# Initialize the Binance exchange object with your API credentials
api_key = 'ZfEY8UJxwAaEkzUpEqHQ6ZI22OWVroA3iFggnKaTiuLkYxVSbMtOyIkTNje4q8yS'
api_secret = 'D1bo6V8bi196PCMlGOgMNcRWEbHD8LgavQyctsBjnCq83kaCkGXx8mLvywG24hN'

exchange = ccxt.binance()
bars = exchange.fetch_ohlcv('BTC/USDT', timeframe='1d', limit=200)
df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')

def tr(df):
    df['previous_close'] = df['close'].shift(1)
    df['high-low'] = df['high'] - df['low']
    df['high-pc'] = abs(df['high'] - df['previous_close'])
    df['low-pc'] = abs(df['low'] - df['previous_close'])
    return df[['high-low', 'high-pc', 'low-pc']].max(axis=1)

def atr(df, period=14):
    df['tr'] = tr(df)
    return df['tr'].rolling(period).mean()

def supertrend(df, period=7, multiplier=3):
    df['atr'] = atr(df, period=period)
    df['basic_upperband'] = ((df['high'] + df['low']) / 2) + (multiplier * df['atr'])
    df['basic_lowerband'] = ((df['high'] + df['low']) / 2) - (multiplier * df['atr'])
    df['upperband'] = df['basic_upperband']
    df['lowerband'] = df['basic_lowerband']
    df['in_uptrend'] = False

    for current in range(1, len(df.index)):
        previous = current - 1
        if df['close'][current] > df['upperband'][previous]:
            df.loc[current, 'in_uptrend'] = True
        elif df['close'][current] < df['lowerband'][previous]:
            df.loc[current, 'in_uptrend'] = False
        else:
            df.loc[current, 'in_uptrend'] = df['in_uptrend'][previous]
            if df['in_uptrend'][current]:
                df.loc[current, 'lowerband'] = max(df['basic_lowerband'][current], df['lowerband'][previous])
            else:
                df.loc[current, 'upperband'] = min(df['basic_upperband'][current], df['upperband'][previous])

    return df

df = supertrend(df, period=5)
print(df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'upperband', 'lowerband', 'in_uptrend','tr','atr']])
