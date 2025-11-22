import streamlit as st
import pandas as pd
import random
import requests  # 🔸 무료 날씨 API 호출용

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(page_title="점심 뭐 먹지?", page_icon="🍱")
st.title("오늘 점심 뭐 먹지? 🍱")

# 테헤란로 231 근방 좌표 (대략값)
CENTER_LAT = 37.5032
CENTER_LON = 127.0415

# -----------------------------
# 무료 날씨 API (Open-Meteo) 호출 함수
# -----------------------------
def get_current_weather(lat: float, lon: float):
    """
    Open-Meteo 무료 날씨 API
    - 엔드포인트: https://api.open-meteo.com/v1/forecast
    - 파라미터: latitude, longitude, current_weather=true
    - 키/회원가입 불필요, 비상업용 무료 :contentReference[oaicite:2]{index=2}
    """
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "current_weather": True,
        "timezone": "Asia/Seoul",
    }

    try:
        resp = requests.get(url, params=params, timeout=5)
        resp.raise_for_status()
        data = resp.json()

        current = data.get("current_weather")
        if not current:
            return None

        return {
            "temp": current.get("temperature"),   # ℃
            "windspeed": current.get("windspeed"),  # m/s
            "winddirection": current.get("winddirection"),
            "time": current.get("time"),
        }

    except Exception as e:
        # streamlit 화면에만 에러 표시
        st.error(f"날씨 정보를 가져오는 데 실패했습니다: {e}")
        return None


# -----------------------------
# 1. 상단에 테헤란로 231 현재 기온 표시
# -----------------------------
with st.container():
    st.subheader("📍 테헤란로 231 현재 날씨")

    weather = get_current_weather(CENTER_LAT, CENTER_LON)

    if weather:
        col1, col2 = st.columns(2)

        with col1:
            if weather["temp"] is not None:
                st.metric("현재 기온", f"{weather['temp']:.1f} ℃")
            else:
                st.metric("현재 기온", "정보 없음")

        with col2:
            if weather["windspeed"] is not None:
                st.write(f"풍속: **{weather['windspeed']} m/s**")
            if weather["winddirection"] is not None:
                st.write(f"풍향: **{weather['winddirection']}°**")
            if weather["time"]:
                st.caption(f"관측 시각 (API 기준): {weather['time']}")
    else:
        st.info("현재 날씨 정보를 가져올 수 없습니다. 잠시 후 다시 시도해 주세요.")

st.divider()  # 구분선

# -----------------------------
# 2. JSON 데이터 읽어오기 (기존 로직)
#    (GitHub 저장소에 함께 올린 'restaurants.json' 파일을 읽음)
# -----------------------------
try:
    df = pd.read_json("restaurants.json")
except Exception as e:
    st.error(
        f"맛집 데이터(restaurants.json)를 불러오는 데 실패했습니다. "
        f"파일이 정확히 있는지 확인하세요. (오류: {e})"
    )
    st.stop()

# -----------------------------
# 3. "랜덤으로 하나만 골라줘!" 버튼 (기존 점심 추천 로직)
# -----------------------------
if st.button("랜덤으로 하나만 골라줘! 🎲"):
    if df.empty:
        st.warning("맛집 데이터가 비어있습니다. restaurants.json 파일을 확인하세요.")
    else:
        random_choice = df.sample(1).iloc[0]

        st.balloons()
        st.success(f"오늘은 **{random_choice['category_name']}** 어때요?")

        st.header(f"추천 맛집: **{random_choice['place_name']}**")
        if 'distance' in random_choice and pd.notna(random_choice['distance']):
            st.subheader(f"내 위치(테헤란로 231)에서 **{random_choice['distance']}m** 떨어져 있어요!")

        # 카카오맵 링크가 있으면 같이 보여주기
        if 'place_url' in random_choice and random_choice['place_url']:
            st.markdown(f"[카카오맵에서 위치 보기]({random_choice['place_url']})")

st.divider()  # 구분선

# -----------------------------
# 4. 전체 맛집 목록 보여주기 (컬럼 정리)
# -----------------------------
st.write("--- 1.5km 이내 전체 맛집/카페 리스트 ---")
try:
    # 보여줄 컬럼만 선택
    display_columns = ['place_name', 'category_name', 'distance', 'road_address_name', 'phone']
    # 실제 df에 있는 컬럼만 필터링
    available_columns = [col for col in display_columns if col in df.columns]
    st.dataframe(df[available_columns])
except Exception as e:
    st.error("데이터프레임 표시에 실패했습니다.")
    st.dataframe(df)  # 실패 시 원본이라도 표시
