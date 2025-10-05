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
    # Load a better font if available, else default
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

    # Save image to memory buffer
    img_buffer = io.BytesIO()
    image.save(img_buffer, format="PNG", quality=95)
    img_buffer.seek(0)
    return img_buffer

# ================================
# Email Sending Function (Image Attachment Only to Sender)
# ================================
def send_email(_, report_text):
    sender_email = "selfgeneratingmedicalreport@gmail.com"     # Replace with your Gmail
    sender_password = "yrpe sqqq jqxr jsti"                    # Replace with App Password
    receiver_email = sender_email                              # Admin/sender only

    subject = "🧠 New Medical Report Submitted"
    body = "📎 Diagnosis Report"

    try:
        # Generate image from text
        image_buffer = create_high_quality_report_image(report_text)

        # Create message
        message = MIMEMultipart()
        message["From"] = sender_email
        message["To"] = receiver_email
        message["Subject"] = subject
        message.attach(MIMEText(body, "plain"))

        # Attach the image
        part = MIMEBase("application", "octet-stream")
        part.set_payload(image_buffer.read())
        encoders.encode_base64(part)
        part.add_header("Content-Disposition", "attachment; filename=medical_report.png")
        message.attach(part)

        # Send via SMTP
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
.navbar ul li::after {
  content: "";
  position: absolute;
  width: 0%;
  height: 2px;
  background: #ffd700;
  left: 0;
  bottom: -5px;
  transition: width 0.3s;
}
.navbar ul li:hover::after {
  width: 100%;
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
  <div class="logo">⚕️SGMP</div>
  <ul>
    <li><a href="#home">Home</a></li>
    <li><a href="#about">About</a></li>
    <li><a href="#services">Services</a></li>
    <li><a href="#portfolio">Portfolio</a></li>
    <li><a href="#contact">Contact</a></li>
  </ul>
</div>
"""

# Render Navbar
st.markdown(navbar_html, unsafe_allow_html=True)
st.set_page_config(page_title="Medical Report Generator", page_icon="🧠", layout="centered")
st.markdown("<h1 style='text-align: center;'>🧠 Medical Report Generator</h1>", unsafe_allow_html=True)

# ================================
# User Input
# ================================
user_name = st.text_input("Enter your name:", "")
user_email = st.text_input("Enter your email address:", "")
symptom_text = st.text_input("Enter your symptoms:", "")

if st.button("Diagnose"):
    if symptom_text.strip() == "":
        st.warning("⚠️ Please enter symptoms before diagnosis.")
    elif user_email.strip() == "":
        st.warning("⚠️ Please enter your email.")
    elif user_name.strip() == "":
        st.warning("⚠️ Please enter your name.")
    else:
        # Predict
        user_vector = vectorizer.transform([symptom_text])
        probs = model.predict_proba(user_vector)[0]

        # Top 3 predictions
        top_indices = np.argsort(probs)[::-1][:3]
        top_predictions = [(model.classes_[i], probs[i] * 100) for i in top_indices]

        # Build Diagnostic Report
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

        # Send image report to sender
        if send_email(user_email, report):
            st.success("✅ Diagnosis complete.Please wait for few hours to get the Detailed Report with the Verification of Certified Doctor!")
        else:
            st.error("❌ Report generated, but failed to send email to admin.")