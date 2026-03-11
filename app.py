import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="코인 데이터 터미널", layout="wide")

def get_now_kst():
    return datetime.utcnow() + timedelta(hours=9)

st.title("📊 거래소별 실시간 추이 및 고저점 분석")

def get_upbit_data():
    t_url = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"
    t_res = requests.get(t_url).json()[0]
    
    c_url = "https://api.upbit.com/v1/candles/minutes/60?market=KRW-BTC&count=24"
    c_res = requests.get(c_url).json()
    # 빗썸과 동일하게 종가(trade_price) 기준으로 통일
    df = pd.DataFrame(c_res)[['candle_date_time_kst', 'trade_price']].rename(columns={'candle_date_time_kst': '시간', 'trade_price': '가격'})
    df['시간'] = pd.to_datetime(df['시간'])
    return t_res, df.set_index('시간').sort_index()

def get_bithumb_data():
    t_url = "https://api.bithumb.com/public/ticker/BTC_KRW"
    t_res = requests.get(t_url).json()['data']
    
    c_url = "https://api.bithumb.com/public/candlestick/BTC_KRW/1h"
    c_res = requests.get(c_url).json()['data']
    df = pd.DataFrame(c_res, columns=['시간', '시가', '종가', '고가', '저가', '거래량'])
    df['시간'] = pd.to_datetime(df['시간'].astype(float), unit='ms') + timedelta(hours=9)
    df = df.tail(24)[['시간', '종가']].rename(columns={'종가': '가격'})
    df['가격'] = df['가격'].astype(float)
    return t_res, df.set_index('시간')

placeholder = st.empty()

while True:
    try:
        up_ticker, up_df = get_upbit_data()
        bi_ticker, bi_df = get_bithumb_data()

        with placeholder.container():
            # 상단 메트릭 (현재가 및 김프)
            m1, m2, m3 = st.columns(3)
            up_p = int(up_ticker['trade_price'])
            bi_p = int(bi_ticker['closing_price'])
            
            m1.metric("업비트", f"{up_p:,}원", f"{up_ticker['signed_change_rate']*100:+.2f}%")
            m2.metric("빗썸", f"{bi_p:,}원", f"{((bi_p-int(bi_ticker['opening_price']))/int(bi_ticker['opening_price']))*100:+.2f}%")
            m3.metric("김치 프리미엄", f"{up_p - bi_p:,}원", f"{((up_p-bi_p)/bi_p)*100:+.2f}%")

            st.divider()

            # 차트 섹션
            ch1, ch2 = st.columns(2)
            
            with ch1:
                # 업비트 최고/최저가 추출
                up_high, up_low = up_df['가격'].max(), up_df['가격'].min()
                st.subheader("🔵 업비트 (24H)")
                st.caption(f"최고: {int(up_high):,}원 / 최저: {int(up_low):,}원")
                st.line_chart(up_df)

            with ch2:
                # 빗썸 최고/최저가 추출
                bi_high, bi_low = bi_df['가격'].max(), bi_df['가격'].min()
                st.subheader("🟠 빗썸 (24H)")
                st.caption(f"최고: {int(bi_high):,}원 / 최저: {int(bi_low):,}원")
                st.line_chart(bi_df)

            st.caption(f"업데이트: {get_now_kst().strftime('%H:%M:%S')}")

        time.sleep(2)

    except Exception as e:
        time.sleep(1)