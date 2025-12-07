<p align="center">
  <img src="https://img.shields.io/badge/AI-Agent-blueviolet?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Platform-YouTube-red?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Analytics-Share_of_Voice-orange?style=for-the-badge" />
  <img src="https://img.shields.io/badge/LLM-GPT--4o--mini-green?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Framework-Microsoft_AutoGen-yellow?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Dashboard-Streamlit-ff4b4b?style=for-the-badge" />
  <img src="https://img.shields.io/badge/Status-LIVE-brightgreen?style=for-the-badge" />
  <img src="https://img.shields.io/badge/License-MIT-lightgrey?style=for-the-badge" />
</p>

<p align="center">
  <a href="https://atomberg-sov-dashboard.streamlit.app/">
    <img src="https://img.shields.io/badge/Live_Dashboard-Open_Now-success?style=for-the-badge" />
  </a>
  <a href="https://github.com/Rusty141/AI-Agent">
    <img src="https://img.shields.io/badge/GitHub_Repo-Open_Project-blue?style=for-the-badge" />
  </a>
</p>



Perfect — here’s a **clean, professional, industry-grade `README.md`** tailored exactly for your project.
You can **copy–paste this directly** into your GitHub repo 👉
**[https://github.com/Rusty141/AI-Agent](https://github.com/Rusty141/AI-Agent)**

---

# 🚀 Atomberg AI – Cross-Platform Share of Voice (SoV) Intelligence Agent

An **AI-powered competitive intelligence system** that tracks brand visibility, engagement, and sentiment for **Atomberg smart & BLDC fans** across digital platforms — starting with **YouTube**, and designed to scale to **Google Search, Instagram, and X (Twitter)**.

✅ Live YouTube Agent
✅ Automated SoV Metrics
✅ AI-Generated Marketing Insights
✅ Interactive Streamlit Dashboard
✅ Enterprise-Ready Multi-Platform Architecture

---

## 📌 Problem Statement

Build an AI agent that:

* Searches smart-fan-related keywords on social platforms
* Analyzes top N results
* Measures **Share of Voice (SoV)** for Atomberg vs competitors
* Performs **Sentiment Analysis & Engagement Weighting**
* Generates **AI-based strategic recommendations**
* Visualizes everything on a **live dashboard**

---

## 🧠 What This System Does

### ✅ 1. Automated Data Collection

* Fetches top **N YouTube videos per keyword**
* Extracts:

  * Title
  * Description
  * Views, Likes, Comments
  * Top viewer comments

### ✅ 2. Brand Detection Engine

Uses regex-based NLP to detect:

* Atomberg
* Havells
* Crompton
* Orient
* Usha
* Bajaj
* Luminous

Across:

* Video titles
* Descriptions
* Comments

### ✅ 3. Sentiment Analysis

Lightweight lexicon-based sentiment scoring:

* Positive Voice
* Negative Voice
* Neutral Mentions

Used to compute:

> **Share of Positive Voice (SoPV)**

### ✅ 4. Share of Voice (SoV) Metrics

Calculated for each brand:

| Metric         | Meaning                          |
| -------------- | -------------------------------- |
| Content SoV    | % of videos mentioning the brand |
| Engagement SoV | % of total weighted engagement   |
| Comment SoV    | % of comment mentions            |
| SoPV           | % of all positive mentions       |

✅ Overall SoV
✅ Per-keyword SoV (Brownie points)

---

## 🤖 AI Marketing Insight Agent

Uses **GitHub Models (GPT-4o-mini)** to:

* Interpret numeric SoV results
* Identify brand strengths & weaknesses
* Analyze keyword-level performance
* Generate **actionable marketing strategies**
* Auto-generate recommendations in **insights.md**

---

## 📊 Live Streamlit Dashboard

🔗 **Live Demo**
👉 [https://atomberg-sov-dashboard.streamlit.app/](https://atomberg-sov-dashboard.streamlit.app/)

### Dashboard Features:

* Overall SoV comparison
* Per-keyword heatmap
* Engagement vs Positive Voice scatter plot
* Brand performance KPIs
* Interactive filters (brand, keyword, metric)
* Platform-ready filtering (YouTube now, others extendable)

---

## 🛠️ Technology Stack

| Layer           | Tool                        |
| --------------- | --------------------------- |
| Language        | Python 3.11                 |
| APIs            | YouTube Data API v3         |
| NLP             | Regex + Lexicon Sentiment   |
| AI Agent        | Microsoft AutoGen           |
| LLM             | GitHub Models (GPT-4o-mini) |
| Data            | Pandas                      |
| Visualization   | Plotly                      |
| Frontend        | Streamlit                   |
| Deployment      | Streamlit Cloud             |
| Version Control | GitHub                      |

---

## 📂 Project Structure

```
AI-Agent/
│
├── projects/
│   └── atomberg_sov/
│       ├── atomberg_sov_agent.py
│       ├── inspect_results.py
│       ├── inspect_sov_by_keyword.py
│
├── streamlit_app.py
├── overall_sov.json
├── sov_by_keyword.json
├── raw_youtube_records.json
├── insights.md
├── requirements.txt
├── .env.example
└── README.md
```

---

## ⚙️ Setup Instructions (Local)

### 1️⃣ Clone Repository

```bash
git clone https://github.com/Rusty141/AI-Agent.git
cd AI-Agent
```

### 2️⃣ Create Virtual Environment

```bash
python -m venv venv
venv\Scripts\activate
```

### 3️⃣ Install Dependencies

```bash
pip install -r requirements.txt
```

### 4️⃣ Create `.env` File

```env
YOUTUBE_API_KEY=your_youtube_key_here
GITHUB_TOKEN=your_github_models_token_here
```

---

## ▶️ Run the AI Agent

```bash
python projects/atomberg_sov/atomberg_sov_agent.py
```

This generates:

* `overall_sov.json`
* `sov_by_keyword.json`
* `raw_youtube_records.json`
* `insights.md`

---

## ▶️ Run the Dashboard

```bash
streamlit run streamlit_app.py
```

---

## 🌍 Multi-Platform Expansion (Future-Ready)

| Platform      | API Required  | Status |
| ------------- | ------------- | ------ |
| YouTube       | ✅ Implemented |        |
| Google Search | ✅ Planned     |        |
| Instagram     | ✅ Planned     |        |
| X (Twitter)   | ✅ Planned     |        |

Architecture already supports:

```python
{
  "platform": "youtube"
}
```

So adding new platforms requires **only new ingestion tools** — no change in analytics core.

---

## 📄 2-Pager Submission Document

✅ Auto-generated
✅ Tech Stack + Findings
✅ Business Impact

Available as:

* PDF
* PPT
* Markdown

---

## 🏆 Business Impact

* Enables **real-time brand intelligence**
* Optimizes **content & ad strategy**
* Identifies **keyword-level dominance**
* Strengthens **market positioning**
* Drives **data-backed marketing decisions**

---

## 👨‍💻 Author

**Rahul Desai**
Electronics & Telecommunication Engineer
AI | Robotics | Data Intelligence | Embedded Systems

---

If you want, I can also:

✅ Add **badges & shields** to your GitHub
✅ Add a **screenshots section**
✅ Create a **GitHub Pages landing site**
✅ Add **Google/Instagram/X mock pipelines for demo**

Just say the word 🔥
