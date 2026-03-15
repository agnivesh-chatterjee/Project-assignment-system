## dashboard.py
import streamlit as st
import requests
import pandas as pd
from pathlib import Path
import os
import time

API = os.getenv("API_BASE_URL", "https://project-assignment-system-2.onrender.com")

ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "database"

st.set_page_config(page_title="Project–Student Matching Dashboard", layout="wide")

st.title("Project–Student Matching Dashboard")

# ---------- TABLE HEADER STYLE ----------
def style_table(df):
    return df.style.set_table_styles(
        [{
            "selector": "th",
            "props": [
                ("background-color", "#00C46A"),
                ("color", "black"),
                ("font-weight", "bold")
            ]
        }]
    )

# ---------- TABS ----------
students_tab, projects_tab, scores_tab, teams_tab = st.tabs(
    ["Students", "Projects", "Match Scores", "Teams"]
)

# ---------------- STUDENTS ----------------
with students_tab:

    st.header("Student Profiles")

    try:
        resp = requests.get(f"{API}/students", timeout=30)
        resp.raise_for_status()
        students = resp.json()
        df = pd.DataFrame(students)
    except Exception as e:
        st.error(f"Failed to load students: {e}")
        df = pd.DataFrame()

    if not df.empty:
        st.dataframe(style_table(df), use_container_width=True)

    st.subheader("Remove Student")

    if not df.empty and "name" in df.columns:

        student_name = st.selectbox(
            "Select Student to Remove",
            df["name"]
        )

        if st.button("Delete Student"):
            try:
                with st.spinner("Removing student and recomputing teams..."):
                    delete_resp = requests.delete(f"{API}/students/{student_name}", timeout=30)
                    delete_resp.raise_for_status()

                st.success("Student removed")
                st.rerun()

            except Exception as e:
                st.error(f"Delete student failed: {e}")

    st.subheader("Add Student")

    try:
        resp = requests.get(f"{API}/projects", timeout=30)
        resp.raise_for_status()
        projects = resp.json()
        project_names = [p["project_name"] for p in projects]
    except Exception:
        project_names = []

    with st.form("student_form", clear_on_submit=True):

        st.write("### Basic Information")

        name = st.text_input("Name")
        college = st.text_input("College")

        resume = st.text_input("Resume Link")
        github = st.text_input("GitHub Profile")

        st.write("### Skills (1–5)")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            python_skill = st.slider("Python", 1, 5)
            ml = st.slider("Machine Learning", 1, 5)

        with col2:
            api = st.slider("APIs", 1, 5)
            frontend = st.slider("Frontend", 1, 5)

        with col3:
            data_skill = st.slider("Data Analysis", 1, 5)
            systems = st.slider("Systems", 1, 5)

        with col4:
            viz = st.slider("Data Viz", 1, 5)
            devops = st.slider("DevOps", 1, 5)

        st.write("### Preferred Projects")

        pref1 = st.selectbox("Preferred Project 1", project_names)
        pref2 = st.selectbox("Preferred Project 2", project_names)
        pref3 = st.selectbox("Preferred Project 3", project_names)

        submit = st.form_submit_button("Submit Student")

        if submit:
            payload = {
                "name": name.strip(),
                "college": college.strip(),
                "resume_link": resume.strip(),
                "github_link": github.strip(),
                "python": python_skill,
                "ml": ml,
                "api": api,
                "frontend": frontend,
                "data": data_skill,
                "systems": systems,
                "viz": viz,
                "devops": devops,
                "pref1": pref1,
                "pref2": pref2,
                "pref3": pref3
            }

            try:
                with st.spinner("Adding student..."):
                    add_resp = requests.post(f"{API}/students", json=payload, timeout=30)
                    add_resp.raise_for_status()

                st.success("Student added")
                st.rerun()

            except Exception as e:
                st.error(f"Add student failed: {e}")

# ---------------- PROJECTS ----------------
with projects_tab:

    st.header("Projects")

    try:
        resp = requests.get(f"{API}/projects", timeout=30)
        resp.raise_for_status()
        projects = resp.json()
        df = pd.DataFrame(projects)
    except Exception as e:
        st.error(f"Failed to load projects: {e}")
        df = pd.DataFrame()

    if not df.empty:
        st.dataframe(style_table(df), use_container_width=True)

# ---------------- MATCH SCORES ----------------
with scores_tab:

    st.header("Compatibility Matrix")

    try:
        with st.spinner("Loading compatibility scores..."):
            scores = requests.get(f"{API}/scores", timeout=30)
            scores.raise_for_status()
            df = pd.DataFrame(scores.json())

        st.dataframe(
            style_table(df).background_gradient(cmap="viridis"),
            use_container_width=True
        )

    except Exception as e:
        st.warning("Compatibility scores not generated yet.")
        st.write(e)

# ---------------- TEAMS ----------------
with teams_tab:

    st.header("Suggested Teams")

    if st.button("Recompute Teams"):
        try:
            with st.spinner("Recomputing teams..."):
                resp = requests.post(f"{API}/recompute", timeout=30)
                resp.raise_for_status()
                st.success("Recompute started.")
        except Exception as e:
            st.error(f"Failed to start recompute: {e}")

    try:
        with st.spinner("Loading teams..."):
            teams = requests.get(f"{API}/teams", timeout=60)
            teams.raise_for_status()
            df = pd.DataFrame(teams.json())

        if not df.empty:
            st.dataframe(style_table(df), use_container_width=True)

    except Exception as e:
        st.error("Failed to load teams.")
        st.write(e)
