# SecureWealth Twin — Digital Wealth Prototype

![SecureWealth Banner](https://img.shields.io/badge/SecureWealth-Digital%20Twin-c8102e?style=for-the-badge)
![Status](https://img.shields.io/badge/Status-Simulation%20Mode-orange?style=for-the-badge)
![Security](https://img.shields.io/badge/Security-Wealth%20Protection%20Shield-green?style=for-the-badge)

SecureWealth Twin is a professional-grade "Digital Twin" prototype designed to safeguard and grow personal and business wealth. It integrates real-time market intelligence, multi-bank account aggregation, and a robust AI-driven security layer to protect against cyber-fraud and unauthorized transactions.

---

## 🛡️ The Wealth Protection Shield
The core innovation of SecureWealth is the **Wealth Protection Shield**, an AI-driven security layer that monitors all sensitive actions.
- **Risk-Based Challenges**: High-value transactions (SIP changes, Asset sales) automatically trigger a security gate.
- **Anti-Bot Verification**: Implements dynamic Captcha and Password re-authentication to prevent automated attacks.
- **Behavioral Analysis**: Evaluates risk scores based on transaction velocity, device trust, and interaction patterns.

## 🚀 Key Features
- **Account Aggregator (AA) Integration**: Seamlessly link external bank accounts (SBI, HDFC, ICICI) to gather a consolidated financial picture.
- **Real-Time Market Data**: Live ticker feeds for NIFTY 50, SENSEX, and BANK NIFTY via verified market engines.
- **Physical Asset Tracking**: Register and manage Gold, Real Estate, and Vehicles with **Blockchain-verified** audit logs.
- **Dual-Mode Dashboard**: Toggle between **Individual** and **Corporate/Business** views for tailored financial metrics.
- **AI-Advisor (RAG)**: A conversational AI assistant powered by a Knowledge Base to provide strategic investment recommendations.
- **Wealth Simulator**: Model 10-year wealth projections based on monthly savings and market performance.

## 🛠️ Tech Stack
### **Frontend**
- **React 18**: Modern, component-based UI.
- **Tailwind CSS**: Premium, responsive styling.
- **Recharts**: Dynamic financial data visualization.
- **WealthContext**: Global state management for real-time updates.

### **Backend (Microservices)**
- **FastAPI (Python)**: High-performance asynchronous API framework.
- **SQLAlchemy**: Robust ORM for asset and audit logging.
- **LangChain & FAISS**: Powering the RAG (Retrieval-Augmented Generation) Chatbot.
- **Yahoo Finance API**: Real-time market data source.
- **HTTPX**: Asynchronous inter-service communication.

---

## 🚦 Getting Started

### **1. AI Intelligence Service (Port 8001)**
```bash
cd SecureWealth-AI-main
pip install -r requirements.txt
python main.py
```

### **2. Main Backend (Port 8000)**
```bash
cd SecureWealth-Project/backend
pip install -r requirements.txt
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### **3. Frontend Dashboard (Port 3000)**
```bash
cd SecureWealth-Project/frontend
npm install
npm start
```

---

## ⚖️ Compliance & Responsibility
- **FOR SIMULATION/DEMO ONLY**: This application is a prototype for the PSB Hackathon 2026.
- **Explainable AI (XAI)**: All investment suggestions include an "Explain" link to provide logic transparency.
- **KYC First**: Real-world transactions are gated by a simulated KYC verification status.

---
**Developed for the PSB Hackathon 2026 — Cyber Security & Fraud in Wealth Management.**
