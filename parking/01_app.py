import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="주차장 정보 제공 시스템",
    page_icon="🚗",
    layout="wide"
)

st.title("🚗 주차장 정보 제공 시스템")

# -----------------------------
# CSV 읽기 함수
# -----------------------------
def load_csv(file):
    encodings = [
        "utf-8",
        "utf-8-sig",
        "cp949",
        "euc-kr",
        "latin1"
    ]

    for enc in encodings:
        try:
            file.seek(0)
            df = pd.read_csv(file, encoding=enc)
            st.success(f"파일을 '{enc}' 인코딩으로 읽었습니다.")
            return df
        except Exception:
            continue

    return None


# -----------------------------
# CSV 업로드
# -----------------------------
uploaded = st.file_uploader(
    "CSV 파일 업로드",
    type=["csv"]
)

if uploaded is None:
    st.info("CSV 파일을 업로드하세요.")
    st.stop()

df = load_csv(uploaded)

if df is None:
    st.error("CSV 파일을 읽을 수 없습니다.")
    st.stop()

# -----------------------------
# 컬럼 확인
# -----------------------------
required = [
    "name",
    "address",
    "lat",
    "lon",
    "fee"
]

missing = [c for c in required if c not in df.columns]

if missing:
    st.error(f"다음 컬럼이 없습니다.\n\n{missing}")
    st.stop()

# -----------------------------
# 숫자형 변환
# -----------------------------
df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
df["fee"] = pd.to_numeric(df["fee"], errors="coerce")

df = df.dropna(subset=["lat", "lon"])

# -----------------------------
# 데이터 표시
# -----------------------------
st.subheader("주차장 데이터")

st.dataframe(df, use_container_width=True)

# -----------------------------
# 주소 검색
# -----------------------------
st.subheader("주소 검색")

keyword = st.text_input("주소 입력")

search_df = df

if keyword:

    search_df = df[
        df["address"].str.contains(
            keyword,
            case=False,
            na=False
        )
    ]

    if len(search_df) == 0:
        st.warning("검색 결과가 없습니다.")
    else:

        st.success(f"{len(search_df)}개의 주차장을 찾았습니다.")

        for _, row in search_df.iterrows():

            with st.container():

                col1, col2 = st.columns([3,1])

                with col1:

                    st.write(f"**{row['name']}**")

                    st.write(row["address"])

                with col2:

                    st.metric(
                        "주차요금",
                        f"{int(row['fee']):,}원"
                    )

# -----------------------------
# 지도
# -----------------------------
st.subheader("주차장 지도")

center_lat = search_df["lat"].mean()
center_lon = search_df["lon"].mean()

m = folium.Map(
    location=[center_lat, center_lon],
    zoom_start=12
)

for _, row in search_df.iterrows():

    popup_html = f"""
    <h4>{row['name']}</h4>
    <b>주소</b><br>
    {row['address']}<br><br>

    <b>주차요금</b><br>
    {int(row['fee']):,}원
    """

    tooltip_html = f"""
    {row['address']}<br>
    {int(row['fee']):,}원
    """

    folium.Marker(
        location=[
            row["lat"],
            row["lon"]
        ],
        popup=folium.Popup(
            popup_html,
            max_width=300
        ),
        tooltip=tooltip_html,
        icon=folium.Icon(
            color="blue",
            icon="info-sign"
        )
    ).add_to(m)

st_folium(
    m,
    width=1200,
    height=650
)
