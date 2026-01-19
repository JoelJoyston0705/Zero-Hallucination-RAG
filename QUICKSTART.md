# 🚀 Bible RAG: Quick Start Guide

Follow these steps to get your own high-fidelity research console running in minutes.

## 🛠️ Prerequisites
- **Python 3.10+**
- **OpenAI API Key**: Required for the generation and verification agents.
- **Git**: To clone the repository.

---

## 💻 Installation

### 1. Clone the Repository
```bash
git clone https://github.com/JoelJoyston0705/Zero-Hallucination-RAG.git
cd Bible_RAG
```

### 2. Setup Virtual Environment (Recommended)
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install Requirements
```bash
pip install -r requirements.txt
```

### 4. Configure Environment
Create a `.env` file in the root directory and add your OpenAI Key:
```env
OPENAI_API_KEY=sk-your-key-here
```

---

## 🧠 System Initialization

Before running the app, you must build the **Vector Indices**. This processes the 7,000+ verses of the Bible into a searchable FAISS database.

```bash
python setup.py
```
*This will download the source text and generate embeddings. It usually takes 1-2 minutes.*

---

## 🚀 Running the Console

To start the premium research interface, run the following command:

```bash
python run_app.py
```
*(Note: Using `run_app.py` is recommended as it includes safety guards for macOS stability.)*

---

## 🛡️ Trying the Features

1. **Register**: On first launch, go to the **Register** tab on the login screen to create your local research account.
2. **The Expert Test**: Ask *"How did Joseph's life change in Egypt?"* to see high-speed retrieval.
3. **The Hallucination Test**: Ask *"What does the Bible say about Tesla cars?"* to see the **Verifier Agent** trigger a red warning badge.
4. **The Pizza Test**: Ask for a pizza recipe to see the **Domain Guard** prevent the model from using outside training data.

---

## 📈 Troubleshooting
| Issue | Solution |
| :--- | :--- |
| **Segmentation Fault** | Always use `python run_app.py` instead of the standard streamlit command. |
| **Index Not Found** | Ensure you ran `python setup.py` completely. |
| **Login Loops** | Registration and logins are stored locally in `data/users.json`. If you get stuck, you can safely delete that file to reset. |

---
**Build for Truth. Built for Trust.**
