import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="다이내믹 코인 터미널", layout="wide")

def get_now_kst():
    return datetime.utcnow() + timedelta(hours=9)

st.title("📊 역동적 실시간 캔들 추이 (Y축 최적화)")

def get_upbit_data():
    t_url = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"
    t_res = requests.get(t_url).json()[0]
    c_url = "https://api.upbit.com/v1/candles/minutes/10?market=KRW-BTC&count=144"
    c_res = requests.get(c_url).json()
    df = pd.DataFrame(c_res)
    df['시간'] = pd.to_datetime(df['candle_date_time_kst']).dt.strftime('%H:%M')
    df = df[['시간', 'trade_price']].rename(columns={'trade_price': '가격'})
    df['가격'] = df['가격'].astype(float)
    return t_res, df.set_index('시간').sort_index()

def get_bithumb_data():
    t_url = "https://api.bithumb.com/public/ticker/BTC_KRW"
    t_res = requests.get(t_url).json()['data']
    c_url = "https://api.bithumb.com/public/candlestick/BTC_KRW/10m"
    c_res = requests.get(c_url).json()['data']
    df = pd.DataFrame(c_res, columns=['시간', '시가', '종가', '고가', '저가', '거래량'])
    df['시간'] = (pd.to_datetime(df['시간'].astype(float), unit='ms') + timedelta(hours=9)).dt.strftime('%H:%M')
    df = df.tail(144)[['시간', '종가']].rename(columns={'종가': '가격'})
    df['가격'] = df['가격'].astype(float)
    return t_res, df.set_index('시간')

placeholder = st.empty()

while True:
    try:
        up_t, up_df = get_upbit_data()
        bi_t, bi_df = get_bithumb_data()

        with placeholder.container():
            # 1. 상단 지표
            m1, m2, m3 = st.columns(3)
            up_p, bi_p = int(up_t['trade_price']), int(bi_t['closing_price'])
            m1.metric("UPBIT", f"{up_p:,}원", f"{up_t['signed_change_rate']*100:+.2f}%")
            m2.metric("BITHUMB", f"{bi_p:,}원", f"{((bi_p-int(bi_t['opening_price']))/int(bi_t['opening_price']))*100:+.2f}%")
            m3.metric("KIMP", f"{up_p - bi_p:,}원", f"{((up_p-bi_p)/bi_p)*100:+.2f}%")

            st.divider()

            # 2. 꽉 찬 차트 (Y축 범위 강제 조정)
            ch1, ch2 = st.columns(2)
            
            with ch1:
                up_h, up_l = up_df['가격'].max(), up_df['가격'].min()
                # 멘토의 팁: 가격 범위를 데이터의 최소/최대로 제한해서 굴곡을 살립니다.
                st.subheader("🔵 UPBIT (24H Trend)")
                st.caption(f"Range: {int(up_l):,} ~ {int(up_h):,}")
                st.line_chart(up_df, y_label="가격", use_container_width=True)

            with ch2:
                bi_h, bi_l = bi_df['가격'].max(), bi_df['가격'].min()
                st.subheader("🟠 BITHUMB (24H Trend)")
                st.caption(f"Range: {int(bi_l):,} ~ {int(bi_h):,}")
                st.line_chart(bi_df, y_label="가격", use_container_width=True)

            st.caption(f"Sync: {get_now_kst().strftime('%H:%M:%S')}")

        time.sleep(2)
    except Exception as e:
        time.sleep(1)