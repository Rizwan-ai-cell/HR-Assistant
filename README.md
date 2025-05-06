# 🧠 AI-Powered Resume Evaluator

This project is an **AI-driven HR assistant** that evaluates resumes against job descriptions using natural language processing. It is designed to simulate an ATS (Applicant Tracking System) and provide structured, professional feedback on candidate suitability — without generating interview questions or MCQs.

---

## 🚀 Features

- 📄 **Resume vs. Job Description Matching**
- 🧠 **AI-generated Matching Score** (0–100%)
- ✅ **Qualification Status** (Qualified / Not Qualified)
- 📊 **Skills Matching Report**
- ⚠️ **Weaknesses or Gaps Identification**
- 📎 **ATS Compatibility Feedback**
- 🧾 Supports resumes and job descriptions in **PDF, DOCX, or plain text**

---

## 🛠️ Tech Stack

- **Python 3.10+**
- **LangChain + LLM (OpenAI/Groq)**
- **Streamlit** (for UI)
- **PyMuPDF / python-docx** (for parsing)
- **faiss** (optional for embedding & retrieval)

---

## 📂 Project Structure


---

## ⚙️ Installation

```bash
git clone https://github.com/yourusername/ai-resume-evaluator.git
cd ai-resume-evaluator
python -m venv venv
source venv/bin/activate    # or .\venv\Scripts\activate on Windows
pip install -r requirements.txt
