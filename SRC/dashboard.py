## dashboard.py
import streamlit as st
import requests
import pandas as pd
from pathlib import Path

API = "https://project-assignment-system-2.onrender.com"

# locate repo root and database folder safely
ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "database"

st.set_page_config(page_title="Project–Student Matching Dashboard", layout="wide")

st.title("Project–Student Matching Dashboard")

menu = st.sidebar.selectbox(
    "Navigation",
    ["Students","Projects","Match Scores","Teams"]
)

# ---------------- STUDENTS ----------------

if menu == "Students":

    st.header("Student Profiles")

    try:
        students = requests.get(f"{API}/students").json()
        df = pd.DataFrame(students)
    except Exception as e:
        st.error(e)
        df = pd.DataFrame()

    st.dataframe(df, use_container_width=True)

    st.subheader("Remove Student")

    if not df.empty and "name" in df.columns:

        student_name = st.selectbox(
            "Select Student to Remove",
            df["name"]
        )

        if st.button("Delete Student"):

            requests.delete(f"{API}/students/{student_name}")

            # recompute scores and teams
            requests.post(f"{API}/recompute")

            st.success("Student removed")
            st.rerun()

    st.subheader("Add Student")

    try:
        projects = requests.get(f"{API}/projects").json()
        project_names = [p["project_name"] for p in projects]
    except:
        project_names = []

    with st.form("student_form"):

        st.write("### Basic Information")

        name = st.text_input("Name")
        college = st.text_input("College")

        resume = st.text_input("Resume Link")
        github = st.text_input("GitHub Profile")

        st.write("### Skills (1–5)")

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            python_skill = st.slider("Python",1,5)
            ml = st.slider("Machine Learning",1,5)

        with col2:
            api = st.slider("APIs",1,5)
            frontend = st.slider("Frontend",1,5)

        with col3:
            data_skill = st.slider("Data Analysis",1,5)
            systems = st.slider("Systems",1,5)

        with col4:
            viz = st.slider("Data Viz",1,5)
            devops = st.slider("DevOps",1,5)

        st.write("### Preferred Projects")

        pref1 = st.selectbox("Preferred Project 1", project_names)
        pref2 = st.selectbox("Preferred Project 2", project_names)
        pref3 = st.selectbox("Preferred Project 3", project_names)

        submit = st.form_submit_button("Submit Student")

        if submit:

            payload = {
                "name": name,
                "college": college,
                "resume_link": resume,
                "github_link": github,
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

            requests.post(f"{API}/students", json=payload)

            # recompute scores and teams
            requests.post(f"{API}/recompute")

            st.success("Student added")
            st.rerun()


# ---------------- PROJECTS ----------------

elif menu == "Projects":

    st.header("Projects")

    try:
        projects = requests.get(f"{API}/projects").json()
        df = pd.DataFrame(projects)
    except Exception as e:
        st.error(e)
        df = pd.DataFrame()

    st.dataframe(df, use_container_width=True)

    st.subheader("Remove Project")

    if not df.empty and "project_name" in df.columns:

        project_name = st.selectbox(
            "Select Project to Remove",
            df["project_name"]
        )

        if st.button("Delete Project"):

            requests.delete(f"{API}/projects/{project_name}")

            # recompute scores and teams
            requests.post(f"{API}/recompute")

            st.success("Project removed")
            st.rerun()

    st.subheader("Add Project")

    project = st.text_input("Project Name")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        python_weight = st.slider("Python Weight",1,5)
        ml = st.slider("ML Weight",1,5)

    with col2:
        api = st.slider("API Weight",1,5)
        frontend = st.slider("Frontend Weight",1,5)

    with col3:
        data_weight = st.slider("Data Weight",1,5)
        systems = st.slider("Systems Weight",1,5)

    with col4:
        viz = st.slider("Viz Weight",1,5)
        devops = st.slider("DevOps Weight",1,5)

    if st.button("Add Project"):

        payload = {
            "project_name": project,
            "Python": python_weight,
            "ML": ml,
            "APIs": api,
            "Frontend": frontend,
            "Data": data_weight,
            "Systems": systems,
            "Viz": viz,
            "DevOps": devops
        }

        requests.post(f"{API}/projects", json=payload)

        # recompute scores and teams
        requests.post(f"{API}/recompute")

        st.success("Project added")
        st.rerun()


# ---------------- MATCH SCORES ----------------

elif menu == "Match Scores":

    st.header("Compatibility Matrix")

    try:
        scores_path = DATA_DIR / "student_project_final_scores.csv"
        scores = pd.read_csv(scores_path)

        st.dataframe(
            scores.style.background_gradient(cmap="viridis"),
            use_container_width=True
        )

    except Exception as e:
        st.warning("Compatibility scores not generated yet.")
        st.write(e)


# ---------------- TEAMS ----------------

elif menu == "Teams":

    st.header("Suggested Teams")

    try:
        teams_path = DATA_DIR / "project_teams.csv"
        teams = pd.read_csv(teams_path)

        st.dataframe(teams, use_container_width=True)

    except Exception as e:
        st.warning("Teams not generated yet.")
        st.write(e)

    if st.button("Recompute Teams"):

        requests.post(f"{API}/recompute")

        st.success("Teams recomputed")

        st.rerun()
