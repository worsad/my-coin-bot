import streamlit as st
import requests
import time

st.set_page_config(page_title="초고속 통합 감시소", layout="wide")

# 멘토의 팁: 세션을 미리 생성해서 통신 속도를 최적화합니다.
if 'session' not in st.session_state:
    st.session_state.session = requests.Session()

st.title("⚡ 초고속 업비트 vs 빗썸 비교")

placeholder = st.empty()

while True:
    try:
        # 통신 세션 재사용으로 속도 향상
        s = st.session_state.session
        
        # 업비트와 빗썸 데이터를 거의 동시에 요청 (데이터 양 최소화)
        up_res = s.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC", timeout=1).json()
        bi_res = s.get("https://api.bithumb.com/public/ticker/BTC_KRW", timeout=1).json()

        up_price = int(up_res[0]['trade_price'])
        bi_price = int(bi_res['data']['closing_price'])
        
        diff = up_price - bi_price
        diff_rate = (diff / bi_price) * 100

        with placeholder.container():
            c1, c2, c3 = st.columns(3)
            c1.metric("업비트", f"{up_price:,}원")
            c2.metric("빗썸", f"{bi_price:,}원")
            c3.metric("가격 차이", f"{diff:,}원", f"{diff_rate:.2f}%")
            
            # 멘토의 디테일: 업데이트 시각 표시
            st.caption(f"최종 갱신: {time.strftime('%H:%M:%S')}")

        # 대기 시간을 0.1초로 줄여서 반응성을 높입니다.
        time.sleep(0.1)

    except Exception as e:
        time.sleep(1) # 에러 시 잠시 대기