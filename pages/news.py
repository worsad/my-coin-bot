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
    
    # 멘토의 핵심 수정 1: 안전 설정 리스트 정의
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    # 멘토의 핵심 수정 2: 모델 생성 시 safety_settings를 '반드시' 포함
    # 모델명은 가장 안정적인 'gemini-1.5-flash-latest' 추천
    model = genai.GenerativeModel(
        model_name='gemini-1.5-flash-latest',
        safety_settings=safety_settings
    )
else:
    st.error("🚨 API 키가 없습니다!")
    st.stop()

st.title("🌐 AI 뉴스 실시간 분석 (디버깅 모드)")

def get_ai_news_scores():
    # RSS 주소 뒤에 &nocache=...를 붙여 항상 새로운 뉴스를 가져오게 함
    url = f"https://news.google.com/rss/search?q=비트코인+코인+when:1d&hl=ko&gl=KR&ceid=KR:ko&timestamp={int(time.time())}"
    
    try:
        res = requests.get(url, timeout=10)
        root = ET.fromstring(res.content) # text 대신 content 사용 (인코딩 안전성)
        items = root.findall('.//item')[:5] 
        
        results = []
        for i, item in enumerate(items):
            title = item.find('title').text
            link = item.find('link').text
            
            # 무료 API 안정성을 위해 지연 시간 2초 유지
            time.sleep(2.0) 
            
            try:
                # 멘토의 핵심 수정 3: AI가 딴소리 못하게 하는 프롬프트 최적화
                prompt = f"Analyze the following crypto news title and rate its market impact from -100 to 100. Give ONLY the number. Title: {title}"
                response = model.generate_content(prompt)
                
                # AI가 실제로 한 말 (디버깅용)
                ai_raw_text = response.text.strip()
                st.write(f"🔍 AI 원문 응답 ({i+1}): {ai_raw_text}") 
                
                # 숫자 추출 로직
                numbers = re.findall(r'-?\d+', ai_raw_text)
                score = int(numbers[0]) if numbers else 0
                
            except Exception as e:
                st.warning(f"⚠️ {i+1}번 기사 분석 실패: {e}")
                score = 0
                
            results.append({'title': title, 'link': link, 'score': score})
            
        return results
    except Exception as e:
        st.error(f"데이터 수집 에러: {e}")
        return []

if st.button('🚀 분석 시작 및 범인 찾기'):
    data = get_ai_news_scores()
    if data:
        st.success("분석 완료!")
        for n in data:
            # 점수에 따른 아이콘 표시
            icon = "🔥" if n['score'] >= 50 else "🚨" if n['score'] <= -50 else "💬"
            st.write(f"**{icon} [{n['score']}점]** {n['title']}")