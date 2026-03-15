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

    print("generate_scores: subprocess finished", flush=True)
    print("generate_scores stdout:", result.stdout, flush=True)
    print("generate_scores stderr:", result.stderr, flush=True)
    print(f"generate_scores returncode: {result.returncode}", flush=True)

    if result.returncode != 0:
        raise RuntimeError(f"Match score generator failed: {result.stderr}")


# ============================================================
# TEAM FORMATION
# ============================================================

def form_teams():

    PAIR_ASSIGN_BONUS = 10
    SINGLE_PENALTY = 1000

    print("form_teams: entered", flush=True)

    # Step 1: generate latest scores
    generate_scores()

    print("form_teams: scores generated", flush=True)

    # ============================================================
    # LOAD DATA
    # ============================================================

    scores_df = pd.read_csv(SCORES_FILE)
    students_df = pd.read_csv(STUDENTS_FILE)
    projects_df = pd.read_csv(PROJECTS_FILE)

    scores_df.columns = scores_df.columns.str.strip().str.lower()
    students_df.columns = students_df.columns.str.strip().str.lower()
    projects_df.columns = projects_df.columns.str.strip().str.lower()

    students_df["name"] = students_df["name"].astype(str).str.strip()
    projects_df["project_name"] = projects_df["project_name"].astype(str).str.strip()
    scores_df["student"] = scores_df["student"].astype(str).str.strip()
    scores_df["project"] = scores_df["project"].astype(str).str.strip()

    scores_df["final_score"] = pd.to_numeric(scores_df["final_score"], errors="coerce").fillna(0)

    valid_students = set(students_df["name"])
    valid_projects = set(projects_df["project_name"])

    scores_df = scores_df[
        scores_df["student"].isin(valid_students) &
        scores_df["project"].isin(valid_projects)
    ].copy()

    students = sorted(scores_df["student"].unique().tolist())
    projects = sorted(projects_df["project_name"].unique().tolist())

    if len(students) > 2 * len(projects):
        raise ValueError(
            f"Infeasible assignment: {len(students)} students but only {len(projects)} projects. "
            f"Max capacity is {2 * len(projects)}."
        )

    print(f"form_teams: students={len(students)}, projects={len(projects)}", flush=True)

    # ============================================================
    # BUILD LOOKUPS
    # ============================================================

    score_lookup = {}
    for _, row in scores_df.iterrows():
        score_lookup[(row["student"], row["project"])] = float(row["final_score"])

    for s in students:
        for p in projects:
            if (s, p) not in score_lookup:
                score_lookup[(s, p)] = 0.0

    # ============================================================
    # BUILD PAIR TEAMS
    # ============================================================

    pair_data = []

    # FIXED: dynamic cap instead of hard 15
    top_students_per_project = min(len(students), 30)

    for p in projects:

        project_scores = [(s, score_lookup[(s, p)]) for s in students]
        project_scores.sort(key=lambda x: x[1], reverse=True)

        top_students = [s for s, _ in project_scores[:top_students_per_project]]

        for s1, s2 in itertools.combinations(top_students, 2):

            final_score = score_lookup[(s1, p)] + score_lookup[(s2, p)]

            pair_data.append({
                "s1": s1,
                "s2": s2,
                "project": p,
                "final_score": final_score
            })

    pair_data = pd.DataFrame(pair_data).reset_index(drop=True)

    print(f"form_teams: pair rows = {len(pair_data)}", flush=True)

    # ============================================================
    # SINGLE ASSIGNMENTS
    # ============================================================

    single_data = []

    for s in students:
        for p in projects:
            single_data.append({
                "student": s,
                "project": p,
                "final_score": score_lookup[(s, p)] - SINGLE_PENALTY
            })

    single_data = pd.DataFrame(single_data).reset_index(drop=True)

    # ============================================================
    # BUILD OPTIMIZATION MODEL
    # ============================================================

    model = LpProblem("Project_Student_Team_Formation", LpMaximize)

    pair_vars = {
        idx: LpVariable(f"pair_{idx}", cat=LpBinary)
        for idx in pair_data.index
    }

    single_vars = {
        idx: LpVariable(f"single_{idx}", cat=LpBinary)
        for idx in single_data.index
    }

    # FIXED OBJECTIVE (no double penalty)

    model += (
        lpSum((row["final_score"] + PAIR_ASSIGN_BONUS) * pair_vars[idx]
              for idx, row in pair_data.iterrows())
        +
        lpSum(row["final_score"] * single_vars[idx]
              for idx, row in single_data.iterrows())
    )

    # ============================================================
    # CONSTRAINTS
    # ============================================================

    # Each student exactly once

    for s in students:

        pair_terms = [
            pair_vars[idx]
            for idx, row in pair_data.iterrows()
            if row["s1"] == s or row["s2"] == s
        ]

        single_terms = [
            single_vars[idx]
            for idx, row in single_data.iterrows()
            if row["student"] == s
        ]

        model += lpSum(pair_terms + single_terms) == 1

    # Each project ≤ 1 team

    for p in projects:

        pair_terms = [
            pair_vars[idx]
            for idx, row in pair_data.iterrows()
            if row["project"] == p
        ]

        single_terms = [
            single_vars[idx]
            for idx, row in single_data.iterrows()
            if row["project"] == p
        ]

        model += lpSum(pair_terms + single_terms) <= 1

    # ============================================================
    # SOLVE
    # ============================================================

    print("form_teams: solving model", flush=True)

    status = model.solve(PULP_CBC_CMD(msg=False))

    status_str = LpStatus[status]

    print(f"Solver status: {status_str}", flush=True)

    if status_str not in ["Optimal", "Feasible"]:
        raise RuntimeError(f"Solver did not return a solution. Status: {status_str}")

    # ============================================================
    # EXTRACT RESULTS
    # ============================================================

    selected_pairs = [
        pair_data.iloc[idx]
        for idx, var in pair_vars.items()
        if value(var) > 0.5
    ]

    selected_singles = [
        single_data.iloc[idx]
        for idx, var in single_vars.items()
        if value(var) > 0.5
    ]

    rows = []

    for row in selected_pairs:
        rows.append({
            "Project Name": row["project"],
            "Student 1": row["s1"],
            "Student 2": row["s2"]
        })

    for row in selected_singles:
        rows.append({
            "Project Name": row["project"],
            "Student 1": row["student"],
            "Student 2": ""
        })

    output_df = pd.DataFrame(rows).sort_values(by="Project Name").reset_index(drop=True)

    # ============================================================
    # SAVE OUTPUT
    # ============================================================

    temp_output = OUTPUT_FILE + ".tmp"

    output_df.to_csv(temp_output, index=False)

    os.replace(temp_output, OUTPUT_FILE)

    print(f"Output written to: {OUTPUT_FILE}", flush=True)

    return output_df


if __name__ == "__main__":
    form_teams()
