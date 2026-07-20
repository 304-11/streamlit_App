import streamlit as st
from googleapiclient.discovery import build
import pandas as pd
import plotly.express as px
from wordcloud import WordCloud
import matplotlib.pyplot as plt
import re
import requests
import os

# 페이지 설정
st.set_page_config(page_title="유튜브 댓글 분석기", layout="wide")
st.title("📊 유튜브 댓글 분석기 (Streamlit Cloud)")

# --- [1. 폰트 다운로드 설정] ---
# 스트림릿 클라우드(리눅스 환경)에서 한글 깨짐을 방지하기 위해 나눔 폰트를 다운로드합니다.
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
FONT_PATH = "NanumGothic-Regular.ttf"

@st.cache_resource
def download_font():
    if not os.path.exists(FONT_PATH):
        response = requests.get(FONT_URL)
        with open(FONT_PATH, "wb") as f:
            f.write(response.content)
    return FONT_PATH

try:
    font_path = download_font()
except Exception as e:
    font_path = None
    st.warning("한글 폰트를 다운로드하지 못했습니다. 워드클라우드 한글이 깨질 수 있습니다.")

# --- [2. 유튜브 API 함수] ---
def get_video_id(url):
    """유튜브 URL에서 비디오 ID 추출"""
    regex = r"(?:v=|\/v\/|youtu\.be\/|\/embed\/)([^#\&\?]*)"
    match = re.search(regex, url)
    return match.group(1) if match else None

def get_youtube_comments(api_key, video_id, max_count):
    """유튜브 댓글 가져오기"""
    youtube = build("youtube", "v3", developerKey=api_key)
    comments = []
    
    try:
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(max_count, 100), # 한 번에 최대 100개
            textFormat="plainText"
        )
        
        while request and len(comments) < max_count:
            response = request.execute()
            for item in response['items']:
                comment_data = item['snippet']['topLevelComment']['snippet']
                comments.append({
                    'author': comment_data['authorDisplayName'],
                    'text': comment_data['textDisplay'],
                    'published_at': pd.to_datetime(comment_data['publishedAt']),
                    'like_count': comment_data['likeCount']
                })
                if len(comments) >= max_count:
                    break
                    
            # 다음 페이지가 있으면 계속 가져옴
            if 'nextPageToken' in response and len(comments) < max_count:
                request = youtube.commentThreads().list_next(request, response)
            else:
                break
                
        return pd.DataFrame(comments)
    except Exception as e:
        st.error(f"API 호출 중 오류가 발생했습니다: {e}")
        return pd.DataFrame()

# --- [3. 사이드바 설정] ---
st.sidebar.header("🔑 설정")
api_key = st.sidebar.text_input("YouTube API Key를 입력하세요", type="password")
video_url = st.sidebar.text_input("유튜브 영상 링크를 입력하세요", placeholder="https://www.youtube.com/watch?v=...")
max_comments = st.sidebar.slider("분석할 댓글 개수 선택", min_value=10, max_value=500, value=100, step=10)

# --- [4. 메인 분석 로직] ---
if api_key and video_url:
    video_id = get_video_id(video_url)
    
    if video_id:
        # 1. 영상 임베드 화면 표시
        st.subheader("📺 대상 영상")
        st.video(video_url)
        
        # 분석 시작 버튼
        if st.sidebar.button("📊 댓글 분석 시작"):
            with st.spinner("댓글을 불러오고 분석하는 중입니다..."):
                df = get_youtube_comments(api_key, video_id, max_comments)
                
            if not df.empty:
                st.success(f"총 {len(df)}개의 댓글을 성공적으로 수집했습니다!")
                
                # 데이터 확인용 (접어두기)
                with st.expander("수집된 데이터 원본 보기"):
                    st.dataframe(df)
                
                # 구역 나누기
                col1, col2 = st.columns(2)
                
                with col1:
                    # 2. 시간대별 댓글 작성 추이 (시계열 차트)
                    st.subheader("📈 시간대별 댓글 작성 추이")
                    # 날짜별로 정렬 및 카운트
                    df_time = df.copy()
                    df_time['date'] = df_time['published_at'].dt.date
                    df_trend = df_time.groupby('date').size().reset_index(name='댓글 수')
                    
                    fig_time = px.line(df_trend, x='date', y='댓글 수', title="날짜별 댓글 등록 수", markers=True)
                    st.plotly_chart(fig_time, use_container_width=True)
                
                with col2:
                    # 3. 댓글 반응도 분석 (좋아요 수 기준)
                    st.subheader("❤️ 댓글 반응도 (좋아요 상위)")
                    df_likes = df.nlargest(5, 'like_count')[['author', 'like_count', 'text']]
                    
                    fig_like = px.bar(df_likes, x='like_count', y='author', orientation='h', 
                                      title="가장 반응이 좋았던 댓글 Top 5 (좋아요 수)",
                                      text='text', labels={'like_count': '좋아요 수', 'author': '작성자'})
                    fig_like.update_layout(yaxis={'categoryorder':'total ascending'})
                    st.plotly_chart(fig_like, use_container_width=True)
                
                # 4. 한글 워드클라우드
                st.subheader("☁️ 댓글 한글 워드클라우드")
                
                # 한글 단어만 추출하는 간단한 전처리
                text_combined = " ".join(df['text'].dropna().astype(str))
                hangul_words = re.findall(r'[가-힣]+', text_combined)
                processed_text = " ".join(hangul_words)
                
                if processed_text.strip():
                    # 불용어(제외할 단어) 간단히 지정
                    stop_words = ["진짜", "너무", "이거", "진짜", "보고", "영상", "완전"]
                    
                    wordcloud = WordCloud(
                        font_path=font_path,
                        background_color="white",
                        width=800,
                        height=400,
                        stopwords=set(stop_words)
                    ).generate(processed_text)
                    
                    fig, ax = plt.subplots(figsize=(10, 5))
                    ax.imshow(wordcloud, interpolation='interlink')
                    ax.axis("off")
                    st.pyplot(fig)
                else:
                    st.info("한글 단어가 포함된 댓글이 없어 워드클라우드를 생성할 수 없습니다.")
                    
            else:
                st.warning("가져온 댓글이 없거나 오류가 발생했습니다.")
    else:
        st.error("올바른 유튜브 URL 형식이 아닙니다.")
else:
    st.info("💡 사이드바에 유튜브 API Key와 영상 링크를 입력한 후 '댓글 분석 시작'을 눌러주세요.")
