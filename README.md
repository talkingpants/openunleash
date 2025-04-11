# OpenUnleash

OpenUnleash enables a [Custom GPT](https://chat.openai.com/gpts) to securely execute code on an AWS EC2 virtual machine using a backend API. Ideal for testing, evaluating, or sandboxing code directly from GPT interactions.

---

## ✨ Features
- Execute code remotely from a GPT via API calls
- Support for multiple languages (e.g., Python, Node.js)
- Secure interaction between ChatGPT and AWS EC2
- Logs and outputs returned to GPT in real-time
- Optional GitHub integration for syncing and testing code from repositories

---

## 🤝 Architecture
```text
Custom GPT → API Action → Backend Server → AWS EC2 (via SSH) → Output Returned
```

---

## ♻ Workflow
1. **Custom GPT** sends code and language info to a backend API.
2. **Backend server** authenticates the request and SSHs into the EC2 instance.
3. **EC2** executes the code in a sandboxed environment (optionally Dockerized).
4. **Output** is sent back to the GPT as a response.

---

## 🚀 Getting Started

### 1. Set Up Your AWS EC2
- Launch an EC2 instance (Ubuntu recommended)
- Install necessary language runtimes (e.g., Python, Node)
- Enable key-based SSH access

### 2. Create Your Backend API
You can use Flask (Python) or Express (Node.js). Example endpoint:
```json
POST /run-code
{
  "language": "python",
  "code": "print('Hello from EC2!')"
}
```
The API securely SSHs into EC2 and executes the received code.

### 3. Add an Action to Your Custom GPT
- Go to https://chat.openai.com/gpts and click **Create**
- Define an action that connects to your backend:
```json
{
  "name": "Run Code",
  "description": "Executes code on your AWS VM",
  "endpoint": "https://your-api.com/run-code",
  "method": "POST",
  "params": ["language", "code"]
}
```
- GPT will now be able to run code on your VM!

### 4. Configure GitHub Integration (Optional)
- Create a **GitHub Personal Access Token (PAT)** with `repo` access
- Set up a new endpoint in your backend (e.g., `/clone-repo`) that:
  - Accepts a GitHub repo URL
  - Clones the repo to the EC2 instance or a temporary container
  - Optionally runs a setup script or test suite
- Update your GPT action or logic to support this workflow:
```json
{
  "name": "Run GitHub Repo",
  "description": "Clones and tests a GitHub repo on the AWS VM",
  "endpoint": "https://your-api.com/clone-repo",
  "method": "POST",
  "params": ["repo_url"]
}
```
- Always verify access levels and sanitize inputs to avoid injection or abuse.

---

## 🔐 Security & Best Practices
- **Never expose SSH keys** or AWS secrets in your GPT or API
- Use **API authentication** (key-based, OAuth, or IP allow-lists)
- **Sandbox code** using Docker or similar tools
- Limit command scope and sanitize all inputs

---

## 🚀 Enhancements (Optional)
- Return output logs as downloadable files
- Store session logs in S3
- Auto-cleanup containers post execution
- Trigger GitHub Actions from GPT
- Deploy containerized test environments per repo

---

## 📖 License
GPL-3.0 License

---

## ✈ Contributing
PRs welcome! If you're using a cool GPT + VM setup, share it via issues or discussions.

---

## 🤝 Let's Connect
Feel free to fork, adapt, and contribute. Got questions or ideas? File an issue or reach out!
