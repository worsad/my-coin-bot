import streamlit as st
import requests
import xml.etree.ElementTree as ET
from google import genai
import os
import re
import time
import plotly.express as px  # 차트용

# 1. 보안 및 AI 설정
api_key = st.secrets.get("GOOGLE_API_KEY")

if api_key:
    try:
        client = genai.Client(api_key=api_key)
        st.sidebar.success("✅ Gemini 2.0 엔진 가동 중")
    except Exception as e:
        st.sidebar.error(f"❌ 엔진 시동 실패: {e}")
        st.stop()
else:
    st.error("🚨 API 키를 등록하세요!")
    st.stop()

st.title("🌐 실시간 AI 뉴스 분석 리포트")

# [멘토의 핵심 수정] 뉴스 분석 함수 (중립 금지 로직 포함)
def fetch_and_analyze():
    now_ts = int(time.time())
    url = f"https://news.google.com/rss/search?q=비트코인+시황+급등락+when:1h&hl=ko&gl=KR&ceid=KR:ko&ts={now_ts}"
    
    try:
        res = requests.get(url, timeout=10)
        root = ET.fromstring(res.content)
        items = root.findall('.//item')[:5] 
        
        if not items:
            return []

        results = []
        progress_bar = st.progress(0, text="AI가 시장 분위기를 파악하고 있습니다...")

        for i, item in enumerate(items):
            title = item.find('title').text
            link = item.find('link').text
            
            time.sleep(2.0) # API 할당량 보호
            
            try:
                prompt = f"너는 공격적인 코인 트레이더야. 이 뉴스가 가격에 미칠 점수를 -100에서 100 사이 숫자로만 답해. 0점은 지양해. 제목: {title}"
                response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
                
                score_text = response.text.strip()
                numbers = re.findall(r'-?\d+', score_text)
                score = int(numbers[0]) if numbers else 0
            except:
                score = 0
                
            results.append({'title': title, 'link': link, 'score': score})
            progress_bar.progress((i + 1) / len(items))
        
        progress_bar.empty()
        return results
    except Exception as e:
        st.error(f"데이터 수집 실패: {e}")
        return []

# --- 자동 분석 실행 및 세션 저장 ---
if 'news_data' not in st.session_state:
    st.session_state.news_data = fetch_and_analyze()

# --- 결과 출력 및 차트 생성 ---
if st.session_state.news_data:
    data = st.session_state.news_data
    avg_score = sum(n['score'] for n in data) / len(data)
    
    # 1. 상단 지표
    st.subheader(f"📊 종합 시장 지수: {avg_score:+.1f}점")
    
    # 2. [에러 해결 포인트] Plotly 차트에 고유 key 부여
    fig = px.bar(data, x='score', y='title', orientation='h', 
                 title="뉴스별 영향력 분석",
                 color='score', color_continuous_scale='RdBu')
    
    # 여기서 key="sentiment_chart"를 넣어야 무한 루프가 안 납니다.
    st.plotly_chart(fig, use_container_width=True, key="sentiment_chart_unique")

    st.divider()
    
    # 3. 뉴스 리스트 출력
    for idx, n in enumerate(data):
        color = "red" if n['score'] < 0 else "blue"
        st.markdown(f"**[:{color}[{n['score']}점]]** [{n['title']}]({n['link']})")

    # 수동 새로고침 버튼
    if st.button('🔄 데이터 새로고침', key="refresh_button"):
        del st.session_state.news_data
        st.rerun()