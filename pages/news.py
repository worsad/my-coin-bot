import streamlit as st
import requests
import xml.etree.ElementTree as ET
from google import genai
import time
import re
import plotly.express as px

# 1. 보안 및 AI 설정 (새 키를 Secrets에 넣었는지 확인하세요!)
api_key = st.secrets.get("GOOGLE_API_KEY")

if api_key:
    try:
        client = genai.Client(api_key=api_key)
        st.sidebar.success("✅ 새 API 키 가동 중")
    except Exception as e:
        st.sidebar.error("❌ 엔진 시동 실패")
        st.stop()
else:
    st.error("🚨 API 키를 등록하세요!")
    st.stop()

st.title("💰 AI 뉴스 정밀 스캐너 (디버깅 모드)")

def fetch_and_analyze():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    now_ts = int(time.time())
    url = f"https://news.google.com/rss/search?q=비트코인+시황&hl=ko&gl=KR&ceid=KR:ko&ts={now_ts}"
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        root = ET.fromstring(res.content)
        items = root.findall('.//item')[:3] 
        
        if not items:
            st.warning("🧐 뉴스를 가져오지 못했습니다.")
            return []

        results = []
        progress_bar = st.progress(0, text="AI 분석 중...")

        for i, item in enumerate(items):
            title = item.find('title').text
            link = item.find('link').text
            
            # 무료 티어 안정권 15초 대기
            time.sleep(15.0) 
            
            try:
                # 프롬프트를 더 엄격하게 수정
                prompt = f"다른 설명 없이 오직 -100에서 100 사이의 숫자 하나만 답해. 제목: {title}"
                response = client.models.generate_content(
                    model='gemini-1.5-flash', 
                    contents=prompt
                )
                
                res_text = response.text.strip()
                
                # [디버깅] AI가 실제로 뭐라고 하는지 확인 (중요!)
                st.info(f"🤖 {i+1}번 AI 답변: {res_text}")
                
                numbers = re.findall(r'-?\d+', res_text)
                if numbers:
                    score = int(numbers[0])
                else:
                    st.warning(f"⚠️ {i+1}번 뉴스에서 숫자를 찾을 수 없음")
                    score = 0
            except Exception as e:
                # 에러 내용을 화면에 직접 표시
                st.error(f"❌ {i+1}번 분석 에러: {str(e)[:100]}")
                score = 0
                
            results.append({'title': title, 'link': link, 'score': score})
            progress_bar.progress((i + 1) / len(items))
        
        progress_bar.empty()
        return results
    except Exception as e:
        st.error(f"🚨 시스템 오류: {e}")
        return []

# --- 실행부 ---
if 'news_data' not in st.session_state:
    st.session_state.news_data = fetch_and_analyze()

if st.session_state.news_data:
    data = st.session_state.news_data
    avg_score = sum(n['score'] for n in data) / len(data)
    
    st.subheader(f"📊 종합 시장 심리: {avg_score:+.1f}점")
    
    fig = px.bar(data, x='score', y='title', orientation='h', 
                 color='score', color_continuous_scale='RdBu', range_x=[-100, 100])
    st.plotly_chart(fig, width='stretch', key="debug_chart")

    st.divider()
    
    for n in data:
        color = "red" if n['score'] < 0 else "blue"
        st.markdown(f"**[:{color}[{n['score']}점]]** [{n['title']}]({n['link']})")

    if st.button('🔄 다시 분석하기', key="refresh_btn"):
        del st.session_state.news_data
        st.rerun()