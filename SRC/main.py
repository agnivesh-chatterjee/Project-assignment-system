import pandas as pd
from . import team_formation
import os
from fastapi import FastAPI, HTTPException, BackgroundTasks

app = FastAPI()

recompute_state = {
    "running": False,
    "status": "idle",
    "detail": ""
}

# ---------------- PATH SETUP ----------------

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "database")

students_path = os.path.join(DATA_DIR, "students.csv")
projects_path = os.path.join(DATA_DIR, "projects.csv")
scores_path = os.path.join(DATA_DIR, "student_project_final_scores.csv")
teams_path = os.path.join(DATA_DIR, "project_teams.csv")


# ---------------- SAFE CSV READ ----------------

def safe_read_csv(path):
    if not os.path.exists(path):
        return pd.DataFrame()

    try:
        return pd.read_csv(path)
    except Exception as e:
        print(f"Failed reading {path}: {e}", flush=True)
        return pd.DataFrame()


# ---------------- STUDENTS ----------------

def load_students():
    return safe_read_csv(students_path)

def save_students(df):
    df.to_csv(students_path, index=False)


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
        existing = set(students["name"].astype(str).str.strip())
        if incoming_name in existing:
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

def load_projects():
    return safe_read_csv(projects_path)

def save_projects(df):
    df.to_csv(projects_path, index=False)


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


# ---------------- SCORES ----------------

def load_scores():
    return safe_read_csv(scores_path)


@app.get("/scores")
def get_scores():
    try:
        team_formation.generate_scores()
        scores = load_scores()
        return scores.to_dict(orient="records")
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# ---------------- TEAM RECOMPUTE ----------------

def _run_recompute_task():

    import traceback

    recompute_state["running"] = True
    recompute_state["status"] = "running"
    recompute_state["detail"] = ""

    print("=== RECOMPUTE BACKGROUND START ===", flush=True)

    try:

        result = team_formation.form_teams()

        if not os.path.exists(teams_path):
            raise RuntimeError("project_teams.csv not created")

        recompute_state["running"] = False
        recompute_state["status"] = "success"
        recompute_state["detail"] = f"Teams recomputed successfully. Rows written: {len(result)}"

        print("=== RECOMPUTE SUCCESS ===", flush=True)

    except Exception as e:

        recompute_state["running"] = False
        recompute_state["status"] = "failed"
        recompute_state["detail"] = str(e)

        print("=== RECOMPUTE FAILED ===", flush=True)
        print(traceback.format_exc(), flush=True)


@app.post("/recompute")
def recompute(background_tasks: BackgroundTasks):

    if recompute_state["running"]:
        return {
            "status": "already_running",
            "detail": "Recompute already running"
        }

    background_tasks.add_task(_run_recompute_task)

    return {
        "status": "started",
        "detail": "Recompute started"
    }


@app.get("/recompute-status")
def get_recompute_status():
    return recompute_state


# ---------------- TEAMS ----------------

def load_teams():
    return safe_read_csv(teams_path)


@app.get("/teams")
def get_teams():

    try:

        # If recompute running return empty list (prevents UI crash)
        if recompute_state["running"]:
            return []

        teams = load_teams()

        if teams.empty:
            return []

        # ensure clean column names
        teams.columns = teams.columns.str.strip()

        return teams.to_dict(orient="records")

    except Exception as e:

        print("Teams endpoint failure:", e, flush=True)

        raise HTTPException(
            status_code=500,
            detail=f"Failed to load teams: {e}"
        )
