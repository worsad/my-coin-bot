import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="코인 트레이딩 터미널", layout="wide")

def get_now_kst():
    return datetime.utcnow() + timedelta(hours=9)

st.title("📊 거래소별 실시간 고저점 차트")

def get_upbit_data():
    # 실시간 시세
    t_url = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"
    t_res = requests.get(t_url).json()[0]
    
    # 60분봉 24개 수집 (빗썸과 동일한 24시간 범위)
    c_url = "https://api.upbit.com/v1/candles/minutes/60?market=KRW-BTC&count=24"
    c_res = requests.get(c_url).json()
    
    # 빗썸 스타일로 데이터 가공 (시간 포맷 정밀화)
    df = pd.DataFrame(c_res)
    df['시간'] = pd.to_datetime(df['candle_date_time_kst'])
    df = df[['시간', 'trade_price']].rename(columns={'trade_price': '가격'})
    df['가격'] = df['가격'].astype(float)
    return t_res, df.set_index('시간').sort_index()

def get_bithumb_data():
    # 실시간 시세
    t_url = "https://api.bithumb.com/public/ticker/BTC_KRW"
    t_res = requests.get(t_url).json()['data']
    
    # 1시간봉 24개 수집
    c_url = "https://api.bithumb.com/public/candlestick/BTC_KRW/1h"
    c_res = requests.get(c_url).json()['data']
    
    # 데이터 가공 및 시간 축 변환 (KST)
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
            # 상단 핵심 지표 (김프 차트 대신 수치로 요약)
            m1, m2, m3 = st.columns(3)
            up_p = int(up_ticker['trade_price'])
            bi_p = int(bi_ticker['closing_price'])
            
            m1.metric("업비트 실시간", f"{up_p:,}원", f"{up_ticker['signed_change_rate']*100:+.2f}%")
            m2.metric("빗썸 실시간", f"{bi_p:,}원", f"{((bi_p-int(bi_ticker['opening_price']))/int(bi_ticker['opening_price']))*100:+.2f}%")
            m3.metric("김치 프리미엄 (KIMP)", f"{up_p - bi_p:,}원", f"{((up_p-bi_p)/bi_p)*100:+.2f}%")

            st.divider()

            # 차트 섹션 (빗썸 방식으로 통일된 두 개의 차트)
            ch1, ch2 = st.columns(2)
            
            with ch1:
                up_high, up_low = up_df['가격'].max(), up_df['가격'].min()
                st.subheader("🔵 UPBIT 1H-Candle (24H)")
                st.markdown(f"📈 **최고:** <span style='color:red'>{int(up_high):,}</span>원 / 📉 **최저:** <span style='color:blue'>{int(up_low):,}</span>원", unsafe_allow_html=True)
                st.line_chart(up_df)

            with ch2:
                bi_high, bi_low = bi_df['가격'].max(), bi_df['가격'].min()
                st.subheader("🟠 BITHUMB 1H-Candle (24H)")
                st.markdown(f"📈 **최고:** <span style='color:red'>{int(bi_high):,}</span>원 / 📉 **최저:** <span style='color:blue'>{int(bi_low):,}</span>원", unsafe_allow_html=True)
                st.line_chart(bi_df)

            st.caption(f"Last Update (KST): {get_now_kst().strftime('%H:%M:%S')}")

        time.sleep(2)

    except Exception as e:
        st.error(f"데이터 갱신 중 오류: {e}")
        time.sleep(1)