## database generator
import pandas as pd
import random
import os

# Locate database folder
BASE_DIR = os.path.dirname(os.path.dirname(__file__))
DATA_DIR = os.path.join(BASE_DIR, "database")

students = [

"Aarcha Mukesh","Aarushi Kumar","Abhisri M","Agnivesh Chatterjee","Ahana Sen",
"Aman Ray","Ankush Agarwal","Anupam Dasgupta","Arkaprabha Chakraborty",
"Arnab Chakraborti","Arushi Marwaha","Aryan Chauhan","Aryan Srivastava",
"Atralita Saha","Bibek Rout","Deepta Basak","Diksa Pal Chowdhury",
"Jith Philipose Xavier","Kanshiya Uday","Meghtithi Mitra","Nandini Agarwal",
"Nikhil","Palak Khuntia","Patel Dhruv Vasantkumar","Radhika Dhama",
"Rajveer Singh","Rushikesh Vishwasrao","Sagnik Chowdhury","Saksham Dheer Singh",
"Sambit Ranjan Rout","Sania Rawat","Shaumik Khanna","Shreyasi Kar",
"Shreya Singhee","Snehash Kumar Behera","Sombit Mazumder","Sourit Mitra",
"Swikriti Paul","Urjaswi Chakraborty",
"Abhinav Malik","Abhishek Harshadbhai Lunagariya","Abhishek Singh",
"Ahana Biswas","Ahana Mondal","Aman Raj","Anirban Chatterjee",
"Anushka Chakraborty","Arnab Bera","Ayushman Anupam","Biswajit Kala",
"Boda Surya Venkata Jyothi Sowmya","Chinmay Shailesh Nandan","Debanjan Das",
"Deepanshi","Devesh Kailash Bajaj","Dhruv singla","Hanani Bathina",
"Hinge Aniket Shriram","Jugaad Singh Sohal","Ketaki Tushar Sahasrabudhe",
"Manami Das","Maria Paul Thurkadayil","Mohit Singh Sinsniwal",
"Nalla Janardhana Rao","Nisith Ranjan Hazra","Parejiya Poojan Shaileshbhai",
"Pranav Pothan","Raja S","Riya Shyam Huddar","Sampriti Mahapatra",
"Shreya Singh","Shruti Sharma","Shuvodeep Dutta","Srishti Lakhotia",
"Tejaswi","Titli Chanda","Trishita Patra"
]
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

rows = []

for s in students:

    prefs = random.sample(projects,3)

    rows.append({
        "name": s,
        "college": "Chennai Mathematical Institute",
        "resume_link": f"https://resume.fake/{s.replace(' ','').lower()}",
        "github_link": f"https://github.com/{s.replace(' ','').lower()}",
        "python": random.randint(2,5),
        "ml": random.randint(1,5),
        "api": random.randint(1,5),
        "frontend": random.randint(1,5),
        "data": random.randint(2,5),
        "systems": random.randint(1,5),
        "viz": random.randint(1,5),
        "devops": random.randint(1,5),
        "pref1": prefs[0],
        "pref2": prefs[1],
        "pref3": prefs[2]
    })

df = pd.DataFrame(rows)

# Save to database folder
students_path = os.path.join(DATA_DIR, "students.csv")
df.to_csv(students_path, index=False)

print("students.csv generated")
