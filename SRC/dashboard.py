## dashboard.py
import streamlit as st
import requests
import pandas as pd
from pathlib import Path
import os
import time

API = os.getenv("API_BASE_URL", "https://project-assignment-system-krrk.onrender.com")


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
        resp = requests.get(f"{API}/students", timeout=30)
        resp.raise_for_status()
        students = resp.json()
        df = pd.DataFrame(students)
    except Exception as e:
        st.error(f"Failed to load students: {e}")
        df = pd.DataFrame()

    st.dataframe(df, use_container_width=True)

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


    with st.form("student_form",clear_on_submit = True):

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
            if name.strip() == "":
                st.error("Student name cannot be empty")
                st.stop()
                
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
                with st.spinner("Adding student and recomputing teams..."):
                    add_resp = requests.post(f"{API}/students", json=payload, timeout=30)
                    add_resp.raise_for_status()

                st.success("Student added")
                st.rerun()
        
            except Exception as e:
                st.error(f"Add student failed: {e}")



# ---------------- PROJECTS ----------------

elif menu == "Projects":
    st.header("Projects")

    try:
        resp = requests.get(f"{API}/projects", timeout=30)
        resp.raise_for_status()
        projects = resp.json()
        df = pd.DataFrame(projects)
    except Exception as e:
        st.error(f"Failed to load projects: {e}")
        df = pd.DataFrame()

    st.dataframe(df, use_container_width=True)

    st.subheader("Remove Project")

    if not df.empty and "project_name" in df.columns:

        project_name = st.selectbox(
            "Select Project to Remove",
            df["project_name"]
        )

        if st.button("Delete Project"):
            try:
                with st.spinner("Removing project and recomputing teams..."):
                    delete_resp = requests.delete(f"{API}/projects/{project_name}", timeout=30)
                    delete_resp.raise_for_status()

                st.success("Project removed")
                st.rerun()

            except Exception as e:
                st.error(f"Delete project failed: {e}")


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
        if project.strip() == "":
            st.error("Project name cannot be empty")
            st.stop()
            
        payload = {
            "project_name": project.strip(),
            "Python": python_weight,
            "ML": ml,
            "APIs": api,
            "Frontend": frontend,
            "Data": data_weight,
            "Systems": systems,
            "Viz": viz,
            "DevOps": devops
        }
        
        try:
            with st.spinner("Adding project and recomputing teams..."):
                add_resp = requests.post(f"{API}/projects", json=payload, timeout=30)
                add_resp.raise_for_status()
            
            st.success("Project added")
            st.rerun()
        
        except Exception as e:
            st.error(f"Add project failed: {e}")



# ---------------- MATCH SCORES ----------------

elif menu == "Match Scores":

    st.header("Compatibility Matrix")

    try:
        with st.spinner("Loading compatibility scores..."):
            scores = requests.get(f"{API}/scores",timeout=30)
            scores.raise_for_status()
            df = pd.DataFrame(scores.json())

        st.dataframe(
            df.style.background_gradient(cmap="viridis"),
            use_container_width=True
        )

    except Exception as e:
        st.warning("Compatibility scores not generated yet.")
        st.write(e)

# ---------------- TEAMS ----------------

elif menu == "Teams":

    st.header("Suggested Teams")
    
    if st.button("Recompute Teams"):
        try:
            with st.spinner("Recomputing teams..."):
                resp = requests.post(f"{API}/recompute",timeout=30)
                resp.raise_for_status()
                data = resp.json()
                if data.get("status") == "already_running":
                    st.warning("Recompute is already running.")
                else:
                    st.success("Recompute started in background.")
        except Exception as e:
            st.error(f"Failed to start recompute: {e}")

    recompute_info = None
    
    try:
        status_resp = requests.get(f"{API}/recompute-status",timeout=15)
        status_resp.raise_for_status()
        recompute_info = status_resp.json()

        st.write(f"Recompute status:{recompute_info.get('status','unknown')}")
        if recompute_info.get("detail"):
            st.write(recompute_info["detail"])
        #AUTO REFRESH WHEN DONE
        if recompute_info.get("status") == "success":
            st.success("Teams ready. Reloading...")
            st.rerun()
    except Exception as e:
        st.warning("Could not fetch recompute status:")
        st.write(e)

    if recompute_info and recompute_info.get("status")=="running":
        st.info("Recompute is still running.Waiting for updated teams...")
        time.sleep(5)
        st.rerun()
        st.stop()

    if recompute_info and recompute_info.get("status") == "success":
        st.success("Teams ready.")

    try:
        with st.spinner("Loading teams..."):
            teams = requests.get(f"{API}/teams",timeout=60)
            teams.raise_for_status()
            df = pd.DataFrame(teams.json())

        st.dataframe(df, use_container_width=True)

    except Exception as e:
        st.error("Failed to loead teams.")
        st.write(e)
