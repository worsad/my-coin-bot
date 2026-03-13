import streamlit as st
import requests
import pandas as pd
import time
import os
from datetime import datetime, timedelta
import plotly.express as px
import google.generativeai as genai
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# --- 1. 보안 및 AI 설정 ---
load_dotenv()
api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("🚨 API 키를 찾을 수 없습니다! Secrets 설정을 확인하세요.")
    st.stop()

st.set_page_config(page_title="AI 코인 터미널", layout="wide")

# --- 2. 뉴스 분석 엔진 (1분 캐싱) ---
def get_ai_news_analysis():
    try:
        url = "https://news.google.com/rss/search?q=비트코인+when:1h&hl=ko&gl=KR&ceid=KR:ko"
        res = requests.get(url)
        soup = BeautifulSoup(res.text, 'xml')
        items = soup.find_all('item')[:3]
        
        results = []
        for item in items:
            title = item.title.text
            prompt = f"트레이더 관점에서 이 뉴스가 비트코인 호재면 +, 악재면 - 점수(-100~100) 숫자만 답해: {title}"
            response = model.generate_content(prompt)
            score = int(''.join(filter(lambda x: x.isdigit() or x == '-', response.text)))
            results.append({"title": title, "score": score})
        return results
    except:
        return []

# --- 3. 데이터 수집 엔진 (업비트/빗썸) ---
def get_market_data(u_unit, u_count, b_unit):
    # 업비트
    u_t = requests.get("https://api.upbit.com/v1/ticker?markets=KRW-BTC").json()[0]
    u_c = requests.get(f"https://api.upbit.com/v1/candles/{u_unit}?market=KRW-BTC&count={u_count}").json()
    u_df = pd.DataFrame(u_c)
    u_df['시간'] = pd.to_datetime(u_df['candle_date_time_kst'])
    
    # 빗썸
    b_t = requests.get("https://api.bithumb.com/public/ticker/BTC_KRW").json()['data']
    b_url = "https://api.bithumb.com/public/candlestick/BTC_KRW/24h" if "d" in b_unit else f"https://api.bithumb.com/public/candlestick/BTC_KRW/{b_unit}"
    b_c = requests.get(b_url).json()['data']
    b_df = pd.DataFrame(b_c, columns=['시간', '시가', '종가', '고가', '저가', '거래량']).tail(u_count)
    b_df['시간'] = pd.to_datetime(b_df['시간'].astype(float), unit='ms') + timedelta(hours=9)
    b_df['가격'] = b_df['종가'].astype(float)
    
    return u_t, u_df[['시간', 'trade_price']].rename(columns={'trade_price':'가격'}), b_t, b_df

# --- 4. 메인 UI 루프 ---
st.title("🚀 AI 파워드 전천후 비트코인 터미널")

interval = st.selectbox("차트 주기", ["1분봉", "5분봉", "10분봉", "30분봉", "1시간봉", "1일봉"], index=2)
mapping = {
    "1분봉": ("minutes/1", 144, "1m"), "5분봉": ("minutes/5", 144, "5m"),
    "10분봉": ("minutes/10", 144, "10m"), "30분봉": ("minutes/30", 144, "30m"),
    "1시간봉": ("minutes/60", 144, "1h"), "1일봉": ("days", 100, "1d")
}
u_u, u_c, b_u = mapping[interval]

# 뉴스 데이터 세션 관리
if 'news_results' not in st.session_state or time.time() - st.session_state.get('last_news_update', 0) > 60:
    st.session_state.news_results = get_ai_news_analysis()
    st.session_state.last_news_update = time.time()

placeholder = st.empty()

while True:
    try:
        ut, udf, bt, bdf = get_market_data(u_u, u_c, b_u)
        
        with placeholder.container():
            # 메트릭 섹션
            c1, c2, c3, c4 = st.columns(4)
            up_p, bi_p = int(ut['trade_price']), int(bt['closing_price'])
            avg_s = sum([n['score'] for n in st.session_state.news_results]) / 3 if st.session_state.news_results else 0
            
            c1.metric("UPBIT", f"{up_p:,}원")
            c2.metric("BITHUMB", f"{bi_p:,}원")
            c3.metric("KIMP", f"{up_p - bi_p:,}원")
            c4.metric("AI 심리", f"{avg_s:+.1f}", "호재" if avg_s > 10 else "악재" if avg_s < -10 else "중립")

            st.divider()

            # 뉴스 리스트 섹션
            st.write("### 📰 실시간 AI 뉴스 판독")
            for n in st.session_state.news_results:
                col_t, col_s = st.columns([5, 1])
                col_t.write(f"• {n['title']}")
                color = "green" if n['score'] > 0 else "red"
                col_s.markdown(f"<span style='color:{color}'>{n['score']}점</span>", unsafe_allow_html=True)

            st.divider()

            # 차트 섹션
            def make_fig(df, title, color):
                fig = px.line(df, x='시간', y='가격', title=title)
                y_min, y_max = df['가격'].min(), df['가격'].max()
                fig.update_yaxes(range=[y_min*0.999, y_max*1.001], tickformat=",d")
                fig.update_traces(line_color=color)
                fig.update_layout(height=400, margin=dict(l=0, r=0, t=40, b=0))
                return fig

            ch1, ch2 = st.columns(2)
            ch1.plotly_chart(make_fig(udf.sort_values('시간'), f"🔵 UPBIT - {interval}", "#0066FF"), use_container_width=True)
            ch2.plotly_chart(make_fig(bdf.sort_values('시간'), f"🟠 BITHUMB - {interval}", "#FF9900"), use_container_width=True)

        time.sleep(2)
    except:
        time.sleep(1)