import streamlit as st
import requests
import xml.etree.ElementTree as ET
import google.generativeai as genai
import os
import re
import time
from datetime import datetime, timedelta, UTC

# 1. 보안 및 AI 설정
api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    
    # 안전 설정: 뉴스 분석 시 차단 방지 (BLOCK_NONE)
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    # [멘토의 핵심 수정] 에러 유발하는 list_models 대신 직접 시도하는 방식
    # 1.5-flash는 현재 가장 가성비 좋고 빠른 최신 표준입니다.
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash', 
            safety_settings=safety_settings
        )
        # 시동 확인용 테스트 (에러 나면 자동으로 예외처리로 넘어감)
        model.generate_content("hi")
        st.sidebar.success("🚀 Gemini 1.5 Flash 엔진 가동!")
    except Exception:
        # 1.5-flash가 안 될 경우를 대비한 2중 방어막 (구형 pro 버전)
        model = genai.GenerativeModel('gemini-pro')
        st.sidebar.warning("⚠️ 1.5 버전 실패로 기본형(Pro) 엔진 전환")
else:
    st.error("🚨 API 키가 설정되지 않았습니다!")
    st.stop()

st.title("🌐 AI 뉴스 실시간 분석 (최종 안정화)")

def get_ai_news_scores():
    url = f"https://news.google.com/rss/search?q=비트코인+코인+when:1d&hl=ko&gl=KR&ceid=KR:ko&ts={int(time.time())}"
    
    try:
        res = requests.get(url, timeout=10)
        root = ET.fromstring(res.content)
        items = root.findall('.//item')[:5] 
        
        results = []
        for i, item in enumerate(items):
            title = item.find('title').text
            link = item.find('link').text
            
            # API 할당량 보호 (2.5초 지연)
            time.sleep(2.5) 
            
            try:
                # AI에게 명확하게 숫자만 요구
                prompt = f"Analyze crypto news title and rate impact from -100 to 100. Answer ONLY with the number. Title: {title}"
                response = model.generate_content(prompt)
                
                ai_raw_text = response.text.strip()
                st.info(f"뉴스 {i+1} 분석 응답: {ai_raw_text}")
                
                # 숫자 추출
                numbers = re.findall(r'-?\d+', ai_raw_text)
                score = int(numbers[0]) if numbers else 0
                
            except Exception as e:
                st.warning(f"⚠️ {i+1}번 분석 실패: {e}")
                score = 0
                
            results.append({'title': title, 'link': link, 'score': score})
            
        return results
    except Exception as e:
        st.error(f"뉴스 수집 실패: {e}")
        return []

# --- UI 레이아웃 ---
if st.button('🚀 실시간 AI 분석 시작'):
    data = get_ai_news_scores()
    if data:
        st.success("모든 분석 완료!")
        avg_score = sum(n['score'] for n in data) / len(data)
        st.metric("📊 종합 심리 지수", f"{avg_score:+.1f}점")
        
        st.divider()
        for n in data:
            icon = "🔥" if n['score'] >= 50 else "🚨" if n['score'] <= -50 else "💬"
            st.write(f"**{icon} [{n['score']}점]** {n['title']}")