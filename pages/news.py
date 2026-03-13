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
    
    # [멘토의 핵심 수정] 안전 설정: 뉴스 분석 시 차단되는 것을 막기 위해 BLOCK_NONE 설정
    safety_settings = [
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
    ]
    
    # [멘토의 핵심 수정] 모델명 앞에 'models/'를 붙여 경로 에러를 원천 봉쇄합니다.
    try:
        model = genai.GenerativeModel(
            model_name='models/gemini-1.5-flash', 
            safety_settings=safety_settings
        )
    except Exception as e:
        # 혹시라도 models/ 경로가 안 먹힐 경우를 대비한 2중 방어막
        model = genai.GenerativeModel('gemini-pro')
else:
    st.error("🚨 API 키가 설정되지 않았습니다!")
    st.stop()

st.title("🌐 AI 뉴스 실시간 분석 (404 박멸 버전)")

def get_ai_news_scores():
    # RSS 쿼리 최적화
    url = f"https://news.google.com/rss/search?q=비트코인+코인+when:1d&hl=ko&gl=KR&ceid=KR:ko&ts={int(time.time())}"
    
    try:
        res = requests.get(url, timeout=10)
        root = ET.fromstring(res.content)
        items = root.findall('.//item')[:5] 
        
        results = []
        for i, item in enumerate(items):
            title = item.find('title').text
            link = item.find('link').text
            
            # 0점 방지를 위한 대기 시간 (무료 API 할당량 보호)
            time.sleep(2.5) 
            
            try:
                # 숫자로만 답하라고 강력하게 명령
                prompt = f"Rate this crypto news impact from -100 to 100. Answer ONLY with the number. Title: {title}"
                response = model.generate_content(prompt)
                
                ai_raw_text = response.text.strip()
                # AI가 실제로 뭐라고 했는지 화면에 바로 출력하여 확인
                st.info(f"뉴스 {i+1} 분석 응답: {ai_raw_text}")
                
                # 정규식을 사용하여 숫자만 추출
                numbers = re.findall(r'-?\d+', ai_raw_text)
                score = int(numbers[0]) if numbers else 0
                
            except Exception as e:
                st.warning(f"⚠️ {i+1}번 분석 실패 (AI 응답 오류): {e}")
                score = 0
                
            results.append({'title': title, 'link': link, 'score': score})
            
        return results
    except Exception as e:
        st.error(f"뉴스 데이터 수집 실패: {e}")
        return []

# --- UI 레이아웃 ---
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