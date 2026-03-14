## team_formation.py
import pandas as pd
import subprocess

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

    # Step 2: load scores
    scores = pd.read_csv("student_project_final_scores.csv")

    # Step 3: sort by best compatibility
    scores = scores.sort_values(by="final_score", ascending=False)

    assigned_students = set()
    teams = []

    # Step 4: iterate project by project
    for project in scores["project"].unique():

        project_candidates = scores[scores["project"] == project]

        team = []

        for _, row in project_candidates.iterrows():

            student = row["student"]

            if student not in assigned_students:
                team.append((student, row["final_score"]))
                assigned_students.add(student)

            if len(team) == 2:
                break

        if len(team) == 2:

            team_score = team[0][1] + team[1][1]

            teams.append({
                "project": project,
                "student1": team[0][0],
                "student2": team[1][0],
                "team_score": team_score
            })

    teams_df = pd.DataFrame(teams)

    teams_df.to_csv("project_teams.csv", index=False)

    print("\nSuggested Teams:\n")
    print(teams_df.head())

    return teams_df


if __name__ == "__main__":
    form_teams()