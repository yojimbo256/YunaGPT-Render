## **Yuna AI – Personal Cognitive Assistant**  
**Version**: 1.0.0  
📅 **Last Updated**: March 7, 2025  

### **🎓 Yuna AI – A PhD Research Project in Systems Engineering**
Yuna AI is part of a **PhD research project** in **Systems Engineering** focused on developing a **personalized cognitive assistant** that adapts and evolves with the user’s needs. This research involves the application of **reinforcement learning (RL)**, **transformer-based architectures (TA)**, and **advanced memory management techniques** (PCM/SSAM) to create an **adaptive AI** system capable of long-term task management, goal tracking, and strategic decision-making.

---

### **🧠 What is Yuna AI?**  
Yuna AI is a **personal cognitive assistant** designed to provide:  
✅ **Long-term memory recall** (persistent storage)  
✅ **Conversational AI capabilities** (via LLM)  
✅ **Secure HTTPS communication**  
✅ **Flask backend** with SQLite memory storage  
✅ **AI model powered by Mistral 7B** for personalized interactions  
✅ **Hybrid AI execution** with local & cloud processing  
✅ **Real-time memory management** using PCM/SSAM  
✅ **Contextual reasoning** and **task management**  
✅ **Scalable infrastructure** with potential for cloud offloading  

---

## **📂 Project Structure**
```
Yuna-AI/
│
├── src/              # Backend API & Core Logic
│   ├── main.py       # Flask application entry point
│   ├── memory.py     # Memory storage & retrieval system
│   ├── database/     # Database interactions
│   ├── models/       # AI models & processing (Mistral 7B)
│   ├── utils/        # Utility functions
│   └── api/          # API endpoints
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

### **2️⃣ Start the Backend (Flask)**
```bash
python3 src/main.py
```

### **3️⃣ Start the Frontend (React/Next.js)** *(if needed)*
```bash
cd frontend/yuna-web
npm install
npm run dev
```
🔗 Open the browser: **https://localhost:3000**

---

## **🔍 Features & Capabilities**
✅ **Secure HTTPS API** (self-signed SSL)  
✅ **Flask Backend** with SQLite memory storage  
✅ **Persistent Memory** via `long_term_memory.db`  
✅ **Fuzzy Search** (search past conversations)  
✅ **Multi-step Reasoning** (task breakdowns)  
✅ **Local & Cloud AI Execution** (scalable, using Mistral 7B)  
✅ **Contextual Reasoning** and **Adaptive Task Management**  
✅ **Memory System** (PCM/SSAM for long-term recall)  

---

## **💡 How to Use**
1. **Chat with Yuna** via the **web UI** at `https://localhost:3000`.  
2. **Yuna remembers conversations** and recalls relevant context for future interactions.  
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
