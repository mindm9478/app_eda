import streamlit as st
import pyrebase
import time
import io
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

# ---------------------
# Firebase 설정
# ---------------------
firebase_config = {
    "apiKey": "AIzaSyCswFmrOGU3FyLYxwbNPTp7hvQxLfTPIZw",
    "authDomain": "sw-projects-49798.firebaseapp.com",
    "databaseURL": "https://sw-projects-49798-default-rtdb.firebaseio.com",
    "projectId": "sw-projects-49798",
    "storageBucket": "sw-projects-49798.firebasestorage.app",
    "messagingSenderId": "812186368395",
    "appId": "1:812186368395:web:be2f7291ce54396209d78e"
}

firebase = pyrebase.initialize_app(firebase_config)
auth = firebase.auth()
firestore = firebase.database()
storage = firebase.storage()

# ---------------------
# 세션 상태 초기화
# ---------------------
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.user_email = ""
    st.session_state.id_token = ""
    st.session_state.user_name = ""
    st.session_state.user_gender = "선택 안함"
    st.session_state.user_phone = ""
    st.session_state.profile_image_url = ""

# ---------------------
# 홈 페이지 클래스
# ---------------------
class Home:
    def __init__(self, login_page, register_page, findpw_page):
        st.title("🏠 Population EDA App")
        if st.session_state.get("logged_in"):
            st.success(f"{st.session_state.get('user_email')}님 환영합니다.")

# ---------------------
# 로그인 페이지 클래스
# ---------------------
class Login:
    def __init__(self):
        st.title("🔐 로그인")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        if st.button("로그인"):
            try:
                user = auth.sign_in_with_email_and_password(email, password)
                st.session_state.logged_in = True
                st.session_state.user_email = email
                st.session_state.id_token = user['idToken']

                user_info = firestore.child("users").child(email.replace(".", "_")).get().val()
                if user_info:
                    st.session_state.user_name = user_info.get("name", "")
                    st.session_state.user_gender = user_info.get("gender", "선택 안함")
                    st.session_state.user_phone = user_info.get("phone", "")
                    st.session_state.profile_image_url = user_info.get("profile_image_url", "")

                st.success("로그인 성공!")
                time.sleep(1)
                st.rerun()
            except Exception:
                st.error("로그인 실패")

# ---------------------
# 회원가입 페이지 클래스
# ---------------------
class Register:
    def __init__(self, login_page_url):
        st.title("📝 회원가입")
        email = st.text_input("이메일")
        password = st.text_input("비밀번호", type="password")
        name = st.text_input("성명")
        gender = st.selectbox("성별", ["선택 안함", "남성", "여성"])
        phone = st.text_input("휴대전화번호")

        if st.button("회원가입"):
            try:
                auth.create_user_with_email_and_password(email, password)
                firestore.child("users").child(email.replace(".", "_")).set({
                    "email": email,
                    "name": name,
                    "gender": gender,
                    "phone": phone,
                    "role": "user",
                    "profile_image_url": ""
                })
                st.success("회원가입 성공! 로그인 페이지로 이동합니다.")
                time.sleep(1)
                st.switch_page(login_page_url)
            except Exception:
                st.error("회원가입 실패")

# ---------------------
# 비밀번호 찾기 페이지 클래스
# ---------------------
class FindPassword:
    def __init__(self):
        st.title("🔎 비밀번호 찾기")
        email = st.text_input("이메일")
        if st.button("비밀번호 재설정 메일 전송"):
            try:
                auth.send_password_reset_email(email)
                st.success("비밀번호 재설정 이메일을 전송했습니다.")
                time.sleep(1)
                st.rerun()
            except:
                st.error("이메일 전송 실패")

# ---------------------
# 사용자 정보 수정 페이지 클래스
# ---------------------
class UserInfo:
    def __init__(self):
        st.title("👤 사용자 정보")

        email = st.session_state.get("user_email", "")
        new_email = st.text_input("이메일", value=email)
        name = st.text_input("성명", value=st.session_state.get("user_name", ""))
        gender = st.selectbox(
            "성별",
            ["선택 안함", "남성", "여성"],
            index=["선택 안함", "남성", "여성"].index(st.session_state.get("user_gender", "선택 안함"))
        )
        phone = st.text_input("휴대전화번호", value=st.session_state.get("user_phone", ""))

        uploaded_file = st.file_uploader("프로필 이미지 업로드", type=["jpg", "jpeg", "png"])
        if uploaded_file:
            file_path = f"profiles/{email.replace('.', '_')}.jpg"
            storage.child(file_path).put(uploaded_file, st.session_state.id_token)
            image_url = storage.child(file_path).get_url(st.session_state.id_token)
            st.session_state.profile_image_url = image_url
            st.image(image_url, width=150)
        elif st.session_state.get("profile_image_url"):
            st.image(st.session_state.profile_image_url, width=150)

        if st.button("수정"):
            st.session_state.user_email = new_email
            st.session_state.user_name = name
            st.session_state.user_gender = gender
            st.session_state.user_phone = phone

            firestore.child("users").child(new_email.replace(".", "_")).update({
                "email": new_email,
                "name": name,
                "gender": gender,
                "phone": phone,
                "profile_image_url": st.session_state.get("profile_image_url", "")
            })

            st.success("사용자 정보가 저장되었습니다.")
            time.sleep(1)
            st.rerun()

# ---------------------
# 로그아웃 페이지 클래스
# ---------------------
class Logout:
    def __init__(self):
        st.session_state.logged_in = False
        st.session_state.user_email = ""
        st.session_state.id_token = ""
        st.session_state.user_name = ""
        st.session_state.user_gender = "선택 안함"
        st.session_state.user_phone = ""
        st.session_state.profile_image_url = ""
        st.success("로그아웃 되었습니다.")
        time.sleep(1)
        st.rerun()

# ---------------------
# EDA 페이지 클래스
# ---------------------
class EDA:
    def __init__(self):
        st.title("📊 Population EDA")
        uploaded = st.file_uploader("데이터셋 업로드 (population_trends.csv)", type="csv")
        if not uploaded:
            st.info("population_trends.csv 파일을 업로드 해주세요.")
            return

        df = pd.read_csv(uploaded, parse_dates=['datetime'])

        tabs = st.tabs([
            "1. 목적 & 절차",
            "2. 데이터셋 설명",
            "3. 데이터 로드 & 품질 체크",
            "4. Datetime 특성 추출",
            "5. 시각화",
            "6. 상관관계 분석",
            "7. 이상치 제거",
            "8. 로그 변환"
        ])

        # 1. 목적 & 분석 절차
        with tabs[0]:
            st.header("🔭 목적 & 분석 절차")
            st.markdown("""

            **절차**:
            1. 결측치 및 중복 확인 
            2. 결측치/중복치 등 품질 체크  
            3. 지역별 인구 변화량 순위  
            4. 증감률 상위 지역 및 연도 도출  
            5. 누적영역그래프 등 적절한 시각화  
            """)

        # 2. 데이터셋 설명
        with tabs[1]:
            st.header("🔍 결측치 및 중복 확인")
            uploaded_file = st.file_uploader("CSV 파일 업로드", type="csv")

            if uploaded_file is not None:
                df = pd.read_csv(uploaded_file)

                st.subheader("원본 데이터 미리보기")
                st.dataframe(df.head())

                # '세종' 지역 필터링
                sejong_df = df[df['행정구역'].str.contains('세종', na=False)].copy()

                # '-'를 0으로 치환
                sejong_df.replace('-', 0, inplace=True)

                # 숫자형으로 변환할 열
                numeric_cols = ['인구', '출생아수(명)', '사망자수(명)']
                for col in numeric_cols:
                    sejong_df[col] = pd.to_numeric(sejong_df[col], errors='coerce').fillna(0).astype(int)

                st.subheader("세종 지역 전처리 데이터")
                st.dataframe(sejong_df.head())

                # describe 출력
                st.subheader("📈 요약 통계 (describe)")
                st.dataframe(sejong_df.describe())

                # info 출력
                st.subheader("🧾 데이터프레임 구조 (info)")

                # info는 문자열로 캡처해서 출력해야 함
                buffer = io.StringIO()
                sejong_df.info(buf=buffer)
                info_str = buffer.getvalue()
                st.text(info_str)


        # 3. 데이터 로드 & 품질 체크
        with tabs[2]:
            st.header("연도별 전체 인구 추이 그래프")
            uploaded_file = st.file_uploader("Upload population_trends.csv", type="csv")

            if uploaded_file is not None:
                df = pd.read_csv(uploaded_file)

                # 결측값 및 타입 처리
                df.replace('-', 0, inplace=True)
                for col in ['인구', '출생아수(명)', '사망자수(명)']:
                    if col in df.columns:
                        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0).astype(int)

                # '전국' 데이터 필터링
                nation_df = df[df['지역'] == '전국'].copy()
                nation_df = nation_df.sort_values(by='연도')

                # 2035년 인구 예측
                recent = nation_df.tail(3)
                mean_births = recent['출생아수(명)'].mean()
                mean_deaths = recent['사망자수(명)'].mean()
                net_change = mean_births - mean_deaths
                last_year = nation_df['연도'].max()
                last_pop = nation_df[nation_df['연도'] == last_year]['인구'].values[0]
                years_to_project = 2035 - last_year
                predicted_pop = int(last_pop + net_change * years_to_project)

                # 그래프 생성
                fig, ax = plt.subplots()
                ax.plot(nation_df['연도'], nation_df['인구'], marker='o', label='Actual Population')
                ax.scatter(2035, predicted_pop, color='red', label='Predicted 2035')
                ax.text(2035, predicted_pop, f'{predicted_pop:,}', va='bottom', ha='right', fontsize=8)

                ax.set_title("Population Trend")
                ax.set_xlabel("Year")
                ax.set_ylabel("Population")
                ax.legend()
                ax.grid(True)

                st.pyplot(fig)

        # 4. Datetime 특성 추출
        with tabs[3]:
            st.header("🕒 지역별 인구 변화량 순위")
            region_ko_to_en = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }

            st.title("Recent 5-Year Regional Population Change")

            uploaded_file = st.file_uploader("Upload population_trends.csv", type="csv")

            if uploaded_file is not None:
                df = pd.read_csv(uploaded_file)

                # 전처리
                df.replace('-', 0, inplace=True)
                df['인구'] = pd.to_numeric(df['인구'], errors='coerce').fillna(0).astype(int)

                # '전국' 제외
                region_df = df[df['지역'] != '전국'].copy()

                # 최근 5년 찾기
                recent_years = sorted(region_df['연도'].unique())[-5:]

                # 지역별 인구 변화량 계산
                changes = []
                for region in region_df['지역'].unique():
                    sub_df = region_df[region_df['지역'] == region]
                    sub_df = sub_df[sub_df['연도'].isin(recent_years)].sort_values('연도')
                    if len(sub_df) == 5:
                        start = sub_df.iloc[0]['인구']
                        end = sub_df.iloc[-1]['인구']
                        diff = end - start
                        pct_change = ((end - start) / start * 100) if start != 0 else 0
                        changes.append({
                            'Region': region_ko_to_en.get(region, region),
                            'Change': round(diff / 1000, 1),  # 천명 단위
                            'ChangeRate': round(pct_change, 2)
                        })

                change_df = pd.DataFrame(changes).sort_values(by='Change', ascending=False)

                # 시각화 1: 절대 인구 변화량
                st.subheader("Absolute Population Change (Last 5 Years)")

                plt.figure(figsize=(10, 8))
                ax1 = sns.barplot(x='Change', y='Region', data=change_df, palette='viridis')
                ax1.set_title("Population Change (Thousands)")
                ax1.set_xlabel("Change (Thousands)")
                ax1.set_ylabel("Region")

                for i in ax1.containers:
                    ax1.bar_label(i, fmt="%.1f", padding=3)

                st.pyplot(plt.gcf())

                # 시각화 2: 변화율
                st.subheader("Percentage Population Change (Last 5 Years)")

                plt.figure(figsize=(10, 8))
                ax2 = sns.barplot(x='ChangeRate', y='Region', data=change_df, palette='coolwarm')
                ax2.set_title("Population Change Rate (%)")
                ax2.set_xlabel("Change Rate (%)")
                ax2.set_ylabel("Region")

                for i in ax2.containers:
                    ax2.bar_label(i, fmt="%.2f%%", padding=3)

                st.pyplot(plt.gcf())

                # 해설
                st.markdown("### Interpretation")
                st.markdown(
                    "- Regions with the highest population **growth** tend to be metropolitan or suburban areas.\n"
                    "- Regions with **population decline** may face challenges such as aging and outmigration.\n"
                    "- Change in absolute numbers and growth rate do not always match (e.g., small population with high % growth).\n"
                    "- This trend may inform regional development or policy decisions."
                )

        # 5. 시각화
        with tabs[4]:
            st.header("📈 증감률 상위 지역 및 연도 도출")
            uploaded_file = st.file_uploader("Upload population_trends.csv", type="csv")

            if uploaded_file is not None:
                df = pd.read_csv(uploaded_file)

            # 전처리
                df.replace('-', 0, inplace=True)
                df['인구'] = pd.to_numeric(df['인구'], errors='coerce').fillna(0).astype(int)

                # '전국' 제외
                region_df = df[df['지역'] != '전국'].copy()

                # 연도 오름차순 정렬
                region_df.sort_values(['지역', '연도'], inplace=True)

                # 인구 증감(diff) 계산
                region_df['인구 증감'] = region_df.groupby('지역')['인구'].diff()

                # 증감 데이터 중 상위 100개(절댓값 기준)
                top_changes = region_df.dropna(subset=['인구 증감'])
                top_changes['abs_change'] = top_changes['인구 증감'].abs()
                top_100 = top_changes.sort_values('abs_change', ascending=False).drop(columns='abs_change').head(100)

                # 천단위 콤마 적용
                top_100_display = top_100.copy()
                top_100_display['인구'] = top_100_display['인구'].apply(lambda x: f"{x:,}")
                top_100_display['인구 증감'] = top_100_display['인구 증감'].apply(lambda x: f"{int(x):,}")

                # 스타일링 함수 정의
                def color_diff(val):
                    try:
                        val = int(val.replace(',', ''))
                        color = 'background-color: #add8e6' if val > 0 else 'background-color: #f4cccc'
                    except:
                        color = ''
                    return color

                st.subheader("Top 100 Population Increase/Decrease Cases")
                styled_df = top_100_display.style.applymap(color_diff, subset=['인구 증감'])

                st.dataframe(styled_df, use_container_width=True)


        # 6. 상관관계 분석
        with tabs[5]:
            st.header("🔗 누적영역그래프 등 적절한 시각화")
            region_ko_to_en = {
                '서울': 'Seoul', '부산': 'Busan', '대구': 'Daegu', '인천': 'Incheon',
                '광주': 'Gwangju', '대전': 'Daejeon', '울산': 'Ulsan', '세종': 'Sejong',
                '경기': 'Gyeonggi', '강원': 'Gangwon', '충북': 'Chungbuk', '충남': 'Chungnam',
                '전북': 'Jeonbuk', '전남': 'Jeonnam', '경북': 'Gyeongbuk', '경남': 'Gyeongnam',
                '제주': 'Jeju'
            }

            uploaded_file = st.file_uploader("Upload population_trends.csv", type="csv")

            if uploaded_file is not None:
                df = pd.read_csv(uploaded_file)

                # 전처리
                df.replace('-', 0, inplace=True)
                df['인구'] = pd.to_numeric(df['인구'], errors='coerce').fillna(0).astype(int)

                # '전국' 제외
                df = df[df['지역'] != '전국']

                # 한글 → 영어 지역명 변환
                df['Region'] = df['지역'].map(region_ko_to_en)

                # 피벗 테이블: index=연도, columns=Region, values=인구
                pivot_df = df.pivot_table(index='연도', columns='Region', values='인구', aggfunc='sum')

                # 연도 기준 정렬
                pivot_df = pivot_df.sort_index()

                st.subheader("Stacked Area Plot (Population by Region)")

                # 누적 영역 그래프
                fig, ax = plt.subplots(figsize=(12, 6))
                pivot_df.plot.area(ax=ax, cmap='tab20')  # 다양한 색상 자동 지정
                ax.set_title("Population Trend by Region")
                ax.set_xlabel("Year")
                ax.set_ylabel("Population")
                ax.legend(title="Region", bbox_to_anchor=(1.05, 1), loc='upper left')
                ax.grid(True)

                st.pyplot(fig)


# ---------------------
# 페이지 객체 생성
# ---------------------
Page_Login    = st.Page(Login,    title="Login",    icon="🔐", url_path="login")
Page_Register = st.Page(lambda: Register(Page_Login.url_path), title="Register", icon="📝", url_path="register")
Page_FindPW   = st.Page(FindPassword, title="Find PW", icon="🔎", url_path="find-password")
Page_Home     = st.Page(lambda: Home(Page_Login, Page_Register, Page_FindPW), title="Home", icon="🏠", url_path="home", default=True)
Page_User     = st.Page(UserInfo, title="My Info", icon="👤", url_path="user-info")
Page_Logout   = st.Page(Logout,   title="Logout",  icon="🔓", url_path="logout")
Page_EDA      = st.Page(EDA,      title="EDA",     icon="📊", url_path="eda")

# ---------------------
# 네비게이션 실행
# ---------------------
if st.session_state.logged_in:
    pages = [Page_Home, Page_User, Page_Logout, Page_EDA]
else:
    pages = [Page_Home, Page_Login, Page_Register, Page_FindPW]

selected_page = st.navigation(pages)
selected_page.run()