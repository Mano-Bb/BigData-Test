# -*- coding: utf-8 -*-

# 필요한 라이브러리 설치
!pip install pandas numpy matplotlib statsmodels requests

# NanumGothic 폰트 설치
!apt-get install -qq fonts-nanum

# Matplotlib 폰트 캐시 초기화
!rm -rf ~/.cache/matplotlib

# 라이브러리 임포트
import matplotlib.pyplot as plt
import matplotlib.font_manager as fm
import pandas as pd
import numpy as np
import requests
import json
from datetime import datetime

# 폰트 확인
fonts = fm.findSystemFonts(fontpaths=None, fontext='ttf')
nanum_fonts = [font for font in fonts if 'NanumGothic' in font]
print(nanum_fonts)

# NanumGothic 폰트 설정
font_path = '/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
fontprop = fm.FontProperties(fname=font_path)
plt.rc('font', family=fontprop.get_name())
plt.rcParams['axes.unicode_minus'] = False

# Alpha Vantage API 키 및 기본 URL 설정
ALPHA_VANTAGE_API_KEY = 'MY_OWN_KEY'
BASE_URL = 'https://www.alphavantage.co/query'

def fetch_stock_data(symbol, interval='daily'):
    """
    주식 데이터를 Alpha Vantage API를 통해 가져오는 함수
    """
    params = {
        'function': 'TIME_SERIES_DAILY',
        'symbol': symbol,
        'apikey': ALPHA_VANTAGE_API_KEY,
        'outputsize': 'full'
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()
        # JSON 데이터를 파일로 저장
    with open(f'{symbol}_stock_data.json', 'w') as json_file:
        json.dump(data, json_file, indent=4)
    return data

def json_to_dataframe(json_data):
    """
    JSON 데이터를 pandas DataFrame으로 변환하는 함수
    """
    time_series = json_data.get('Time Series (Daily)', {})
    df = pd.DataFrame.from_dict(time_series, orient='index')
    df = df.rename(columns={
        '1. open': 'Open',
        '2. high': 'High',
        '3. low': 'Low',
        '4. close': 'Close',
        '5. volume': 'Volume'
    })
    df.index = pd.to_datetime(df.index)
    df = df.sort_index()
    df = df.astype(float)
    return df

def calculate_moving_average(df, window):
    """
    이동평균선을 계산하는 함수
    """
    return df['Close'].rolling(window=window).mean()

def calculate_rsi(df, window=14):
    """
    상대강도지수(RSI)를 계산하는 함수
    """
    delta = df['Close'].diff()
    gain = (delta.where(delta > 0, 0)).rolling(window=window).mean()
    loss = (-delta.where(delta < 0, 0)).rolling(window=window).mean()
    rs = gain / loss
    rsi = 100 - (100 / (1 + rs))
    return rsi

def calculate_macd(df, span_short=12, span_long=26, span_signal=9):
    """
    MACD 지표를 계산하는 함수
    """
    ema_short = df['Close'].ewm(span=span_short, adjust=False).mean()
    ema_long = df['Close'].ewm(span=span_long, adjust=False).mean()
    macd = ema_short - ema_long
    signal = macd.ewm(span=span_signal, adjust=False).mean()
    return macd, signal

# 주요 주식 종목 리스트
symbols = ['AAPL', 'TSLA', 'MSFT']

# 종목별 데이터 가져오기 및 DataFrame으로 변환
stock_data = {}
for symbol in symbols:
    data = fetch_stock_data(symbol)
    df = json_to_dataframe(data)
    stock_data[symbol] = df

# 기술적 지표 계산
for symbol in symbols:
    df = stock_data[symbol]
    df['MA50'] = calculate_moving_average(df, 50)
    df['MA200'] = calculate_moving_average(df, 200)
    df['RSI'] = calculate_rsi(df)
    df['MACD'], df['Signal'] = calculate_macd(df)
    stock_data[symbol] = df

# 데이터 시각화
for symbol in symbols:
    df = stock_data[symbol]

    # 종가 및 이동평균선 플롯
    plt.figure(figsize=(14,7))
    plt.plot(df.index, df['Close'], label='종가')
    plt.plot(df.index, df['MA50'], label='MA50')
    plt.plot(df.index, df['MA200'], label='MA200')
    plt.title(f'{symbol} 종가 및 이동평균선')
    plt.xlabel('날짜')
    plt.ylabel('가격')
    plt.legend()
    plt.show()

    # RSI 플롯
    plt.figure(figsize=(14,4))
    plt.plot(df.index, df['RSI'], label='RSI')
    plt.axhline(70, color='red', linestyle='--')
    plt.axhline(30, color='green', linestyle='--')
    plt.title(f'{symbol} 상대강도지수(RSI)')
    plt.xlabel('날짜')
    plt.ylabel('RSI')
    plt.legend()
    plt.show()

    # MACD 플롯
    plt.figure(figsize=(14,4))
    plt.plot(df.index, df['MACD'], label='MACD')
    plt.plot(df.index, df['Signal'], label='Signal Line')
    plt.title(f'{symbol} MACD')
    plt.xlabel('날짜')
    plt.ylabel('MACD')
    plt.legend()
    plt.show()

# 주가 변동성 분석
for symbol in symbols:
    df = stock_data[symbol]
    df['Daily_Return'] = df['Close'].pct_change()
    volatility = df['Daily_Return'].std() * np.sqrt(252)  # 연간 변동성
    print(f"{symbol} 연간 변동성: {volatility:.2%}")

    # 일일 수익률 히스토그램
    plt.figure(figsize=(10,5))
    df['Daily_Return'].hist(bins=50)
    plt.title(f'{symbol} 일일 수익률 분포')
    plt.xlabel('수익률')
    plt.ylabel('빈도수')
    plt.show()

# 투자 전략 수립: MA 교차 매매 전략
for symbol in symbols:
    df = stock_data[symbol].copy()
    df = df.dropna()
    df['Signal'] = 0
    df['Signal'][df['MA50'] > df['MA200']] = 1
    df['Position'] = df['Signal'].diff()

    plt.figure(figsize=(14,7))
    plt.plot(df.index, df['Close'], label='종가', alpha=0.5)
    plt.plot(df.index, df['MA50'], label='MA50', alpha=0.9)
    plt.plot(df.index, df['MA200'], label='MA200', alpha=0.9)

    # 매수 신호
    plt.plot(df[df['Position'] == 1].index,
             df['MA50'][df['Position'] == 1],
             '^', markersize=10, color='g', label='매수 신호')

    # 매도 신호
    plt.plot(df[df['Position'] == -1].index,
             df['MA50'][df['Position'] == -1],
             'v', markersize=10, color='r', label='매도 신호')

    plt.title(f'{symbol} MA 교차 매매 전략')
    plt.xlabel('날짜')
    plt.ylabel('가격')
    plt.legend()
    plt.show()

    # 전략 수익률 계산
    df['Strategy_Return'] = df['Daily_Return'] * df['Signal'].shift(1)
    cumulative_strategy = (1 + df['Strategy_Return']).cumprod() - 1
    cumulative_market = (1 + df['Daily_Return']).cumprod() - 1

    plt.figure(figsize=(14,7))
    plt.plot(cumulative_strategy, label='전략 수익률')
    plt.plot(cumulative_market, label='시장 수익률')
    plt.title(f'{symbol} 전략 vs 시장 수익률')
    plt.xlabel('날짜')
    plt.ylabel('누적 수익률')
    plt.legend()
    plt.show()

# 투자 전략 수립: MA 교차 매매 전략
for symbol in symbols:
    df = stock_data[symbol].copy()
    df = df.dropna()
    df['Signal'] = 0
    df['Signal'][df['MA50'] > df['MA200']] = 1
    df['Position'] = df['Signal'].diff()

    # 초기 투자 금액과 잔고 설정
    initial_balance = 10000  # 초기 투자 금액
    balance = initial_balance
    shares = 0  # 보유 주식 수
    buy_price = 0  # 매수 가격

    # 거래 내역 저장
    trades = []

    for i in range(len(df)):
        if df['Position'].iloc[i] == 1 and balance > 0:  # 매수 신호
            shares = balance // df['Close'].iloc[i]  # 매수할 수 있는 주식 수
            buy_price = df['Close'].iloc[i]
            balance -= shares * buy_price  # 잔고에서 매수 금액 차감
            trades.append(('Buy', df.index[i], df['Close'].iloc[i], shares))

        elif df['Position'].iloc[i] == -1 and shares > 0:  # 매도 신호
            balance += shares * df['Close'].iloc[i]  # 매도 금액 추가
            trades.append(('Sell', df.index[i], df['Close'].iloc[i], shares))
            shares = 0  # 모든 주식을 매도하였으므로 보유 주식 수 0으로 설정

    # 최종 잔고 계산
    final_balance = balance + shares * df['Close'].iloc[-1]  # 매도 후 잔고 + 보유 주식의 현재 가치
    total_return = (final_balance - initial_balance) / initial_balance * 100  # 총 수익률 계산

    print(f"{symbol} 최종 잔고: {final_balance:.2f}, 총 수익률: {total_return:.2f}%")
    print("거래 내역:")
    for trade in trades:
        print(trade)

    # 시각화
    plt.figure(figsize=(14,7))
    plt.plot(df.index, df['Close'], label='종가', alpha=0.5)
    plt.plot(df.index, df['MA50'], label='MA50', alpha=0.9)
    plt.plot(df.index, df['MA200'], label='MA200', alpha=0.9)

    # 매수 신호
    plt.plot(df[df['Position'] == 1].index,
             df['MA50'][df['Position'] == 1],
             '^', markersize=10, color='g', label='매수 신호')

    # 매도 신호
    plt.plot(df[df['Position'] == -1].index,
             df['MA50'][df['Position'] == -1],
             'v', markersize=10, color='r', label='매도 신호')

    plt.title(f'{symbol} MA 교차 매매 전략')
    plt.xlabel('날짜')
    plt.ylabel('가격')
    plt.legend()
    plt.show()
