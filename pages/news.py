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
    # 안전 설정을 모두 해제하여 뉴스 분석 차단을 방지 (중요!)
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    model = genai.GenerativeModel('gemini-1.5-flash-latest', safety_settings=safety_settings)
else:
    st.error("🚨 API 키가 없습니다!")
    st.stop()

st.title("🌐 AI 뉴스 실시간 분석 (디버깅 모드)")

def get_ai_news_scores():
    url = "https://news.google.com/rss/search?q=비트코인+코인+when:1d&hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        res = requests.get(url, timeout=10)
        root = ET.fromstring(res.text)
        items = root.findall('.//item')[:5] 
        
        results = []
        for i, item in enumerate(items):
            title = item.find('title').text
            link = item.find('link').text
            
            # 멘토의 조언: 호출 전 지연 시간은 필수!
            time.sleep(2.0) 
            
            try:
                # 프롬프트를 더 강력하게 수정
                prompt = f"Analyze this crypto news title and give a score from -100 to 100 based on market impact. Give ONLY the number. Title: {title}"
                response = model.generate_content(prompt)
                
                # AI가 실제로 한 말을 로그에 찍음 (범인 검거용)
                ai_raw_text = response.text.strip()
                st.write(f"🔍 AI 원문 응답 ({i+1}): {ai_raw_text}") 
                
                # 숫자 추출 로직 (더 정교하게)
                numbers = re.findall(r'-?\d+', ai_raw_text)
                score = int(numbers[0]) if numbers else 0
                
            except Exception as e:
                st.warning(f"⚠️ {i+1}번 기사 분석 중 에러: {e}")
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
            st.write(f"**[{n['score']}점]** {n['title']}")