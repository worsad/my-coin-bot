import streamlit as st
import requests
import xml.etree.ElementTree as ET
from google import genai  # 최신 SDK
import os
import re
import time

# 1. 보안 및 AI 설정
api_key = st.secrets.get("GOOGLE_API_KEY")

if api_key:
    try:
        # 최신 SDK 클라이언트 생성
        client = genai.Client(api_key=api_key)
        
        # 연결 확인 및 초록 불(Success) 표시용 테스트
        client.models.generate_content(
            model='gemini-2.0-flash',
            contents="connection check"
        )
        st.sidebar.success("✅ Gemini 2.0 Flash 엔진 가동 중")
    except Exception as e:
        st.sidebar.error(f"❌ 엔진 시동 실패: {e}")
        st.stop()
else:
    st.error("🚨 Streamlit Secrets에 API 키를 등록하세요!")
    st.stop()

st.title("🌐 AI 뉴스 실시간 분석 (2.0 Flash)")

def get_ai_news_scores():
    # 타임스탬프를 추가해 캐시를 방지 (매번 새로운 뉴스를 긁어옴)
    now_ts = int(time.time())
    url = f"https://news.google.com/rss/search?q=비트코인+시황+급등락+when:1h&hl=ko&gl=KR&ceid=KR:ko&ts={now_ts}"
    
    try:
        res = requests.get(url, timeout=10)
        root = ET.fromstring(res.content)
        items = root.findall('.//item')[:5] 
        
        results = []
        for i, item in enumerate(items):
            title = item.find('title').text
            link = item.find('link').text
            
            # API 할당량 보호 (2.0초 지연)
            time.sleep(2.0) 
            
            try:
                # [멘토의 비책] AI에게 강력한 트레이더 자아를 부여하여 중립 방지
                prompt = f"""
                너는 1분 1초가 급한 전문 가상화폐 데이트레이더야.
                다음 뉴스 제목을 읽고 시장의 심리를 분석해.
                -100(지옥)에서 100(천국) 사이의 숫자로만 답해.
                애매한 0점(중립)을 주면 너의 전 재산이 청산당한다고 생각하고 반드시 방향성을 정해.
                뉴스: {title}
                """
                
                # 최신 SDK 호출 방식
                response = client.models.generate_content(
                    model='gemini-2.0-flash',
                    contents=prompt
                )
                
                ai_raw_text = response.text.strip()
                st.info(f"🔍 뉴스 {i+1} 분석: {ai_raw_text}")
                
                # 숫자만 추출
                numbers = re.findall(r'-?\d+', ai_raw_text)
                score = int(numbers[0]) if numbers else 0
                
            except Exception as e:
                st.warning(f"⚠️ 기사 {i+1} 분석 건너뜀: {e}")
                score = 0
                
            results.append({'title': title, 'link': link, 'score': score})
            
        return results
    except Exception as e:
        st.error(f"뉴스 수집 실패: {e}")
        return []

# --- UI 실행부 ---
if st.button('🚀 실시간 시장 분석 가동'):
    with st.spinner('최신 뉴스를 긁어와서 AI가 분석 중...'):
        data = get_ai_news_scores()
        
    if data:
        st.success("분석 완료!")
        avg_score = sum(n['score'] for n in data) / len(data)
        st.metric("📊 종합 심리 지수", f"{avg_score:+.1f}점")
        
        st.divider()
        for n in data:
            icon = "🔥" if n['score'] >= 50 else "🚨" if n['score'] <= -50 else "💬"
            st.write(f"**{icon} [{n['score']}점]** [{n['title']}]({n['link']})")