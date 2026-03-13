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
    
    # [멘토의 핵심 수정] 가용한 모델 중 가장 적합한 것을 자동으로 찾는 로직
    try:
        # 현재 API 키로 사용 가능한 모델 목록 확인
        available_models = [m.name for m in genai.list_models() if 'generateContent' in m.supported_methods]
        
        # 우선순위: gemini-1.5-flash -> gemini-1.0-pro -> 첫 번째 가용 모델
        target_model = ''
        if any('gemini-1.5-flash' in m for m in available_models):
            target_model = 'gemini-1.5-flash'
        elif any('gemini-pro' in m for m in available_models):
            target_model = 'gemini-pro'
        else:
            target_model = available_models[0] if available_models else 'gemini-pro'

        # 안전 설정
        safety_settings = [
            {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
            {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        ]

        model = genai.GenerativeModel(model_name=target_model, safety_settings=safety_settings)
        st.sidebar.success(f"✅ 사용 모델: {target_model}")
    except Exception as e:
        st.error(f"모델 로드 실패: {e}")
        st.stop()
else:
    st.error("🚨 API 키가 설정되지 않았습니다!")
    st.stop()

st.title("🌐 AI 뉴스 실시간 분석 (자동 모델 매칭)")

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
            
            # 무료 API 할당량 보호를 위한 대기 시간
            time.sleep(2.0) 
            
            try:
                # 점수 산출 프롬프트
                prompt = f"Analyze crypto news title and rate impact from -100 to 100. Answer ONLY with the number. Title: {title}"
                response = model.generate_content(prompt)
                
                ai_raw_text = response.text.strip()
                # UI에 실시간 분석 내용 표시
                st.info(f"뉴스 {i+1} 분석: {ai_raw_text}")
                
                numbers = re.findall(r'-?\d+', ai_raw_text)
                score = int(numbers[0]) if numbers else 0
                
            except Exception as e:
                st.warning(f"⚠️ {i+1}번 기사 분석 실패: {e}")
                score = 0
                
            results.append({'title': title, 'link': link, 'score': score})
            
        return results
    except Exception as e:
        st.error(f"뉴스 수집 실패: {e}")
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