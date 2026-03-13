import streamlit as st
import requests
import xml.etree.ElementTree as ET
from google import genai
import os
import re
import time

# 1. 보안 및 AI 설정
api_key = st.secrets.get("GOOGLE_API_KEY")

if api_key:
    try:
        client = genai.Client(api_key=api_key)
        # 시동 확인 (사이드바 상태 표시)
        st.sidebar.success("✅ Gemini 2.0 엔진 대기 중")
    except Exception as e:
        st.sidebar.error(f"❌ 엔진 시동 실패: {e}")
        st.stop()
else:
    st.error("🚨 API 키를 등록하세요!")
    st.stop()

st.title("🌐 실시간 AI 뉴스 브리핑 (자동)")

# [멘토의 핵심 수정] 뉴스 수집 및 분석 함수
def fetch_and_analyze():
    now_ts = int(time.time())
    url = f"https://news.google.com/rss/search?q=비트코인+시황+급등락+when:1h&hl=ko&gl=KR&ceid=KR:ko&ts={now_ts}"
    
    try:
        res = requests.get(url, timeout=10)
        root = ET.fromstring(res.content)
        items = root.findall('.//item')[:5] 
        
        if not items:
            st.warning("🧐 최근 1시간 내에 분석할 새로운 뉴스가 없습니다.")
            return []

        results = []
        # 분석 중임을 알리는 프로그레스 바
        progress_text = "AI가 최신 뉴스를 정밀 분석 중입니다..."
        my_bar = st.progress(0, text=progress_text)

        for i, item in enumerate(items):
            title = item.find('title').text
            link = item.find('link').text
            
            # API 보호를 위한 지연 (2.0초)
            time.sleep(2.0) 
            
            try:
                prompt = f"너는 냉철한 코인 분석가야. 이 뉴스가 비트코인 가격에 미칠 점수를 -100에서 100 사이 숫자로만 답해. 0점(중립)은 지양해. 제목: {title}"
                
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=prompt
                )
                
                score_text = response.text.strip()
                numbers = re.findall(r'-?\d+', score_text)
                score = int(numbers[0]) if numbers else 0
                
            except:
                score = 0
                
            results.append({'title': title, 'link': link, 'score': score})
            my_bar.progress((i + 1) / len(items))
        
        my_bar.empty() # 완료 후 바 제거
        return results
    except Exception as e:
        st.error(f"데이터 수집 실패: {e}")
        return []

# --- 자동 실행 로직 ---
# 버튼 없이 바로 실행되지만, 한 번 실행되면 페이지를 새로고침하기 전까지 결과를 유지합니다.
if 'news_data' not in st.session_state:
    with st.spinner('📢 실시간 데이터 수집 중...'):
        st.session_state.news_data = fetch_and_analyze()

# 결과 출력
if st.session_state.news_data:
    data = st.session_state.news_data
    avg_score = sum(n['score'] for n in data) / len(data)
    
    # 상단 요약 지표
    st.subheader(f"📊 현재 시장 심리: {avg_score:+.1f}점")
    
    st.divider()
    for n in data:
        color = "red" if n['score'] < 0 else "blue"
        st.markdown(f"**[:{color}[{n['score']}점]]** [{n['title']}]({n['link']})")

    # 수동 새로고침 버튼만 남겨둠
    if st.button('🔄 데이터 새로고침'):
        del st.session_state.news_data
        st.rerun()