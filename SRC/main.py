from fastapi import FastAPI
import pandas as pd
from . import team_formation
from . import matchscore_generator
import os

app = FastAPI()

# ---------------- PATH SETUP ----------------

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "database")

students_path = os.path.join(DATA_DIR, "students.csv")
projects_path = os.path.join(DATA_DIR, "projects.csv")
scores_path = os.path.join(DATA_DIR, "student_project_final_scores.csv")
teams_path = os.path.join(DATA_DIR, "project_teams.csv")

# ---------------- HELPER FUNCTIONS ----------------

def load_students():
    try:
        if os.path.exists(students_path):
            return pd.read_csv(students_path)
    except:
        pass
    return pd.DataFrame()

def save_students(df):
    df.to_csv(students_path, index=False)

def load_projects():
    try:
        if os.path.exists(projects_path):
            df = pd.read_csv(projects_path)

            # normalize column casing
            df.columns = df.columns.str.lower()

            return df
    except:
        pass
    return pd.DataFrame()

def save_projects(df):
    df.to_csv(projects_path, index=False)

def recompute_all():
    """
    Regenerate compatibility scores and optimal teams
    """
    matchscore_generator.generate_match_scores()
    team_formation.form_teams()


# ---------------- STUDENTS ----------------

@app.get("/students")
def get_students():
    students = load_students()
    return students.to_dict(orient="records")


@app.post("/students")
def add_student(student: dict):

    students = load_students()

    student_df = pd.DataFrame([student])

    students = pd.concat(
        [students, student_df],
        ignore_index=True
    )

    save_students(students)

    # recompute system
    recompute_all()

    return {"status": "student added and teams recomputed"}


@app.delete("/students/{name}")
def delete_student(name: str):

    students = load_students()

    students = students[students["name"] != name]

    save_students(students)

    # recompute system
    recompute_all()

    return {"status": "student removed and teams recomputed"}


# ---------------- PROJECTS ----------------

@app.get("/projects")
def get_projects():

    projects = load_projects()

    return projects.to_dict(orient="records")


@app.post("/projects")
def add_project(project: dict):

    projects = load_projects()

    project_df = pd.DataFrame([project])

    # normalize column names (fixes Python vs python issue)
    project_df = project_df.rename(columns={
        "Python": "python",
        "ML": "ml",
        "APIs": "api",
        "Frontend": "frontend",
        "Data": "data",
        "Systems": "systems",
        "Viz": "viz",
        "DevOps": "devops"
    })

    projects = pd.concat(
        [projects, project_df],
        ignore_index=True
    )

    save_projects(projects)

    # recompute system
    recompute_all()

    return {"status": "project added and teams recomputed"}


@app.delete("/projects/{project_name}")
def delete_project(project_name: str):

    projects = load_projects()

    projects = projects[projects["project_name"] != project_name]

    save_projects(projects)

    # recompute system
    recompute_all()

    return {"status": "project removed and teams recomputed"}


# ---------------- MATCH SCORES ----------------

@app.get("/scores")
def get_scores():

    if not os.path.exists(scores_path):
        return []

    df = pd.read_csv(scores_path)

    return df.to_dict(orient="records")


# ---------------- TEAMS ----------------

@app.get("/teams")
def get_teams():

    if not os.path.exists(teams_path):
        return []

    df = pd.read_csv(teams_path)

    return df.to_dict(orient="records")


# ---------------- MANUAL RECOMPUTE ----------------

@app.post("/recompute")
def recompute():

    recompute_all()

    return {"status": "match scores and teams recomputed"}
