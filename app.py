from flask import Flask, request, jsonify
from flask_cors import CORS
from waitress import serve
import os
import json
import requests
import subprocess
import whisper
from dotenv import load_dotenv
import pdfplumber

from summary import *
from quiz import *
from preprocessing import *

from langchain_groq import ChatGroq
from langchain.chains import LLMChain
from langchain_core.prompts import ChatPromptTemplate, HumanMessagePromptTemplate
from langchain_core.messages import SystemMessage

app = Flask(__name__)
CORS(app, supports_credentials=True)

load_dotenv()

UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

GROQ_API_KEY = os.getenv("GROQ_API_KEY")
if not GROQ_API_KEY:
    raise ValueError("GROQ_API_KEY is not set in .env file")

os.environ["GROQ_API_KEY"] = GROQ_API_KEY
model_name = "llama3-8b-8192"

llm = ChatGroq(
    groq_api_key=GROQ_API_KEY,
    model_name=model_name,
    temperature=0.4,
    max_tokens=500,
)

def Summary(text):
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt_Summary),
        HumanMessagePromptTemplate.from_template("{human_input}"),
    ])
    chain = prompt | llm
    response = chain.invoke({"human_input": text})
    return json.loads(response.content.strip())

def Quiz(text):
    prompt = ChatPromptTemplate.from_messages([
        SystemMessage(content=system_prompt_Quiz),
        HumanMessagePromptTemplate.from_template("{human_input}"),
    ])
    chain = prompt | llm
    response = chain.invoke({"human_input": text})
    return json.loads(response.content.strip())

def preprocess_audio(input_path, output_path):
    print(f"[DEBUG] Starting audio preprocessing: {input_path} -> {output_path}")
    command = ["ffmpeg", "-y", "-i", input_path, "-ac", "1", "-ar", "16000", output_path]
    result = subprocess.run(command, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"[ERROR] FFmpeg failed: {result.stderr}")
        raise Exception(f"FFmpeg error: {result.stderr}")
    print("[DEBUG] Audio preprocessing completed.")

@app.route("/getTranscript", methods=["POST"])
def get_transcript():
    subject_id = request.form.get("subject_id")
    faculty_id = request.form.get("faculty_id")
    topic = request.form.get("topic")
    heading = topic  
    class_id = 1
    status = 2
    difficulty = 1

    file = request.files.get("audio")
    if not all([subject_id, faculty_id, topic, file]):
        return jsonify({"error": "Missing required fields"}), 400
    if not file.filename.lower().endswith(".wav"):
        return jsonify({"error": "Invalid file type. Only .wav is supported"}), 400

    input_path = os.path.join(UPLOAD_FOLDER, file.filename)
    cleaned_path = os.path.join(UPLOAD_FOLDER, f"cleaned_{file.filename}")
    file.save(input_path)

    try:
        preprocess_audio(input_path, cleaned_path)
        model = whisper.load_model("base")
        result = model.transcribe(cleaned_path)
        transcript = result["text"]

        # Debug - sending to /summary
        print("[DEBUG] Sending transcript to /summary endpoint...")
        summary_payload = {
            "transcript": transcript,
            "class_id": class_id,
            "teacher_id": faculty_id,
            "heading": heading
        }
        print("[DEBUG] Summary payload:", summary_payload)
        summary_response = requests.post("http://localhost:5000/summary", json=summary_payload)

        # Debug - sending to /quiz
        print("[DEBUG] Sending transcript to /quiz endpoint...")
        quiz_payload = {
            "transcript": transcript,
            "heading": heading,
            "topic": topic,
            "class_id": class_id,
            "status": status,
            "difficulty": difficulty
        }
        quiz_response = requests.post("http://localhost:5000/quiz", json=quiz_payload)
        return jsonify({
            "subject_id": subject_id,
            "faculty_id": faculty_id,
            "topic": topic,
            "transcript": transcript,
            "summary_response": summary_response.json(),
            "quiz_response": quiz_response.json()
        })

    except Exception as e:
        print(f"[ERROR] Exception in get_transcript: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/summary", methods=["POST"])
def summary():
    try:
        data = request.get_json()
        if not data or "transcript" not in data:
            return jsonify({"error": "No transcript provided"}), 400

        transcript = data["transcript"]
        class_id = data.get("class_id")
        teacher_id = data.get("teacher_id")
        heading = data.get("heading")

        print("[DEBUG] Generating summary...")
        summary_data = Summary(transcript)

        if not summary_data or "summary" not in summary_data:
            return jsonify({"error": "Summary generation failed or returned empty"}), 500

        express_payload = {
            "heading": heading,
            "transcript": transcript,
            "summary": summary_data.get("summary", []),
            "topics": summary_data.get("related_topics", []),
            "class_id": class_id,
            "teacher_id": teacher_id
        }
        print("[DEBUG] Sending summary to Express...")
        express_response = requests.post("http://localhost:1000/summary", json=express_payload)

        if express_response.status_code == 201:
            return jsonify(express_response.json()), 201
        else:
            return jsonify({
                "error": "Summary generated but failed to save to DB",
                "details": express_response.text
            }), 500

    except Exception as e:
        print(f"[ERROR] Exception in /summary: {str(e)}")
        return jsonify({"error": str(e)}), 500

@app.route("/quiz", methods=["POST"])
def quiz():
    data = request.get_json()
    if not data or "transcript" not in data:
        return jsonify({"error": "No transcript provided"}), 400

    transcript = data["transcript"]
    heading = data.get("heading", "Quiz Heading")
    topic = data.get("topic", "General Topic")
    difficulty = data.get("difficulty", 1)
    class_id = data.get("class_id", 1)
    status = data.get("status", 2)

    max_attempts = 10

    for attempt in range(1, max_attempts + 1):
        try:
            print(f"[DEBUG] Attempt {attempt}: Generating quiz...")
            quiz_data = Quiz(transcript)

            if not quiz_data or "questions" not in quiz_data or not quiz_data["questions"]:
                print("[WARNING] No questions generated, retrying...")
                continue  # Try again if question generation failed

            quiz_payload = {
                "heading": heading,
                "topic": topic,
                "difficulty": difficulty,
                "class_id": class_id,
                "status": status,
                "questions": []
            }

            for question in quiz_data["questions"]:
                formatted_question = {
                    "question": question.get("question", ""),
                    "options": question.get("options", []),
                    "subtopics": question.get("subtopics", []),
                    "difficulty": question.get("difficulty", 1),
                    "correct_answer": question.get("correct_answer", 0)
                }
                quiz_payload["questions"].append(formatted_question)

            print("[DEBUG] Sending quiz to Express...")
            express_response = requests.post("http://localhost:1000/quiz", json=quiz_payload)

            if express_response.status_code == 201:
                print("[SUCCESS] Quiz created and saved.")
                return jsonify(express_response.json()), 201
            else:
                print(f"[ERROR] Express save failed (status {express_response.status_code})")
                return jsonify({"error": "Quiz generation succeeded but failed to save to Express."}), 502

        except Exception as e:
            print(f"[ERROR] Attempt {attempt} failed: {e}")

    return jsonify({"error": "Failed to generate quiz after 5 attempts"}), 500


@app.route("/pdf", methods=["POST"])
def parse_uploaded_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']

    if file.filename == '':
        return jsonify({"error": "Empty filename"}), 400

    try:
        with pdfplumber.open(file.stream) as pdf:
            text = "\n".join(page.extract_text() or "" for page in pdf.pages)
        return jsonify({"text": text}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500
    

if __name__ == "__main__":
    serve(app, host="0.0.0.0", port=8080)
