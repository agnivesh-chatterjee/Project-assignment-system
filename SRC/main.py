## main.py

from fastapi import FastAPI
import pandas as pd
import team_formation
import os

app = FastAPI()

# Locate database folder
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "database")

students_path = os.path.join(DATA_DIR, "students.csv")
projects_path = os.path.join(DATA_DIR, "projects.csv")

students = pd.read_csv(students_path)
projects = pd.read_csv(projects_path)


# ---------------- STUDENTS ----------------

@app.get("/students")
def get_students():
    return students.to_dict(orient="records")


@app.post("/students")
def add_student(student: dict):
    global students

    students = pd.concat([students, pd.DataFrame([student])], ignore_index=True)
    students.to_csv(students_path, index=False)

    return {"status": "student added"}


@app.delete("/students/{name}")
def delete_student(name: str):
    global students
    students = students[students["name"] != name]
    students.to_csv(students_path, index=False)
    return {"status": "student removed"}


# ---------------- PROJECTS ----------------

@app.get("/projects")
def get_projects():
    return projects.to_dict(orient="records")


@app.post("/projects")
def add_project(project: dict):
    global projects

    projects = pd.concat([projects, pd.DataFrame([project])], ignore_index=True)
    projects.to_csv(projects_path, index=False)

    return {"status": "project added"}


@app.delete("/projects/{project_name}")
def delete_project(project_name: str):
    global projects
    projects = projects[projects["project_name"] != project_name]
    projects.to_csv(projects_path, index=False)
    return {"status": "project removed"}


# ---------------- TEAM RECOMPUTE ----------------

@app.post("/recompute")
def recompute():
    team_formation.form_teams()
    return {"status": "teams recomputed"}
