import streamlit as st
import requests
import xml.etree.ElementTree as ET
import google.generativeai as genai
import os
import re
import time
from datetime import datetime, timedelta, UTC # 최신 표준 UTC 임포트

# 1. 보안 및 AI 설정 (Secrets 우선 로드)
api_key = st.secrets.get("GOOGLE_API_KEY") or os.getenv("GOOGLE_API_KEY")

if api_key:
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("🚨 API 키가 설정되지 않았습니다! Streamlit Secrets를 확인하세요.")
    st.stop()

st.set_page_config(page_title="AI 뉴스 분석 센터", layout="wide")
st.title("🌐 AI 실시간 뉴스 수치 판독기")

def get_ai_news_scores():
    # 수집 범위를 1d(24시간)로 설정하여 데이터 확보
    url = "https://news.google.com/rss/search?q=비트코인+when:1d&hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        res = requests.get(url, timeout=10)
        res.encoding = 'utf-8' # 한글 깨짐 방지
        root = ET.fromstring(res.text)
        items = root.findall('.//item')[:7] # RPM 제한을 고려해 7개로 최적화
        
        results = []
        
        # 진행 상황 표시를 위한 Streamlit 요소
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, item in enumerate(items):
            title = item.find('title').text
            link = item.find('link').text
            
            status_text.text(f" 분석 중 ({i+1}/{len(items)}): {title[:30]}...")
            
            # AI 호출 전 짧은 휴식 (무료 API 차단 방지)
            time.sleep(0.5) 
            
            try:
                prompt = f"이 뉴스 제목을 읽고 비트코인 시장 호재면 +, 악재면 - 점수(-100~100) 숫자만 답해: {title}"
                response = model.generate_content(prompt)
                
                # 숫자만 정교하게 추출
                score_match = re.search(r'-?\d+', response.text)
                score = int(score_match.group()) if score_match else 0
            except:
                score = 0 # 에러 발생 시 중립 점수
                
            results.append({'title': title, 'link': link, 'score': score})
            progress_bar.progress((i + 1) / len(items))
            
        status_text.empty()
        progress_bar.empty()
        return results
    except Exception as e:
        st.error(f"데이터 수집 중 오류 발생: {e}")
        return []

# --- UI 레이아웃 ---
if st.button('🚀 실시간 뉴스 점수 분석 시작'):
    news_data = get_ai_news_scores()
    
    if news_data:
        # 전체 평균 점수 계산 및 표시
        avg_score = sum(n['score'] for n in news_data) / len(news_data)
        st.metric("📊 오늘 비트코인 뉴스 심리 지수", f"{avg_score:+.1f}점", 
                  width='stretch') # 2026년형 옵션 적용

        st.divider()

        # 점수별로 내림차순 정렬 (호재부터 보기)
        news_data.sort(key=lambda x: x['score'], reverse=True)

        for n in news_data:
            # 점수에 따른 동적 색상/아이콘 적용
            if n['score'] >= 50:
                bg_color, label = "#D4EDDA", "🔥 강력호재" # 녹색
            elif n['score'] <= -50:
                bg_color, label = "#F8D7DA", "🚨 강력악재" # 적색
            elif n['score'] > 0:
                bg_color, label = "#E7F3FF", "🟢 긍정" # 청색
            elif n['score'] < 0:
                bg_color, label = "#FFF3CD", "🔴 하락주의" # 황색
            else:
                bg_color, label = "#F2F2F2", "💬 정보" # 회색

            with st.expander(f"[{n['score']}점] {n['title']}"):
                st.markdown(f"""
                <div style="background-color:{bg_color}; padding:10px; border-radius:5px;">
                    <strong>AI 판독: {label} ({n['score']}점)</strong><br>
                    <a href="{n['link']}" target="_blank">기사 원문 읽기</a>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("분석할 뉴스를 가져오지 못했습니다. 잠시 후 다시 시도하세요.")

# 하단 타임스탬프 (최신 표준 적용)
st.caption(f"Last Analysis Sync: {datetime.now(UTC).astimezone().strftime('%Y-%m-%d %H:%M:%S')}")