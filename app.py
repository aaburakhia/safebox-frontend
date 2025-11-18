import streamlit as st
import requests
import json

# --- CONFIGURATION ---
# REPLACE THIS with your API Gateway Invoke URL
# It usually ends with .com/ or .com/default/
API_BASE_URL = "https://7lvz4qlxsk.execute-api.us-east-2.amazonaws.com"
# ---------------------

st.set_page_config(page_title="Serverless Safebox", layout="centered")

st.title("🔒 Serverless Safebox")
st.write("Secure, self-destructing file sharing. Files are deleted permanently after one download.")

# Create Tabs for Upload and Download
tab1, tab2 = st.tabs(["📤 Upload File", "📥 Download File"])

# --- TAB 1: UPLOAD ---
with tab1:
    st.header("Upload a File")
    uploaded_file = st.file_uploader("Choose a file (Max 10MB)")
    password_input = st.text_input("Set a PIN/Password (Optional)", type="password")
    
    if st.button("Secure Upload"):
        if uploaded_file is not None:
            with st.spinner("Encrypting and uploading..."):
                try:
                    # 1. Request Presigned URL from our Lambda
                    file_name = uploaded_file.name
                    file_bytes = uploaded_file.getvalue()
                    
                    payload = {
                        "filename": file_name,
                        "password": password_input if password_input else None
                    }
                    
                    # Call our /upload endpoint
                    api_url = f"{API_BASE_URL.rstrip('/')}/upload"
                    response = requests.post(api_url, json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        file_id = data['file_id']
                        presigned_data = data['upload_data']
                        
                        # 2. Upload DIRECTLY to S3 (Bypassing Lambda limit)
                        # We use the 'fields' and 'url' provided by AWS
                        s3_response = requests.post(
                            presigned_data['url'],
                            data=presigned_data['fields'],
                            files={'file': (file_name, file_bytes)}
                        )
                        
                        if s3_response.status_code == 204:
                            st.success("✅ File Secured!")
                            st.info(f"**File ID:** `{file_id}`")
                            st.warning("Copy this ID. You need it to download the file.")
                        else:
                            st.error(f"Failed to upload to S3. Status: {s3_response.status_code}")
                    else:
                        st.error(f"Backend Error: {response.text}")
                        
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please select a file first.")

# --- TAB 2: DOWNLOAD ---
with tab2:
    st.header("Retrieve a File")
    download_id = st.text_input("Enter File ID")
    download_pass = st.text_input("Enter PIN/Password (if set)", type="password")
    
    if st.button("Retrieve & Destroy"):
        if download_id:
            with st.spinner("Verifying and retrieving..."):
                try:
                    payload = {
                        "file_id": download_id,
                        "password": download_pass if download_pass else None
                    }
                    
                    # Call our /download endpoint
                    api_url = f"{API_BASE_URL.rstrip('/')}/download"
                    response = requests.post(api_url, json=payload)
                    
                    if response.status_code == 200:
                        data = response.json()
                        download_link = data['download_url']
                        st.success("✅ Access Granted!")
                        st.write("This file has been marked for destruction. Download it now.")
                        st.link_button("⬇️ Download File", download_link)
                    else:
                        st.error(f"Access Denied: {response.text}")
                        
                except Exception as e:
                    st.error(f"Error: {e}")
        else:
            st.warning("Please enter a File ID.")
