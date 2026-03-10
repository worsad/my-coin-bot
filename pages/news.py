import streamlit as st
import requests
from bs4 import BeautifulSoup

st.set_page_config(page_title="AI 뉴스 분석기", layout="wide")
st.title("📰 비트코인 실시간 뉴스 심리 분석")

# 멘토의 팁: 단어장을 대폭 늘려야 정확해집니다.
POS = ['상승', '호재', '폭등', '돌파', '반등', '긍정', '신고가', '매수', '급등', 'ETF', '채택']
NEG = ['하락', '악재', '폭락', '규제', '우려', '유의', '금지', '매도', '급락', '경고', '조정']

def get_news():
    # 최신순 정렬(&sort=1)로 비트코인 관련 뉴스 수집
    url = "https://search.naver.com/search.naver?where=news&query=비트코인&sort=1"
    headers = {'User-Agent': 'Mozilla/5.0'}
    res = requests.get(url, headers=headers)
    soup = BeautifulSoup(res.text, 'html.parser')
    return soup.select('.news_tit')

if st.button('🚀 최신 뉴스 분석 시작'):
    news_items = get_news()
    
    if not news_items:
        st.warning("뉴스를 가져오지 못했습니다. 잠시 후 다시 시도하세요.")
    else:
        st.info(f"총 {len(news_items)}개의 최신 뉴스를 발견했습니다!")
        total_score = 0
        
        for item in news_items:
            title = item.get_text()
            link = item['href']
            
            # 단어 감지 로직
            current_score = 0
            found_pos = [p for p in POS if p in title]
            found_neg = [n for n in NEG if n in title]
            
            current_score += len(found_pos)
            current_score -= len(found_neg)
            total_score += current_score
            
            # 화면 출력
            with st.expander(f"📄 {title}"):
                st.write(f"🔗 [기사 원문 보기]({link})")
                if found_pos: st.success(f"긍정 단어 발견: {', '.join(found_pos)}")
                if found_neg: st.error(f"부정 단어 발견: {', '.join(found_neg)}")
                if not found_pos and not found_neg: st.write("⚪ 감지된 감성 단어 없음")

        # 종합 결과 비주얼
        st.divider()
        st.subheader("📊 오늘의 시장 심리 점수")
        
        if total_score > 0:
            st.balloons() # 축하 풍선!
            st.success(f"최종 점수: {total_score}점 | 시장은 현재 **탐욕/긍정** 단계입니다.")
        elif total_score < 0:
            st.error(f"최종 점수: {total_score}점 | 시장은 현재 **공포/부정** 단계입니다.")
        else:
            st.warning("최종 점수: 0점 | 시장은 현재 **방향성 탐색 중(중립)**입니다.")