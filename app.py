import streamlit as st
import requests
import time

# 페이지 설정
st.set_page_config(page_title="코인 시세 비교", layout="wide")
st.sidebar.info("왼쪽 메뉴에서 'news'를 선택하면 뉴스를 볼 수 있습니다.")

st.title("⚖️ 업비트 vs 빗썸 실시간 시세")

# 실시간 데이터를 뿌려줄 빈 공간
placeholder = st.empty()

# 무한 루프 시작
while True:
    try:
        # 업비트 데이터
        up_res = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC").json()
        up_price = int(up_res[0]['trade_price'])

        # 빗썸 데이터
        bi_res = requests.get("https://api.bithumb.com/public/ticker/BTC_KRW").json()
        bi_price = int(bi_res['data']['closing_price'])

        # 가격 차이 계산
        diff = up_price - bi_price
        diff_rate = (diff / bi_price) * 100

        with placeholder.container():
            c1, c2, c3 = st.columns(3)
            c1.metric("업비트", f"{up_price:,}원")
            c2.metric("빗썸", f"{bi_price:,}원")
            c3.metric("가격 차이", f"{diff:,}원", f"{diff_rate:.2f}%")
            
            st.caption(f"최종 갱신 시각: {time.strftime('%H:%M:%S')}")

        time.sleep(1) # 1초마다 갱신

    except Exception as e:
        st.error(f"연결 오류 발생: {e}")
        time.sleep(2)