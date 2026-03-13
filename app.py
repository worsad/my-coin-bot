import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime, timedelta, UTC # UTC 추가

st.set_page_config(page_title="멀티 타임프레임 터미널", layout="wide")

# 1. 멘토의 수정: 구식 utcnow()를 최신 표준으로 교체
def get_now_kst():
    # 로그 에러 원인 해결: datetime.now(UTC) 사용
    return datetime.now(UTC) + timedelta(hours=9)

st.title("🚀 비트코인 전천후 분석 터미널")

# 2. 멘토의 핵심: 분봉 선택 메뉴
interval = st.selectbox(
    "차트 주기를 선택하세요",
    ["1분봉", "5분봉", "10분봉", "30분봉", "1시간봉", "1일봉"],
    index=2 # 기본값 10분봉
)

# 선택에 따른 API 파라미터 매핑
mapping = {
    "1분봉": ("minutes/1", 144, "1m"),
    "5분봉": ("minutes/5", 144, "5m"),
    "10분봉": ("minutes/10", 144, "10m"),
    "30분봉": ("minutes/30", 144, "30m"),
    "1시간봉": ("minutes/60", 144, "1h"),
    "1일봉": ("days", 100, "1d")
}

up_unit, up_count, bi_unit = mapping[interval]

def get_upbit_data(unit, count):
    t_url = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"
    t_res = requests.get(t_url).json()[0]
    
    c_url = f"https://api.upbit.com/v1/candles/{unit}?market=KRW-BTC&count={count}"
    c_res = requests.get(c_url).json()
    df = pd.DataFrame(c_res)
    df['시간'] = pd.to_datetime(df['candle_date_time_kst'])
    df = df[['시간', 'trade_price']].rename(columns={'trade_price': '가격'})
    return t_res, df.sort_values('시간')

def get_bithumb_data(unit, count):
    t_url = "https://api.bithumb.com/public/ticker/BTC_KRW"
    t_res = requests.get(t_url).json()['data']
    
    if "d" in unit:
        c_url = "https://api.bithumb.com/public/candlestick/BTC_KRW/24h"
    else:
        c_url = f"https://api.bithumb.com/public/candlestick/BTC_KRW/{unit}"
        
    c_res = requests.get(c_url).json()['data']
    df = pd.DataFrame(c_res, columns=['시간', '시가', '종가', '고가', '저가', '거래량'])
    df['시간'] = pd.to_datetime(df['시간'].astype(float), unit='ms') + timedelta(hours=9)
    df = df.tail(count)[['시간', '종가']].rename(columns={'종가': '가격'})
    df['가격'] = df['가격'].astype(float)
    return t_res, df.sort_values('시간')

placeholder = st.empty()

while True:
    try:
        up_t, up_df = get_upbit_data(up_unit, up_count)
        bi_t, bi_df = get_bithumb_data(bi_unit, up_count)

        with placeholder.container():
            m1, m2, m3 = st.columns(3)
            up_p, bi_p = int(up_t['trade_price']), int(bi_t['closing_price'])
            m1.metric(f"UPBIT ({interval})", f"{up_p:,}원", f"{up_t['signed_change_rate']*100:+.2f}%")
            m2.metric(f"BITHUMB ({interval})", f"{bi_p:,}원", f"{((bi_p-int(bi_t['opening_price']))/int(bi_t['opening_price']))*100:+.2f}%")
            m3.metric("KIMP", f"{up_p - bi_p:,}원", f"{((up_p-bi_p)/bi_p)*100:+.2f}%")

            st.divider()

            def create_chart(df, title, color):
                fig = px.line(df, x='시간', y='가격', title=title)
                y_min, y_max = df['가격'].min(), df['가격'].max()
                margin = (y_max - y_min) * 0.05
                fig.update_yaxes(range=[y_min - margin, y_max + margin], tickformat=",d")
                fig.update_traces(line_color=color)
                fig.update_layout(height=450, margin=dict(l=0, r=0, t=40, b=0))
                return fig

            ch1, ch2 = st.columns(2)
            # 3. 멘토의 수정: use_container_width=True를 width='stretch'로 교체
            with ch1:
                st.plotly_chart(create_chart(up_df, f"🔵 UPBIT - {interval}", "#0066FF"), width='stretch')
            with ch2:
                st.plotly_chart(create_chart(bi_df, f"🟠 BITHUMB - {interval}", "#FF9900"), width='stretch')

            st.caption(f"Last Update: {get_now_kst().strftime('%H:%M:%S')}")

        time.sleep(2)
    except Exception as e:
        # 에러 로깅 추가 (무슨 에러인지 알아야 하니까)
        print(f"Loop Error: {e}")
        time.sleep(1)