import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime, timedelta
import plotly.express as px # 전문 차트 라이브러리 추가

st.set_page_config(page_title="고해상도 다이내믹 터미널", layout="wide")

def get_now_kst():
    return datetime.utcnow() + timedelta(hours=9)

st.title("📈 24시간 실시간 다이내믹 차트 (Y축 최적화)")

def get_upbit_data():
    t_url = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"
    t_res = requests.get(t_url).json()[0]
    c_url = "https://api.upbit.com/v1/candles/minutes/10?market=KRW-BTC&count=144"
    c_res = requests.get(c_url).json()
    df = pd.DataFrame(c_res)
    df['시간'] = pd.to_datetime(df['candle_date_time_kst'])
    df = df[['시간', 'trade_price']].rename(columns={'trade_price': '가격'})
    df['가격'] = df['가격'].astype(float)
    return t_res, df.sort_values('시간')

def get_bithumb_data():
    t_url = "https://api.bithumb.com/public/ticker/BTC_KRW"
    t_res = requests.get(t_url).json()['data']
    c_url = "https://api.bithumb.com/public/candlestick/BTC_KRW/10m"
    c_res = requests.get(c_url).json()['data']
    df = pd.DataFrame(c_res, columns=['시간', '시가', '종가', '고가', '저가', '거래량'])
    df['시간'] = pd.to_datetime(df['시간'].astype(float), unit='ms') + timedelta(hours=9)
    df = df.tail(144)[['시간', '종가']].rename(columns={'종가': '가격'})
    df['가격'] = df['가격'].astype(float)
    return t_res, df.sort_values('시간')

placeholder = st.empty()

while True:
    try:
        up_t, up_df = get_upbit_data()
        bi_t, bi_df = get_bithumb_data()

        with placeholder.container():
            m1, m2, m3 = st.columns(3)
            up_p, bi_p = int(up_t['trade_price']), int(bi_t['closing_price'])
            m1.metric("UPBIT", f"{up_p:,}원", f"{up_t['signed_change_rate']*100:+.2f}%")
            m2.metric("BITHUMB", f"{bi_p:,}원", f"{((bi_p-int(bi_t['opening_price']))/int(bi_t['opening_price']))*100:+.2f}%")
            m3.metric("KIMP", f"{up_p - bi_p:,}원", f"{((up_p-bi_p)/bi_p)*100:+.2f}%")

            st.divider()

            ch1, ch2 = st.columns(2)
            
            # 멘토의 핵심: Plotly를 이용한 Y축 다이내믹 스케일링 함수
            def create_dynamic_chart(df, title, color):
                fig = px.line(df, x='시간', y='가격', title=title)
                # 최고/최저가에 맞춰 Y축 범위를 강제로 줌인 (여백 0.1%)
                y_min, y_max = df['가격'].min(), df['가격'].max()
                margin = (y_max - y_min) * 0.1
                fig.update_yaxes(range=[y_min - margin, y_max + margin], tickformat=",d")
                fig.update_traces(line_color=color)
                fig.update_layout(height=400, margin=dict(l=0, r=0, t=40, b=0))
                return fig

            with ch1:
                st.plotly_chart(create_dynamic_chart(up_df, "🔵 UPBIT 24H (Dynamic)", "#0066FF"), use_container_width=True)
            with ch2:
                st.plotly_chart(create_dynamic_chart(bi_df, "🟠 BITHUMB 24H (Dynamic)", "#FF9900"), use_container_width=True)

            st.caption(f"Sync: {get_now_kst().strftime('%H:%M:%S')}")

        time.sleep(2)
    except Exception as e:
        time.sleep(1)