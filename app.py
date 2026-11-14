import json
import random
import calendar
from urllib.parse import quote
from pathlib import Path
from datetime import date, datetime
from uuid import uuid4

import streamlit as st
import plotly.express as px  # 차트 시각화를 위한 라이브러리 추가

# --------------------------------------------------
# MY LIFE - 개인 일정 관리 웹사이트 (Ultimate Version)
# 실행: python -m streamlit run app.py
# --------------------------------------------------

st.set_page_config(
    page_title="MY LIFE",
    page_icon="🌷",
    layout="wide",
)

DATA_FILE = Path(__file__).with_name("data.json")
DEFAULT_DATA = {"tasks": [], "ddays": [], "songs": []}

def load_data():
    """저장된 JSON 데이터를 불러옵니다."""
    if not DATA_FILE.exists():
        return DEFAULT_DATA.copy()
    try:
        with DATA_FILE.open("r", encoding="utf-8") as f:
            loaded = json.load(f)
        for key in DEFAULT_DATA:
            if key not in loaded or not isinstance(loaded[key], list):
                loaded[key] = []
        for task in loaded["tasks"]:
            task.setdefault("id", str(uuid4()))
            task.setdefault("title", "제목 없음")
            task.setdefault("category", "기타")
            task.setdefault("priority", "보통")
            task.setdefault("due_date", "")
            task.setdefault("done", False)
            task.setdefault("created_at", datetime.now().isoformat())
        return loaded
    except (json.JSONDecodeError, OSError, TypeError):
        st.error("data.json 파일을 읽지 못했습니다. 파일이 손상되었는지 확인해 주세요.")
        return DEFAULT_DATA.copy()

def save_data():
    """현재 데이터를 data.json 파일에 저장합니다."""
    with DATA_FILE.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def dday_text(target_date):
    target = date.fromisoformat(target_date)
    gap = (target - date.today()).days
    if gap > 0: return f"D-{gap}"
    if gap == 0: return "D-Day"
    return f"D+{abs(gap)}"

data = load_data()

# --------------------------------------------------
# 사이드바 (내비게이션 메뉴)
# --------------------------------------------------
with st.sidebar:
    st.title("🌷 MY LIFE")
    st.write("나의 하루를 계획하고 기록하는 공간")
    st.divider()
    menu = st.radio(
        "이동할 메뉴를 선택하세요",
        ["🏠 홈 대시보드", "✅ 투 두 리스트", "🗓️ D-DAY 관리", "📅 월간 달력", "🎵 플레이리스트", "💗 기분별 추천"]
    )
    st.divider()
    st.caption(f"오늘 날짜: {date.today().strftime('%Y년 %m월 %d일')}")

# --------------------------------------------------
# 홈 대시보드
# --------------------------------------------------
if menu == "🏠 홈 대시보드":
    st.header("🏠 오늘의 대시보드")
    total = len(data["tasks"])
    completed = sum(1 for task in data["tasks"] if task.get("done", False))
    remaining = total - completed

    col_metric, col_chart = st.columns([1, 1.2])
    
    with col_metric:
        st.subheader("📊 나의 성취도")
        c1, c2, c3 = st.columns(3)
        c1.metric("전체 할 일", total)
        c2.metric("완료", completed)
        c3.metric("남음", remaining)
        
        if total:
            st.progress(completed / total, text=f"현재 완료율 {completed / total:.0%}")
        else:
            st.info("등록된 할 일이 없어요. 투 두 리스트에서 일정을 추가해 보세요!")
            
        st.divider()
        st.subheader("📌 미완료 할 일 (가까운 마감일순)")
        unfinished = [t for t in data["tasks"] if not t.get("done", False)]
        unfinished.sort(key=lambda t: t.get("due_date") or "9999-12-31")
        if unfinished:
            for task in unfinished[:5]:
                due = task.get("due_date", "")
                title = f"**{task['title']}** [{task.get('category', '기타')}]"
                if due:
                    due_day = date.fromisoformat(due)
                    if due_day < date.today(): st.error(f"{title} · 마감: {due} (기한 지남)")
                    elif due_day == date.today(): st.warning(f"{title} · 마감: {due} (오늘 마감!)")
                    else: st.write(f"• {title} · 마감: {due}")
                else:
                    st.write(f"• {title}")
        else:
            st.success("미완료된 할 일이 없습니다! 훌륭해요👏")

    with col_chart:
        if total > 0:
            pie_data = {"상태": ["완료", "미완료"], "비율": [completed, remaining]}
            fig = px.pie(
                pie_data, values="비율", names="상태", 
                hole=0.5, color="상태", 
                color_discrete_map={"완료":"#28a745", "미완료":"#dc3545"}
            )
            fig.update_layout(margin=dict(t=0, b=0, l=0, r=0), showlegend=True)
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.write("") 

# --------------------------------------------------
# 투 두 리스트
# --------------------------------------------------
elif menu == "✅ 투 두 리스트":
    st.header("✅ 투 두 리스트")
    
    with st.expander("➕ 새로운 할 일 추가", expanded=False):
        with st.form("add_task_form", clear_on_submit=True):
            new_title = st.text_input("할 일 제목", placeholder="예: 수학 문제집 20쪽 풀기")
            left, right = st.columns(2)
            with left:
                new_category = st.selectbox("분야", ["공부", "개인", "동아리", "기타"])
                new_priority = st.selectbox("우선순위", ["높음", "보통", "낮음"])
            with right:
                new_due_date = st.date_input("마감일", value=date.today(), format="YYYY-MM-DD")
            if st.form_submit_button("할 일 추가", use_container_width=True):
                if not new_title.strip(): st.warning("제목을 입력해 주세요.")
                else:
                    data["tasks"].append({
                        "id": str(uuid4()), "title": new_title.strip(), "category": new_category,
                        "priority": new_priority, "due_date": new_due_date.isoformat(),
                        "done": False, "created_at": datetime.now().isoformat()
                    })
                    save_data(); st.rerun()

    f1, f2, f3 = st.columns(3)
    category_filter = f1.selectbox("분야", ["전체", "공부", "개인", "동아리", "기타"])
    status_filter = f2.selectbox("상태", ["전체", "미완료", "완료"])
    sort_filter = f3.selectbox("정렬", ["마감일순", "우선순위순", "최근 추가순"])

    filtered = [t for t in data["tasks"] if (category_filter == "전체" or t.get("category") == category_filter) 
                and (status_filter == "전체" or (status_filter == "미완료" and not t.get("done")) or (status_filter == "완료" and t.get("done")))]
    
    if sort_filter == "마감일순": filtered.sort(key=lambda t: t.get("due_date") or "9999-12-31")
    elif sort_filter == "우선순위순": filtered.sort(key=lambda t: {"높음":0, "보통":1, "낮음":2}.get(t.get("priority"), 1))
    else: filtered.sort(key=lambda t: t.get("created_at", ""), reverse=True)

    c_del_col = st.columns([4, 1])
    if c_del_col[1].button("🧹 완료 항목 삭제", use_container_width=True):
        data["tasks"] = [t for t in data["tasks"] if not t.get("done", False)]
        save_data(); st.rerun()

    for task in filtered:
        task_id = task["id"]
        with st.container(border=True):
            col_check, col_info, col_del = st.columns([1, 8, 1])
            with col_check:
                is_done = st.checkbox("", value=bool(task.get("done", False)), key=f"chk_{task_id}")
                if is_done != task.get("done", False):
                    task["done"] = is_done
                    save_data(); st.rerun()
            with col_info:
                p_color = {"높음": "red", "보통": "orange", "낮음": "green"}.get(task.get('priority'), "gray")
                strike = "line-through; color:gray;" if task.get("done") else "none;"
                st.markdown(f"<h5 style='text-decoration:{strike}; margin-bottom:0;'>{task['title']}</h5>", unsafe_allow_html=True)
                st.markdown(f"<span style='font-size:0.8em; color:gray;'>{task.get('category')} | </span>"
                            f"<span style='font-size:0.8em; font-weight:bold; color:{p_color};'>{task.get('priority')}</span>"
                            f"<span style='font-size:0.8em; color:gray;'> | 마감: {task.get('due_date') or '없음'}</span>", unsafe_allow_html=True)
            with col_del:
                if st.button("❌", key=f"del_{task_id}"):
                    data["tasks"] = [t for t in data["tasks"] if t["id"] != task_id]
                    save_data(); st.rerun()

# --------------------------------------------------
# D-DAY
# --------------------------------------------------
elif menu == "🗓️ D-DAY 관리":
    st.header("🗓️ D-DAY 관리")
    with st.form("add_dday_form", clear_on_submit=True):
        col1, col2 = st.columns(2)
        event_title = col1.text_input("일정 이름", placeholder="예: 기말고사")
        event_date = col2.date_input("목표 날짜", value=date.today())
        if st.form_submit_button("D-DAY 추가", use_container_width=True):
            if not event_title.strip(): st.warning("이름을 입력하세요.")
            else:
                data["ddays"].append({"id": str(uuid4()), "title": event_title.strip(), "target_date": event_date.isoformat()})
                save_data(); st.rerun()
                
    st.divider()
    future_events = sorted([e for e in data["ddays"] if date.fromisoformat(e["target_date"]) >= date.today()], key=lambda x: x["target_date"])
    past_events = sorted([e for e in data["ddays"] if date.fromisoformat(e["target_date"]) < date.today()], key=lambda x: x["target_date"], reverse=True)

    c1, c2 = st.columns(2)
    with c1:
        st.subheader("🚀 다가오는 일정")
        if not future_events: st.caption("일정이 없습니다.")
        for e in future_events:
            with st.container(border=True):
                st.markdown(f"#### {e['title']} <span style='float:right; color:#ff4b4b;'>{dday_text(e['target_date'])}</span>", unsafe_allow_html=True)
                st.caption(f"날짜: {e['target_date']}")
                if st.button("삭제", key=f"df_{e['id']}"):
                    data["ddays"] = [x for x in data["ddays"] if x["id"] != e["id"]]; save_data(); st.rerun()
    with c2:
        st.subheader("🕰️ 지나간 일정")
        if not past_events: st.caption("일정이 없습니다.")
        for e in past_events:
            with st.container(border=True):
                st.markdown(f"#### {e['title']} <span style='float:right; color:gray;'>{dday_text(e['target_date'])}</span>", unsafe_allow_html=True)
                st.caption(f"날짜: {e['target_date']}")
                if st.button("삭제", key=f"dp_{e['id']}"):
                    data["ddays"] = [x for x in data["ddays"] if x["id"] != e["id"]]; save_data(); st.rerun()

# --------------------------------------------------
# 월간 달력
# --------------------------------------------------
elif menu == "📅 월간 달력":
    st.header("📅 월간 달력")
    if "cal_year" not in st.session_state: st.session_state.cal_year = date.today().year
    if "cal_month" not in st.session_state: st.session_state.cal_month = date.today().month

    c1, c2, c3 = st.columns([1, 2, 1])
    if c1.button("◀ 이전 달", use_container_width=True):
        if st.session_state.cal_month == 1: st.session_state.cal_month = 12; st.session_state.cal_year -= 1
        else: st.session_state.cal_month -= 1
        st.rerun()
    c2.markdown(f"<h3 style='text-align: center;'>{st.session_state.cal_year}년 {st.session_state.cal_month}월</h3>", unsafe_allow_html=True)
    if c3.button("다음 달 ▶", use_container_width=True):
        if st.session_state.cal_month == 12: st.session_state.cal_month = 1; st.session_state.cal_year += 1
        else: st.session_state.cal_month += 1
        st.rerun()

    st.divider()
    header_cols = st.columns(7)
    for i, day_name in enumerate(["월", "화", "수", "목", "금", "토", "일"]):
        color = "red" if i == 6 else "blue" if i == 5 else "black"
        header_cols[i].markdown(f"<div style='text-align:center; color:{color}; font-weight:bold;'>{day_name}</div>", unsafe_allow_html=True)

    for week in calendar.monthcalendar(st.session_state.cal_year, st.session_state.cal_month):
        week_cols = st.columns(7)
        for i, day in enumerate(week):
            if day == 0: week_cols[i].write("")
            else:
                is_today = (day == date.today().day and st.session_state.cal_month == date.today().month and st.session_state.cal_year == date.today().year)
                with week_cols[i].container(border=True, height=140):
                    # 수정된 달력 날짜 하이라이트 부분 (오류 해결)
                    if is_today:
                        st.markdown(f"<div style='background-color:#ff4b4b; color:white; border-radius:4px; text-align:center; font-weight:bold; width:100%; padding:2px 0;'>{day}</div>", unsafe_allow_html=True)
                    else:
                        day_color = "red" if i == 6 else "blue" if i == 5 else "black"
                        st.markdown(f"<div style='color:{day_color}; text-align:center; font-weight:bold;'>{day}</div>", unsafe_allow_html=True)
                    
                    cur_str = f"{st.session_state.cal_year}-{st.session_state.cal_month:02d}-{day:02d}"
                    
                    for d in [x for x in data["ddays"] if x.get("target_date") == cur_str]:
                        st.markdown(f"<div style='font-size:0.75em; color:red; font-weight:bold; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>🎯 {d['title']}</div>", unsafe_allow_html=True)
                        
                    for t in [x for x in data["tasks"] if x.get("due_date") == cur_str]:
                        color = "#aaaaaa" if t.get("done") else "#333333"
                        strike = "line-through" if t.get("done") else "none"
                        icon = "✅" if t.get("done") else "📌"
                        st.markdown(f"<div style='font-size:0.75em; color:{color}; text-decoration:{strike}; white-space:nowrap; overflow:hidden; text-overflow:ellipsis;'>{icon} {t['title']}</div>", unsafe_allow_html=True)

# --------------------------------------------------
# 플레이리스트
# --------------------------------------------------
elif menu == "🎵 플레이리스트":
    st.header("🎵 나만의 플레이리스트")
    with st.form("add_song_form", clear_on_submit=True):
        col1, col2, col3 = st.columns(3)
        song_title = col1.text_input("노래 제목")
        artist = col2.text_input("가수")
        song_url = col3.text_input("유튜브 링크")
        if st.form_submit_button("➕ 노래 추가", use_container_width=True):
            if not song_title.strip(): st.warning("노래 제목을 입력해 주세요.")
            else:
                data["songs"].append({"id": str(uuid4()), "title": song_title.strip(), "artist": artist.strip(), "url": song_url.strip()})
                save_data(); st.rerun()

    if not data["songs"]: st.info("저장한 노래가 없습니다.")
    for song in data["songs"]:
        with st.container(border=True):
            info_col, action_col = st.columns([5, 1])
            with info_col:
                st.write(f"**{song['title']}** - {song.get('artist', '가수 미상')}")
                url = song.get("url", "")
                if url:
                    if "youtube.com" in url or "youtu.be" in url:
                        with st.expander("▶️ 바로 재생하기"): st.video(url)
                    else: st.markdown(f"[🔗 링크 열기]({url})")
            with action_col:
                if st.button("🗑️ 삭제", key=f"ds_{song['id']}"):
                    data["songs"] = [s for s in data["songs"] if s["id"] != song["id"]]; save_data(); st.rerun()

# --------------------------------------------------
# 기분별 추천
# --------------------------------------------------
elif menu == "💗 기분별 추천":
    st.header("💗 지금 기분에 맞는 노래")
    mood_songs = {
        "신나고 에너지가 필요해": [("Dynamite", "BTS"), ("After LIKE", "IVE"), ("Super Shy", "NewJeans")],
        "우울하거나 위로가 필요해": [("밤편지", "아이유"), ("한숨", "이하이"), ("That's Okay", "도경수")],
        "공부에 집중하고 싶어": [("River Flows in You", "Yiruma"), ("Nuvole Bianche", "Ludovico Einaudi"), ("Kiss the Rain", "Yiruma")],
        "편안하게 쉬고 싶어": [("밤양갱", "비비"), ("사랑은 늘 도망가", "임영웅"), ("제주도의 푸른 밤", "태연")],
    }
    
    selected_mood = st.selectbox("어떤 기분인가요?", list(mood_songs.keys()))
    if st.button("🎧 노래 추천받기", use_container_width=True):
        st.session_state["mood_rec"] = random.sample(mood_songs[selected_mood], k=2)
        st.session_state["mood_type"] = selected_mood

    if st.session_state.get("mood_type") == selected_mood:
        st.subheader(f"🎶 '{selected_mood}' 추천")
        for i, (s_name, singer) in enumerate(st.session_state["mood_rec"], 1):
            with st.container(border=True):
                c1, c2 = st.columns([5, 1])
                with c1:
                    st.write(f"**{s_name}** - {singer}")
                    st.markdown(f"[유튜브 검색 ↗](https://www.youtube.com/results?search_query={quote(f'{s_name} {singer}')})")
                with c2:
                    if st.button("저장", key=f"save_{i}_{s_name}"):
                        data["songs"].append({"id": str(uuid4()), "title": s_name, "artist": singer, "url": f"https://www.youtube.com/results?search_query={quote(f'{s_name} {singer}')}"})
                        save_data(); st.success("저장 완료!"); st.rerun()