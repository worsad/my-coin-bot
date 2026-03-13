import streamlit as st
import requests
import xml.etree.ElementTree as ET
import google.generativeai as genai
import os
import re
import time
from datetime import datetime, UTC

# 1. 보안 및 AI 설정
api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    
    # 안전 설정 (차단 방지)
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]

    # [멘토의 핵심 수정] 무조건 작동하게 만드는 순차적 모델 로드
    model = None
    # 시도할 모델 이름 후보들 (가장 최신부터 구형순)
    model_candidates = ['gemini-1.5-flash', 'gemini-1.5-flash-latest', 'gemini-pro']
    
    for model_name in model_candidates:
        try:
            temp_model = genai.GenerativeModel(model_name=model_name, safety_settings=safety_settings)
            # 실제로 작동하는지 테스트 호출 (아주 짧게)
            temp_model.generate_content("test") 
            model = temp_model
            st.sidebar.success(f"✅ 연결 성공: {model_name}")
            break
        except Exception:
            continue # 실패하면 다음 후보로

    if model is None:
        st.error("🚨 모든 AI 모델 접속에 실패했습니다. API 키나 권한을 확인하세요.")
        st.stop()
else:
    st.error("🚨 API 키가 설정되지 않았습니다!")
    st.stop()

st.title("🌐 AI 뉴스 실시간 분석 (최종 안정화 버전)")

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
            
            time.sleep(2.0) 
            
            try:
                prompt = f"Rate this crypto news impact from -100 to 100. Answer ONLY with the number. Title: {title}"
                response = model.generate_content(prompt)
                
                ai_raw_text = response.text.strip()
                st.info(f"뉴스 {i+1} 분석 응답: {ai_raw_text}")
                
                numbers = re.findall(r'-?\d+', ai_raw_text)
                score = int(numbers[0]) if numbers else 0
                
            except Exception as e:
                st.warning(f"⚠️ {i+1}번 분석 실패: {e}")
                score = 0
                
            results.append({'title': title, 'link': link, 'score': score})
            
        return results
    except Exception as e:
        st.error(f"뉴스 수집 에러: {e}")
        return []

if st.button('🚀 실시간 AI 분석 가동'):
    data = get_ai_news_scores()
    if data:
        st.success("모든 뉴스 분석이 완료되었습니다!")
        avg_score = sum(n['score'] for n in data) / len(data)
        st.metric("📊 종합 심리 지수", f"{avg_score:+.1f}점")
        
        st.divider()
        for n in data:
            icon = "🔥" if n['score'] >= 50 else "🚨" if n['score'] <= -50 else "💬"
            st.write(f"**{icon} [{n['score']}점]** {n['title']}")