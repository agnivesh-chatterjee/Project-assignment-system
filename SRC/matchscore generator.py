## matchscore generator
import pandas as pd

students = pd.read_csv("students.csv")
projects = pd.read_csv("projects.csv")

# Normalize project skill column names
projects = projects.rename(columns={
    "Python":"python",
    "ML":"ml",
    "APIs":"api",
    "Frontend":"frontend",
    "Data":"data",
    "Systems":"systems",
    "Viz":"viz",
    "DevOps":"devops"
})

skills = ["python","ml","api","frontend","data","systems","viz","devops"]

# Compute compatibility matrix
student_skill_matrix = students[skills].values
project_weight_matrix = projects[skills].values

score_matrix = student_skill_matrix @ project_weight_matrix.T

score_df = pd.DataFrame(
    score_matrix,
    index=students["name"],
    columns=projects["project_name"]
)

# Convert to long format
matches = score_df.reset_index().melt(
    id_vars="name",
    var_name="project",
    value_name="match_score"
)

matches.rename(columns={"name":"student"}, inplace=True)

# Merge student preferences
matches = matches.merge(
    students[["name","pref1","pref2","pref3"]],
    left_on="student",
    right_on="name"
)

# Compute preference bonus
def get_bonus(row):
    if row["project"] == row["pref1"]:
        return 10
    elif row["project"] == row["pref2"]:
        return 5
    elif row["project"] == row["pref3"]:
        return 2
    else:
        return 0

matches["preference_bonus"] = matches.apply(get_bonus, axis=1)

# Final score
matches["final_score"] = matches["match_score"] + matches["preference_bonus"]

# Clean dataframe
matches = matches[["student","project","match_score","preference_bonus","final_score"]]

print(matches.head())

# Save results
matches.to_csv("student_project_final_scores.csv", index=False)