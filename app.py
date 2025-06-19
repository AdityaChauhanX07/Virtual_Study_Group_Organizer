import streamlit as st
import time
import uuid
import pandas as pd
import plotly.express as px
from datetime import date, datetime
from streamlit_confetti import confetti

import plotly.graph_objects as go  # if not already imported

def render_progress_ring(progress, group_id):
    fig = go.Figure(go.Pie(
        values=[progress, 1 - progress],
        labels=["Completed", ""],
        marker=dict(colors=["#00c6ff", "#e0e0e0"]),
        hole=0.7,
        sort=False,
        direction="clockwise",
        textinfo='none',
    ))
    fig.update_layout(
        showlegend=False,
        margin=dict(t=0, b=0, l=0, r=0),
        annotations=[dict(
            text=f"{int(progress*100)}%",
            x=0.5, y=0.5, font_size=20, showarrow=False
        )]
    )
    st.plotly_chart(fig, use_container_width=True, key=f"{group_id}_ring")


# ✅ Matchmaking Engine: Suggest Similar Study Groups
def get_matching_groups(current_group, all_groups):
    matches = []
    current_subject = current_group["subject"].lower()
    current_goal = current_group["goal"].lower()

    try:
        current_time = pd.to_datetime(current_group["free_time"])
    except:
        current_time = None

    for other in all_groups:
        if other["id"] == current_group["id"]:
            continue

        other_subject = other["subject"].lower()
        other_goal = other["goal"].lower()

        score = 0

        # Subject similarity
        if current_subject in other_subject or other_subject in current_subject:
            score += 1

        # Goal similarity
        if current_goal in other_goal or other_goal in current_goal:
            score += 1

        # Time similarity
        try:
            other_time = pd.to_datetime(other["free_time"])
            if current_time and abs((current_time - other_time).total_seconds()) <= 2 * 3600:
                score += 1
        except:
            pass

        if score >= 2:
            matches.append(other)

    return matches


# ✅ GPT Suggestion Function — updated for OpenAI v1.x
# ✅ GPT Suggestion Function — now using simulated suggestions
def get_gpt_suggestions(subject, goal):
    subject = subject.lower()

    if "math" in subject:
        return """
        1. ✅ Review key formulas and theorems relevant to your goal.
        2. ✅ Solve 3-5 practice problems with increasing difficulty.
        3. ✅ Summarize mistakes and retry incorrect ones after 10 minutes.
        """

    elif "physics" in subject:
        return """
        1. 🔍 Revisit key physical laws and their derivations.
        2. 🎯 Solve conceptual and numerical questions from your syllabus.
        3. 💡 Watch a short visual explanation of the topic on YouTube.
        """

    elif "cs" in subject or "computer" in subject or "coding" in subject:
        return """
        1. 💻 Write a short program related to your topic.
        2. 📘 Review concepts with flashcards or spaced repetition.
        3. 🧪 Debug past code errors and document your learnings.
        """

    elif "chemistry" in subject:
        return """
        1. 🔬 Draw and review reaction mechanisms or chemical equations.
        2. 🧪 Practice balancing equations and solving numericals.
        3. 📊 Create summary tables for periodic trends or compound types.
        """

    elif "biology" in subject:
        return """
        1. 🌱 Diagram key biological processes (e.g., photosynthesis).
        2. 🧠 Use memory tricks to recall terminology and classifications.
        3. 📖 Review NCERT or textbook summary points and quiz yourself.
        """

    else:
        return f"""
        1. 🧭 Break your study goal '{goal}' into 3 small tasks and complete one now.
        2. 📚 Spend 20 focused minutes on any material you've been avoiding.
        3. 📝 Write a 3-point summary of what you learned at the end of the session.
        """


# ----- SETUP -----
st.set_page_config(page_title="Virtual Study Group Organizer", layout="centered")

# Dark mode toggle
dark_mode = st.toggle("🌙 Dark Mode", value=False)

# Apply style based on dark mode
st.markdown(
    f"""
    <link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;600&display=swap" rel="stylesheet">
    <style>
        html, body, [class*="css"] {{
            font-family: 'Inter', sans-serif;
        }}

        body {{
            background-color: {"#0e1117" if dark_mode else "#ffffff"};
            color: {"#ffffff" if dark_mode else "#000000"};
        }}
        .stButton > button {{
            font-weight: 600;
            border-radius: 8px;
            padding: 10px 24px;
            font-size: 16px;
            background-color: #4CAF50;
            color: white;
            transition: all 0.2s ease-in-out;
            box-shadow: 2px 2px 8px rgba(0,0,0,0.05);
        }}
        .stButton > button:hover {{
            background-color: #45a049;
            transform: translateY(-2px) scale(1.03);
            box-shadow: 0 4px 12px rgba(0, 198, 255, 0.2);
        }}
        .group-card {{
            background: {"linear-gradient(145deg, #1a1d24, #262730)" if dark_mode else "#f9f9f9"};
            color: {"#ffffff" if dark_mode else "#000000"};
            border: 1px solid #444444;
            border-radius: 16px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 2px 2px 12px rgba(0,0,0,0.05);
            transition: all 0.2s ease-in-out;
        }}
        .group-card:hover {{
        box-shadow: 0 0 16px rgba(0, 198, 255, 0.35);
        transform: translateY(-2px) scale(1.01);
        }}
        .streak-card:hover {{
        box-shadow: 0 0 14px rgba(0, 198, 255, 0.35);
        transform: translateY(-2px) scale(1.01);
        }}

        .streak-card {{
            background: {"linear-gradient(145deg, #1a1d24, #262730)" if dark_mode else "#e9f5ff"};
            color: {"#ffffff" if dark_mode else "#000000"};
            border: 1px solid {"#444444" if dark_mode else "#b3d9ff"};
            border-radius: 16px;
            padding: 15px 20px;
            margin-bottom: 20px;
            box-shadow: 2px 2px 12px rgba(0,0,0,0.05);
            transition: all 0.3s ease;
        }}
        .streak-card:hover {{
            box-shadow: 0 0 12px rgba(0, 198, 255, 0.3);
            transform: scale(1.01);
        }}
        /* ✅ Custom Scrollbar (Dark Mode Only) */
        body::-webkit-scrollbar {{
            width: 8px;
        }}
        body::-webkit-scrollbar-thumb {{
            background: #00c6ff;
            border-radius: 10px;
        }}
    </style>
    """,
    unsafe_allow_html=True
)



st.title("🎓 Virtual Study Group Organizer")

# Session state init
if "groups" not in st.session_state:
    st.session_state.groups = []

if "history" not in st.session_state:
    st.session_state.history = []

if "progress" not in st.session_state:
    st.session_state.progress = {}

if "streak_data" not in st.session_state:
    st.session_state.streak_data = {
        "last_completed": None,
        "streak": 0,
        "xp": 0
    }

if "gpt_suggestions_cache" not in st.session_state:
    st.session_state.gpt_suggestions_cache = {}

# Default subgoals
default_subgoals = ["📖 Read material", "📝 Take notes", "🧠 Practice problems"]

# ----- INPUT FORM -----
with st.form("group_form", clear_on_submit=True):
    subject = st.text_input("Enter your subject:")
    goal = st.text_input("Enter your study goal:")
    free_time = st.text_input("Enter your free time (e.g., Sunday, Evening):")
    time_input = st.time_input("Choose study time")

    submitted = st.form_submit_button("➕ Start Study Group")

    if submitted and subject and goal and free_time:
        group_id = str(uuid.uuid4())

        from datetime import datetime, date
        full_time_obj = datetime.combine(date.today(), time_input)

        new_group = {
            "id": group_id,
            "subject": subject,
            "goal": goal,
            "free_time": str(full_time_obj),
            "created_at": time.strftime("%Y-%m-%d %H:%M:%S")
        }

        st.session_state.groups.append(new_group)
        st.session_state.history.append(new_group)

        default_subgoals = ["Read Chapter 1", "Take Notes", "Practice Problems"]  # Or pull from config
        st.session_state.progress[group_id] = {
            task: False for task in default_subgoals
        }

        st.success("✅ Group Created Successfully!")
        confetti(emojis=["🎯", "📚", "🌟"])
        st.markdown(
            """
            <div style="text-align:center; font-size:1.3rem; margin-top:10px; animation: fadeInMessage 1.5s ease-in-out;">
                📘 Study group successfully launched!
            </div>
            <style>
                @keyframes fadeInMessage {
                    from { opacity: 0; transform: translateY(10px); }
                    to { opacity: 1; transform: translateY(0); }
                }
            </style>
            """,
            unsafe_allow_html=True,
        )
        time.sleep(1)
        st.rerun()

st.divider()

# ----- SEARCH -----
search = st.text_input("🔍 Search study groups (subject or time):").lower()

# 🔔 Show reminder for sessions starting soon
now = datetime.now()
for group in st.session_state.groups:
    try:
        session_time = datetime.fromisoformat(group["free_time"])
        time_to_session = (session_time - now).total_seconds()
        if 0 < time_to_session <= 300:  # within next 5 minutes
            st.warning(f"🔔 Your study session on **{group['subject']}** starts in less than 5 minutes!")
    except:
        continue  # skip if parsing fails


# ----- GROUP DISPLAY -----
st.subheader("📋 Current Study Groups")
filtered = [g for g in st.session_state.groups if search in g["subject"].lower() or search in g["free_time"].lower()]

st.markdown(f"""
<div class="streak-card">
    <h5 style="margin-bottom: 6px;">🔥 Daily Streak: {st.session_state.streak_data['streak']} days</h5>
    <p>💠 Total XP: {st.session_state.streak_data['xp']} pts</p>
</div>
""", unsafe_allow_html=True)

if not filtered:
    st.info("No matching groups found.")
else:
    for group in filtered:
        avatar_url = f"https://api.dicebear.com/7.x/bottts-neutral/svg?seed={group['id'][:8]}"

        with st.container():
            st.markdown(f"""
                <div class="group-card" style="display: flex; align-items: center;">
                    <img src="{avatar_url}" width="60" style="margin-right: 15px; border-radius: 12px;">
                    <div>
                        <b>Subject:</b> {group["subject"]}  
                        <br><b>Goal:</b> {group["goal"]}  
                        <br><b>Free Time:</b> {group["free_time"]}  
                        <br><b>Created:</b> {group["created_at"]}
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Countdown Timer
            try:
                group_time = pd.to_datetime(group["free_time"])
                time_left = group_time - pd.Timestamp.now()
                countdown_str = str(time_left).split('.')[0] if time_left.total_seconds() > 0 else "⏱️ Time passed"
            except:
                countdown_str = "❓ Invalid time"

            st.markdown(f"**⏳ Countdown:** {countdown_str}")

            # 📈 Visual Progress Ring using reusable function
            st.markdown("**📈 Subgoal Progress:**")
            progress_dict = st.session_state.progress.get(group["id"], {})

            if progress_dict:
                completed = sum(progress_dict.values())
                total = len(progress_dict)
                progress = completed / total
                render_progress_ring(progress, group["id"])
            else:
                st.info("No subgoals yet.")


            for task, done in progress_dict.items():
                new_status = st.checkbox(task, value=done, key=group["id"] + task)
                st.session_state.progress[group["id"]][task] = new_status

            # Check if all tasks completed
            if all(st.session_state.progress[group["id"]].values()):
                today_str = date.today().isoformat()
                last = st.session_state.streak_data["last_completed"]

                if last != today_str:
                    # First full completion today
                    st.session_state.streak_data["last_completed"] = today_str
                    st.session_state.streak_data["streak"] += 1
                    st.session_state.streak_data["xp"] += 100

            # ✅ Animated Success Feedback
            if all(st.session_state.progress[group["id"]].values()) and progress_dict:
                st.success("🎉 All tasks completed! Great job!")
                st.balloons()

            # GPT Study Suggestions Panel
            with st.expander("🤖 GPT Study Suggestions"):
                cache_key = group["id"]
                
                if cache_key in st.session_state.gpt_suggestions_cache:
                    st.markdown(st.session_state.gpt_suggestions_cache[cache_key])
                elif st.button(f"💡 Get Suggestions for {group['subject']}", key=group["id"] + "_gpt"):
                    with st.spinner("Thinking..."):
                        suggestions = get_gpt_suggestions(group["subject"], group["goal"])
                        st.session_state.gpt_suggestions_cache[cache_key] = suggestions
                        st.markdown(suggestions)


            # Matching Groups Panel
            with st.expander("🧑‍🤝‍🧑 Matching Study Groups"):
                matches = get_matching_groups(group, st.session_state.groups)
                if matches:
                    for m in matches:
                        st.markdown(f"- **{m['subject']}** | 🎯 {m['goal']} | 🕒 {m['free_time']}")
                else:
                    st.info("No close matches found yet.")

            # Remove button
            if st.button(f"❌ Remove {group['subject']}", key=group["id"] + "_remove"):
                st.session_state.groups = [g for g in st.session_state.groups if g["id"] != group["id"]]
                if group["id"] in st.session_state.progress:
                    del st.session_state.progress[group["id"]]
                st.success("Group removed!")
                time.sleep(0.5)
                st.rerun()

st.divider()

# ----- PRODUCTIVITY CHART -----
st.subheader("📊 Study Group History")
if st.session_state.history:
    history_df = pd.DataFrame(st.session_state.history)
    fig = px.histogram(
        history_df,
        x="subject",
        color="free_time",
        title="Study Sessions by Subject",
        labels={"free_time": "Scheduled Time"},
        barmode="group"
    )
    st.plotly_chart(fig, use_container_width=True, key=f"plot_{uuid.uuid4()}")
else:
    st.info("No study group data yet.")

# ----- DATA EXPORT -----
st.subheader("📥 Export Your Data")

if st.session_state.history:
    export_df = pd.DataFrame(st.session_state.history)
    csv = export_df.to_csv(index=False).encode('utf-8')

    st.download_button(
        label="📄 Download Study History as CSV",
        data=csv,
        file_name='study_group_history.csv',
        mime='text/csv',
    )
else:
    st.info("Nothing to export yet.")