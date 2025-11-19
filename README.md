# 🛡️ Serverless Safebox

### A secure, "self-destructing" file sharing service built on AWS.

[![Streamlit App](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)](https://safebox.streamlit.app)

**The Problem:** Sending sensitive files (API keys, contracts, passwords) via email or Slack is insecure because the data persists indefinitely in history logs.

**The Solution:** Serverless Safebox allows users to upload a file and generate a unique link. The file is permanently deleted from the server immediately after it is downloaded once, or after 24 hours—whichever comes first.

---

## 🏗️ Architecture & Workflow

This project uses a **Serverless Architecture** to ensure low cost (pay-per-use) and high scalability.

### The Stack
*   **Frontend:** Streamlit (Python)
*   **API:** AWS API Gateway (HTTP API)
*   **Compute:** AWS Lambda (Python 3.12)
*   **Database:** Amazon DynamoDB
*   **Storage:** Amazon S3

### System Logic
1.  **Direct-to-S3 Uploads:** Instead of passing file data through the Lambda function (which is expensive and has a 6MB payload limit), the backend generates an **S3 Presigned URL**. The frontend uses this "VIP pass" to upload the file directly to the S3 bucket.
2.  **Atomic State Management:** DynamoDB tracks the state of every file.
3.  **The "Self-Destruct" Mechanism:** When a download is requested, the Lambda function performs an atomic `UpdateItem` operation on DynamoDB to mark the file as `Destroyed`. This prevents "Race Conditions"—if two users try to download the file at the exact same millisecond, only one will succeed.

---

## 🚀 Key Technical Decisions

### 1. Why Presigned URLs?
Streaming large files through an API Gateway + Lambda setup introduces latency and strict size limits. By generating a Presigned Post URL, I offloaded the heavy network traffic directly to S3, allowing the Lambda function to run for only milliseconds (saving cost).

### 2. Handling Race Conditions
A naive approach would be to `Get` the file status, check if it's active, and then `Update` it. However, in a distributed system, two requests could happen between the "Get" and the "Update."
**My Solution:** I used DynamoDB's conditional `UpdateItem` to perform the check and the lock in a single, atomic transaction.

### 3. Security & Lifecycle
*   **Principle of Least Privilege:** The Lambda functions use a custom IAM role with strictly scoped permissions (only specific actions on specific resources).
*   **Auto-Expiration:** I enabled **DynamoDB TTL (Time-To-Live)** to automatically expire and delete records after 24 hours, ensuring no "digital waste" is left behind.

---

## 📸 How to Run Locally

**Prerequisites:**
*   Python 3.10+
*   An active AWS Account (if deploying your own backend)

```bash
# 1. Clone the repository
git clone https://github.com/your-username/safebox-frontend.git

# 2. Install dependencies
pip install -r requirements.txt

# 3. Run the Streamlit App
streamlit run app.py
