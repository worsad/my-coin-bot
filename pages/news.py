import streamlit as st
import requests
import xml.etree.ElementTree as ET
from google import genai
import time
import re
import plotly.express as px

# 1. 보안 및 AI 설정
api_key = st.secrets.get("GOOGLE_API_KEY")

if api_key:
    try:
        client = genai.Client(api_key=api_key)
        st.sidebar.success("✅ Gemini 엔진 온라인")
    except Exception as e:
        st.sidebar.error("❌ 엔진 시동 실패")
        st.stop()
else:
    st.error("🚨 API 키를 등록하세요!")
    st.stop()

st.title("💰 AI 뉴스 제목 스캐너")

def fetch_and_analyze():
    headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"}
    now_ts = int(time.time())
    url = f"https://news.google.com/rss/search?q=비트코인+시황&hl=ko&gl=KR&ceid=KR:ko&ts={now_ts}"
    
    try:
        res = requests.get(url, headers=headers, timeout=15)
        root = ET.fromstring(res.content)
        # 안정성을 위해 딱 3개만 집중 분석합니다.
        items = root.findall('.//item')[:3] 
        
        if not items:
            st.warning("🧐 현재 분석할 뉴스가 없습니다.")
            return []

        results = []
        progress_bar = st.progress(0, text="API를 보호하며 제목 분석 중...")

        for i, item in enumerate(items):
            title = item.find('title').text
            link = item.find('link').text
            
            # [생존 전략] 무료 티어는 10초 대기가 가장 안전합니다.
            time.sleep(10.0) 
            
            try:
                # 멘토의 프롬프트: 점수와 짧은 이유를 함께 요구 (정확도 향상)
                prompt = f"코인 분석가로서 다음 뉴스 제목이 가격에 미칠 영향을 분석해. 점수는 -100~100 사이로 주고, 이유를 10자 이내로 써. 형식: [점수] 숫자 [이유] 내용. 제목: {title}"
                
                response = client.models.generate_content(
                    model='gemini-1.5-flash', 
                    contents=prompt
                )
                
                res_text = response.text
                score = int(re.findall(r'-?\d+', res_text)[0])
                # 이유 부분 추출 (없으면 공백)
                reason_match = re.search(r'\[이유\]\s*(.*)', res_text)
                reason = reason_match.group(1) if reason_match else "분석 완료"
                
            except:
                score, reason = 0, "분석 지연"
                
            results.append({'title': title, 'link': link, 'score': score, 'reason': reason})
            progress_bar.progress((i + 1) / len(items))
        
        progress_bar.empty()
        return results
    except Exception as e:
        st.error(f"🚨 시스템 오류: {e}")
        return []

# --- 실행 및 결과 출력 ---
if 'news_data' not in st.session_state:
    st.session_state.news_data = fetch_and_analyze()

if st.session_state.news_data:
    data = st.session_state.news_data
    avg_score = sum(n['score'] for n in data) / len(data)
    
    # 종합 지표
    st.subheader(f"📊 종합 시장 점수: {avg_score:+.1f}점")
    
    fig = px.bar(data, x='score', y='title', orientation='h', 
                 color='score', color_continuous_scale='RdBu', range_x=[-100, 100])
    st.plotly_chart(fig, use_container_width=True, key="fixed_title_chart")

    st.divider()
    
    for n in data:
        color = "red" if n['score'] < 0 else "blue"
        with st.expander(f"**[:{color}[{n['score']}점]]** {n['title']}"):
            st.write(f"💡 **AI 판단:** {n['reason']}")
            st.write(f"🔗 [기사 원문]({n['link']})")

    if st.button('🔄 다시 분석하기', key="refresh_btn"):
        del st.session_state.news_data
        st.rerun()