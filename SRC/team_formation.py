## team formation
import pandas as pd
import subprocess
import itertools
import os
import sys
from pulp import (
    LpProblem, LpMaximize, LpVariable, lpSum, LpBinary,
    PULP_CBC_CMD, value, LpStatus
)

# ============================================================
# PATH SETUP
# ============================================================

BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "database")

SCORES_FILE = os.path.join(DATA_DIR, "student_project_final_scores.csv")
STUDENTS_FILE = os.path.join(DATA_DIR, "students.csv")
PROJECTS_FILE = os.path.join(DATA_DIR, "projects.csv")
OUTPUT_FILE = os.path.join(DATA_DIR, "project_teams.csv")


# ============================================================
# GENERATE MATCH SCORES
# ============================================================

def generate_scores():

    result = subprocess.run(
        [sys.executable, os.path.join(BASE_DIR, "SRC", "matchscore_generator.py")],
        capture_output=True,
        text=True,
        cwd=BASE_DIR
    )

    print(result.stdout)
    print(result.stderr)

    if result.returncode != 0:
        raise RuntimeError("Match score generator failed")


# ============================================================
# TEAM FORMATION
# ============================================================

def form_teams():

    # Step 1: generate latest scores
    generate_scores()

    # ============================================================
    # CONFIG
    # ============================================================

    ALLOW_SINGLE_MEMBER_TEAMS = False
    COMPLEMENTARITY_WEIGHT = 0.15
    SOLVER_MSG = False

    # ============================================================
    # HELPERS
    # ============================================================

    SKILL_MAP_STUDENTS = {
        "python": "python",
        "ml": "ml",
        "apis": "api",
        "api": "api",
        "frontend": "frontend",
        "data": "data",
        "systems": "systems",
        "viz": "viz",
        "devops": "devops",
    }

    SKILL_MAP_PROJECTS = {
        "python": "python",
        "ml": "ml",
        "apis": "api",
        "api": "api",
        "frontend": "frontend",
        "data": "data",
        "systems": "systems",
        "viz": "viz",
        "devops": "devops",
    }

    SKILLS = ["python", "ml", "api", "frontend", "data", "systems", "viz", "devops"]

    def normalize_columns(df: pd.DataFrame) -> pd.DataFrame:
        df = df.copy()
        df.columns = (
            df.columns.str.strip()
            .str.lower()
            .str.replace(" ", "_", regex=False)
            .str.replace("/", "", regex=False)
            .str.replace("-", "_", regex=False)
        )
        return df

    def coerce_numeric(df: pd.DataFrame, cols):
        for c in cols:
            if c in df.columns:
                df[c] = pd.to_numeric(df[c], errors="coerce").fillna(0)
        return df

    def get_student_skill_col(col_name: str):
        c = col_name.strip().lower().replace(" ", "_")
        return SKILL_MAP_STUDENTS.get(c, c)

    def get_project_skill_col(col_name: str):
        c = col_name.strip().lower().replace(" ", "_")
        return SKILL_MAP_PROJECTS.get(c, c)

    # ============================================================
    # LOAD DATA
    # ============================================================

    scores_df = pd.read_csv(SCORES_FILE)
    students_df = pd.read_csv(STUDENTS_FILE)
    projects_df = pd.read_csv(PROJECTS_FILE)

    scores_df = normalize_columns(scores_df)
    students_df = normalize_columns(students_df)
    projects_df = normalize_columns(projects_df)

    project_rename = {}
    for c in projects_df.columns:
        mapped = get_project_skill_col(c)
        if mapped in SKILLS and c != mapped:
            project_rename[c] = mapped
    projects_df = projects_df.rename(columns=project_rename)

    student_rename = {}
    for c in students_df.columns:
        mapped = get_student_skill_col(c)
        if mapped in SKILLS and c != mapped:
            student_rename[c] = mapped
    students_df = students_df.rename(columns=student_rename)

    students_df = coerce_numeric(students_df, [c for c in SKILLS if c in students_df.columns])
    projects_df = coerce_numeric(projects_df, [c for c in SKILLS if c in projects_df.columns])
    scores_df["final_score"] = pd.to_numeric(scores_df["final_score"], errors="coerce").fillna(0)

    students_df["name"] = students_df["name"].astype(str).str.strip()
    projects_df["project_name"] = projects_df["project_name"].astype(str).str.strip()
    scores_df["student"] = scores_df["student"].astype(str).str.strip()
    scores_df["project"] = scores_df["project"].astype(str).str.strip()

    valid_students = set(students_df["name"])
    valid_projects = set(projects_df["project_name"])

    scores_df = scores_df[
        scores_df["student"].isin(valid_students) &
        scores_df["project"].isin(valid_projects)
    ].copy()

    students = sorted(scores_df["student"].unique().tolist())
    projects = sorted(projects_df["project_name"].unique().tolist())

    if len(students) == 0:
        raise ValueError("No valid students found after merging files.")
    if len(projects) == 0:
        raise ValueError("No valid projects found after merging files.")

    # ============================================================
    # BUILD LOOKUPS
    # ============================================================

    score_lookup = {}
    for _, row in scores_df.iterrows():
        score_lookup[(row["student"], row["project"])] = float(row["final_score"])

    student_skill = {}
    for _, row in students_df.iterrows():
        name = str(row["name"])
        student_skill[name] = {s: float(row[s]) if s in row.index else 0.0 for s in SKILLS}

    project_weight = {}
    for _, row in projects_df.iterrows():
        pname = str(row["project_name"])
        project_weight[pname] = {s: float(row[s]) if s in row.index else 0.0 for s in SKILLS}

    for s in students:
        for p in projects:
            if (s, p) not in score_lookup:
                score_lookup[(s, p)] = 0.0

    # ============================================================
    # BUILD TEAMS
    # ============================================================

    student_pairs = list(itertools.combinations(students, 2))

    pair_data = []
    for s1, s2 in student_pairs:
        for p in projects:
            final_score = score_lookup[(s1, p)] + score_lookup[(s2, p)]
            pair_data.append({
                "s1": s1,
                "s2": s2,
                "project": p,
                "final_score": final_score
            })

    model = LpProblem("Project_Student_Team_Formation", LpMaximize)

    pair_vars = {}
    for idx, row in enumerate(pair_data):
        pair_vars[idx] = LpVariable(f"pair_{idx}", cat=LpBinary)

    model += lpSum(row["final_score"] * pair_vars[idx] for idx, row in enumerate(pair_data))

    for s in students:
        terms = []
        for idx, row in enumerate(pair_data):
            if row["s1"] == s or row["s2"] == s:
                terms.append(pair_vars[idx])
        model += lpSum(terms) <= 1

    for p in projects:
        terms = [pair_vars[idx] for idx, row in enumerate(pair_data) if row["project"] == p]
        model += lpSum(terms) <= 1

    model.solve(PULP_CBC_CMD(msg=SOLVER_MSG))

    selected_pairs = []
    for idx, var in pair_vars.items():
        if value(var) > 0.5:
            selected_pairs.append(pair_data[idx])

    rows = []
    for row in selected_pairs:
        rows.append({
            "Project Name": row["project"],
            "Student 1": row["s1"],
            "Student 2": row["s2"]
        })

    output_df = pd.DataFrame(rows)
    output_df = output_df.sort_values(by="Project Name")

    output_df.to_csv(OUTPUT_FILE, index=False)

    print(f"Output written to: {OUTPUT_FILE}")

    return output_df


if __name__ == "__main__":
    form_teams()
