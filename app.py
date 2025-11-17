import streamlit as st
import pandas as pd
import random

# 1. 제목 설정
st.set_page_config(page_title="점심 뭐 먹지?", page_icon="🍱")
st.title("오늘 점심 뭐 먹지? 🍱 (정식 Ver.)")

# 2. JSON 데이터 읽어오기
#    (GitHub 저장소에 함께 올린 'restaurants.json' 파일을 읽음)
try:
    df = pd.read_json("restaurants.json")
except Exception as e:
    st.error(f"맛집 데이터(restaurants.json)를 불러오는 데 실패했습니다. 파일이 정확히 있는지 확인하세요. (오류: {e})")
    st.stop()

# 3. "오늘의 추천" 버튼 만들기
if st.button("랜덤으로 하나만 골라줘! 🎲"):
    # 데이터가 비어있는지 확인
    if df.empty:
        st.warning("맛집 데이터가 비어있습니다. restaurants.json 파일을 확인하세요.")
    else:
        # 데이터에서 랜덤으로 1줄 뽑기
        random_choice = df.sample(1).iloc[0]
        
        st.balloons() # 풍선 효과!
        st.success(f"오늘은 **{random_choice['category_name']}** 어때요?")
        
        # 'place_name'과 'distance' 컬럼을 사용
        st.header(f"추천 맛집: **{random_choice['place_name']}**")
        st.subheader(f"내 위치(테헤란로 231)에서 **{random_choice['distance']}m** 떨어져 있어요!")
        
        # 카카오맵 링크 (place_url 컬럼이 있다면 사용)
        if 'place_url' in random_choice and random_choice['place_url']:
            st.markdown(f"[카카오맵에서 위치 보기]({random_choice['place_url']})")

st.divider() # 구분선

# 4. 전체 맛집 목록 보여주기 (컬럼 정리)
st.write("--- 1km 이내 전체 맛집 리스트 ---")
try:
    # 보여줄 컬럼만 선택
    display_columns = ['place_name', 'category_name', 'distance', 'road_address_name', 'phone']
    # 실제 df에 있는 컬럼만 필터링
    available_columns = [col for col in display_columns if col in df.columns]
    st.dataframe(df[available_columns])
except Exception as e:
    st.error("데이터프레임 표시에 실패했습니다.")
    st.dataframe(df) # 실패 시 원본이라도 표시
