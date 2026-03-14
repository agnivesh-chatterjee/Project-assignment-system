## team_formation.py
import pandas as pd
import subprocess
import itertools
from pulp import (
    LpProblem, LpMaximize, LpVariable, lpSum, LpBinary,
    PULP_CBC_CMD, value, LpStatus
)


def generate_scores():
    result = subprocess.run(
        ["python", "matchscore generator.py"],
        capture_output=True,
        text=True
    )

    print(result.stdout)
    print(result.stderr)

    if result.returncode != 0:
        raise RuntimeError("Match score generator failed")


def form_teams():
    # Step 1: generate latest scores
    generate_scores()

    # ============================================================
    # CONFIG
    # ============================================================
    SCORES_FILE = "../database/student_project_final_scores.csv"
    STUDENTS_FILE = "../database/students.csv"
    PROJECTS_FILE = "../database/projects.csv"
    OUTPUT_FILE = "optimal_project_teams.csv"

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

    # Expected:
    # scores_df: student, project, final_score
    # students_df: name, college, resume_link, github_link, python, ml, api, frontend, data, systems, viz, devops, preference
    # projects_df: project_name, description, difficulty, python, ml, apis, frontend, data, systems, viz, devops

    # Rename project skill columns to canonical names
    project_rename = {}
    for c in projects_df.columns:
        mapped = get_project_skill_col(c)
        if mapped in SKILLS and c != mapped:
            project_rename[c] = mapped
    projects_df = projects_df.rename(columns=project_rename)

    # Rename student skill columns to canonical names
    student_rename = {}
    for c in students_df.columns:
        mapped = get_student_skill_col(c)
        if mapped in SKILLS and c != mapped:
            student_rename[c] = mapped
    students_df = students_df.rename(columns=student_rename)

    students_df = coerce_numeric(students_df, [c for c in SKILLS if c in students_df.columns])
    projects_df = coerce_numeric(projects_df, [c for c in SKILLS if c in projects_df.columns])
    scores_df["final_score"] = pd.to_numeric(scores_df["final_score"], errors="coerce").fillna(0)

    # Clean names
    students_df["name"] = students_df["name"].astype(str).str.strip()
    projects_df["project_name"] = projects_df["project_name"].astype(str).str.strip()
    scores_df["student"] = scores_df["student"].astype(str).str.strip()
    scores_df["project"] = scores_df["project"].astype(str).str.strip()

    # Keep only valid student/project combinations
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

    # Fill missing score pairs with 0
    for s in students:
        for p in projects:
            if (s, p) not in score_lookup:
                score_lookup[(s, p)] = 0.0

    # ============================================================
    # TEAM SCORING
    # ============================================================

    def complementarity_bonus(student_a, student_b, project):
        wa = project_weight[project]
        sa = student_skill[student_a]
        sb = student_skill[student_b]

        weighted_abs_diff = 0.0
        total_weight = 0.0

        for sk in SKILLS:
            w = wa.get(sk, 0.0)
            total_weight += w
            weighted_abs_diff += w * abs(sa.get(sk, 0.0) - sb.get(sk, 0.0))

        if total_weight == 0:
            return 0.0

        normalized = weighted_abs_diff / total_weight
        return COMPLEMENTARITY_WEIGHT * normalized

    def pair_project_score(student_a, student_b, project):
        base_score = (
            score_lookup[(student_a, project)] +
            score_lookup[(student_b, project)]
        )
        bonus = complementarity_bonus(student_a, student_b, project)
        final_score = base_score + bonus
        return final_score, base_score, bonus

    def solo_project_score(student, project):
        return score_lookup[(student, project)]

    # ============================================================
    # BUILD CANDIDATES
    # ============================================================

    student_pairs = list(itertools.combinations(students, 2))

    pair_data = []
    for s1, s2 in student_pairs:
        for p in projects:
            final_score, base_score, bonus = pair_project_score(s1, s2, p)
            pair_data.append({
                "s1": s1,
                "s2": s2,
                "project": p,
                "final_score": final_score,
                "base_score": base_score,
                "bonus": bonus
            })

    solo_data = []
    if ALLOW_SINGLE_MEMBER_TEAMS:
        for s in students:
            for p in projects:
                solo_data.append({
                    "student": s,
                    "project": p,
                    "final_score": solo_project_score(s, p)
                })

    # ============================================================
    # ILP MODEL
    # ============================================================

    model = LpProblem("Project_Student_Team_Formation", LpMaximize)

    pair_vars = {}
    for idx, row in enumerate(pair_data):
        pair_vars[idx] = LpVariable(f"pair_{idx}", cat=LpBinary)

    solo_vars = {}
    if ALLOW_SINGLE_MEMBER_TEAMS:
        for idx, row in enumerate(solo_data):
            solo_vars[idx] = LpVariable(f"solo_{idx}", cat=LpBinary)

    active_vars = {p: LpVariable(f"active_{p}", cat=LpBinary) for p in projects}

    objective_terms = []
    for idx, row in enumerate(pair_data):
        objective_terms.append(row["final_score"] * pair_vars[idx])

    if ALLOW_SINGLE_MEMBER_TEAMS:
        for idx, row in enumerate(solo_data):
            objective_terms.append(row["final_score"] * solo_vars[idx])

    model += lpSum(objective_terms)

    # Each student used at most once
    for s in students:
        terms = []

        for idx, row in enumerate(pair_data):
            if row["s1"] == s or row["s2"] == s:
                terms.append(pair_vars[idx])

        if ALLOW_SINGLE_MEMBER_TEAMS:
            for idx, row in enumerate(solo_data):
                if row["student"] == s:
                    terms.append(solo_vars[idx])

        model += lpSum(terms) <= 1, f"student_once_{s}"

    if not ALLOW_SINGLE_MEMBER_TEAMS:
        for p in projects:
            pair_terms = [pair_vars[idx] for idx, row in enumerate(pair_data) if row["project"] == p]
            model += lpSum(pair_terms) == active_vars[p], f"project_pair_exactly_one_pair_if_active_{p}"
    else:
        for p in projects:
            pair_terms = [pair_vars[idx] for idx, row in enumerate(pair_data) if row["project"] == p]
            solo_terms = [solo_vars[idx] for idx, row in enumerate(solo_data) if row["project"] == p]
            model += lpSum(pair_terms) + lpSum(solo_terms) == active_vars[p], f"project_one_team_if_active_{p}"

    max_full_projects = len(students) // 2
    model += lpSum(active_vars[p] for p in projects) <= len(projects), "project_count_upper"

    if not ALLOW_SINGLE_MEMBER_TEAMS:
        model += lpSum(active_vars[p] for p in projects) <= max_full_projects, "max_active_projects_by_students"

    # ============================================================
    # SOLVE
    # ============================================================

    model.solve(PULP_CBC_CMD(msg=SOLVER_MSG))

    if LpStatus[model.status] not in {"Optimal", "Integer Feasible"}:
        raise RuntimeError(f"Solver did not find a valid solution. Status: {LpStatus[model.status]}")

    # ============================================================
    # EXTRACT FINAL TEAMS
    # ============================================================

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

    print(f"Solution status: {LpStatus[model.status]}")
    print(f"Output written to: {OUTPUT_FILE}")
    print(f"Projects assigned: {len(output_df)} / {len(projects)}")
    print(f"Assigned students: {2 * len(output_df)} / {len(students)}")
    print(f"Objective value: {value(model.objective):.4f}")

    return output_df

if __name__ == "__main__":
    form_teams()
