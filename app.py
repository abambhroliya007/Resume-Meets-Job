import os
import json
import streamlit as st
from dotenv import load_dotenv
from openai import OpenAI
from pypdf import PdfReader
from docx import Document

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

st.set_page_config(
    page_title="Resume-Meets-Job",
    page_icon="📄",
    layout="centered"
)

st.title("📄 Resume-Meets-Job")
st.write(
    "Upload your resume and paste a job description. "
    "This AI agent will analyze your job match, skill gaps, and improvements."
)

st.sidebar.title("About")
st.sidebar.write("""
Resume-Meets-Job helps you:
- Match your resume with a job
- Find missing skills
- Improve your resume
- Generate interview questions
- Create a short learning plan
""")


def read_pdf(file):
    reader = PdfReader(file)
    text = ""

    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"

    return text


def read_docx(file):
    doc = Document(file)
    text = ""

    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"

    return text


def read_txt(file):
    return file.read().decode("utf-8")


def extract_resume_text(uploaded_file):
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".pdf"):
        return read_pdf(uploaded_file)

    if file_name.endswith(".docx"):
        return read_docx(uploaded_file)

    if file_name.endswith(".txt"):
        return read_txt(uploaded_file)

    return ""


uploaded_resume = st.file_uploader(
    "Upload your resume",
    type=["pdf", "docx", "txt"]
)

job_description = st.text_area(
    "Paste the job description here",
    height=250
)

analyze_button = st.button("Analyze Resume Match")


if analyze_button:
    if uploaded_resume is None:
        st.warning("Please upload your resume first.")
        st.stop()

    if job_description.strip() == "":
        st.warning("Please paste a job description first.")
        st.stop()

    resume_text = extract_resume_text(uploaded_resume)

    if resume_text.strip() == "":
        st.error("Could not read your resume. Try uploading a PDF, DOCX, or TXT file.")
        st.stop()

    prompt = f"""
You are an expert resume reviewer and job-matching AI agent.

Your task:
Compare the resume with the job description.

Think through these steps:
1. Extract key skills from the job description.
2. Extract visible skills from the resume.
3. Compare both.
4. Identify strengths, gaps, and improvements.
5. Create interview preparation questions.
6. Create a short learning plan for missing skills.

Return ONLY valid JSON.

Resume:
{resume_text}

Job Description:
{job_description}
"""

    with st.spinner("AI agent is analyzing your resume..."):
        response = client.responses.create(
            model="gpt-5.5",
            input=prompt,
            text={
                "format": {
                    "type": "json_schema",
                    "name": "resume_analysis",
                    "schema": {
                        "type": "object",
                        "properties": {
                            "match_score": {
                                "type": "number"
                            },
                            "overall_summary": {
                                "type": "string"
                            },
                            "matched_skills": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "missing_skills": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "resume_improvements": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "tailored_resume_summary": {
                                "type": "string"
                            },
                            "interview_questions": {
                                "type": "array",
                                "items": {"type": "string"}
                            },
                            "learning_plan": {
                                "type": "string"
                            }
                        },
                        "required": [
                            "match_score",
                            "overall_summary",
                            "matched_skills",
                            "missing_skills",
                            "resume_improvements",
                            "tailored_resume_summary",
                            "interview_questions",
                            "learning_plan"
                        ],
                        "additionalProperties": False
                    }
                }
            }
        )

    raw_output = response.output_text
    result = json.loads(raw_output)

    st.success("Analysis complete!")

    st.subheader("Match Score")
    st.metric("Resume Match", f"{result['match_score']}%")

    st.subheader("Overall Summary")
    st.write(result["overall_summary"])

    st.subheader("Matched Skills")
    for skill in result["matched_skills"]:
        st.write(f"- {skill}")

    st.subheader("Missing Skills")
    for skill in result["missing_skills"]:
        st.write(f"- {skill}")

    st.subheader("Resume Improvements")
    for improvement in result["resume_improvements"]:
        st.write(f"- {improvement}")

    st.subheader("Tailored Resume Summary")
    st.write(result["tailored_resume_summary"])

    st.subheader("Interview Questions")
    for question in result["interview_questions"]:
        st.write(f"- {question}")

    st.subheader("Learning Plan")
    st.write(result["learning_plan"])

    improved_text = f"""
Tailored Resume Summary:
{result['tailored_resume_summary']}

Resume Improvements:
{chr(10).join("- " + item for item in result['resume_improvements'])}

Missing Skills:
{chr(10).join("- " + item for item in result['missing_skills'])}

Learning Plan:
{result['learning_plan']}
"""

    st.download_button(
        label="Download Improved Resume Notes",
        data=improved_text,
        file_name="resume_meets_job_analysis.txt",
        mime="text/plain"
    )