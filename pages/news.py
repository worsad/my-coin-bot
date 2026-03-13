import streamlit as st
import requests
import xml.etree.ElementTree as ET
import google.generativeai as genai
import os
import re
from dotenv import load_dotenv

# 보안 및 설정
load_dotenv()
api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("🚨 API 키가 설정되지 않았습니다!")
    st.stop()

def get_ai_news_scores():
    url = "https://news.google.com/rss/search?q=비트코인+when:1d&hl=ko&gl=KR&ceid=KR:ko"
    try:
        res = requests.get(url, timeout=10)
        root = ET.fromstring(res.text)
        results = []
        
        for item in root.findall('.//item')[:10]:
            title = item.find('title').text
            link = item.find('link').text
            
            # --- 멘토의 핵심: AI에게 점수(숫자) 요구 ---
            prompt = f"이 뉴스 제목을 읽고 비트코인 시장에 미칠 영향을 -100에서 100 사이의 '정수' 하나로만 답해: {title}"
            response = model.generate_content(prompt)
            
            # 숫자만 뽑아내는 정규식 (이게 있어야 숫자로 찍힙니다)
            score_match = re.search(r'-?\d+', response.text)
            score = int(score_match.group()) if score_match else 0
            
            results.append({'title': title, 'link': link, 'score': score})
        return results
    except:
        return []

# --- UI 출력 부분 ---
st.title("🌐 AI 실시간 뉴스 수치 판독기")

if st.button('🚀 실시간 뉴스 점수 분석'):
    with st.spinner('AI가 뉴스를 숫자로 변환 중...'):
        news_data = get_ai_news_scores()
        
        for n in news_data:
            # 숫자에 따라 색상 결정
            if n['score'] >= 50: color = "#00FF00" # 강한 초록
            elif n['score'] > 0: color = "#CCE5FF" # 연한 파랑
            elif n['score'] <= -50: color = "#FF0000" # 강한 빨강
            elif n['score'] < 0: color = "#FFCCCC" # 연한 빨강
            else: color = "#FFFFFF"

            # 숫자를 강조한 레이아웃
            with st.expander(f"[{n['score']}점] {n['title']}"):
                st.markdown(f"### AI 신뢰 점수: <span style='color:{color}'>{n['score']}점</span>", unsafe_allow_html=True)
                st.write(f"🔗 [기사 원문 읽기]({n['link']})")