import streamlit as st
import sqlite3
import pandas as pd
from PIL import Image
import datetime
import tensorflow as tf

# -----------------------------
# DATABASE SETUP
# -----------------------------

conn = sqlite3.connect("civicfix.db", check_same_thread=False)
c = conn.cursor()

c.execute("""
CREATE TABLE IF NOT EXISTS issues(
id INTEGER PRIMARY KEY AUTOINCREMENT,
description TEXT,
issue_type TEXT,
location TEXT,
severity TEXT,
status TEXT,
time TEXT,
user TEXT
)
""")

conn.commit()
# -----------------------------
# LOAD AI MODELS
# -----------------------------

pothole_model = tf.keras.models.load_model("pothole_model.keras")
water_model = tf.keras.models.load_model("water_model.keras")

def predict_pothole(img):
 img = img.resize((224,224))
 img_array = np.array(img)
 img_array = np.expand_dims(img_array, axis=0)
 img_array = img_array / 255.0
 prediction = pothole_model.predict(img_array)
 return prediction.argmax()

def predict_water(img):
 img = img.resize((224,224))
 img_array = np.array(img)
 img_array = np.expand_dims(img_array, axis=0)
 img_array = img_array / 255.0
 prediction = water_model.predict(img_array)
 return prediction.argmax()
# -----------------------------
# SEVERITY LOGIC
# -----------------------------

def get_severity(issue_type):

    if issue_type == "Water Leakage":
        return "Critical"
    elif issue_type == "Pothole":
        return "High"
    elif issue_type == "Streetlight":
        return "Medium"
    else:
        return "Low"

# -----------------------------
# STREAMLIT UI
# -----------------------------

st.title("🏙 CivicFix – Urban Issue Reporting System")

menu = ["Report Issue", "Issue Dashboard", "Authority Panel", "City Stats", "Leaderboard", "City Map"]
choice = st.sidebar.selectbox("Menu", menu)

# -----------------------------
# REPORT ISSUE
# -----------------------------

if choice == "Report Issue":

    st.header("Report an Infrastructure Issue")
    user = st.text_input("Your Name")
    description = st.text_input("Issue Description")

    issue_type = st.selectbox(
        "Issue Type",
        ["Pothole", "Water Leakage", "Streetlight", "Garbage", "Road Damage"]
    )

    location = st.text_input("Location")

    image = st.file_uploader("Upload Issue Photo")
    if image is not None:

      img = Image.open(image)

      st.image(img, caption="Uploaded Image")

      if issue_type == "Pothole":

           result = predict_pothole(img)

           if result == 0:
               st.success("AI Detection: Pothole Detected 🕳")
           else:
               st.info("AI Detection: No pothole detected")

      elif issue_type == "Water Leakage":

             result = predict_water(img)

             if result == 0:
                 st.success("AI Detection: Water Leakage Detected 💧")
             else:
                 st.info("AI Detection: No water leakage detected")

    if st.button("Submit Report"):

        severity = get_severity(issue_type)
        status = "Pending"
        time = str(datetime.datetime.now())

        c.execute(
            "INSERT INTO issues(description,issue_type,location,severity,status,time,user) VALUES (?,?,?,?,?,?,?)",
            (description, issue_type, location, severity, status, time, user)
        )

        conn.commit()

        st.success("Issue reported successfully!")

        st.write("Severity Level:", severity)

        if severity == "Critical":
           st.error("🚨 CRITICAL ISSUE ALERT – Authorities Notified Immediately!")

# -----------------------------
# ISSUE DASHBOARD
# -----------------------------

elif choice == "Issue Dashboard":

    st.header("Reported Issues")

    df = pd.read_sql_query("SELECT * FROM issues", conn)

    st.dataframe(df)

# -----------------------------
# AUTHORITY PANEL
# -----------------------------

elif choice == "Authority Panel":

    st.header("Authority Task Panel")

    df = pd.read_sql_query("SELECT * FROM issues", conn)

    st.dataframe(df)

    issue_id = st.number_input("Enter Issue ID")

    new_status = st.selectbox(
        "Update Status",
        ["Pending", "In Progress", "Resolved"]
    )

    if st.button("Update Status"):

        c.execute(
            "UPDATE issues SET status=? WHERE id=?",
            (new_status, issue_id)
        )

        conn.commit()

        st.success("Status Updated")

# -----------------------------
# CITY STATS
# -----------------------------

elif choice == "City Stats":

    st.header("City Infrastructure Dashboard")

    df = pd.read_sql_query("SELECT * FROM issues", conn)

    total = len(df)
    resolved = len(df[df["status"] == "Resolved"])
    pending = len(df[df["status"] == "Pending"])

    st.metric("Total Issues", total)
    st.metric("Resolved Issues", resolved)
    st.metric("Pending Issues", pending)

    st.bar_chart(df["issue_type"].value_counts())
elif choice == "Leaderboard":

    st.header("🏆 Citizen Leaderboard")

    df = pd.read_sql_query("SELECT user, COUNT(*) as reports FROM issues GROUP BY user", conn)

    df = df.sort_values(by="reports", ascending=False)

    st.dataframe(df)

    st.bar_chart(df.set_index("user"))

elif choice == "City Map":

    st.header("🗺 Reported Issues Map")

    df = pd.read_sql_query("SELECT * FROM issues", conn)

    if not df.empty:

        map_data = pd.DataFrame({
            "lat":[13.0827]*len(df),
            "lon":[80.2707]*len(df)
        })

        st.map(map_data)

    else:
        st.write("No issues reported yet.")




