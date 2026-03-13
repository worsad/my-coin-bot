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
        # 최신 google-genai 클라이언트 설정
        client = genai.Client(api_key=api_key)
        st.sidebar.success("✅ Gemini 엔진 가동 중")
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
            st.warning("🧐 분석할 뉴스를 가져오지 못했습니다.")
            return []

        results = []
        progress_bar = st.progress(0, text="AI가 시장 심리를 정밀 분석 중...")

        for i, item in enumerate(items):
            title = item.find('title').text
            link = item.find('link').text
            
            # [생존 전략] 무료 티어 안정권 15초 대기 (429 에러 방지)
            time.sleep(15.0) 
            
            try:
                prompt = f"다른 설명 없이 오직 -100에서 100 사이의 숫자 하나만 답해. 제목: {title}"
                
                # 🔥 [404 해결] 'models/'를 제거한 최신 호출 방식
                response = client.models.generate_content(
                    model='gemini-1.5-flash', 
                    contents=prompt
                )
                
                res_text = response.text.strip()
                
                # AI 답변 확인용 디버깅 메시지
                st.info(f"🤖 {i+1}번 AI 분석 결과: {res_text}")
                
                numbers = re.findall(r'-?\d+', res_text)
                score = int(numbers[0]) if numbers else 0
                
            except Exception as e:
                # 에러 발생 시 상세 원인 출력
                st.error(f"❌ {i+1}번 분석 실패: {str(e)[:100]}")
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
    
    # [2026 규격] width='stretch' 적용
    fig = px.bar(data, x='score', y='title', orientation='h', 
                 color='score', color_continuous_scale='RdBu', range_x=[-100, 100])
    st.plotly_chart(fig, width='stretch', key="news_sentiment_chart")

    st.divider()
    
    for n in data:
        color = "red" if n['score'] < 0 else "blue"
        st.markdown(f"**[:{color}[{n['score']}점]]** [{n['title']}]({n['link']})")

    if st.button('🔄 다시 분석하기', key="refresh_btn"):
        del st.session_state.news_data
        st.rerun()