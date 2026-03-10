import streamlit as st
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="비트코인 뉴스 분석", layout="wide")

st.title("📰 실시간 비트코인 뉴스 분석")
st.write("최신 뉴스를 가져와서 시장의 분위기를 파악합니다.")

# 뉴스 분석용 키워드
POS = ['상승', '호재', '급등', '폭등', '반등', '긍정']
NEG = ['하락', '악재', '폭락', '규제', '우려', '유의']

def get_news():
    url = "https://search.naver.com/search.naver?where=news&query=비트코인&sort=1"
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    return soup.select('.news_tit')

if st.button('뉴스 불러오기 및 분석'):
    news_items = get_news()
    score = 0
    
    for item in news_items[:10]:
        title = item.get_text()
        link = item['href']
        
        # 간단한 감성 분석
        current_score = 0
        for p in POS:
            if p in title: current_score += 1
        for n in NEG:
            if n in title: current_score -= 1
        
        score += current_score
        
        # 화면 출력
        st.write(f"🔗 [{title}]({link})")
        if current_score > 0: st.caption("🟢 긍정적 단어 감지")
        elif current_score < 0: st.caption("🔴 부정적 단어 감지")
        st.divider()

    # 종합 평가
    if score > 0:
        st.success(f"종합 점수: {score}점 - 현재 시장 분위기는 **긍정적**입니다.")
    elif score < 0:
        st.error(f"종합 점수: {score}점 - 현재 시장 분위기는 **부정적**입니다.")
    else:
        st.info("종합 점수: 0점 - 현재 시장은 **중립적**입니다.")