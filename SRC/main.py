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


def recompute_all():
    """
    Regenerates compatibility scores and optimal teams
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

    students = pd.concat(
        [students, pd.DataFrame([student])],
        ignore_index=True
    )

    save_students(students)

    # recompute scores + teams
    recompute_all()

    return {"status": "student added and teams recomputed"}


@app.delete("/students/{name}")
def delete_student(name: str):

    students = load_students()

    students = students[students["name"] != name]

    save_students(students)

    # recompute scores + teams
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

    projects = pd.concat(
        [projects, pd.DataFrame([project])],
        ignore_index=True
    )

    save_projects(projects)

    # recompute scores + teams
    recompute_all()

    return {"status": "project added and teams recomputed"}


@app.delete("/projects/{project_name}")
def delete_project(project_name: str):

    projects = load_projects()

    projects = projects[projects["project_name"] != project_name]

    save_projects(projects)

    # recompute scores + teams
    recompute_all()

    return {"status": "project removed and teams recomputed"}


# ---------------- MANUAL RECOMPUTE ----------------

@app.post("/recompute")
def recompute():

    recompute_all()

    return {"status": "match scores and teams recomputed"}
