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

st.title("💰 AI 뉴스 분석 (생존 모드)")

def fetch_and_analyze():
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    
    # 캐시 방지를 위한 타임스탬프
    now_ts = int(time.time())
    url = f"https://news.google.com/rss/search?q=비트코인+시황&hl=ko&gl=KR&ceid=KR:ko&ts={now_ts}"
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        if res.status_code != 200:
            return []
            
        root = ET.fromstring(res.content)
        # [생존 전략 1] 분석 개수를 2개로 줄여서 확실한 성공을 보장합니다.
        items = root.findall('.//item')[:2] 
        
        if not items:
            st.warning("🧐 현재 분석할 뉴스가 없습니다.")
            return []

        results = []
        progress_bar = st.progress(0, text="할당량 보호를 위해 천천히 진행 중...")

        for i, item in enumerate(items):
            title = item.find('title').text
            link = item.find('link').text
            
            # [생존 전략 2] 대기 시간을 10초로 대폭 늘립니다. 
            # 무료 티어는 분당 요청 횟수가 매우 적기 때문입니다.
            time.sleep(10.0) 
            
            try:
                # [생존 전략 3] 2.0-flash 대신 1.5-flash를 사용합니다. 
                # 1.5 모델은 무료 티어 제한이 훨씬 널널합니다.
                prompt = f"뉴스 제목을 보고 코인 가격 영향력을 -100에서 100 사이 숫자로만 답해. 제목: {title}"
                response = client.models.generate_content(
                    model='gemini-1.5-flash', 
                    contents=prompt
                )
                
                score_text = response.text.strip()
                numbers = re.findall(r'-?\d+', score_text)
                score = int(numbers[0]) if numbers else 0
            except Exception as e:
                # 에러 발생 시 사용자에게 알리고 0점 처리
                st.info(f"💡 {i+1}번 뉴스 분석 대기 중 (API 제한 가능성)")
                score = 0
                
            results.append({'title': title, 'link': link, 'score': score})
            progress_bar.progress((i + 1) / len(items))
        
        progress_bar.empty()
        return results
    except Exception as e:
        st.error(f"🚨 시스템 오류: {e}")
        return []

# --- 실행 및 세션 관리 ---
# 페이지 로드 시 바로 실행하지 않고, 데이터가 없을 때만 실행
if 'news_data' not in st.session_state:
    with st.spinner('📢 시장 데이터를 가져오는 중입니다...'):
        st.session_state.news_data = fetch_and_analyze()

if st.session_state.news_data:
    data = st.session_state.news_data
    avg_score = sum(n['score'] for n in data) / len(data)
    
    st.subheader(f"📊 종합 시장 심리: {avg_score:+.1f}점")
    
    # 시각화 (중복 ID 방지 key)
    fig = px.bar(data, x='score', y='title', orientation='h', 
                 title="AI 뉴스 분석 결과",
                 color='score', color_continuous_scale='RdBu',
                 range_x=[-100, 100])
    
    st.plotly_chart(fig, use_container_width=True, key="fixed_sentiment_chart")

    st.divider()
    
    for n in data:
        color = "red" if n['score'] < 0 else "blue"
        st.markdown(f"**[:{color}[{n['score']}점]]** [{n['title']}]({n['link']})")

    # 새로고침 버튼
    if st.button('🔄 새 뉴스 가져오기', key="news_refresh_btn"):
        del st.session_state.news_data
        st.rerun()