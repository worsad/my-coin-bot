import streamlit as st
import requests

# 1. 앱 제목 (브라우저에 뜰 이름)
st.title("🛰️ 내 서버 생존 확인: 실시간 코인")

# 2. 업비트에서 비트코인 가격 가져오기 (실시간 데이터)
url = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"
res = requests.get(url).json()
price = res[0]['trade_price']

# 3. 화면에 멋지게 표시하기
st.header(f"현재 비트코인: {price:,.0f}원")
st.success("데이터 연결 성공! 이제 서버로 갈 준비가 됐습니다.")