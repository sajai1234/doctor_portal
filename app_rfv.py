import streamlit as st
import joblib
import numpy as np
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from PIL import Image, ImageDraw, ImageFont
import io
import os
import tempfile
import sounddevice as sd
import wavio
import speech_recognition as sr

# ================================
# Load model and vectorizer
# ================================
model = joblib.load("disease_model.pkl")
vectorizer = joblib.load("vectorizer.pkl")
disease_id_to_name = joblib.load("disease_id_to_name.pkl")
disease_name_to_severity = joblib.load("disease_name_to_severity.pkl")
metadata = joblib.load("metadata.pkl")
accuracy = metadata["accuracy"]

def get_severity(disease_id):
    disease_name = disease_id_to_name.get(disease_id, f"Unknown Disease {disease_id}")
    return disease_name_to_severity.get(disease_name, "Unknown")

# ================================
# Convert text report to high-quality image
# ================================
def create_high_quality_report_image(report_text, font_size=28, padding=40):
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except:
        font = ImageFont.load_default()

    lines = report_text.strip().split('\n')
    max_line_width = max([font.getlength(line) for line in lines])
    img_width = int(max_line_width + padding * 2)
    img_height = int(len(lines) * (font_size + 10) + padding * 2)

    image = Image.new("RGB", (img_width, img_height), color="white")
    draw = ImageDraw.Draw(image)

    y = padding
    for line in lines:
        draw.text((padding, y), line, font=font, fill="black")
        y += font_size + 10

    img_buffer = io.BytesIO()
    image.save(img_buffer, format="PNG", quality=95)
    img_buffer.seek(0)
    return img_buffer


# ================================
# Email Sending Function (with Doctor Link)
# ================================
def send_email(report_text, patient_email):
    sender_email = "selfgeneratingmedicalreport@gmail.com"
    sender_password = "yrpe sqqq jqxr jsti"  # 🔒 Use app password or env variable
    receiver_email = sender_email  # Doctor receives it

    # Create unique Case ID
    import uuid, json, os
    case_id = str(uuid.uuid4())[:8]

    # Save patient case data locally
    os.makedirs("cases", exist_ok=True)
    case_data = {"email": patient_email, "report": report_text}
    with open(f"cases/{case_id}.json", "w") as f:
        json.dump(case_data, f)

    # Doctor link for review (customize this URL for your deployment)
    doctor_link = f"https://doctorapp-duchcijxmgpokztq2ertyz.streamlit.app/?case_id={case_id}"


    subject = f"🧠 New Patient Report Received (Case ID: {case_id})"
    body = f"""
Dear Doctor,

A new patient report has been submitted for review.

🧍 Patient Email: {patient_email}
📋 Case ID: {case_id}

Please review and send your verified diagnosis back to the patient using the link below:
🔗 {doctor_link}

Best regards,
Self-Generating Medical Report System
"""

    try:
        # Create image of report
        image_buffer = create_high_quality_report_image(report_text)

        # Compose email
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Attach image
        part = MIMEBase("application", "octet-stream")
        part.set_payload(image_buffer.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment; filename=medical_report.png")
        message.attach(part)

        # Send email
        server = smtplib.SMTP("smtp.gmail.com", 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.sendmail(sender_email, receiver_email, message.as_string())
        server.quit()
        return True
    except Exception as e:
        print("Email error:", e)
        return False




# ================================
# Streamlit Page Config
# ================================
st.set_page_config(page_title="Medical Report Generator", page_icon="🧠", layout="centered")

navbar_html = """
<style>
.navbar {
  background: linear-gradient(90deg, #4e54c8, #8f94fb);
  padding: 0.8rem 2rem;
  display: flex;
  align-items: center;
  justify-content: space-between;
  color: white;
  font-family: "Segoe UI", Tahoma, sans-serif;
  border-radius: 8px;
  box-shadow: 0px 4px 10px rgba(0,0,0,0.15);
  margin-bottom: 20px;
}
.navbar .logo {
  font-size: 1.4rem;
  font-weight: bold;
}
.navbar ul {
  list-style: none;
  display: flex;
  gap: 1.5rem;
}
.navbar ul li a {
  text-decoration: none;
  color: white;
  font-size: 1rem;
  transition: 0.3s;
}
.navbar ul li a:hover {
  color: #ffd700;
}
@media (max-width: 768px) {
  .navbar {
    flex-direction: column;
    align-items: flex-start;
  }
  .navbar ul {
    flex-direction: column;
    gap: 0.8rem;
    margin-top: 10px;
  }
}
</style>
<div class="navbar">
  <div class="logo">⚕️SGMR</div>
  <ul>
    <li><a href="#home">Home</a></li>
    <li><a href="#about">About</a></li>
    <li><a href="#services">Services</a></li>
    <li><a href="#portfolio">Portfolio</a></li>
    <li><a href="#contact">Contact</a></li>
  </ul>
</div>
"""
st.markdown(navbar_html, unsafe_allow_html=True)
st.markdown("<h1 style='text-align: center;'>🧠 Medical Report Generator</h1>", unsafe_allow_html=True)

# ================================
# User Input Section
# ================================
user_name = st.text_input("Enter your name:", "")
user_email = st.text_input("Enter your email address:", "")

st.subheader("🩺 Describe your symptoms")

# Maintain session state for text
if "symptom_text" not in st.session_state:
    st.session_state["symptom_text"] = ""

typed_text = st.text_input("Type your symptoms:", st.session_state["symptom_text"])

# 🎙️ Voice Input Feature (No PyAudio)
st.write("Or record your symptoms below:")

duration = st.slider("🎚️ Recording duration (seconds)", 3, 15, 5)
if st.button("🎤 Record Voice Symptoms"):
    recognizer = sr.Recognizer()
    try:
        st.info("🎙️ Recording... please speak clearly.")
        fs = 44100
        recording = sd.rec(int(duration * fs), samplerate=fs, channels=1, dtype='int16')
        sd.wait()

        # Save as temporary WAV file
        temp_audio = tempfile.NamedTemporaryFile(delete=False, suffix=".wav")
        wavio.write(temp_audio.name, recording, fs, sampwidth=2)

        # Recognize speech
        with sr.AudioFile(temp_audio.name) as source:
            audio = recognizer.record(source)
        text = recognizer.recognize_google(audio)

        st.session_state["symptom_text"] = text
        st.success(f"✅ Detected Symptoms: {text}")

        temp_audio.close()
        os.remove(temp_audio.name)
    except sr.UnknownValueError:
        st.error("⚠️ Could not understand audio. Please try again.")
    except sr.RequestError:
        st.error("⚠️ Speech recognition service unavailable.")
    except Exception as e:
        st.error(f"⚠️ Error: {e}")

# Final input sync
symptom_text = st.session_state["symptom_text"] or typed_text

# ================================
# Diagnose Button
# ================================
if st.button("🧾 Diagnose"):
    if symptom_text.strip() == "":
        st.warning("⚠️ Please enter or record symptoms before diagnosis.")
    elif user_email.strip() == "":
        st.warning("⚠️ Please enter your email.")
    elif user_name.strip() == "":
        st.warning("⚠️ Please enter your name.")
    else:
        user_vector = vectorizer.transform([symptom_text])
        probs = model.predict_proba(user_vector)[0]

        top_indices = np.argsort(probs)[::-1][:3]
        top_predictions = [(model.classes_[i], probs[i] * 100) for i in top_indices]

        high_disease_id, high_prob = top_predictions[0]
        high_disease_name = disease_id_to_name.get(high_disease_id, f"Unknown Disease {high_disease_id}")
        high_severity = get_severity(high_disease_id)

        report = f"""
🧠 Medical Report
-----------------------
Patient Name: {user_name}
Patient Email: {user_email}
Symptoms: {symptom_text}

⭐ High Possibility: {high_disease_name} ({high_disease_id}) → {high_prob:.2f}% | Severity: {high_severity}
"""

        for disease_id, prob in top_predictions[1:]:
            disease_name = disease_id_to_name.get(disease_id, f"Unknown Disease {disease_id}")
            severity = get_severity(disease_id)
            report += f"\n• {disease_name} ({disease_id}) → {prob:.2f}% | Severity: {severity}"

        report += f"\n\n📊 Model Accuracy: {accuracy*100:.2f}%"

        # Send the report and generate doctor link
        if send_email(report, user_email):
            st.success("✅ Diagnosis complete. Please wait for a doctor-verified detailed report!")
        else:
            st.error("❌ Report generated, but email sending failed.")

