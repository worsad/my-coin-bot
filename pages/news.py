import streamlit as st
import requests
from bs4 import BeautifulSoup
import xml.etree.ElementTree as ET

st.set_page_config(page_title="글로벌 코인 뉴스", layout="wide")
st.title("🌐 구글 뉴스 실시간 수집 (차단 방지형)")

def get_google_news():
    # 구글 뉴스 RSS (한글, 대한민국 설정)
    url = "https://news.google.com/rss/search?q=비트코인&hl=ko&gl=KR&ceid=KR:ko"
    
    try:
        res = requests.get(url, timeout=10)
        # XML 구조 파싱 (구글 뉴스는 XML로 데이터를 줍니다)
        root = ET.fromstring(res.text)
        
        results = []
        # 구글 뉴스 RSS의 기사 아이템(item)들만 추출
        for item in root.findall('.//item')[:15]: # 최신 15개
            title = item.find('title').text
            link = item.find('link').text
            pub_date = item.find('pubDate').text
            results.append({'title': title, 'link': link, 'date': pub_date})
            
        return results
    except Exception as e:
        st.error(f"구글 뉴스 연결 중 오류: {e}")
        return []

if st.button('🚀 구글 뉴스 강제 호출'):
    with st.spinner('구글 서버에서 뉴스를 가져오는 중...'):
        news = get_google_news()
        
        if news:
            st.success(f"성공! 구글에서 {len(news)}개의 뉴스를 확보했습니다.")
            for i, n in enumerate(news):
                with st.expander(f"{i+1}. {n['title']}"):
                    st.write(f"📅 게시일: {n['date']}")
                    st.write(f"🔗 [기사 원문 읽기]({n['link']})")
                    
                    # 간단한 키워드 분석 (상승/하락)
                    if any(word in n['title'] for word in ['상승', '호재', '돌파', '폭등']):
                        st.success("🟢 긍정 신호 포착")
                    elif any(word in n['title'] for word in ['하락', '악재', '폭락', '규제']):
                        st.error("🔴 부정 신호 포착")
        else:
            st.error("구글 뉴스조차 응답하지 않습니다. 네트워크 설정을 확인하세요.")