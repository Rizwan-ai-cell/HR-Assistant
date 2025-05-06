import streamlit as st
import fitz  # PyMuPDF
import smtplib
from email.message import EmailMessage
from dotenv import load_dotenv
from langchain_groq import ChatGroq
import os
import re
import json

# --------- LOAD ENV ---------
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASS = os.getenv("EMAIL_PASS")
SMTP_SERVER = os.getenv("SMTP_SERVER")
SMTP_PORT = int(os.getenv("SMTP_PORT"))

# --------- LangChain GROQ Model ---------
llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name="llama3-8b-8192",
)

# --------- Functions ---------

def extract_text_from_pdf(file):
    doc = fitz.open(stream=file.read(), filetype="pdf")
    text = ""
    for page in doc:
        text += page.get_text()
    return text

def call_groq(prompt):
    response = llm.invoke(prompt)
    return response.content

def send_email(to_email, subject, html_body):
    msg = EmailMessage()
    msg['Subject'] = subject
    msg['From'] = EMAIL_USER
    msg['To'] = to_email
    msg.add_alternative(html_body, subtype='html')

    with smtplib.SMTP(SMTP_SERVER, SMTP_PORT) as smtp:
        smtp.starttls()
        smtp.login(EMAIL_USER, EMAIL_PASS)
        smtp.send_message(msg)

def generate_html_email(candidate_name, status, job_title, company_name, mcqs=None, improvements=None):
    if status.lower() == 'qualified':
        mcq_html = ""
        for q in mcqs:
            mcq_html += f"<p><b>{q['question']}</b></p><ul>"
            for opt in q['options']:
                mcq_html += f"<li>{opt}</li>"
            mcq_html += "</ul>"

        html = f"""
        <html><body>
        <h2>Congratulations!</h2>
        <p>Dear {candidate_name},</p>
        <p>You have been shortlisted for the <strong>{job_title}</strong> position at <strong>{company_name}</strong>.</p>
        <p>Please complete the following MCQ assessment:</p>
        {mcq_html}
        <p>Submit your answers within 48 hours.</p>
        <br><p>Best regards,<br>HR Team</p>
        </body></html>
        """
    else:
        improvement_html = "".join(f"<li>{i}</li>" for i in improvements)
        html = f"""
        <html><body>
        <h2>Thank You for Applying</h2>
        <p>Dear {candidate_name},</p>
        <p>Thank you for applying for the <strong>{job_title}</strong> position at <strong>{company_name}</strong>.</p>
        <p>Suggestions to strengthen your profile:</p>
        <ul>{improvement_html}</ul>
        <p>We hope to hear from you again soon.</p>
        <br><p>Best regards,<br>HR Team</p>
        </body></html>
        """
    return html

def generate_mcqs_with_answers(job_title):
    prompt = f"""
    Create 5 MCQs for the role '{job_title}'.
    For each question, provide:
    - Question text
    - 4 options (A, B, C, D)
    - Correct Answer (mention only option letter)
    - One line Explanation why the correct answer is correct.

    Format it like JSON:
    {{
      "questions": [
        {{
          "question": "...",
          "options": ["A) ...", "B) ...", "C) ...", "D) ..."],
          "correct_answer": "B",
          "explanation": "Brief reason here."
        }}
      ]
    }}
    """
    response = call_groq(prompt)

    # Try to extract JSON
    match = re.search(r'\{.*\}', response, re.DOTALL)
    if match:
        response = match.group(0)

    try:
        parsed = json.loads(response)
        return parsed.get("questions", [])
    except Exception:
        return []

# --------- Streamlit App ---------

st.set_page_config(page_title="HR ATS Assistant", layout="wide")
st.title("HR ATS Assistant")

tabs = st.tabs(["1. Analyze Resume", "2. Analysis Result", "3. Send Email"])

# ------ TAB 1: Analyze ------
with tabs[0]:
    st.header("Step 1: Upload Resume and Enter Details")
    resume_file = st.file_uploader("Upload Resume (PDF)", type=["pdf"])
    jd_text = st.text_area("Paste Job Description")

    candidate_name = st.text_input("Enter Candidate Name")
    job_title = st.text_input("Enter Job Title")
    company_name = st.text_input("Enter Company Name")

    if st.button("Analyze Resume"):
        if not resume_file or not jd_text or not candidate_name or not job_title or not company_name:
            st.error("Please upload resume and fill all fields.")
        else:
            with st.spinner('Analyzing resume, please wait...'):
                resume_text = extract_text_from_pdf(resume_file)

                prompt = f"""
You are an AI-powered HR Assistant specialized in resume screening and job matching.

Please analyze the **Resume** against the **Job Description** provided below.

---

**Resume:**
{resume_text}

**Job Description:**
{jd_text}

---

Your task is to return the following:

1. **Skills Matched:** List key skills from the job description found in the resume.
2. **Experience Match Score:** Provide a percentage (0–100%) that reflects how well the candidate's experience aligns with the job.
3. **Qualification Status:** Return **Qualified** if the match score is 70% or higher, otherwise **Not Qualified**.
4. **Brief Reasoning:** A concise, professional explanation of why the candidate is (or isn’t) a good fit based on the resume.
5. **Bonus (Optional):** If the candidate is Qualified, list 3 personalized interview questions related to their profile and the job.

Be concise, unbiased, and ATS-aware in your evaluation.
"""


                result = call_groq(prompt)

                # Extract Experience Score
                score_match = re.search(r"(\d{1,3})%", result)
                score = int(score_match.group(1)) if score_match else 0
                qualified = "Qualified" if score >= 70 else "Not Qualified"

                if qualified == "Qualified":
                    mcqs = generate_mcqs_with_answers(job_title)
                    improvements = []
                else:
                    mcqs = []
                    improvements = [
                        "Improve technical skills related to the role.",
                        "Work on more projects to gain experience.",
                        "Enhance your resume with measurable results."
                    ]

                # Save
                st.session_state['resume_analysis'] = {
                    "candidate_name": candidate_name,
                    "job_title": job_title,
                    "company_name": company_name,
                    "score": score,
                    "qualified": qualified,
                    "mcqs": mcqs,
                    "improvements": improvements
                }
            st.success("✅ Analysis Completed! Go to Step 2.")

# ------ TAB 2: Analysis Result ------
with tabs[1]:
    st.header("Step 2: Result")
    if 'resume_analysis' in st.session_state:
        data = st.session_state['resume_analysis']

        st.write(f"**Experience Match Score:** {data['score']}%")
        st.write(f"**Qualification Status:** {data['qualified']}")

        if data['qualified'] == "Qualified":
            st.markdown("### MCQs (with Correct Answer and Explanation):")
            for idx, q in enumerate(data['mcqs'], 1):
                st.write(f"**Q{idx}. {q['question']}**")
                for opt in q['options']:
                    st.write(f"- {opt}")
                st.write(f"✅ **Correct Answer:** {q['correct_answer']}")
                st.write(f"📝 **Explanation:** {q['explanation']}")
                st.markdown("---")
        else:
            st.markdown("### Improvement Suggestions:")
            for idx, suggestion in enumerate(data['improvements'], 1):
                st.write(f"{idx}. {suggestion}")
    else:
        st.warning("Please complete analysis first.")

# ------ TAB 3: Send Email ------
with tabs[2]:
    st.header("Step 3: Send Email Automatically")
    if 'resume_analysis' in st.session_state:
        data = st.session_state['resume_analysis']

        candidate_email = st.text_input("Enter Candidate Email")

        if st.button("Send Email"):
            if not candidate_email:
                st.error("Please enter the candidate's email address.")
            else:
                # Only send Question + Options (not answer/explanation)
                mcqs_for_email = [{"question": q["question"], "options": q["options"]} for q in data["mcqs"]]

                subject = f"Application Update - {data['job_title']} at {data['company_name']}"
                email_body = generate_html_email(
                    data['candidate_name'],
                    data['qualified'],
                    data['job_title'],
                    data['company_name'],
                    mcqs=mcqs_for_email,
                    improvements=data['improvements']
                )
                with st.spinner('Sending Email...'):
                    try:
                        send_email(candidate_email, subject, email_body)
                        st.success(f"✅ Email successfully sent to {candidate_email}")
                    except Exception as e:
                        st.error(f"❌ Failed to send email: {str(e)}")
    else:
        st.warning("Please complete analysis first.")
