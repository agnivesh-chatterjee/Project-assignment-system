## dashboard.py
import streamlit as st
import requests
import pandas as pd

API = "http://127.0.0.1:8000"

st.title("Project–Student Matching Dashboard")

menu = st.sidebar.selectbox(
    "Navigation",
    ["Students","Projects","Match Scores","Teams"]
)

# ---------------- STUDENTS ----------------

if menu == "Students":

    st.header("Student Profiles")

    students = requests.get(f"{API}/students").json()
    df = pd.DataFrame(students)

    st.dataframe(df)

    st.subheader("Remove Student")

    if len(df) > 0:

        student_id = st.selectbox(
            "Select Student to Remove",
            df["id"]
        )

        if st.button("Delete Student"):

            requests.delete(f"{API}/students/{student_id}")

            st.success("Student removed")
            st.rerun()

    st.subheader("Add Student")

    name = st.text_input("Name")
    python = st.slider("Python",1,5)
    ml = st.slider("ML",1,5)

    if st.button("Add Student"):

        data = {
            "name": name,
            "python": python,
            "ml": ml
        }

        requests.post(f"{API}/students", json=data)

        st.success("Student added")
        st.rerun()


# ---------------- PROJECTS ----------------

elif menu == "Projects":

    st.header("Projects")

    projects = requests.get(f"{API}/projects").json()
    df = pd.DataFrame(projects)

    st.dataframe(df)

    st.subheader("Remove Project")

    if len(df) > 0:

        project_id = st.selectbox(
            "Select Project to Remove",
            df["id"]
        )

        if st.button("Delete Project"):

            requests.delete(f"{API}/projects/{project_id}")

            st.success("Project removed")
            st.rerun()

    st.subheader("Add Project")

    project = st.text_input("Project Name")
    python = st.slider("Python Weight",1,5)
    ml = st.slider("ML Weight",1,5)

    if st.button("Add Project"):

        data = {
            "project_name": project,
            "Python": python,
            "ML": ml
        }

        requests.post(f"{API}/projects", json=data)

        st.success("Project added")
        st.rerun()


# ---------------- MATCH SCORES ----------------

elif menu == "Match Scores":

    st.header("Compatibility Matrix")

    scores = pd.read_csv("student_project_final_scores.csv")

    st.dataframe(scores)


# ---------------- TEAMS ----------------

elif menu == "Teams":

    st.header("Suggested Teams")

    teams = pd.read_csv("project_teams.csv")

    st.dataframe(teams)

    if st.button("Recompute Teams"):

        requests.post(f"{API}/recompute")

        st.success("Teams recomputed")
        st.rerun()