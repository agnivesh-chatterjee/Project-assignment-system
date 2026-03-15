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
    print(result.stdout)
    print(result.stderr)

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
    # CONFIG
    # ============================================================

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

    print("form_teams: reading csv files", flush=True)

    scores_df = pd.read_csv(SCORES_FILE)
    students_df = pd.read_csv(STUDENTS_FILE)
    projects_df = pd.read_csv(PROJECTS_FILE)

    print("form_teams: csv files loaded", flush=True)
    
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

    if len(students) > 2 * len(projects):
        raise ValueError(
            f"Infeasible assignment: {len(students)} students but only {len(projects)} projects. "
            f"Max capacity is {2 * len(projects)}."
        )

    print(f"form_teams: students={len(students)}, projects={len(projects)}", flush=True)


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
    top_students_per_project = 15
    for p in projects:
        project_scores = [(s,score_lookup[(s,p)]) for s in students]
        project_scores.sort(key=lambda x: x[1],reverse=True)
        top_students = [s for s,_ in project_scores[:top_students_per_project]]
        for s1,s2 in itertools.combinations(top_students,2):
            final_score = score_lookup[(s1, p)] + score_lookup[(s2, p)]
            pair_data.append({
                "s1": s1,
                "s2": s2,
                "project": p,
                "final_score": final_score
            })
    print(f"form_teams: pair_data rows before dataframe={len(pair_data)}", flush=True)
    pair_data = pd.DataFrame(pair_data).reset_index(drop=True)
    print(f"form_teams: pair_data rows after dataframe={len(pair_data)}", flush=True)

    #-------------Single assignments-------------------------------------------------------------------
    single_data = []

    for s in students:
        for p in projects:
            single_data.append({
                "student":s,
                "project":p,
                "final_score":score_lookup[(s,p)] - SINGLE_PENALTY})
            
    students_in_pairs = set(pair_data["s1"]).union(set(pair_data["s2"]))
    missing_students = [s for s in students if s not in students_in_pairs]
    if missing_students:
        print(f"Adding fallback singles for:{missing_students}",flush=True)
        for s in missing_students:
            best_project = max(projects,key=lambda p:score_lookup[(s,p)])
            single_data.append({
                "student":s,
                "project":best_project,
                "final_score": score_lookup[(s,best_project)] - SINGLE_PENALTY
            })

    single_data = pd.DataFrame(single_data).reset_index(drop=True)
    
    model = LpProblem("Project_Student_Team_Formation", LpMaximize)
    print("form_teams: model built", flush=True)

    pair_vars = {}
    for idx, row in pair_data.iterrows():
        pair_vars[idx] = LpVariable(f"pair_{idx}", cat=LpBinary)

    single_vars = {}
    for idx, row in single_data.iterrows():
        single_vars[idx] = LpVariable(f"single_{idx}", cat=LpBinary)

    model += lpSum((row["final_score"]+PAIR_ASSIGN_BONUS) * pair_vars[idx] for idx, row in pair_data.iterrows()) + lpSum((row["final_score"]-SINGLE_PENALTY) * single_vars[idx] for idx, row in single_data.iterrows())

       # Each student can appear in exactly one selected team
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
        model += lpSum(pair_terms + single_terms) == 1, f"student_once_{s}"

    # Each project can be assigned at most one team
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
        model += lpSum(pair_terms + single_terms) <= 1, f"project_once_{p}"

    print("form_teams: starting solver", flush=True)
    status = model.solve(PULP_CBC_CMD(msg = False))
    print(f"form_teams: solver finished with status={LpStatus[status]}", flush=True)
    status_str = LpStatus[status]
    if status_str != "Optimal":
        raise RuntimeError(f"Solver did not return an optimal solution. Status: {status_str}")

    selected_pairs = []
    for idx, var in pair_vars.items():
        if value(var) > 0.5:
            selected_pairs.append(pair_data.iloc[idx])

    selected_singles = []
    for idx, var in single_vars.items():
        if value(var) > 0.5:
            selected_singles.append(single_data.iloc[idx])
    
    print(f"form_teams: selected_pairs={len(selected_pairs)}", flush=True)

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

    output_df = pd.DataFrame(rows)
    output_df = output_df.sort_values(by="Project Name").reset_index(drop=True)

    # Hard validation: no duplicate projects, no duplicate students
    if output_df["Project Name"].duplicated().any():
        dup_projects = output_df.loc[
            output_df["Project Name"].duplicated(), "Project Name"
        ].tolist()
        raise RuntimeError(f"Duplicate project assignments found: {dup_projects}")

    assigned_students = pd.concat(
        [output_df["Student 1"], output_df["Student 2"]],
        ignore_index=True
    )
    assigned_students = assigned_students.astype(str).str.strip()
    assigned_students = assigned_students[assigned_students != ""]

    if assigned_students.duplicated().any():
        dup_students = assigned_students[assigned_students.duplicated()].tolist()
        raise RuntimeError(f"Duplicate student assignments found: {dup_students}")

    temp_output = OUTPUT_FILE + ".tmp"
    output_df.to_csv(temp_output, index=False)
    os.replace(temp_output,OUTPUT_FILE)

    print(f"Output written to: {OUTPUT_FILE}",flush=True)

    return output_df

if __name__ == "__main__":
    form_teams()
