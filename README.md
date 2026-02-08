# 🔍 Cross-Stack Incident Analyzer

AI-powered tool that finds **production incident solutions across different programming languages**
(Java, Python, Node.js).

---

## 🧠 Problem

Developers waste hours debugging issues that someone in **another tech stack already solved**.

- Knowledge is siloed by language
- Root causes are the same, but fixes are rediscovered repeatedly
- On-call time is wasted reinventing solutions

---

## 💡 Solution

**Semantic Search + AI** finds similar production incidents across stacks and generates
**actionable, language-specific runbooks**.

---

## 🎯 What It Does

1. You describe an incident  
   _Example: “API timing out to database”_
2. AI searches historical production incidents using **semantic similarity**
3. Finds matches from **your stack** *and* **other stacks** with the same root cause
4. Generates a **step-by-step solution** adapted to your language

> **Key Insight:**  
> A database timeout in Java has the same fix as Python — just different syntax.

---

## 🛠️ Tech Stack

- **Frontend:** Streamlit
- **Database:** PostgreSQL (incident metadata)
- **Vector Search:** Qdrant (semantic embeddings)
- **AI:** Groq (Llama-3.3-70B, free API)
- **Embeddings:** Sentence-Transformers

---

## 🚀 Quick Setup

### 1️⃣ Install Dependencies

```bash
pip install streamlit groq sentence-transformers qdrant-client psycopg2-binary python-dotenv torch


### 2. Setup PostgreSQL

```bash
# Install PostgreSQL, then:
psql -U postgres

CREATE DATABASE incidents;
CREATE USER incident_user WITH PASSWORD 'yourpassword';
GRANT ALL PRIVILEGES ON DATABASE incidents TO incident_user;
\c incidents
GRANT ALL ON SCHEMA public TO incident_user;
\q
```

### 3. Configure Environment

Create `.env` file:

```bash
GROQ_API_KEY=gsk_your_key_here
DB_HOST=localhost
DB_NAME=incidents
DB_USER=incident_user
DB_PASSWORD=yourpassword
DB_PORT=5432
```

Get free Groq API key: https://console.groq.com/keys

### 4. Generate & Import Data

```bash
# Generate 45 mock incidents
python generateData.py

# Setup databases (PostgreSQL + Qdrant)
python setup_database.py
```

### 5. Run App

```bash
streamlit run main.py
```

Open: http://localhost:8501

---

## 📖 How to Use

**Try Quick Examples (sidebar):**
- 🔴 Database Timeout
- 🟡 Null Reference  
- 🟠 Memory Leak

**Or describe your own incident:**
1. Enter incident description
2. Select your tech stack (Java/Python/Node.js)
3. Paste error message (optional)
4. Click "Analyze"

**You'll get:**
- Root cause analysis
- Step-by-step solution
- Similar incidents from same stack
- Cross-stack insights (other languages with same issue)

---

## 🔬 How It Works

```
User Input → PostgreSQL (fetch data) 
          → Qdrant (vector similarity search)
          → Groq LLM (generate solution)
          → Display results
```

**Example Flow:**
1. User: "Payment API timeout to database"
2. Vector search finds: Java Stripe timeout (92% similar) + Python pool exhaustion (89% similar)
3. AI generates runbook: "Increase connection pool from 50 to 200..."
4. Shows why Python solution applies to Java (same root cause)

---

## 📁 Project Files

```
├── main.py              # Streamlit UI
├── llm_service.py       # AI + Search logic
├── search_engine.py     # Hybrid search (Qdrant + PostgreSQL)
├── generateData.py      # Creates 45 mock incidents
├── setup_database.py    # Database setup
├── .env                 # API keys (create this)
└── data/
    ├── incidents.json
    └── qdrant_storage/
```

---

## 🧪 Test Queries

**Database Timeout:**
```
"Payment API timing out after 30 seconds when connecting to PostgreSQL. 
Customers can't checkout."

Tech: java
Error: SocketTimeoutException
```

**Null Reference:**
```
"NullPointerException when accessing user object after account deletion."

Tech: java
Error: NullPointerException at line 156
```

**Memory Leak:**
```
"Node.js memory growing from 200MB to 4GB in 6 hours. Server crashes."

Tech: nodejs  
Error: JavaScript heap out of memory
```

---

## 💡 Why This Matters

- **Cross-Stack Learning:** Java devs learn from Python solutions
- **Faster Debugging:** Find fixes in seconds, not hours
- **Pattern Recognition:** Same root cause, different syntax
- **Real Incidents:** Based on actual production scenarios

---

## 🔧 Troubleshooting

**Can't connect to database?**
```bash
# Check PostgreSQL is running
psql -U postgres -d incidents
```

**Groq API error?**
- Check your API key in `.env`
- Get new key: https://console.groq.com/keys

**No data found?**
```bash
# Re-run setup
python setup_database.py
```

---

## 📊 Dataset

45 realistic production incidents:
- 15 Java (payment gateway, order service, auth)
- 15 Python (user service, billing, analytics)  
- 15 Node.js (notification, API gateway, inventory)

Each with:
- Root cause
- Error message
- Step-by-step solution
- Infrastructure context

---

## 🚀 Future Ideas

- Real-time incident ingestion
- More tech stacks (Go, Rust)
- Integration with monitoring tools
- Export runbooks as PDF

---

