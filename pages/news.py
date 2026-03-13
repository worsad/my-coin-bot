import streamlit as st
import requests
import xml.etree.ElementTree as ET
import google.generativeai as genai
import os
import re
import time
from datetime import datetime, timedelta

# 1. 보안 및 AI 설정
api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    # 안전 설정 최적화
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    try:
        model = genai.GenerativeModel(model_name='gemini-1.5-flash', safety_settings=safety_settings)
        # 가벼운 시동 확인
        model.generate_content("ok")
        st.sidebar.success("🚀 초고속 Flash 엔진 대기 중")
    except:
        model = genai.GenerativeModel('gemini-pro')
        st.sidebar.warning("⚠️ 기본 Pro 엔진 사용 중")
else:
    st.error("🚨 API 키 누락!")
    st.stop()

st.title("💰 AI 코인 뉴스 분석기")

def get_ai_news_scores():
    # 멘토의 팁: 검색어를 더 구체화하여 노이즈 제거
    query = "비트코인 (ETF OR 반감기 OR 폭락 OR 급등)"
    url = f"https://news.google.com/rss/search?q={query}+when:1d&hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        res = requests.get(url, timeout=10)
        root = ET.fromstring(res.content)
        items = root.findall('.//item')[:7] # 분석 기사 수를 7개로 확대
        
        results = []
        progress_bar = st.progress(0)
        
        for i, item in enumerate(items):
            title = item.find('title').text
            link = item.find('link').text
            pub_date = item.find('pubDate').text # 뉴스 발행 시간 추출
            
            # API 할당량 초과 방지를 위한 최소 대기 (2.0초로 최적화)
            time.sleep(2.0) 
            
            try:
                # 멘토의 프롬프트: '트레이더'의 관점에서 점수 매기기 지시
                prompt = f"당신은 전문 코인 트레이더입니다. 다음 뉴스가 비트코인 가격에 미칠 영향을 -100(매우 부정)에서 100(매우 긍정) 사이의 숫자로만 답하세요. 뉴스 제목: {title}"
                response = model.generate_content(prompt)
                
                score_text = response.text.strip()
                numbers = re.findall(r'-?\d+', score_text)
                score = int(numbers[0]) if numbers else 0
                
            except Exception:
                score = 0
                
            results.append({'title': title, 'link': link, 'score': score, 'date': pub_date})
            progress_bar.progress((i + 1) / len(items))
            
        return results
    except Exception as e:
        st.error(f"데이터 수집 에러: {e}")
        return []

# --- UI 레이아웃 ---
if st.button('📈 시장 심리 실시간 스캔'):
    with st.spinner('AI가 뉴스를 읽고 시장 분위기를 파악 중입니다...'):
        data = get_ai_news_scores()
        
    if data:
        st.success("스캔 완료!")
        avg_score = sum(n['score'] for n in data) / len(data)
        
        # 종합 지수 시각화
        col1, col2 = st.columns([1, 2])
        with col1:
            color = "green" if avg_score > 0 else "red"
            st.metric("📊 종합 시장 심리", f"{avg_score:+.1f}", delta=f"{avg_score:+.1f}")
        with col2:
            sentiment = "탐욕(Greed)" if avg_score > 20 else "공포(Fear)" if avg_score < -20 else "중립"
            st.info(f"현재 시장은 **{sentiment}** 상태입니다.")

        st.divider()
        
        # 기사별 상세 리포트
        for n in data:
            with st.expander(f"{n['score'] : >4}점 | {n['title']}"):
                st.write(f"📅 **발행일:** {n['date']}")
                st.write(f"🔗 [기사 원문 보기]({n['link']})")
                if n['score'] >= 50:
                    st.write("🔥 **강력 호재:** 매수 관점 검토")
                elif n['score'] <= -50:
                    st.write("🚨 **강력 악재:** 리스크 관리 필수")