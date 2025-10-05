import streamlit as st
import json
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

# ===============================
# CONFIG
# ===============================
st.set_page_config(page_title="Doctor Portal", page_icon="⚕️", layout="centered")

st.markdown("<h1 style='text-align:center;'>⚕️ Doctor Portal</h1>", unsafe_allow_html=True)
st.write("Welcome, doctor. Review the patient’s report and send a verified response.")

# ===============================
# RETRIEVE CASE
# ===============================
case_id = st.query_params.get("case_id", None)

if not case_id:
    st.warning("⚠️ No case ID provided in the link.")
    st.stop()

file_path = f"cases/{case_id}.json"

if not os.path.exists(file_path):
    st.error("❌ Case not found or expired.")
    st.stop()

with open(file_path, "r") as f:
    case_data = json.load(f)

patient_email = case_data["email"]
patient_report = case_data["report"]

st.subheader("🧾 Patient’s Original Report")
st.text_area("Report", patient_report, height=250, disabled=True)

# ===============================
# DOCTOR INPUT
# ===============================
st.subheader("🩺 Doctor’s Verified Feedback")
doctor_name = st.text_input("Doctor Name")
verified_report = st.text_area("Write your verified report below:", height=200)

if st.button("📤 Send Verified Report to Patient"):
    if not doctor_name.strip() or not verified_report.strip():
        st.warning("⚠️ Please fill in all fields before sending.")
    else:
        try:
            sender_email = "selfgeneratingmedicalreport@gmail.com"
            sender_password = "yrpe sqqq jqxr jsti"

            subject = f"Verified Medical Report from {doctor_name}"
            body = f"""
Dear Patient,

Your doctor ({doctor_name}) has reviewed your case.

🧠 Verified Report:
-------------------
{verified_report}

Thank you for using our SGMR service.
"""

            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = patient_email
            message["Subject"] = subject
            message.attach(MIMEText(body, "plain"))

            server = smtplib.SMTP("smtp.gmail.com", 587)
            server.starttls()
            server.login(sender_email, sender_password)
            server.sendmail(sender_email, patient_email, message.as_string())
            server.quit()

            st.success(f"✅ Verified report sent to patient ({patient_email}) successfully!")
        except Exception as e:
            st.error(f"❌ Error sending email: {e}")
