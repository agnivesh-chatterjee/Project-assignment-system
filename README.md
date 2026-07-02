# Intelligent Project Assignment System

> An optimization-based project allocation system that automatically matches students to projects based on skills, preferences, and project requirements.

Developed as a full-stack decision support system, this project combines **optimization**, **linear programming**, **backend API development**, and **interactive dashboards** to automate project assignments while maximizing overall assignment quality.

---

## Overview

Assigning students to projects is a constrained optimization problem involving multiple competing objectives:

- Match student skills with project requirements
- Respect student project preferences
- Maximize overall assignment quality
- Maintain project capacity constraints
- Encourage balanced team formation

This system models the assignment problem as an **Integer Linear Programming (ILP)** optimization task. A compatibility score is computed for every student-project pair, after which an optimization solver generates the assignment that maximizes the total objective score.

The project includes a complete end-to-end workflow:

- Student management
- Project management
- Match score generation
- Optimization-based team formation
- REST API backend
- Interactive Streamlit dashboard

---

# Features

## Student Management

- Add new student profiles
- Delete existing students
- Store student skill profiles
- Record project preferences
- Store portfolio links (GitHub, Resume)

Each student profile includes skill ratings across multiple technical domains.

---

## Project Management

- Create new projects
- Remove projects
- Define required skill weights
- Maintain project database

Projects specify the importance of different technical skills, allowing the system to identify the most suitable candidates.

---

## Match Score Generation

A compatibility score is computed for every student-project pair using:

- Student skill vector
- Project requirement vector
- Preference bonuses

The scoring process consists of:

### Skill Matching

Student skills and project requirements are represented as vectors.

Compatibility is computed using matrix multiplication:

```
Score = Student Skills × Project Requirements
```

### Preference Bonus

Additional points are awarded based on project preferences.

| Preference | Bonus |
|------------|------:|
| First Choice | +10 |
| Second Choice | +5 |
| Third Choice | +2 |

Final score:

```
Final Score = Skill Match + Preference Bonus
```

The resulting compatibility matrix is stored for downstream optimization.

---

# Team Formation

The assignment engine formulates project allocation as an **Integer Linear Programming** problem.

The optimizer considers:

- Student-project compatibility
- Project capacity constraints
- One project per student
- Team size limits
- Pair assignments
- Single-member penalties

The optimization objective maximizes the total assignment score while minimizing undesirable assignments.

The project uses the **PuLP** optimization library with the **CBC solver**.

---

# Dashboard

A Streamlit dashboard provides an interface for managing the system.

Available tabs include:

- Students
- Projects
- Match Scores
- Final Teams

The dashboard supports:

- Live student management
- Live project management
- Automatic score recomputation
- Team regeneration
- Interactive data tables

---

# REST API

The backend is implemented using **FastAPI**.

Available endpoints include:

## Students

- `GET /students`
- `POST /students`
- `DELETE /students/{name}`

## Projects

- `GET /projects`
- `POST /projects`
- `DELETE /projects/{project_name}`

## Match Scores

- `GET /scores`

## Team Formation

- Trigger optimization
- Monitor recomputation status
- Retrieve generated teams

The backend automatically updates the underlying datasets after each modification.

---

# Repository Structure

```
Project-assignment-system
│
├── SRC/
│   ├── main.py                    # FastAPI backend
│   ├── dashboard.py               # Streamlit dashboard
│   ├── matchscore_generator.py    # Compatibility scoring
│   ├── team_formation.py          # Optimization engine
│   ├── student_database_generator.py
│   ├── project_database_generator.py
│   └── form.html
│
├── database/
│   ├── students.csv
│   ├── projects.csv
│   ├── student_project_final_scores.csv
│   └── project_teams.csv
│
├── requirements.txt
└── runtime.txt
```

---

# Technologies Used

### Backend

- FastAPI
- Python

### Frontend

- Streamlit

### Data Processing

- Pandas
- NumPy

### Optimization

- PuLP
- CBC Solver
- Integer Linear Programming

---

# Optimization Workflow

```text
Student Database
        │
        ▼
Project Database
        │
        ▼
Compatibility Matrix Generation
        │
        ▼
Preference Bonus Integration
        │
        ▼
Final Match Scores
        │
        ▼
Integer Linear Programming Solver
        │
        ▼
Optimal Team Assignment
        │
        ▼
Interactive Dashboard
```

---

# Design Highlights

- Modular architecture
- Separation of scoring and optimization
- Automatic recomputation pipeline
- RESTful API
- Interactive web dashboard
- Optimization-driven decision making
- CSV-based persistent storage

---

# Collaborators

Developed collaboratively by:

- **Anupam Dasgupta**
- **Agnivesh Chatterjee**
