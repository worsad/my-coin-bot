import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime, timedelta

# 페이지 설정: 화면을 최대한 넓게 사용
st.set_page_config(page_title="빗썸 스타일 터미널", layout="wide")

def get_now_kst():
    return datetime.utcnow() + timedelta(hours=9)

st.title("📊 거래소별 꽉 찬 실시간 차트 (24H)")

def get_upbit_data():
    t_url = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"
    t_res = requests.get(t_url).json()[0]
    
    c_url = "https://api.upbit.com/v1/candles/minutes/60?market=KRW-BTC&count=24"
    c_res = requests.get(c_url).json()
    
    df = pd.DataFrame(c_res)
    # 시간 축을 짧게 변환 (HH:mm 형식으로 가독성 증대)
    df['시간'] = pd.to_datetime(df['candle_date_time_kst']).dt.strftime('%H:%M')
    df = df[['시간', 'trade_price']].rename(columns={'trade_price': '가격'})
    return t_res, df.set_index('시간').sort_index()

def get_bithumb_data():
    t_url = "https://api.bithumb.com/public/ticker/BTC_KRW"
    t_res = requests.get(t_url).json()['data']
    
    c_url = "https://api.bithumb.com/public/candlestick/BTC_KRW/1h"
    c_res = requests.get(c_url).json()['data']
    
    df = pd.DataFrame(c_res, columns=['시간', '시가', '종가', '고가', '저가', '거래량'])
    # 시간 축 변환
    df['시간'] = (pd.to_datetime(df['시간'].astype(float), unit='ms') + timedelta(hours=9)).dt.strftime('%H:%M')
    df = df.tail(24)[['시간', '종가']].rename(columns={'종가': '가격'})
    df['가격'] = df['가격'].astype(float)
    return t_res, df.set_index('시간')

# 화면 전체를 채우기 위한 공간 확보
placeholder = st.empty()

while True:
    try:
        up_ticker, up_df = get_upbit_data()
        bi_ticker, bi_df = get_bithumb_data()

        with placeholder.container():
            # 1. 상단 실시간 지표 (깔끔하게 3칸)
            m1, m2, m3 = st.columns(3)
            up_p = int(up_ticker['trade_price'])
            bi_p = int(bi_ticker['closing_price'])
            
            m1.metric("UPBIT 현재가", f"{up_p:,}원", f"{up_ticker['signed_change_rate']*100:+.2f}%")
            m2.metric("BITHUMB 현재가", f"{bi_p:,}원", f"{((bi_p-int(bi_ticker['opening_price']))/int(bi_ticker['opening_price']))*100:+.2f}%")
            m3.metric("KIMP (가격차)", f"{up_p - bi_p:,}원", f"{((up_p-bi_p)/bi_p)*100:+.2f}%")

            # 2. 차트 구역 (여백 최소화)
            ch1, ch2 = st.columns(2)
            
            with ch1:
                st.write("### 🔵 UPBIT")
                # 최고/최저가 표시
                up_h, up_l = up_df['가격'].max(), up_df['가격'].min()
                st.caption(f"Max: {int(up_h):,} | Min: {int(up_l):,}")
                # 멘토의 팁: st.area_chart는 빗썸 느낌을 줍니다.
                st.area_chart(up_df, use_container_width=True)

            with ch2:
                st.write("### 🟠 BITHUMB")
                bi_h, bi_l = bi_df['가격'].max(), bi_df['가격'].min()
                st.caption(f"Max: {int(bi_h):,} | Min: {int(bi_l):,}")
                st.area_chart(bi_df, use_container_width=True)

            # 불필요한 하단 공간 없이 바로 업데이트 시각 표시
            st.caption(f"Last sync: {get_now_kst().strftime('%H:%M:%S')}")

        time.sleep(2)

    except Exception as e:
        time.sleep(1)