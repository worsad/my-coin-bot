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
    # 안전 설정(Safety Settings)을 해제하여 뉴스 분석 시 거부 반응 최소화
    model = genai.GenerativeModel('gemini-1.5-flash')
else:
    st.error("🚨 API 키가 설정되지 않았습니다! Streamlit Secrets를 확인하세요.")
    st.stop()

st.set_page_config(page_title="AI 뉴스 분석 센터", layout="wide")
st.title("🌐 AI 실시간 뉴스 수치 판독기")

def get_ai_news_scores():
    # 쿼리에 '코인' 추가하여 더 명확한 데이터 수집
    url = "https://news.google.com/rss/search?q=비트코인+코인+when:1d&hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        res = requests.get(url, timeout=10)
        res.encoding = 'utf-8'
        root = ET.fromstring(res.text)
        items = root.findall('.//item')[:5] # 안정성을 위해 5개로 압축 진행
        
        results = []
        progress_bar = st.progress(0)
        status_text = st.empty()

        for i, item in enumerate(items):
            title = item.find('title').text
            link = item.find('link').text
            
            status_text.text(f"🤖 AI가 뉴스 맥락 분석 중 ({i+1}/{len(items)})...")
            
            # --- 멘토의 핵심 수정: RPM 제한 회피를 위한 지연 시간 강화 ---
            time.sleep(2.0) 
            
            try:
                # 딴소리 못하게 프롬프트를 매우 엄격하게 수정
                prompt = f"""
                Analyze the following crypto news title.
                Rate its impact on Bitcoin price from -100(Very Bearish) to 100(Very Bullish).
                Respond ONLY with the number. Do not write anything else.
                Title: {title}
                """
                response = model.generate_content(prompt)
                ai_text = response.text.strip()
                
                # 숫자 추출 로직 강화
                score_match = re.search(r'-?\d+', ai_text)
                score = int(score_match.group()) if score_match else 0
                
            except Exception as e:
                print(f"AI 분석 개별 에러: {e}")
                score = 0
                
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
        avg_score = sum(n['score'] for n in news_data) / len(news_data)
        
        # 종합 점수 게이지 스타일 표시
        col1, col2 = st.columns([1, 2])
        col1.metric("📊 평균 심리", f"{avg_score:+.1f}점")
        
        if avg_score > 10:
            col2.success("현재 시장 뉴스는 대체로 '호재' 위주입니다.")
        elif avg_score < -10:
            col2.error("현재 시장 뉴스는 대체로 '악재' 위주입니다.")
        else:
            col2.warning("현재 시장 뉴스는 '중립' 상태입니다.")

        st.divider()
        news_data.sort(key=lambda x: x['score'], reverse=True)

        for n in news_data:
            if n['score'] >= 50: bg, lb = "#D4EDDA", "🔥 강력호재"
            elif n['score'] <= -50: bg, lb = "#F8D7DA", "🚨 강력악재"
            elif n['score'] > 0: bg, lb = "#E7F3FF", "🟢 긍정"
            elif n['score'] < 0: bg, lb = "#FFF3CD", "🔴 하락주의"
            else: bg, lb = "#F2F2F2", "💬 정보"

            with st.expander(f"[{n['score']}점] {n['title']}"):
                st.markdown(f"""
                <div style="background-color:{bg}; padding:15px; border-radius:10px; border: 1px solid #ddd;">
                    <h4 style="margin:0; color:black;">AI 판독: {lb} ({n['score']}점)</h4>
                    <p style="margin:10px 0 0 0;"><a href="{n['link']}" target="_blank" style="color:#0066cc;">기사 전문 보기</a></p>
                </div>
                """, unsafe_allow_html=True)
    else:
        st.warning("뉴스를 가져오지 못했습니다. 잠시 후 다시 시도하세요.")

st.caption(f"Last Analysis Sync: {datetime.now(UTC).astimezone().strftime('%Y-%m-%d %H:%M:%S')}")