import streamlit as st
import requests
import xml.etree.ElementTree as ET
from google import genai  # 패키지명이 바뀌었습니다!
import os
import re
import time
from datetime import datetime

# 1. 보안 및 AI 설정 (최신 SDK 방식)
api_key = st.secrets.get("GOOGLE_API_KEY")

if api_key:
    # 최신 SDK는 Client 객체를 생성하여 통신합니다.
    client = genai.Client(api_key=api_key)
else:
    st.error("🚨 API 키가 없습니다!")
    st.stop()

st.title("🌐 AI 뉴스 실시간 분석 (최신 엔진)")

def get_ai_news_scores():
    # 타임스탬프를 추가해 캐시를 방지하고 1시간 내 뉴스만 수집
    now_ts = int(time.time())
    url = f"https://news.google.com/rss/search?q=비트코인+시황+급등락+when:1h&hl=ko&gl=KR&ceid=KR:ko&ts={now_ts}"
    
    try:
        res = requests.get(url, timeout=10)
        root = ET.fromstring(res.content)
        items = root.findall('.//item')[:5] 
        
        results = []
        for i, item in enumerate(items):
            title = item.find('title').text
            
            # API 할당량 보호 (2.0초 지연)
            time.sleep(2.0) 
            
            try:
                # 최신 SDK의 호출 방식: models.generate_content
                prompt = f"당신은 공격적인 코인 트레이더입니다. 다음 뉴스를 보고 -100에서 100 사이의 숫자로만 점수를 매기세요. 중립(0점)은 금지입니다. 제목: {title}"
                
                response = client.models.generate_content(
                    model='gemini-2.0-flash', # 이제 최신 2.0 모델도 쓸 수 있습니다!
                    contents=prompt
                )
                
                ai_raw_text = response.text.strip()
                st.info(f"🔍 뉴스 {i+1} 분석: {ai_raw_text}")
                
                numbers = re.findall(r'-?\d+', ai_raw_text)
                score = int(numbers[0]) if numbers else 0
                
            except Exception as e:
                st.warning(f"⚠️ 분석 에러: {e}")
                score = 0
                
            results.append({'title': title, 'score': score})
            
        return results
    except Exception as e:
        st.error(f"데이터 수집 에러: {e}")
        return []

if st.button('🚀 최신 엔진으로 분석 시작'):
    data = get_ai_news_scores()
    if data:
        st.success("분석 완료!")
        for n in data:
            icon = "🔥" if n['score'] >= 50 else "🚨" if n['score'] <= -50 else "💬"
            st.write(f"**{icon} [{n['score']}점]** {n['title']}")