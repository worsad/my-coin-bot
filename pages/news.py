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
        st.sidebar.success("✅ Gemini 엔진 온라인")
    except Exception as e:
        st.sidebar.error(f"❌ 엔진 시동 실패: {e}")
        st.stop()
else:
    st.error("🚨 API 키를 등록하세요!")
    st.stop()

st.title("🌐 실시간 AI 뉴스 분석 (안정 모드)")

def fetch_and_analyze():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    now_ts = int(time.time())
    # 멘토의 조언: 데이터가 꼬이지 않게 검색어를 간결하게 유지
    url = f"https://news.google.com/rss/search?q=비트코인+시황&hl=ko&gl=KR&ceid=KR:ko&ts={now_ts}"
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200:
            st.error(f"🚨 뉴스 서버 응답 오류: {res.status_code}")
            return []
            
        root = ET.fromstring(res.content)
        # [할당량 방어] 무료 티어 안정성을 위해 분석 개수를 3개로 제한합니다.
        items = root.findall('.//item')[:3] 
        
        if not items:
            st.warning("🧐 최신 뉴스가 없습니다. 잠시 후 다시 시도하세요.")
            return []

        results = []
        progress_bar = st.progress(0, text="무료 할당량을 보호하며 천천히 분석 중...")

        for i, item in enumerate(items):
            title = item.find('title').text
            link = item.find('link').text
            
            # [핵심] 무료 API는 요청 간격을 넓혀야 429 에러를 피할 수 있습니다 (5초 권장)
            time.sleep(5.0) 
            
            try:
                prompt = f"코인 트레이더로서 이 뉴스 제목의 영향력을 -100에서 100 사이 숫자로만 답해. 제목: {title}"
                # 2.0-flash가 할당량이 빡빡하다면 1.5-flash로 변경하는 것도 방법입니다.
                response = client.models.generate_content(model='gemini-2.0-flash', contents=prompt)
                
                score_text = response.text.strip()
                numbers = re.findall(r'-?\d+', score_text)
                score = int(numbers[0]) if numbers else 0
            except Exception as e:
                if "429" in str(e):
                    st.warning(f"⚠️ API 한도 초과! {i+1}번 뉴스는 자동 중립 처리합니다.")
                score = 0
                
            results.append({'title': title, 'link': link, 'score': score})
            progress_bar.progress((i + 1) / len(items))
        
        progress_bar.empty()
        return results
    except Exception as e:
        st.error(f"🚨 시스템 오류: {e}")
        return []

# --- 실행 및 세션 관리 ---
if 'news_data' not in st.session_state:
    st.session_state.news_data = fetch_and_analyze()

if st.session_state.news_data:
    data = st.session_state.news_data
    avg_score = sum(n['score'] for n in data) / len(data)
    
    st.subheader(f"📊 종합 시장 심리: {avg_score:+.1f}점")
    
    # 시각화 (중복 ID 방지를 위해 고유 key 유지)
    fig = px.bar(data, x='score', y='title', orientation='h', 
                 title="AI 뉴스 영향력 분석",
                 color='score', color_continuous_scale='RdBu',
                 range_x=[-100, 100])
    
    st.plotly_chart(fig, use_container_width=True, key="fixed_sentiment_chart")

    st.divider()
    
    for n in data:
        color = "red" if n['score'] < 0 else "blue"
        st.markdown(f"**[:{color}[{n['score']}점]]** [{n['title']}]({n['link']})")

    if st.button('🔄 새 뉴스 가져오기', key="news_refresh_btn"):
        del st.session_state.news_data
        st.rerun()