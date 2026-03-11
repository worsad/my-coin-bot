import streamlit as st
import requests
import time
from datetime import datetime, timedelta
import pandas as pd

st.set_page_config(page_title="코인 실시간 분석 터미널", layout="wide")

# 멘토의 팁: 한국 시간을 가져오는 함수 (UTC + 9시간)
def get_now_kst():
    return datetime.utcnow() + timedelta(hours=9)

st.title("📈 실시간 비트코인 시세 및 추이")

# 실시간 데이터를 누적할 공간 (세션 상태 활용)
if 'price_history' not in st.session_state:
    st.session_state.price_history = pd.DataFrame(columns=['시간', '업비트', '빗썸'])

placeholder = st.empty()

while True:
    try:
        # 데이터 수집
        up_res = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC").json()
        bi_res = requests.get("https://api.bithumb.com/public/ticker/BTC_KRW").json()

        up_price = int(up_res[0]['trade_price'])
        bi_price = int(bi_res['data']['closing_price'])
        now_time = get_now_kst().strftime('%H:%M:%S')

        # 데이터 누적 (최근 20개만 유지해서 렉 방지)
        new_data = pd.DataFrame({'시간': [now_time], '업비트': [up_price], '빗썸': [bi_price]})
        st.session_state.price_history = pd.concat([st.session_state.price_history, new_data]).iloc[-20:]

        with placeholder.container():
            # 상단 지표
            c1, c2, c3 = st.columns(3)
            c1.metric("업비트", f"{up_price:,}원")
            c2.metric("빗썸", f"{bi_price:,}원")
            c3.metric("현재 시각 (KST)", now_time)

            # 멘토의 핵심: 실시간 차트 그리기
            st.subheader("📊 최근 시세 추이 (20회 측정)")
            chart_data = st.session_state.price_history.set_index('시간')
            st.line_chart(chart_data)

        time.sleep(2) # 렉 방지를 위해 2초 주기로 설정

    except Exception as e:
        time.sleep(2)