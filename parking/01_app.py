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


# ----------------------------
# CSV 읽기
# ----------------------------
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
            st.success(f"파일 인코딩 : {enc}")
            return df
        except Exception:
            continue

    return None


uploaded = st.file_uploader(
    "CSV 업로드",
    type=["csv"]
)

if uploaded is None:
    st.info("CSV 파일을 업로드하세요.")
    st.stop()

df = load_csv(uploaded)

if df is None:
    st.error("CSV를 읽을 수 없습니다.")
    st.stop()

# -----------------------------------
# 컬럼명 자동 변경
# -----------------------------------
column_map = {}

for col in df.columns:

    c = col.strip()

    # 이름
    if c in ["name", "주차장명", "주차장명칭", "명칭"]:
        column_map[col] = "name"

    # 주소
    elif c in [
        "address",
        "주소",
        "도로명주소",
        "소재지도로명주소",
        "소재지지번주소"
    ]:
        column_map[col] = "address"

    # 위도
    elif c in [
        "lat",
        "위도",
        "LAT",
        "Latitude"
    ]:
        column_map[col] = "lat"

    # 경도
    elif c in [
        "lon",
        "lng",
        "경도",
        "LON",
        "Longitude"
    ]:
        column_map[col] = "lon"

    # 요금
    elif c in [
        "fee",
        "주차요금",
        "기본주차요금",
        "요금",
        "1시간요금"
    ]:
        column_map[col] = "fee"

df.rename(columns=column_map, inplace=True)

# 현재 컬럼 확인
st.write("인식된 컬럼")
st.write(df.columns.tolist())

required = ["name", "address", "lat", "lon", "fee"]

missing = [c for c in required if c not in df.columns]

if missing:
    st.error(f"필수 컬럼이 없습니다 : {missing}")
    st.stop()

# ----------------------------
# 데이터 타입 변환
# ----------------------------
df["lat"] = pd.to_numeric(df["lat"], errors="coerce")
df["lon"] = pd.to_numeric(df["lon"], errors="coerce")
df["fee"] = pd.to_numeric(df["fee"], errors="coerce")

df = df.dropna(subset=["lat", "lon"])

# ----------------------------
# 데이터 보기
# ----------------------------
st.subheader("주차장 목록")

st.dataframe(df, use_container_width=True)

# ----------------------------
# 주소 검색
# ----------------------------
st.subheader("주소 검색")

keyword = st.text_input("주소 입력")

result_df = df

if keyword:

    result_df = df[
        df["address"].astype(str).str.contains(
            keyword,
            case=False,
            na=False
        )
    ]

    if result_df.empty:

        st.warning("검색 결과가 없습니다.")

    else:

        st.success(f"{len(result_df)}개의 결과")

        for _, row in result_df.iterrows():

            st.markdown(f"### {row['name']}")
            st.write(row["address"])
            st.metric("주차요금", f"{int(row['fee']):,}원")

# ----------------------------
# 지도
# ----------------------------
st.subheader("주차장 지도")

center = [
    result_df["lat"].mean(),
    result_df["lon"].mean()
]

m = folium.Map(
    location=center,
    zoom_start=12
)

for _, row in result_df.iterrows():

    tooltip = f"""
    {row['address']}<br>
    {int(row['fee']):,}원
    """

    popup = f"""
    <h4>{row['name']}</h4>
    <hr>
    <b>주소</b><br>
    {row['address']}<br><br>

    <b>주차요금</b><br>
    {int(row['fee']):,}원
    """

    folium.Marker(
        [row["lat"], row["lon"]],
        tooltip=tooltip,
        popup=popup,
        icon=folium.Icon(
            color="blue",
            icon="info-sign"
        )
    ).add_to(m)

st_folium(
    m,
    width=1200,
    height=700
)
