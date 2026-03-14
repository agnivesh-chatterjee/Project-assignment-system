## main.py
from fastapi import FastAPI
import pandas as pd

app = FastAPI()

students = pd.read_csv("students.csv")
projects = pd.read_csv("projects.csv")


# ---------------- STUDENTS ----------------

@app.get("/students")
def get_students():
    return students.to_dict(orient="records")


@app.post("/students")
def add_student(student: dict):
    global students
    students = pd.concat([students, pd.DataFrame([student])])
    students.to_csv("students.csv", index=False)
    return {"status": "student added"}


@app.delete("/students/{name}")
def delete_student(name: str):
    global students
    students = students[students["name"] != name]
    students.to_csv("students.csv", index=False)
    return {"status": "student removed"}


# ---------------- PROJECTS ----------------

@app.get("/projects")
def get_projects():
    return projects.to_dict(orient="records")


@app.post("/projects")
def add_project(project: dict):
    global projects
    projects = pd.concat([projects, pd.DataFrame([project])])
    projects.to_csv("projects.csv", index=False)
    return {"status": "project added"}


@app.delete("/projects/{project_name}")
def delete_project(project_name: str):
    global projects
    projects = projects[projects["project_name"] != project_name]
    projects.to_csv("projects.csv", index=False)
    return {"status": "project removed"}