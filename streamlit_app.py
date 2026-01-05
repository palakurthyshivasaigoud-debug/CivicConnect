import streamlit as st
import requests
from PIL import Image
import io
import json
from voice_utils import transcribe_audio_bytes

API_BASE = "http://127.0.0.1:5000/api"

st.set_page_config(page_title="CivicConnect", page_icon="🗣️", layout="wide")

lang_map = {"English": "en", "Hindi": "hi", "Telugu": "te"}
selected_language = st.sidebar.selectbox("UI Language", list(lang_map.keys()), index=0)
lang_code = lang_map[selected_language]

st.title("🗣️ CivicConnect — Smart Citizen Service Portal")

menu = st.sidebar.radio("Navigate", [
    "Home", "Submit Complaint", "Track Complaint", "My Complaints", "Admin Dashboard", "Chatbot", "Voice Input"
])

if menu == "Home":
    st.header("Welcome to CivicConnect")
    st.write("Use the sidebar to navigate. Switch language at top-left.")
    st.write("This demo supports: submission, tracking, admin workflow, analytics, chatbot, voice upload and translation.")

# ---------- Submit ----------
elif menu == "Submit Complaint":
    st.header("Submit a Complaint")
    with st.form("submit_form"):
        name = st.text_input("Your Name")
        email = st.text_input("Email (optional)")
        title = st.text_input("Title")
        description = st.text_area("Description")
        col1, col2 = st.columns(2)
        with col1:
            latitude = st.text_input("Latitude (optional)")
            longitude = st.text_input("Longitude (optional)")
        with col2:
            image = st.file_uploader("Attach Image (optional)", type=["jpg", "jpeg", "png"])
            if image:
                img = Image.open(image)
                st.image(img, width=250, caption="Preview")
        submitted = st.form_submit_button("Submit")
    if submitted:
        data = {
            "user_name": name,
            "email": email,
            "title": title,
            "description": description,
            "latitude": latitude,
            "longitude": longitude,
            "language": lang_code
        }
        files = {}
        if image:
            files["image"] = (image.name, image.getvalue(), image.type)
        try:
            r = requests.post(f"{API_BASE}/complaints", data=data, files=files)
            if r.status_code == 200:
                st.success(f"Submitted — Tracking ID: **{r.json().get('tracking_id')}**")
            else:
                st.error("Submission failed: " + r.text)
        except Exception as e:
            st.error("Request error: " + str(e))

# ---------- Track ----------
elif menu == "Track Complaint":
    st.header("Track a Complaint")
    tid = st.text_input("Enter Tracking ID")
    if st.button("Track"):
        if not tid:
            st.error("Enter tracking ID.")
        else:
            try:
                r = requests.get(f"{API_BASE}/complaints/{tid}")
                if r.status_code == 200:
                    c = r.json()
                    st.markdown(f"**Title:** {c['title']}")
                    st.markdown(f"**Category:** {c['category']} — **Sentiment:** {c['sentiment']}")
                    st.markdown(f"**Status:** {c['status']} — **Priority:** {c['priority']}")
                    st.markdown(f"**Location:** {c.get('latitude')}, {c.get('longitude')}")
                    if c.get("image_path"):
                        st.image(f"{API_BASE.replace('/api','')}/uploads/{c.get('image_path')}", width=300)
                else:
                    st.error("Not found.")
            except Exception as e:
                st.error("Error: " + str(e))

# ---------- My Complaints ----------
elif menu == "My Complaints":
    st.header("My Complaints")
    username = st.text_input("Enter your name")
    if st.button("Show"):
        if not username:
            st.error("Enter name.")
        else:
            try:
                r = requests.get(f"{API_BASE}/complaints/user/{username}")
                if r.status_code == 200:
                    comps = r.json()
                    if not comps:
                        st.info("No complaints found.")
                    for c in comps:
                        st.markdown(f"**{c['title']}** — {c['category']} — **{c['status']}**")
                        st.write(c['description'])
                        if c.get('image_path'):
                            st.image(f"{API_BASE.replace('/api','')}/uploads/{c.get('image_path')}", width=250)
                        st.write("---")
                else:
                    st.error("Failed to fetch.")
            except Exception as e:
                st.error("Error: " + str(e))

# ---------- Admin ----------
elif menu == "Admin Dashboard":
    st.header("Admin Dashboard")
    admin_token = st.text_input("Admin Token", type="password")
    if admin_token:
        # Stats
        try:
            r = requests.get(f"{API_BASE}/stats")
            if r.status_code == 200:
                stats = r.json()
                st.metric("Total complaints", stats.get("total"))
                st.write("By status:", stats.get("by_status"))
                st.write("By category:", stats.get("by_category"))
                st.write("Average rating:", stats.get("avg_rating"))
            else:
                st.error("Unable to fetch stats.")
        except Exception as e:
            st.error("Error fetching stats: " + str(e))

        # List & actions
        try:
            r = requests.get(f"{API_BASE}/complaints/list")
            if r.status_code == 200:
                comps = r.json()
                for c in comps:
                    st.markdown(f"**{c['title']}** — ID: {c['tracking_id']} — Status: **{c['status']}** — Priority: {c['priority']}")
                    col1, col2 = st.columns([1,4])
                    with col1:
                        # Use session_state to manage buttons and force refresh
                        if st.button(f"In Progress_{c['tracking_id']}", key=f"ip_{c['tracking_id']}"):
                            headers = {"X-Admin-Token": admin_token}
                            rr = requests.put(f"{API_BASE}/complaints/update_status/{c['tracking_id']}", json={"status": "In Progress"}, headers=headers)
                            st.success(f"Status updated to In Progress for {c['tracking_id']}")
                            st.experimental_set_query_params(refresh=c['tracking_id'])

                        if st.button(f"Resolve_{c['tracking_id']}", key=f"res_{c['tracking_id']}"):
                            headers = {"X-Admin-Token": admin_token}
                            rr = requests.put(f"{API_BASE}/complaints/update_status/{c['tracking_id']}", json={"status": "Resolved"}, headers=headers)
                            st.success(f"Status updated to Resolved for {c['tracking_id']}")
                            st.experimental_set_query_params(refresh=c['tracking_id'])
                    with col2:
                        st.write(c['description'])
                        if c.get('image_path'):
                            st.image(f"{API_BASE.replace('/api','')}/uploads/{c.get('image_path')}", width=300)
                    st.write("---")
            else:
                st.error("Failed to fetch complaints.")
        except Exception as e:
            st.error("Error: " + str(e))
    else:
        st.info("Enter admin token to manage.")


# ---------- Chatbot ----------
elif menu == "Chatbot":
    st.header("Chatbot (text)")
    user_input = st.text_input("Ask (e.g., 'status 123456' or 'submit a pothole')")
    if user_input:
        if any(ch.isdigit() for ch in user_input):
            # extract digits as tracking id
            tid = ''.join(ch for ch in user_input if ch.isdigit())
            try:
                r = requests.get(f"{API_BASE}/complaints/{tid}")
                if r.status_code == 200:
                    c = r.json()
                    st.success(f"Status: {c['status']} | Category: {c['category']} | Sentiment: {c['sentiment']}")
                else:
                    st.error("Tracking ID not found.")
            except Exception as e:
                st.error("Error: " + str(e))
        else:
            st.info("Chatbot can currently help with tracking. More features can be added.")

# ---------- Voice Input ----------
elif menu == "Voice Input":
    st.header("Voice Input (Upload an audio file)")
    st.info("Supported: wav, mp3. This will attempt to transcribe using Google STT.")
    audio_file = st.file_uploader("Upload audio file", type=["wav", "mp3"])
    if audio_file:
        st.write("Transcribing...")
        text = transcribe_audio_bytes(audio_file.getvalue(), audio_file.name)
        if text:
            st.success("Transcription:")
            st.write(text)
            # Populate submit form prefilled
            if st.button("Create complaint from this text"):
                # naive title+desc split
                title = text[:60]
                description = text
                data = {"user_name": "VoiceUser", "title": title, "description": description, "language": lang_code}
                r = requests.post(f"{API_BASE}/complaints", data=data)
                if r.status_code == 200:
                    st.success(f"Created — Tracking ID {r.json()['tracking_id']}")
                else:
                    st.error("Failed to create complaint.")
        else:
            st.error("Transcription failed.")
