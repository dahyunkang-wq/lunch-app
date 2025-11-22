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
    - 키/회원가입 불필요, 비상업용 무료
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
# 2. JSON 데이터 읽어오기
# -----------------------------
try:
    base_df = pd.read_json("restaurants.json")
except Exception as e:
    st.error(
        f"맛집 데이터(restaurants.json)를 불러오는 데 실패했습니다. "
        f"파일이 정확히 있는지 확인하세요. (오류: {e})"
    )
    base_df = pd.DataFrame()  # 그래도 앱은 죽지 않게 빈 DF로 시작

# 세션 상태에 DF 저장 (추가/수정 반영용)
if "df" not in st.session_state:
    st.session_state.df = base_df.copy()

df = st.session_state.df

# -----------------------------
# 2-1. 새 음식점 추가하기 기능
# -----------------------------
with st.expander("🍽 새 맛집/카페 추가하기", expanded=False):
    st.write("임의로 음식점을 추가하면 아래 전체 리스트와 추천에도 바로 반영됩니다.")

    with st.form("add_place_form"):
        col_left, col_right = st.columns(2)

        with col_left:
            place_name = st.text_input("가게 이름", placeholder="예) 센터필드 김밥천국")
            category_name = st.text_input("카테고리 이름", placeholder="예) 한식, 카페 등")
            distance = st.number_input("거리 (m)", min_value=0, step=10, help="테헤란로 231 기준 대략 거리 (미터)")
        with col_right:
            road_address_name = st.text_input("도로명 주소", placeholder="예) 서울 강남구 테헤란로 231")
            phone = st.text_input("전화번호", placeholder="예) 02-123-4567")
            place_url = st.text_input("카카오맵/웹 링크", placeholder="지도 링크가 있으면 넣어주세요")

        submitted = st.form_submit_button("추가하기 ✅")

    if submitted:
        if not place_name:
            st.warning("가게 이름은 필수입니다.")
        else:
            new_row = {
                "place_name": place_name,
                "category_name": category_name,
                "distance": int(distance) if distance is not None else None,
                "road_address_name": road_address_name,
                "phone": phone,
                "place_url": place_url,
            }

            # 세션 DF에 추가
            st.session_state.df = pd.concat(
                [st.session_state.df, pd.DataFrame([new_row])],
                ignore_index=True,
            )
            df = st.session_state.df  # 로컬 변수도 업데이트

            # 파일에도 저장 (가능한 환경일 때)
            try:
                st.session_state.df.to_json(
                    "restaurants.json",
                    force_ascii=False,
                    orient="records",
                    indent=2,
                )
                st.success(f"'{place_name}' 이(가) 목록에 추가되었습니다. (파일에도 저장 완료)")
            except Exception as e:
                st.warning(f"메모리에는 추가되었지만 파일 저장에 실패했습니다: {e}")

st.divider()

# -----------------------------
# 3. "랜덤으로 하나만 골라줘!" 버튼 (기존 점심 추천 로직)
# -----------------------------
if st.button("랜덤으로 하나만 골라줘! 🎲"):
    if df.empty:
        st.warning("맛집 데이터가 비어있습니다. restaurants.json 파일 또는 추가 기능을 확인하세요.")
    else:
        random_choice = df.sample(1).iloc[0]

        st.balloons()
        st.success(f"오늘은 **{random_choice.get('category_name', '알 수 없음')}** 어때요?")

        st.header(f"추천 맛집: **{random_choice.get('place_name', '이름 없음')}**")
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
    display_columns = ['place_name', 'category_name', 'distance', 'road_address_name', 'phone']
    available_columns = [col for col in display_columns if col in df.columns]
    if available_columns:
        st.dataframe(df[available_columns])
    else:
        st.dataframe(df)
except Exception as e:
    st.error("데이터프레임 표시에 실패했습니다.")
    st.dataframe(df)  # 실패 시 원본이라도 표시
