import streamlit as st
import pandas as pd
import random
from streamlit_gsheets import GSheetsConnection  # 구글 시트 연결 도구

# 1. 페이지 설정
st.set_page_config(page_title="고2 영단어 마스터", page_icon="📝")
st.title("☁️ 영단어 테스트")

# 2. 구글 스프레드시트 연결 (여기에 본인 시트 URL을 넣으세요)
# 중요: 시트 공유 설정이 '링크가 있는 모든 사용자 - 뷰어'로 되어 있어야 합니다.
SHEET_URL = "https://docs.google.com/spreadsheets/d/1emiGs_8fHsEGx4Pr9hRwwfkE-issnQ_L8Mrt3SfcB4E/edit?usp=sharing"

@st.cache_data(ttl=600) # 10분마다 데이터를 새로고침함
def load_data_from_gsheet():
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # 구글 시트의 첫 번째 워크시트를 읽어옵니다.
        df = conn.read(spreadsheet=SHEET_URL)
        return df
    except Exception as e:
        st.error(f"구글 시트를 불러오지 못했습니다. URL과 공유 설정을 확인하세요: {e}")
        return None

# 3. 데이터 로드 및 퀴즈 준비
if 'df_quiz' not in st.session_state:
    raw_df = load_data_from_gsheet()
    if raw_df is not None:
        # B. 랜덤 섞기 기능 포함
        st.session_state.df_quiz = raw_df.sample(frac=1).reset_index(drop=True)

# 4. 세션 상태 초기화 (기존 로직과 동일)
if 'current_index' not in st.session_state:
    st.session_state.current_index = 0
if 'score' not in st.session_state:
    st.session_state.score = 0
if 'quiz_finished' not in st.session_state:
    st.session_state.quiz_finished = False
if 'wrong_answers' not in st.session_state:
    st.session_state.wrong_answers = []
if 'show_hint' not in st.session_state:
    st.session_state.show_hint = False

# 5. 퀴즈 실행 로직 (데이터가 로드된 경우에만 실행)
if 'df_quiz' in st.session_state and not st.session_state.quiz_finished:
    df = st.session_state.df_quiz
    correct_word = df.iloc[st.session_state.current_index]['word']
    problem_meaning = df.iloc[st.session_state.current_index]['meaning']

    # 진행바
    st.progress((st.session_state.current_index) / len(df))
    st.write(f"문제 {st.session_state.current_index + 1} / {len(df)}")

    st.info(f"### 뜻: **{problem_meaning}**")

    # A. 힌트 버튼
    if st.button("힌트 보기 💡"):
        st.session_state.show_hint = True

    if st.session_state.show_hint:
        hint = correct_word[0] + " _ " * (len(correct_word) - 1)
        st.caption(f"힌트: {hint} ({len(correct_word)}글자)")

    user_answer = st.text_input("영어 단어를 입력하세요:", key=f"ans_{st.session_state.current_index}")

    if st.button("정답 확인"):
        if user_answer.strip().lower() == correct_word.strip().lower():
            st.success("정답입니다! 🎉")
            st.session_state.score += 1
        else:
            st.error(f"오답입니다. 정답은 '{correct_word}'")
            st.session_state.wrong_answers.append({
                "뜻": problem_meaning, "정답": correct_word, "내답": user_answer
            })

        st.session_state.show_hint = False
        if st.session_state.current_index < len(df) - 1:
            st.button("다음 문제로 ▶️", on_click=lambda: setattr(st.session_state, 'current_index', st.session_state.current_index + 1))
        else:
            if st.button("최종 결과 확인 🏁"):
                st.session_state.quiz_finished = True
                st.rerun()

# 6. 결과 화면
elif st.session_state.get('quiz_finished'):
    st.balloons()
    st.header("테스트 결과 🎓")
    st.metric("내 점수", f"{st.session_state.score} / {len(st.session_state.df_quiz)}")

    if st.session_state.wrong_answers:
        st.warning("📖 틀린 단어 복습하기")
        st.table(pd.DataFrame(st.session_state.wrong_answers))

    if st.button("새로운 순서로 다시 시작"):
        # 전체 세션 초기화
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()