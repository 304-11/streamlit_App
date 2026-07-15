import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium


# -------------------------
# 기본 설정
# -------------------------

st.set_page_config(
    page_title="서울시 공영주차장 안내",
    page_icon="🚗",
    layout="wide"
)


st.title("🚗 서울시 공영주차장 정보 안내")


# -------------------------
# CSV 읽기
# -------------------------

def read_csv_auto(file):

    encodings = [
        "utf-8",
        "utf-8-sig",
        "cp949",
        "euc-kr"
    ]

    for enc in encodings:

        try:
            file.seek(0)

            df = pd.read_csv(
                file,
                encoding=enc
            )

            st.success(
                f"CSV 인코딩 : {enc}"
            )

            return df


        except Exception:
            pass


    return None



# -------------------------
# 컬럼 자동 찾기
# -------------------------

def find_column(df, keywords):

    for col in df.columns:

        col_name = str(col)

        for key in keywords:

            if key.lower() in col_name.lower():

                return col


    return None



# -------------------------
# CSV 업로드
# -------------------------

uploaded_file = st.file_uploader(
    "서울시 공영주차장 CSV 업로드",
    type=["csv"]
)


if uploaded_file is None:

    st.info(
        "서울시 공영주차장 CSV 파일을 업로드하세요."
    )

    st.stop()



df = read_csv_auto(uploaded_file)


if df is None:

    st.error(
        "CSV 파일을 읽지 못했습니다."
    )

    st.stop()



# -------------------------
# 컬럼 자동 매칭
# -------------------------

name_col = find_column(
    df,
    [
        "주차장명",
        "주차장명칭",
        "시설명",
        "name"
    ]
)



address_col = find_column(
    df,
    [
        "주소",
        "도로명",
        "소재지",
        "address"
    ]
)



lat_col = find_column(
    df,
    [
        "위도",
        "lat",
        "latitude"
    ]
)



lon_col = find_column(
    df,
    [
        "경도",
        "lon",
        "lng",
        "longitude"
    ]
)



fee_col = find_column(
    df,
    [
        "요금",
        "주차요금",
        "기본요금",
        "기본주차요금",
        "최초",
        "30분",
        "10분"
    ]
)



# -------------------------
# 컬럼 변환
# -------------------------

mapping = {}


if name_col:
    mapping[name_col] = "name"


if address_col:
    mapping[address_col] = "address"


if lat_col:
    mapping[lat_col] = "lat"


if lon_col:
    mapping[lon_col] = "lon"


if fee_col:
    mapping[fee_col] = "fee"



df.rename(
    columns=mapping,
    inplace=True
)



# -------------------------
# 필수 데이터 확인
# -------------------------

required = [
    "name",
    "address",
    "lat",
    "lon"
]


missing = [
    x for x in required
    if x not in df.columns
]


if missing:

    st.error(
        f"필수 컬럼을 찾지 못했습니다 : {missing}"
    )

    st.write(
        "현재 CSV 컬럼명"
    )

    st.write(
        df.columns.tolist()
    )

    st.stop()



# 요금 없으면 처리

if "fee" not in df.columns:

    df["fee"] = "요금정보 없음"



# -------------------------
# 숫자 변환
# -------------------------

df["lat"] = pd.to_numeric(
    df["lat"],
    errors="coerce"
)


df["lon"] = pd.to_numeric(
    df["lon"],
    errors="coerce"
)


df = df.dropna(
    subset=[
        "lat",
        "lon"
    ]
)



# -------------------------
# 데이터 확인
# -------------------------

st.subheader(
    "📋 주차장 데이터"
)


st.dataframe(
    df[
        [
            "name",
            "address",
            "fee"
        ]
    ],
    use_container_width=True
)



# -------------------------
# 주소 검색
# -------------------------

st.subheader(
    "🔍 주소 검색"
)


keyword = st.text_input(
    "검색할 주소 입력"
)



result = df.copy()



if keyword:

    result = df[
        df["address"]
        .astype(str)
        .str.contains(
            keyword,
            case=False,
            na=False
        )
    ]



if len(result) > 0:


    st.success(
        f"{len(result)}개 주차장 검색"
    )


    for _, row in result.iterrows():

        st.write(
            "### 🚗 "
            + str(row["name"])
        )


        st.write(
            "📍 "
            + str(row["address"])
        )


        st.write(
            "💰 요금 : "
            + str(row["fee"])
        )


        st.divider()



# -------------------------
# 지도
# -------------------------

st.subheader(
    "🗺 주차장 지도"
)



center = [

    result["lat"].mean(),

    result["lon"].mean()

]



map = folium.Map(

    location=center,

    zoom_start=12

)



for _, row in result.iterrows():


    popup = f"""

    <b>{row['name']}</b><br><br>

    주소 : {row['address']}<br>

    주차요금 : {row['fee']}

    """



    tooltip = f"""

    {row['address']}<br>

    {row['fee']}

    """



    folium.Marker(

        location=[

            row["lat"],

            row["lon"]

        ],

        popup=folium.Popup(

            popup,

            max_width=300

        ),

        tooltip=tooltip,

        icon=folium.Icon(

            color="blue",

            icon="car"

        )

    ).add_to(map)



st_folium(

    map,

    width=1200,

    height=700

)
