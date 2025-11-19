import streamlit as st
import requests
import time

# --- CONFIGURATION ---
API_BASE_URL = "https://7lvz4qlxsk.execute-api.us-east-2.amazonaws.com"
# ---------------------

# Page Config: Set title and icon
st.set_page_config(page_title="Serverless Safebox", page_icon="🛡️", layout="centered")

# --- CUSTOM CSS FOR "HACKER" VIBE ---
st.markdown("""
<style>
    .stButton button {
        width: 100%;
        font-weight: bold;
        border-radius: 5px;
    }
    .success-box {
        padding: 20px;
        background-color: rgba(0, 255, 65, 0.1);
        border: 1px solid #00FF41;
        border-radius: 5px;
        text-align: center;
        margin-bottom: 20px;
    }
    .warning-box {
        padding: 20px;
        background-color: rgba(255, 80, 80, 0.1);
        border: 1px solid #FF5050;
        border-radius: 5px;
        text-align: center;
    }
</style>
""", unsafe_allow_html=True)

# --- SIDEBAR ---
with st.sidebar:
    st.title("🛡️ Safebox Intel")
    st.markdown("""
    **Protocol:**
    1.  **Encrypt:** File is uploaded to S3 Vault.
    2.  **Lock:** A unique Key ID is generated.
    3.  **Destroy:** Upon retrieval, the Key ID is burned.
    
    **Security Level:**
    *   AES-256 Encryption (S3 Standard)
    *   Atomic State DB (DynamoDB)
    *   Auto-Wipe (24hr TTL)
    """)
    st.divider()
    st.caption("Powered by AWS Serverless")

# --- MAIN HEADER ---
st.title("🛡️ Serverless Safebox")
st.markdown("### The Self-Destructing File Exchange")
st.write("Files are permanently deleted from the server immediately after they are downloaded.")

# --- TABS ---
tab_upload, tab_download = st.tabs(["📤  Secure Upload", "📥  Retrieve & Destroy"])

# ==========================================
# TAB 1: UPLOAD LOGIC
# ==========================================
with tab_upload:
    st.info("ℹ️ **Privacy Note:** Max file size is 10MB. Files expire in 24 hours if not retrieved.")
    
    col1, col2 = st.columns(2)
    with col1:
        uploaded_file = st.file_uploader("Select Payload", label_visibility="collapsed")
    with col2:
        password_input = st.text_input("PIN Code (Optional)", type="password", placeholder="e.g. 1234")

    if uploaded_file:
        st.write(f"**Selected:** `{uploaded_file.name}` ({uploaded_file.size / 1024:.1f} KB)")

    if st.button("🔒 Upload to Vault", type="primary"):
        if uploaded_file:
            # Progress Bar Effect
            progress_text = "Initiating Handshake..."
            my_bar = st.progress(0, text=progress_text)

            try:
                # 1. Get Presigned URL
                my_bar.progress(30, text="Requesting Secure Link...")
                file_name = uploaded_file.name
                file_bytes = uploaded_file.getvalue()
                
                payload = {"filename": file_name, "password": password_input if password_input else None}
                api_url = f"{API_BASE_URL.rstrip('/')}/upload"
                response = requests.post(api_url, json=payload)
                
                if response.status_code == 200:
                    my_bar.progress(60, text="Uploading Payload to S3...")
                    data = response.json()
                    file_id = data['file_id']
                    presigned_data = data['upload_data']
                    
                    # 2. Upload to S3
                    s3_response = requests.post(
                        presigned_data['url'],
                        data=presigned_data['fields'],
                        files={'file': (file_name, file_bytes)}
                    )
                    
                    if s3_response.status_code == 204:
                        my_bar.progress(100, text="Complete.")
                        time.sleep(0.5)
                        my_bar.empty()
                        
                        st.markdown(f"""
                        <div class="success-box">
                            <h3>✅ Upload Successful</h3>
                            <p>Share this File ID with the recipient.</p>
                            <h2 style="color: #00FF41; letter-spacing: 2px;">{file_id}</h2>
                        </div>
                        """, unsafe_allow_html=True)
                        st.warning("⚠️ Copy the ID now. It cannot be recovered.")
                    else:
                        st.error("Upload Failed.")
                else:
                    st.error(f"Server Error: {response.text}")
            except Exception as e:
                st.error(f"Connection Error: {e}")
        else:
            st.toast("⚠️ Please choose a file first.")

# ==========================================
# TAB 2: DOWNLOAD LOGIC
# ==========================================
with tab_download:
    # Initialize State
    if 'file_found' not in st.session_state:
        st.session_state.file_found = False
        st.session_state.dl_link = ""

    if not st.session_state.file_found:
        st.markdown("#### Enter Credentials")
        
        col_d1, col_d2 = st.columns([3, 2])
        with col_d1:
            download_id = st.text_input("File ID", placeholder="Enter the unique ID")
        with col_d2:
            download_pass = st.text_input("PIN Code", type="password", placeholder="If required")
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        if st.button("🔓 Retrieve File"):
            if download_id:
                with st.status("Accessing Vault...", expanded=True) as status:
                    st.write("Searching DynamoDB ledger...")
                    time.sleep(0.5)
                    
                    try:
                        payload = {"file_id": download_id, "password": download_pass if download_pass else None}
                        api_url = f"{API_BASE_URL.rstrip('/')}/download"
                        response = requests.post(api_url, json=payload)
                        
                        if response.status_code == 200:
                            data = response.json()
                            st.write("File found. Verifying integrity...")
                            st.write("⚠️ **Self-Destruct Triggered**")
                            status.update(label="Access Granted!", state="complete", expanded=False)
                            
                            # Update State
                            st.session_state.dl_link = data['download_url']
                            st.session_state.file_found = True
                            st.rerun()
                        else:
                            status.update(label="Access Denied", state="error", expanded=False)
                            st.error(f"Error: {response.text}")
                    except Exception as e:
                        st.error(f"Error: {e}")
            else:
                st.toast("Please enter a File ID.")
    
    else:
        # SUCCESS STATE - FILE RETRIEVED
        st.markdown("""
        <div class="warning-box">
            <h1>💣 FILE DESTROYED</h1>
            <p>The database record has been permanently deleted.</p>
            <p><strong>You have 5 seconds to download this file.</strong></p>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
        # The Download Button
        st.link_button("⬇️ Download Payload Now", st.session_state.dl_link, type="primary")
        
        st.divider()
        if st.button("🔄 Reset System"):
            st.session_state.file_found = False
            st.session_state.dl_link = ""
            st.rerun()
