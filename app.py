import streamlit as st
import pandas as pd
import random
import requests  # 무료 날씨 API 호출용
import os
import json

# -----------------------------
# 기본 설정
# -----------------------------
st.set_page_config(page_title="점심 뭐 먹지?", page_icon="🍱")
st.title("오늘 점심 뭐 먹지? 🍱")

# 테헤란로 231 근방 좌표 (대략값)
CENTER_LAT = 37.5032
CENTER_LON = 127.0415

RATINGS_FILE = "ratings.json"  # 평점 저장 파일 경로

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
        st.error(f"날씨 정보를 가져오는 데 실패했습니다: {e}")
        return None


# -----------------------------
# 평점 데이터 로드/저장 함수
# -----------------------------
def load_ratings() -> dict:
    """ratings.json 파일에서 평점 데이터 로드"""
    if not os.path.exists(RATINGS_FILE):
        return {}
    try:
        with open(RATINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_ratings(ratings: dict):
    """평점 데이터를 ratings.json에 저장"""
    with open(RATINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(ratings, f, ensure_ascii=False, indent=2)


def get_average_rating(place_name: str, ratings: dict) -> float | None:
    """특정 가게의 평균 평점 계산"""
    info = ratings.get(place_name)
    if not info:
        return None
    count = info.get("count", 0)
    total = info.get("sum", 0)
    if count <= 0:
        return None
    return round(total / count, 1)


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
    base_df = pd.DataFrame()

# 세션 상태에 DF 저장 (추가/수정 반영용)
if "df" not in st.session_state:
    st.session_state.df = base_df.copy()

df = st.session_state.df

# -----------------------------
# 2-2. 평점 남기기 기능
# -----------------------------
ratings = load_ratings()

with st.expander("⭐ 맛집 평점 남기기", expanded=False):
    if df.empty:
        st.info("먼저 맛집 데이터를 추가해 주세요.")
    else:
        place_options = df["place_name"].dropna().unique().tolist()
        selected_place = st.selectbox("가게 선택", place_options)

        # 기본 평점 5.0, 0.1 단위로 조정 가능
        score = st.slider("평점 (0.0 ~ 5.0점)", 0.0, 5.0, 5.0, 0.1)

        with st.form("rating_form"):
            st.write(f"선택한 가게: **{selected_place}**")
            st.write(f"이번에 줄 점수: **{score:.1f}점**")
            submitted_rating = st.form_submit_button("평점 등록하기 ✅")

        if submitted_rating:
            # 기존 데이터 불러와서 갱신
            ratings = load_ratings()
            info = ratings.get(selected_place, {"sum": 0.0, "count": 0})
            info["sum"] = info.get("sum", 0.0) + float(score)
            info["count"] = info.get("count", 0) + 1
            ratings[selected_place] = info
            save_ratings(ratings)

            avg = get_average_rating(selected_place, ratings)
            st.success(f"'{selected_place}' 평점이 등록되었습니다. 현재 평균 평점: {avg:.1f} / 5.0")

st.divider()

# -----------------------------
# 3. "랜덤으로 하나만 골라줘!" 버튼
# -----------------------------
if st.button("랜덤으로 하나만 골라줘! 🎲"):
    if df.empty:
        st.warning("맛집 데이터가 비어있습니다. restaurants.json 파일 또는 추가 기능을 확인하세요.")
    else:
        random_choice = df.sample(1).iloc[0]
        place_name = random_choice.get("place_name", "이름 없음")

        st.balloons()
        st.success(f"오늘은 **{random_choice.get('category_name', '알 수 없음')}** 어때요?")

        st.header(f"추천 맛집: **{place_name}**")

        # 추천된 가게의 현재 평균 평점 표시
        avg_rating = get_average_rating(place_name, ratings)
        if avg_rating is not None:
            st.write(f"현재 평균 평점: ⭐ **{avg_rating:.1f} / 5.0**")

        if 'distance' in random_choice and pd.notna(random_choice['distance']):
            st.subheader(f"내 위치(테헤란로 231)에서 **{random_choice['distance']}m** 떨어져 있어요!")

        # 카카오맵 링크가 있으면 같이 보여주기
        if 'place_url' in random_choice and random_choice['place_url']:
            st.markdown(f"[카카오맵에서 위치 보기]({random_choice['place_url']})")

st.divider()  # 구분선

# -----------------------------
# 4. 전체 맛집 목록 보여주기 (평점 포함) + 접기/펼치기 + 삭제 기능
# -----------------------------
with st.expander("📋 1.5km 이내 전체 맛집/카페 리스트", expanded=False):
    st.write("--- 1.5km 이내 전체 맛집/카페 리스트 ---")

    # 평점을 컬럼으로 붙이기
    ratings = load_ratings()  # 최신 값 다시 로드
    df_with_rating = df.copy()
    if not df_with_rating.empty:
        df_with_rating["rating"] = df_with_rating["place_name"].apply(
            lambda name: get_average_rating(name, ratings)
        )

    try:
        if not df_with_rating.empty:
            # place_name 옆에 rating이 오도록 컬럼 순서 지정
            display_columns = [
                "place_name",
                "rating",
                "category_name",
                "distance",
                "road_address_name",
                "phone",
            ]
            available_columns = [col for col in display_columns if col in df_with_rating.columns]
            if available_columns:
                st.dataframe(df_with_rating[available_columns])
            else:
                st.dataframe(df_with_rating)
        else:
            st.info("현재 등록된 맛집/카페가 없습니다.")
    except Exception as e:
        st.error("데이터프레임 표시에 실패했습니다.")
        st.dataframe(df_with_rating)  # 실패 시 원본이라도 표시

    st.markdown("---")

    # 🗑 리스트에서 가게 삭제 기능
    if not df_with_rating.empty:
        st.subheader("가게 삭제하기 🗑️")

        delete_options = df_with_rating["place_name"].dropna().unique().tolist()
        delete_choice = st.selectbox(
            "삭제할 가게를 선택하세요",
            ["선택 안 함"] + delete_options,
            key="delete_place_select",
        )

        if st.button("선택한 가게 삭제하기 🗑️"):
            if delete_choice == "선택 안 함":
                st.warning("삭제할 가게를 먼저 선택해 주세요.")
            else:
                # session_state.df에서 해당 가게 삭제
                st.session_state.df = st.session_state.df[
                    st.session_state.df["place_name"] != delete_choice
                ].reset_index(drop=True)

                # 파일에도 반영
                try:
                    st.session_state.df.to_json(
                        "restaurants.json",
                        force_ascii=False,
                        orient="records",
                        indent=2,
                    )
                    st.success(f"'{delete_choice}' 가(이) 목록에서 삭제되었습니다. (파일에도 저장 완료)")
                except Exception as e:
                    st.warning(f"메모리에서는 삭제했지만 파일 저장에 실패했습니다: {e}")

                # 화면 갱신
                st.experimental_rerun()
    else:
        st.caption("삭제할 가게가 없습니다.")

st.divider()

# -----------------------------
# 5. 새 음식점 추가하기 기능
# (리스트 아래에 위치 + 카테고리 드롭다운 & "음식점 > 카테고리" 저장)
# -----------------------------
with st.expander("🍽 새 맛집/카페 추가하기", expanded=False):
    st.write("임의로 음식점을 추가하면 위 전체 리스트와 추천에도 바로 반영됩니다.")

    with st.form("add_place_form"):
        col_left, col_right = st.columns(2)

        with col_left:
            place_name = st.text_input("가게 이름", placeholder="예) 센터필드 김밥천국")

            # 카테고리 드롭다운
            category_options = ["한식", "양식", "중식", "일식", "분식", "간식"]
            selected_category = st.selectbox("카테고리 선택", category_options)

            distance = st.number_input(
                "거리 (m)",
                min_value=0,
                step=10,
                help="테헤란로 231 기준 대략 거리 (미터)",
            )

        with col_right:
            road_address_name = st.text_input("도로명 주소", placeholder="예) 서울 강남구 테헤란로 231")
            phone = st.text_input("전화번호", placeholder="예) 02-123-4567")
            place_url = st.text_input("카카오맵/웹 링크", placeholder="지도 링크가 있으면 넣어주세요")

        submitted = st.form_submit_button("추가하기 ✅")

    if submitted:
        if not place_name:
            st.warning("가게 이름은 필수입니다.")
        else:
            # 저장되는 category_name 형식: "음식점 > 선택된 카테고리"
            category_name = f"음식점 > {selected_category}" if selected_category else None

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
