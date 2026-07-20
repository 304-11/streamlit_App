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

# --- [1. 한글 폰트 다운로드 설정] ---
FONT_URL = "https://github.com/google/fonts/raw/main/ofl/nanumgothic/NanumGothic-Regular.ttf"
FONT_PATH = "NanumGothic-Regular.ttf"

@st.cache_resource
def download_font():
    """스트림릿 클라우드(리눅스) 환경에서 한글 깨짐을 방지하기 위해 폰트 다운로드"""
    if not os.path.exists(FONT_PATH):
        try:
            response = requests.get(FONT_URL, timeout=10)
            with open(FONT_PATH, "wb") as f:
                f.write(response.content)
        except Exception:
            return None
    return FONT_PATH

font_path = download_font()

# --- [2. 유튜브 API 및 데이터 정제 함수] ---
def get_video_id(url):
    """유튜브 URL에서 비디오 ID 추출"""
    regex = r"(?:v=|\/v\/|youtu\.be\/|\/embed\/)([^#\&\?]*)"
    match = re.search(regex, url)
    return match.group(1) if match else None

def clean_api_key(key_input):
    """사용자가 API_KEY = 'XYZ' 형태로 잘못 입력했을 때 문자열만 추출하는 예외 처리 함수"""
    if not key_input:
        return ""
    # 따옴표 내부의 API 키 값 추출 시도
    match = re.search(r'["\'](AIzaSy[^"\']+)["\']', key_input)
    if match:
        return match.group(1).strip()
    
    # 등호(=) 기준 뒤쪽 문자열 추출 시도
    if "=" in key_input:
        return key_input.split("=")[-1].replace('"', '').replace("'", "").strip()
        
    return key_input.strip()

def get_youtube_comments(api_key, video_id, max_count):
    """유튜브 API를 사용해 댓글 수집"""
    refined_key = clean_api_key(api_key)
    
    try:
        youtube = build("youtube", "v3", developerKey=refined_key)
        comments = []
        
        request = youtube.commentThreads().list(
            part="snippet",
            videoId=video_id,
            maxResults=min(max_count, 100),
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
                    
            if 'nextPageToken' in response and len(comments) < max_count:
                request = youtube.commentThreads().list_next(request, response)
            else:
                break
                
        return pd.DataFrame(comments), None
    except Exception as e:
        return pd.DataFrame(), str(e)

# --- [3. 사이드바 UI 설정] ---
st.sidebar.header("🔑 설정")
raw_api_key = st.sidebar.text_input("YouTube API Key를 입력하세요", type="password")
video_url = st.sidebar.text_input("유튜브 영상 링크를 입력하세요", placeholder="https://www.youtube.com/watch?v=...")
max_comments = st.sidebar.slider("분석할 댓글 개수 선택", min_value=10, max_value=500, value=100, step=10)

# --- [4. 세션 상태(Session State) 관리] ---
if "df_comments" not in st.session_state:
    st.session_state.df_comments = None
if "current_url" not in st.session_state:
    st.session_state.current_url = ""

# --- [5. 메인 로직 구동부] ---
if raw_api_key and video_url:
    video_id = get_video_id(video_url)
    
    if video_id:
        st.subheader("📺 대상 영상")
        st.video(video_url)
        
        # 새로운 영상 링크가 입력되면 이전 수집 데이터를 초기화
        if st.session_state.current_url != video_url:
            st.session_state.df_comments = None
            st.session_state.current_url = video_url

        # 분석 데이터 수집 실행 버튼
        if st.sidebar.button("📊 댓글 분석 시작"):
            with st.spinner("댓글을 불러오고 분석하는 중입니다..."):
                df, error_msg = get_youtube_comments(raw_api_key, video_id, max_comments)
                if error_msg:
                    st.error(f"API 호출 중 오류가 발생했습니다: {error_msg}")
                    st.session_state.df_comments = None
                elif df.empty:
                    st.warning("가져온 댓글이 없거나 비공개 영상입니다.")
                    st.session_state.df_comments = None
                else:
                    st.session_state.df_comments = df
                    st.success(f"총 {len(df)}개의 댓글을 성공적으로 수집했습니다!")

        # 데이터가 안전하게 세션에 로드되었을 경우 대시보드 시각화 출력
        if st.session_state.df_comments is not None:
            df = st.session_state.df_comments
            
            with st.expander("수집된 데이터 원본 보기"):
                st.dataframe(df, use_container_width=True)
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📈 시간대별 댓글 작성 추이")
                df_time = df.copy()
                df_time['date'] = df_time['published_at'].dt.date
                df_trend = df_time.groupby('date').size().reset_index(name='댓글 수')
                
                fig_time = px.line(df_trend, x='date', y='댓글 수', title="날짜별 댓글 등록 수", markers=True)
                st.plotly_chart(fig_time, use_container_width=True)
            
            with col2:
                st.subheader("❤️ 댓글 반응도 (좋아요 상위)")
                df_likes = df.nlargest(5, 'like_count')[['author', 'like_count', 'text']]
                
                fig_like = px.bar(
                    df_likes, x='like_count', y='author', orientation='h', 
                    title="가장 반응이 좋았던 댓글 Top 5 (좋아요 수)",
                    text='text', labels={'like_count': '좋아요 수', 'author': '작성자'}
                )
                fig_like.update_layout(yaxis={'categoryorder':'total ascending'})
                st.plotly_chart(fig_like, use_container_width=True)
            
            # 워드클라우드 시각화 구역
            st.subheader("☁️ 댓글 한글 워드클라우드")
            text_combined = " ".join(df['text'].dropna().astype(str))
            hangul_words = re.findall(r'[가-힣]+', text_combined)
            processed_text = " ".join(hangul_words)
            
            if processed_text.strip():
                stop_words = ["진짜", "너무", "이거", "보고", "영상", "완전", "그냥", "진심", "다들", "내가"]
                current_font = font_path if font_path else None
                
                wordcloud = WordCloud(
                    font_path=current_font,
                    background_color="white",
                    width=800,
                    height=400,
                    stopwords=set(stop_words)
                ).generate(processed_text)
                
                fig, ax = plt.subplots(figsize=(10, 5))
                ax.imshow(wordcloud, interpolation='bilinear')
                ax.axis("off")
                st.pyplot(fig)
                plt.close(fig)  # 메모리 백그라운드 누수 방지
            else:
                st.info("한글 단어가 포함된 댓글이 없어 워드클라우드를 생성할 수 없습니다.")
    else:
        st.error("올바른 유튜브 URL 형식이 아닙니다.")
else:
    st.info("💡 사이드바에 유튜브 API Key와 영상 링크를 입력한 후 '댓글 분석 시작'을 눌러주세요.")
