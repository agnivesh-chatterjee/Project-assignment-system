## main.py
import pandas as pd
from . import team_formation
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks

app = FastAPI()

recompute_state = {
    "running":False,
    "status":"idle",
    "detail":""
}

# ---------------- PATH SETUP ----------------

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "database")

students_path = os.path.join(DATA_DIR, "students.csv")
projects_path = os.path.join(DATA_DIR, "projects.csv")


# ---------------- HELPER FUNCTIONS ----------------

def load_students():
    if os.path.exists(students_path):
        return pd.read_csv(students_path)
    return pd.DataFrame()

def save_students(df):
    df.to_csv(students_path, index=False)

def load_projects():
    if os.path.exists(projects_path):
        return pd.read_csv(projects_path)
    return pd.DataFrame()

def save_projects(df):
    df.to_csv(projects_path, index=False)


# ---------------- STUDENTS ----------------

@app.get("/students")
def get_students():
    students = load_students()
    return students.to_dict(orient="records")


@app.post("/students")
def add_student(student: dict):
    students = load_students()

    incoming_name = str(student.get("name", "")).strip()

    if incoming_name == "":
        raise HTTPException(status_code=400, detail="Student name is required")

    if not students.empty and "name" in students.columns:
        existing_names = set(students["name"].astype(str).str.strip())
        if incoming_name in existing_names:
            raise HTTPException(status_code=400, detail="Student already exists")

    student["name"] = incoming_name

    students = pd.concat(
        [students, pd.DataFrame([student])],
        ignore_index=True
    )

    save_students(students)

    return {"status": "student added"}



@app.delete("/students/{name}")
def delete_student(name: str):

    students = load_students()

    students = students[students["name"] != name]

    save_students(students)

    return {"status": "student removed"}


# ---------------- PROJECTS ----------------

@app.get("/projects")
def get_projects():

    projects = load_projects()

    return projects.to_dict(orient="records")


@app.post("/projects")
def add_project(project: dict):

    projects = load_projects()

    projects = pd.concat(
        [projects, pd.DataFrame([project])],
        ignore_index=True
    )

    save_projects(projects)

    return {"status": "project added"}


@app.delete("/projects/{project_name}")
def delete_project(project_name: str):

    projects = load_projects()

    projects = projects[projects["project_name"] != project_name]

    save_projects(projects)

    return {"status": "project removed"}


# ---------------- TEAM RECOMPUTE ----------------
def _run_recompute_task():
    import traceback
    recompute_state["running"] = True
    recompute_state["status"] = "running"
    recompute_state["detail"] = ""

    print("=== RECOMPUTEBACKGROUND START ===",flush=True)

    try:
        result = team_formation.form_teams()
        recompute_state["running"] = False
        recompute_state["status"] = "success"
        recompute_state["detail"] = (
            f"Teams recomputed successfully. "
            f"Rows written: {0 if result is None else len(result)}"
        )
        print("=== RECOMPUTE BACKGROUND SUCCESS ===",flush=True)
    except Exception as e:
        recompute_state["running"] = False
        recompute_state["status"] = "failed"
        recompute_state["detail"] = str(e)
        print("=== RECOMPUTE BACKGROUND FAILED ===",flush=True)
        print(traceback.format_exc(),flush=True)
        
@app.post("/recompute")
def recompute(background_tasks:BackgroundTasks):
    if recompute_state["running"]:
        return {
            "status":"already_running",
            "detail":"Recompute is already in progress."
        }
    background_tasks.add_task(_run_recompute_task)
    return {
        "status" : "started",
        "detail" : "Recompute started in background."
    }

@app.get("/recompute-status")
def get_recompute_status():
    return recompute_state

scores_path = os.path.join(DATA_DIR, "student_project_final_scores.csv")
teams_path = os.path.join(DATA_DIR, "project_teams.csv")

def load_scores():
    if os.path.exists(scores_path):
        return pd.read_csv(scores_path)
    return pd.DataFrame()

def load_teams():
    if os.path.exists(teams_path):
        try:
            return pd.read_csv(teams_path)
        except Exception:
            return pd.DataFrame()
    return pd.DataFrame()


@app.get("/scores")
def get_scores():
    try:
        team_formation.generate_scores()
        scores = load_scores()
        return scores.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate scores: {e}")


@app.get("/teams")
def get_teams():
    try:
        teams = load_teams()
        if teams.empty:
            return []
            
        return teams.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500,detail=f"Failed to load teams:{e}")
