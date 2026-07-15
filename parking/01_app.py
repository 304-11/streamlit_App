import streamlit as st
import pandas as pd
import folium
from streamlit_folium import st_folium

st.set_page_config(
    page_title="주차장 정보 제공 시스템",
    layout="wide"
)

st.title("🚗 주차장 정보 제공 시스템")

uploaded = st.file_uploader(
    "CSV 파일 업로드",
    type=["csv"]
)

if uploaded is not None:

    df = pd.read_csv(uploaded)

    st.success("CSV 업로드 완료!")

    st.subheader("주차장 목록")

    st.dataframe(df,use_container_width=True)

    st.divider()

    keyword = st.text_input("주소 검색")

    if keyword:

        result = df[df["address"].str.contains(keyword,case=False,na=False)]

        if len(result)>0:

            st.success("검색 결과")

            st.dataframe(result)

            for _,row in result.iterrows():

                st.metric(
                    label=row["name"],
                    value=f"{row['fee']} 원"
                )

        else:

            st.error("검색 결과가 없습니다.")

    st.divider()

    st.subheader("주차장 지도")

    center_lat=df["lat"].mean()
    center_lon=df["lon"].mean()

    m=folium.Map(
        location=[center_lat,center_lon],
        zoom_start=12
    )

    for _,row in df.iterrows():

        popup=f"""
        <b>{row['name']}</b><br>
        주소 : {row['address']}<br>
        주차요금 : {row['fee']}원
        """

        tooltip=f"""
        {row['address']}<br>
        {row['fee']}원
        """

        folium.Marker(
            [row["lat"],row["lon"]],
            popup=popup,
            tooltip=tooltip,
            icon=folium.Icon(color="blue",icon="info-sign")
        ).add_to(m)

    st_folium(
        m,
        width=1200,
        height=650
    )

else:

    st.info("CSV 파일을 업로드하세요.")
