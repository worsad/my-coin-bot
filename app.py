import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="실시간 비트코인 분석기", layout="wide")

def get_now_kst():
    return datetime.utcnow() + timedelta(hours=9)

st.title("⚡ 실시간 비트코인 통합 대시보드")

# 1. 업비트 실시간 & 차트 데이터
def get_upbit_data():
    # 실시간 시세 및 변동률
    t_url = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"
    t_res = requests.get(t_url).json()[0]
    
    # 차트용 (60분봉 24개)
    c_url = "https://api.upbit.com/v1/candles/minutes/60?market=KRW-BTC&count=24"
    c_res = requests.get(c_url).json()
    df = pd.DataFrame(c_res)[['candle_date_time_kst', 'trade_price']].rename(columns={'candle_date_time_kst': '시간', 'trade_price': '업비트'})
    
    return t_res, df.set_index('시간').sort_index()

# 2. 빗썸 실시간 & 차트 데이터
def get_bithumb_data():
    # 실시간 시세 및 변동률
    t_url = "https://api.bithumb.com/public/ticker/BTC_KRW"
    t_res = requests.get(t_url).json()['data']
    
    # 차트용 (1시간봉 24개)
    c_url = "https://api.bithumb.com/public/candlestick/BTC_KRW/1h"
    c_res = requests.get(c_url).json()['data']
    df = pd.DataFrame(c_res, columns=['시간', '시가', '종가', '고가', '저가', '거래량'])
    df['시간'] = pd.to_datetime(df['시간'].astype(float), unit='ms') + timedelta(hours=9)
    df = df.tail(24)[['시간', '종가']].rename(columns={'종가': '빗썸'})
    
    return t_res, df.set_index('시간')

placeholder = st.empty()

while True:
    try:
        up_ticker, up_df = get_upbit_data()
        bi_ticker, bi_df = get_bithumb_data()

        with placeholder.container():
            # --- 상단 실시간 전광판 ---
            c1, c2, c3 = st.columns(3)
            
            # 업비트 실시간 (전일대비 변동률 포함)
            up_price = int(up_ticker['trade_price'])
            up_change = up_ticker['signed_change_rate'] * 100
            c1.metric("업비트 실시간", f"{up_price:,}원", f"{up_change:+.2f}%")

            # 빗썸 실시간 (전일대비 변동률 계산)
            bi_price = int(bi_ticker['closing_price'])
            bi_open = int(bi_ticker['opening_price'])
            bi_change = ((bi_price - bi_open) / bi_open) * 100
            c2.metric("빗썸 실시간", f"{bi_price:,}원", f"{bi_change:+.2f}%")

            # 김치 프리미엄
            diff = up_price - bi_price
            diff_rate = (diff / bi_price) * 100
            c3.metric("김치 프리미엄", f"{diff:,}원", f"{diff_rate:+.2f}%")

            # --- 중단 차트 섹션 ---
            st.divider()
            ch1, ch2 = st.columns(2)
            with ch1:
                st.subheader("🔵 업비트 24시간 추이")
                st.line_chart(up_df)
            with ch2:
                st.subheader("🟠 빗썸 24시간 추이")
                st.line_chart(bi_df)

            st.caption(f"최종 갱신 (KST): {get_now_kst().strftime('%H:%M:%S')}")

        time.sleep(2) # 렉 방지 및 API 부하 조절

    except Exception as e:
        time.sleep(1)