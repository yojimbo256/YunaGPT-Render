## **Yuna AI – Personal Cognitive Assistant**  
**Version:** 1.0.0  
📅 **Last Updated:** March 7, 2025  

---

### **🧠 What is Yuna AI?**  
Yuna AI is a **personal cognitive assistant** designed to provide:  
✅ **Long-term memory recall** (persistent storage)  
✅ **Conversational AI capabilities** (via LLM)  
✅ **Secure HTTPS communication**  
✅ **FastAPI backend** with SQLite memory storage  
✅ **Modern web UI** (Next.js frontend)

---

## **📂 Project Structure**
```
Yuna-AI/
│
├── src/              # Backend API & Core Logic
│   ├── main.py       # FastAPI application entry point
│   ├── memory.py     # Memory storage & retrieval system
│   ├── database/     # Database interactions
│   ├── models/       # AI models & processing
│   ├── utils/        # Utility functions
│   └── api/          # API endpoints
│
├── frontend/         # Next.js Web Interface (Chat UI)
│
├── data/             # Stored data & logs
│   ├── database/     # SQLite memory storage
│   ├── yuna_log.txt  # Debug logs
│   ├── yuna_memory.json  # Cached memory
│   ├── yuna_tasks.json   # Task tracking
│
├── scripts/          # Automation & server scripts
│   ├── run_server.sh
│   ├── generate_ssl.sh
│   ├── migrate_db.py
│   ├── init_db.py
│
├── tests/            # Unit tests
│   ├── test_api.py
│   ├── test_chat.py
│   ├── test_memory.py
│
├── config/           # Configuration files
│   ├── config.ini
│   ├── requirements.txt
│
├── README.md         # Project documentation
└── LICENSE           # License information
```

---

## **🚀 Getting Started**
### **1️⃣ Install Dependencies**
```bash
cd ~/Desktop/Yuna-AI
python3 -m venv venv
source venv/bin/activate
pip install -r config/requirements.txt
```

### **2️⃣ Start the Backend (FastAPI)**
```bash
uvicorn src.main:app --host 0.0.0.0 --port 8000 \
    --ssl-keyfile /home/yojimbo256/server.key \
    --ssl-certfile /home/yojimbo256/server.crt --reload
```

### **3️⃣ Start the Frontend (Next.js)**
```bash
cd frontend/yuna-web
npm install
npm run dev
```
🔗 Open the browser: **https://localhost:3000**

---

## **🔍 Features & Capabilities**
✅ **Secure HTTPS API** (self-signed SSL)  
✅ **FastAPI Backend** with SQLite memory storage  
✅ **Persistent Memory** via `long_term_memory.db`  
✅ **Fuzzy Search** (search past conversations)  
✅ **Multi-step Reasoning** (task breakdowns)  
✅ **Local & Cloud AI Execution** (scalable)  

---

## **💡 How to Use**
1. **Chat with Yuna** via the **web UI** at `https://localhost:3000`.  
2. Yuna **remembers conversations** and recalls relevant context.  
3. Use `/history` API to **retrieve past interactions**.  
4. Use `/chat` API to **send and receive AI responses**.  

---

## **🛠️ Contributing**
We welcome contributions!  
- **Fork the repo** and create a new branch.  
- **Submit a PR** for review.  
- **Report bugs** via GitHub issues.  

---

## **📜 License**
Yuna AI is **open-source software** licensed under the **MIT License**.  

---
