import pandas as pd
import ta
import ccxt 
import schedule
import time 
import numpy as np
from datetime import datetime

pd.set_option('display.max_rows', None)

# Initialize the Binance exchange object with your API credentials
exchange = ccxt.binance({
    'apiKey': 'ohwFslNAUzRcflAEsj7snpKANezjutxxNqokUIJAKkWZClF1WIQVj9wYOM5tw3Yo',
    'secret': 'HsEKBjMsp2fXlqFoggJ1b5nMRAbaKKHP0iQ98Ss83WyFQ0Fop1ftslsEdb4IosPh',
    'enableRateLimit': True,  
    'options': {
        'defaultType': 'spot',
    'urls': {
        'api': {
            'public': 'https://testnet.binance.vision/api/v3',
            'private': 'https://testnet.binance.vision/api/v3',
        }
    }
    },
})
exchange.set_sandbox_mode(True)

# Fetch the balance
balance = exchange.fetch_balance()

in_position = True

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
    df['in_uptrend'] = True

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

#df = supertrend(df, period=5)
#print(df[['timestamp', 'open', 'high', 'low', 'close', 'volume', 'upperband', 'lowerband', 'in_uptrend','tr','atr']])

def check_buy_sell_signals(df):
    global in_position
    print("checking for buy or sells")
    print(df.tail(2))
    last_row_index = len(df.index) - 1
    previous_row_index = last_row_index - 1

    #print(last_row_index)
    #print(previous_row_index)

    if not df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
        print("changed to uptrend, buy")
        if not in_Position:
            order = exchange.create_market_buy_order('ETH/USDT',0.01 )
            print(order)
            in_position = True
        else:
            print("Already in a position")

    if df['in_uptrend'][previous_row_index] and df['in_uptrend'][last_row_index]:
        print("changed to downtrend, sell")
        if in_position:
            order = exchange.create_market_sell_order('ETH/USDT',0.01 )
            print(order)
            in_position = False
        else:
            print("You are not in a position")



    

def run_bot():
    print("Fetching new bars for {}".format(datetime.now().isoformat()))
    bars = exchange.fetch_ohlcv('ETH/USDT', timeframe='1m', limit=5 )
    df = pd.DataFrame(bars[:-1], columns=['timestamp', 'open', 'high', 'low', 'close', 'volume'])
    df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
    #print(df)

    supertrend_data = supertrend(df)
    #print(supertrend_data)

    check_buy_sell_signals(supertrend_data)

schedule.every(1).minutes.do(run_bot)

while True:
    schedule.run_pending()
    time.sleep(1)
