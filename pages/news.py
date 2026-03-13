import streamlit as st
import requests
import xml.etree.ElementTree as ET
from google import genai
import time
import re
import plotly.express as px

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

def fetch_and_analyze():
    # 멘토의 조언: 구글 뉴스 차단을 피하기 위해 브라우저인 척 헤더 추가
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    now_ts = int(time.time())
    # 검색 쿼리를 조금 더 단순화해서 수집 확률을 높임
    url = f"https://news.google.com/rss/search?q=비트코인+when:1h&hl=ko&gl=KR&ceid=KR:ko&ts={now_ts}"
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        
        # [디버깅] 뉴스 응답 상태 확인
        if res.status_code != 200:
            st.error(f"🚨 뉴스 서버 응답 오류: {res.status_code}")
            return []
            
        root = ET.fromstring(res.content)
        items = root.findall('.//item')[:5] 
        
        if not items:
            st.warning("🧐 현재 분석할 최신 뉴스가 없습니다. 잠시 후 다시 시도하세요.")
            return []

        results = []
        progress_bar = st.progress(0, text="AI가 분석을 시작합니다...")

        for i, item in enumerate(items):
            title = item.find('title').text
            link = item.find('link').text
            
            time.sleep(2.0) 
            
            try:
                prompt = f"너는 코인 분석가야. 이 뉴스가 가격에 미칠 점수를 -100에서 100 사이 숫자로만 답해. 제목: {title}"
                response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
                
                score_text = response.text.strip()
                numbers = re.findall(r'-?\d+', score_text)
                score = int(numbers[0]) if numbers else 0
            except Exception as e:
                st.write(f"⚠️ {i+1}번 뉴스 분석 에러: {e}")
                score = 0
                
            results.append({'title': title, 'link': link, 'score': score})
            progress_bar.progress((i + 1) / len(items))
        
        progress_bar.empty()
        return results
    except Exception as e:
        st.error(f"🚨 데이터 수집 중 치명적 오류: {e}")
        return []

# --- 자동 분석 실행 및 세션 저장 ---
if 'news_data' not in st.session_state:
    st.session_state.news_data = fetch_and_analyze()

# --- 결과 출력 ---
if st.session_state.news_data:
    data = st.session_state.news_data
    avg_score = sum(n['score'] for n in data) / len(data)
    
    st.subheader(f"📊 종합 시장 심리: {avg_score:+.1f}점")
    
    # 그래프 출력
    fig = px.bar(data, x='score', y='title', orientation='h', 
                 title="뉴스별 영향력 분석",
                 color='score', color_continuous_scale='RdBu',
                 range_x=[-100, 100])
    
    st.plotly_chart(fig, use_container_width=True, key="news_sentiment_chart")

    st.divider()
    
    for n in data:
        color = "red" if n['score'] < 0 else "blue"
        st.markdown(f"**[:{color}[{n['score']}점]]** [{n['title']}]({n['link']})")

    if st.button('🔄 데이터 새로고침', key="news_refresh_btn"):
        del st.session_state.news_data
        st.rerun()