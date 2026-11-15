
import streamlit as st
import pandas as pd
import io

st.set_page_config(
    page_title="Job Market Intelligence",
    page_icon="📊",
    layout="wide"
)

st.title("📊 Job Market Intelligence Dashboard")

st.write(
    "Analyze Data Analyst job opportunities, "
    "employer skill demand, and candidate skill gaps."
)

@st.cache_data
def load_data():
    jobs = pd.read_csv("data/linkedin_job_postings.csv")
    skills = pd.read_csv("data/job_skills.csv")
    return jobs, skills

jobs, skills = load_data()

col1, col2, col3 = st.columns(3)

with col1:
    st.metric("Total Job Postings", f"{len(jobs):,}")

with col2:
    st.metric("Companies", f"{jobs['company'].nunique():,}")

with col3:
    st.metric("Job Locations", f"{jobs['job_location'].nunique():,}")

st.success("Datasets loaded successfully!")
st.header("📌 Data Analyst Job Analysis")

analyst_jobs = jobs[
    jobs["job_title"].str.contains(
        "data analyst",
        case=False,
        na=False
    )
]

st.metric(
    "Data Analyst Job Postings",
    f"{len(analyst_jobs):,}"
)
# Location filter
st.subheader("📍 Filter Jobs by Location")

locations = sorted(
    analyst_jobs["job_location"].dropna().unique()
)

selected_location = st.selectbox(
    "Select a job location",
    ["All Locations"] + locations
)

if selected_location == "All Locations":
    filtered_jobs = analyst_jobs.copy()
else:
    filtered_jobs = analyst_jobs[
        analyst_jobs["job_location"] == selected_location
    ]

st.metric("Jobs in Selected Location", f"{len(filtered_jobs):,}")

st.subheader("Top 10 Data Analyst Job Titles")
top_titles = filtered_jobs["job_title"].value_counts().head(10)
st.bar_chart(top_titles)
st.subheader("Top 10 Companies Hiring Data Analysts")

top_companies = (
    filtered_jobs["company"]
    .value_counts()
    .head(10)
)

st.bar_chart(top_companies)
st.subheader("Top 10 Locations for Data Analyst Jobs")

top_locations = (
    filtered_jobs["job_location"]
    .value_counts()
    .head(10)
)

st.bar_chart(top_locations)
# Location Comparison

st.header("🌍 Data Analyst Opportunities by Location")

location_comparison = (
    analyst_jobs["job_location"]
    .value_counts()
    .head(10)
)

st.subheader("Top 10 Locations by Job Postings")
st.bar_chart(location_comparison)

selected_cities = st.multiselect(  
  "Choose cities to compare",
    options=locations,
    default=location_comparison.index.tolist()[:3]
)
if selected_cities:
    city_comparison = (
        analyst_jobs[
            analyst_jobs["job_location"].isin(selected_cities)
        ]["job_location"]
        .value_counts()
        .reindex(selected_cities, fill_value=0)
    )

    st.subheader("City-wise Job Opportunity Comparison")
    st.bar_chart(city_comparison)
# City-wise Skill Demand Comparison

if selected_cities:

    city_skill_data = analyst_jobs[
        analyst_jobs["job_location"].isin(selected_cities)
    ].merge(skills, on="job_link", how="inner")

    city_skill_data["skill"] = city_skill_data["job_skills"].str.split(",")

    city_skill_data = city_skill_data.explode("skill")

    city_skill_data["skill"] = (
        city_skill_data["skill"]
        .str.strip()
        .str.lower()
    )

    city_skill_data = city_skill_data.dropna(subset=["skill"])

    city_skill_data["skill"] = city_skill_data["skill"].replace({
        "communication skills": "communication"
    })
    # Selected Cities KPI Analysis

    st.subheader("📌 Selected Cities – Key Statistics")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric(
            "Total Job Postings",
            f"{city_skill_data['job_link'].nunique():,}"
        )

    with col2:
        st.metric(
            "Companies Hiring",
            f"{city_skill_data['company'].nunique():,}"
        )

    with col3:
        st.metric(
            "Distinct Skills Required",
            f"{city_skill_data['skill'].nunique():,}"
        )

    city_skill_comparison = city_skill_data.pivot_table(
        index="skill",
        columns="job_location",
        values="job_link",
        aggfunc="nunique",
        fill_value=0
    )

    top_city_skills = city_skill_comparison.sum(axis=1).nlargest(10).index

    st.subheader("📊 Skill Demand Across Selected Cities")
    st.bar_chart(city_skill_comparison.loc[top_city_skills])

st.header("💡 Data Analyst Skill Demand Analysis")

st.write("We will analyze the skills employers require for Data Analyst jobs.")
# Select Data Analyst job IDs
analyst_links = filtered_jobs["job_link"].dropna().unique()
# Match Data Analyst jobs with their skills
analyst_skills = skills[
    skills["job_link"].isin(analyst_links)
].copy()

st.metric(
    "Data Analyst Jobs with Skill Information",
    f"{analyst_skills['job_link'].nunique():,}"
)
# Split skills into individual skills
analyst_skills["skill"] = analyst_skills["job_skills"].str.split(",")

# Create one row for each skill
analyst_skills = analyst_skills.explode("skill")

# Clean skill names
analyst_skills["skill"] = (
    analyst_skills["skill"]
    .str.strip()
    .str.lower()
)

# Remove empty skills
analyst_skills = analyst_skills.dropna(subset=["skill"])
# Combine different names for the same skill
analyst_skills["skill"] = analyst_skills["skill"].replace({
    "communication skills": "communication"
})

# Count unique jobs mentioning each skill
skill_demand = (
    analyst_skills.groupby("skill")["job_link"]
    .nunique()
    .sort_values(ascending=False)
    .head(20)
)

st.subheader("Top 20 Skills Required by Employers")

st.bar_chart(skill_demand)


# Personal Skill Gap Analyzer

st.header("🎯 Personal Skill Gap Analyzer")

st.write("Enter your current technical and professional skills.")

candidate_input = st.text_input(
    "Enter your skills separated by commas",
    placeholder="Example: Python, SQL, Excel, Power BI"
)

if candidate_input:

    aliases = {
        "powerbi": "power bi",
        "microsoft power bi": "power bi",
        "ms excel": "excel",
        "microsoft excel": "excel",
        "python programming": "python",
        "communication skills": "communication"
    }

    candidate_skills = {
        aliases.get(skill.strip().lower(), skill.strip().lower())
        for skill in candidate_input.split(",")
        if skill.strip()
    }

    required_skills = set(skill_demand.index)
    matched_skills = candidate_skills.intersection(required_skills)
    missing_skills = required_skills - candidate_skills

    coverage = (len(matched_skills) / len(required_skills)) * 100

    total_skill_demand = skill_demand.sum()
    matched_skill_demand = skill_demand[
        skill_demand.index.isin(matched_skills)
    ].sum()

    weighted_coverage = (
        matched_skill_demand / total_skill_demand
    ) * 100

    st.subheader("Your Skill Gap Report")

    col1, col2, col3 = st.columns(3)

    with col1:
        st.metric("Matched Skills", len(matched_skills))

    with col2:
        st.metric("Missing Skills", len(missing_skills))

    with col3:
        st.metric("Skill Coverage", f"{coverage:.2f}%")

    st.metric("Demand-Weighted Coverage", f"{weighted_coverage:.2f}%")

    st.subheader("✅ Your Matching Skills")
    st.write(", ".join(sorted(matched_skills)) or "No matching skills yet.")

    st.subheader("📚 Skills You Can Learn")
    st.write(", ".join(sorted(missing_skills)) or "You matched all 20 skills!")

    st.subheader("🚀 Recommended Learning Priorities")

    learning_priorities = skill_demand[
        skill_demand.index.isin(missing_skills)
    ].sort_values(ascending=False)
    # Personalized Skill Learning Roadmap

    roadmap = learning_priorities.reset_index()
    roadmap.columns = ["Skill", "Employer Demand"]

    roadmap["Learning Priority"] = [
        "High Priority" if i < 5
        else "Medium Priority" if i < 10
        else "Build Later"
        for i in range(len(roadmap))
    ]

    roadmap["Learning Order"] = range(1, len(roadmap) + 1)

    # Learning resources for missing skills
    resource_links = {
        "sql": "https://sqlbolt.com/",
        "python": "https://www.kaggle.com/learn/python",
        "excel": "https://support.microsoft.com/excel",
        "power bi": "https://learn.microsoft.com/training/powerplatform/power-bi/",
        "tableau": "https://www.tableau.com/learn/training",
        "statistics": "https://www.khanacademy.org/math/statistics-probability",
        "machine learning": "https://www.kaggle.com/learn/intro-to-machine-learning",
        "r": "https://www.r-project.org/",
        "communication": "https://www.coursera.org/browse/business/communication",
        "data visualization": "https://www.kaggle.com/learn/data-visualization",
        "data analysis": "https://www.kaggle.com/learn",
        "business intelligence": "https://learn.microsoft.com/",
        "data analytics": "https://www.coursera.org/",
        "data management": "https://www.ibm.com/think/topics/data-management",
        "data mining": "https://www.kaggle.com/learn",
        "data modeling": "https://learn.microsoft.com/power-bi/transform-model/",
        "analytical skills": "https://www.coursera.org/",
        "problem solving": "https://www.hackerrank.com/domains/algorithms",
        "project management": "https://www.coursera.org/browse/business/project-management",
        "reporting": "https://learn.microsoft.com/power-bi/",
    }

    roadmap["Learning Resource"] = roadmap["Skill"].map(resource_links)


    st.subheader("🗺️ Your Personalized Learning Roadmap")

    st.write(
        "Follow this roadmap to focus on skills "
        "that appear more frequently in Data Analyst job postings."
    )


    st.dataframe(
        roadmap[
            ["Learning Order", "Skill", "Employer Demand",
             "Learning Priority", "Learning Resource"]
        ],
        use_container_width=True,
        hide_index=True,
        column_config={
            "Learning Resource": st.column_config.LinkColumn(
                "Learning Resource",
                display_text="Open Learning Resource"
            )
        }
    )

    st.dataframe(
        learning_priorities.rename("Number of Job Postings"),
        use_container_width=True
    )

    st.bar_chart(learning_priorities)

    # Excel Report Download
    
    excel_buffer = io.BytesIO()

    with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
        roadmap.to_excel(
            writer,
            sheet_name="Learning Roadmap",
            index=False
        )

        skill_report = pd.DataFrame({
            "Category": ["Matched Skills", "Missing Skills"],
            "Skills": [
                ", ".join(sorted(matched_skills)),
                ", ".join(sorted(missing_skills))
            ]
        })

        skill_report.to_excel(
            writer,
            sheet_name="Skill Gap Report",
            index=False
        )

    excel_data = excel_buffer.getvalue()

    st.download_button(
        label="📥 Download Excel Skill Gap Report",
        data=excel_data,
        file_name="My_Skill_Gap_Report.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        key="excel_report_download"
    )
