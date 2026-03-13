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
    
    # 안전 설정 (이게 없으면 뉴스 분석 시 AI가 입을 닫습니다)
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    # 멘토의 핵심 수정: 'models/'를 명시적으로 붙여서 경로 에러 차단
    try:
        model = genai.GenerativeModel(
            model_name='gemini-1.5-flash', # -latest 보다는 기본형이 더 안정적일 때가 있습니다.
            safety_settings=safety_settings
        )
    except:
        # 혹시라도 실패하면 가장 기초 모델인 gemini-pro로 후퇴(Fallback)
        model = genai.GenerativeModel('gemini-pro')
else:
    st.error("🚨 API 키가 없습니다!")
    st.stop()

st.title("🌐 AI 뉴스 실시간 분석 (마종 단계)")

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
            
            # 멘토의 조언: 0점 방지를 위해 2.5초로 지연 시간 소폭 상향
            time.sleep(2.5) 
            
            try:
                prompt = f"Rate this crypto news impact from -100 to 100. Answer ONLY with the number. Title: {title}"
                response = model.generate_content(prompt)
                
                ai_raw_text = response.text.strip()
                # 화면에 직접 찍어서 확인 (성공 시 삭제 가능)
                st.info(f"뉴스 {i+1} 분석 응답: {ai_raw_text}")
                
                numbers = re.findall(r'-?\d+', ai_raw_text)
                score = int(numbers[0]) if numbers else 0
                
            except Exception as e:
                st.warning(f"⚠️ {i+1}번 분석 에러: {e}")
                score = 0
                
            results.append({'title': title, 'link': link, 'score': score})
            
        return results
    except Exception as e:
        st.error(f"데이터 수집 에러: {e}")
        return []

if st.button('🚀 최종 분석 실행'):
    data = get_ai_news_scores()
    if data:
        st.success("분석이 완료되었습니다!")
        for n in data:
            icon = "🔥" if n['score'] >= 50 else "🚨" if n['score'] <= -50 else "💬"
            st.write(f"**{icon} [{n['score']}점]** {n['title']}")