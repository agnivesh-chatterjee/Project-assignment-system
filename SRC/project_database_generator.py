## second database generator
import pandas as pd
import random
import os

# Locate database folder
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "database")

projects = [

"Real-Time Flight Tracker",
"Global Ship Radar – Strait of Hormuz & Arabian Sea",
"Real-Time Satellite Tracker",
"Satellites Over My City Predictor",
"Global Cyber Attack Map",
"Urban Intelligence Dashboard",
"Fake News & Narrative Tracker",
"Satellite Collision Risk Detector",
"Skill Intelligence Dashboard App",
"Task Continuity Analysis System",
"AI-Based Soft Skills Analyzer",
"Hands-On Persona Evaluation",
"Debugging Skill Evaluator",
"Global Social Media Activity Map",
"Internship Project Selection and Team Formation",
"Global Earthquake Activity Monitor",
"Real-Time Air Traffic Density Map",
"Global Climate Anomaly Tracker",
"Global Power Outage Map",
"Global Pandemic Surveillance Dashboard",
"Resume Skill Extractor using NLP",
"Job Market Trend Analyzer",
"AI Research Paper Recommendation System",
"Automated Code Review Assistant",
"GitHub Repository Quality Analyzer",
"Interactive Global Population Dashboard",
"Global Renewable Energy Map",
"Smart City Traffic Visualization",
"Global Internet Connectivity Map",
"World Economic Indicators Explorer",
"Global Ransomware Attack Tracker",
"Dark Web Threat Intelligence Dashboard",
"Phishing Email Detection System",
"Network Intrusion Detection Visualizer",
"Malware Propagation Simulation",
"Space Debris Tracking Dashboard",
"Satellite Communication Coverage Map",
"Launch Event Tracker for Space Missions",
"ISS Visibility Predictor",
"Orbital Path Visualization Tool",
"Online Toxicity Detection System",
"Social Media Sentiment Heatmap",
"Global Misinformation Spread Analyzer",
"Digital Persona Classification System",
"News Bias Detection Dashboard",
"Distributed System Failure Simulator",
"Microservice Latency Monitoring Dashboard",
"API Dependency Visualizer",
"Cloud Resource Usage Analyzer",
"Real-Time Log Analytics Platform"
]

descriptions = [
"Real-time visualization and analysis dashboard",
"AI-powered analytics platform",
"Large-scale global data monitoring system",
"Interactive map-based data explorer",
"Machine learning prediction and analysis tool"
]

rows = []

for p in projects:

    rows.append({

        "project_name": p,
        "description": random.choice(descriptions),
        "difficulty": random.choice(["Easy","Medium","Hard"]),

        "Python": random.randint(3,5),
        "ML": random.randint(1,5),
        "APIs": random.randint(2,5),
        "Frontend": random.randint(1,4),
        "Data": random.randint(2,5),
        "Systems": random.randint(1,5),
        "Viz": random.randint(1,5),
        "DevOps": random.randint(1,4)

    })

projects_df = pd.DataFrame(rows)

# Save into database folder
projects_path = os.path.join(DATA_DIR, "projects.csv")
projects_df.to_csv(projects_path, index=False)

print("projects.csv generated")
print(projects_df.head())
