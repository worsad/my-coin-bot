import streamlit as st
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="AI 뉴스 분석기", layout="wide")
st.title("📰 비트코인 실시간 뉴스 수집기")

def get_news():
    # 1. 네이버 뉴스 최신순 검색 결과 URL
    url = "https://search.naver.com/search.naver?where=news&query=비트코인&sort=1"
    
    # 2. 멘토의 핵심 팁: 브라우저인 척 위장하는 신분증(User-Agent)
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        res = requests.get(url, headers=headers, timeout=5)
        res.raise_for_status() # 접속 에러 시 즉시 예외 발생
        
        soup = BeautifulSoup(res.text, 'html.parser')
        
        # 3. 뉴스 제목 요소 찾기 (네이버의 현재 뉴스 제목 클래스)
        news_items = soup.select('a.news_tit')
        
        results = []
        for item in news_items:
            title = item.get_text()
            link = item['href']
            results.append({'title': title, 'link': link})
            
        return results
    except Exception as e:
        st.error(f"데이터 수집 중 오류 발생: {e}")
        return []

if st.button('🚀 최신 뉴스 강제 수집 시작'):
    with st.spinner('네이버 뉴스를 긁어오는 중...'):
        news = get_news()
        
        if news:
            st.success(f"성공! {len(news)}개의 뉴스를 가져왔습니다.")
            for i, n in enumerate(news):
                st.write(f"{i+1}. [{n['title']}]({n['link']})")
                st.divider()
        else:
            st.error("뉴스를 하나도 발견하지 못했습니다. 네이버 차단 혹은 태그 이름 변경 가능성이 있습니다.")
            # 멘토의 디버깅: 실제 페이지 내용을 살짝 보여줌
            if st.checkbox("수집된 원본 텍스트 확인 (디버깅용)"):
                res = requests.get("https://search.naver.com/search.naver?where=news&query=비트코인&sort=1")
                st.text(res.text[:500])