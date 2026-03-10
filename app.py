import streamlit as st
import requests
import time

st.set_page_config(page_title="거래소 통합 감시소", layout="wide")

st.title("⚖️ 업비트 vs 빗썸 실시간 가격 비교")
st.caption("두 거래소의 비트코인(BTC) 가격 차이를 실시간으로 추적합니다.")

placeholder = st.empty()

while True:
    try:
        # 1. 업비트 데이터 가져오기
        upbit_url = "https://api.upbit.com/v1/ticker?markets=KRW-BTC"
        upbit_data = requests.get(upbit_url).json()
        upbit_price = int(upbit_data[0]['trade_price'])

        # 2. 빗썸 데이터 가져오기
        bithumb_url = "https://api.bithumb.com/public/ticker/BTC_KRW"
        bithumb_data = requests.get(bithumb_url).json()
        bithumb_price = int(bithumb_data['data']['closing_price'])

        # 3. 가격 차이(괴리) 계산
        diff = upbit_price - bithumb_price
        diff_percent = (diff / bithumb_price) * 100

        with placeholder.container():
            # 상단 메트릭 배치
            col1, col2, col3 = st.columns(3)
            
            col1.metric("업비트 (Upbit)", f"{upbit_price:,} 원")
            col2.metric("빗썸 (Bithumb)", f"{bithumb_price:,} 원")
            
            # 차이가 플러스면 업비트가 비쌈, 마이너스면 빗썸이 비쌈
            if diff > 0:
                col3.metric("가격 차이 (Gap)", f"+{diff:,} 원", f"{diff_percent:.2f}% (업비트 높음)")
            else:
                col3.metric("가격 차이 (Gap)", f"{diff:,} 원", f"{diff_percent:.2f}% (빗썸 높음)")

            # 시각적 피드백 (간단한 경고)
            if abs(diff_percent) > 0.1:
                st.warning(f"⚠️ 현재 두 거래소 간 가격 차이가 {abs(diff_percent):.2f}% 발생 중입니다.")
            else:
                st.success("✅ 두 거래소 가격이 안정적으로 유지되고 있습니다.")

        time.sleep(1) # 두 곳을 찌르므로 1초 정도의 여유를 줍니다.

    except Exception as e:
        st.error(f"데이터 연결 오류: {e}")
        time.sleep(2)