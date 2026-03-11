import streamlit as st
import requests
import pandas as pd
import time
from datetime import datetime, timedelta

st.set_page_config(page_title="프로 트레이더 터미널", layout="wide")

# 한국 시간 설정
def get_now_kst():
    return datetime.utcnow() + timedelta(hours=9)

st.title("📊 비트코인 거래소별 전체 추이 분석")

# 1. 업비트 데이터 가져오기 (1시간 봉 24개)
def get_upbit_candles():
    url = "https://api.upbit.com/v1/candles/minutes/60?market=KRW-BTC&count=24"
    res = requests.get(url).json()
    df = pd.DataFrame(res)
    # 시간 순서 정렬 및 필요한 컬럼만 추출
    df = df[['candle_date_time_kst', 'trade_price']].rename(columns={'candle_date_time_kst': '시간', 'trade_price': '업비트'})
    return df.set_index('시간').sort_index()

# 2. 빗썸 데이터 가져오기 (1시간 봉 24개)
def get_bithumb_candles():
    url = "https://api.bithumb.com/public/candlestick/BTC_KRW/1h"
    res = requests.get(url).json()
    # 빗썸은 데이터 구조가 다름 [시간, 시가, 종가, 고가, 저가, 거래량]
    df = pd.DataFrame(res['data'])
    df.columns = ['시간', '시가', '종가', '고가', '저가', '거래량']
    # 밀리초 단위를 읽기 쉬운 시간으로 변환
    df['시간'] = pd.to_datetime(df['시간'].astype(float), unit='ms') + timedelta(hours=9)
    df = df[['시간', '종가']].rename(columns={'종가': '빗썸'})
    return df.tail(24).set_index('시간')

# 화면 구성
col1, col2 = st.columns(2)

try:
    up_df = get_upbit_candles()
    bi_df = get_bithumb_candles()

    with col1:
        st.subheader("🔵 업비트 (최근 24시간)")
        st.line_chart(up_df)
        st.metric("현재가", f"{int(up_df['업비트'].iloc[-1]):,}원")

    with col2:
        st.subheader("🟠 빗썸 (최근 24시간)")
        st.line_chart(bi_df)
        st.metric("현재가", f"{int(bi_df['빗썸'].iloc[-1]):,}원")

    # 하단 통합 비교 (김치 프리미엄 추이)
    st.divider()
    st.subheader("⚖️ 거래소간 가격 격차 추이")
    merged = pd.concat([up_df, bi_df], axis=1).dropna()
    merged['차이'] = merged['업비트'].astype(float) - merged['빗썸'].astype(float)
    st.area_chart(merged['차이'])

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류 발생: {e}")

st.caption(f"마지막 업데이트 (KST): {get_now_kst().strftime('%Y-%m-%d %H:%M:%S')}")