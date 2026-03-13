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
        st.sidebar.error("❌ 엔진 시동 실패")
        st.stop()
else:
    st.error("🚨 API 키를 등록하세요!")
    st.stop()

st.title("💰 AI 뉴스 정밀 스캐너")

def fetch_and_analyze():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    now_ts = int(time.time())
    url = f"https://news.google.com/rss/search?q=비트코인+시황&hl=ko&gl=KR&ceid=KR:ko&ts={now_ts}"
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        root = ET.fromstring(res.content)
        items = root.findall('.//item')[:3] 
        
        if not items:
            return []

        results = []
        progress_bar = st.progress(0, text="AI가 시장 흐름을 읽고 있습니다...")

        for i, item in enumerate(items):
            title = item.find('title').text
            link = item.find('link').text
            
            # [생존 전략] 무료 API 보호를 위한 13초 대기
            time.sleep(13.0) 
            
            try:
                # [개선] 숫자를 더 잘 추출할 수 있게 프롬프트 수정
                prompt = f"코인 트레이더로서 이 뉴스 제목을 -100에서 100 사이 숫자로 평가해. 다른 말 하지 말고 숫자만 딱 말해. 제목: {title}"
                response = client.models.generate_content(
                    model='gemini-1.5-flash', 
                    contents=prompt
                )
                
                # [개선] 0점 방지용 정규표현식
                res_text = response.text.strip()
                numbers = re.findall(r'-?\d+', res_text)
                score = int(numbers[0]) if numbers else 0
            except:
                score = 0
                
            results.append({'title': title, 'link': link, 'score': score})
            progress_bar.progress((i + 1) / len(items))
        
        progress_bar.empty()
        return results
    except Exception as e:
        st.error(f"🚨 시스템 오류: {e}")
        return []

# --- 실행 및 결과 출력 ---
if 'news_data' not in st.session_state:
    st.session_state.news_data = fetch_and_analyze()

if st.session_state.news_data:
    data = st.session_state.news_data
    avg_score = sum(n['score'] for n in data) / len(data)
    
    st.subheader(f"📊 종합 시장 심리: {avg_score:+.1f}점")
    
    fig = px.bar(data, x='score', y='title', orientation='h', 
                 color='score', color_continuous_scale='RdBu', range_x=[-100, 100])
    
    # 🔥 [로그 에러 해결] use_container_width=True 대신 width='stretch' 사용
    st.plotly_chart(fig, width='stretch', key="fixed_news_chart")

    st.divider()
    
    for n in data:
        color = "red" if n['score'] < 0 else "blue"
        st.markdown(f"**[:{color}[{n['score']}점]]** [{n['title']}]({n['link']})")

    if st.button('🔄 다시 분석하기', key="refresh_btn"):
        del st.session_state.news_data
        st.rerun()