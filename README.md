# hse-ai-assistant
AI-powered system for Health, Safety &amp; Environment (HSE) risk management and hazard assessment using text and image data.

# Overview 
This project implements an intelligent HSE assistant using AI agents in LangChain. The system analyzes workplace hazards from text and images, checks compliance with CFST 6508 standards, and generates structured, professional HSE reports automatically. It demonstrates the use of modular AI agents for risk assessment, compliance verification, and report generation.

# Features
- Analyze text or images of workplace hazards.
- Generate structured JSON analysis (type of hazard, description, risks, estimated severity).
- Compliance checking against CFST 6508 PDF documents.
- Automatic generation of professional HSE reports in PDF.
- Modular architecture using LangChain tools and OpenAI LLMs.

# Tech Stack
- **Language:** Python 3
- **Libraries:** LangChain, FPDF, FAISS, PyPDFLoader, OpenAI API
- **AI Models:** GPT-4o-mini (OpenAI)
- **Frontend:** HTML, CSS, JavaScript  
- **Backend:** Python 3, Flask 
- **Other Tools:** virtual environment (venv)

# How to Run
1. Clone the repository:
```bash
git clone https://github.com/YourUser/hse-ai-assistant.git 
```
2. Activate the virtual environment:
- Windows (PowerShell):
```bash
venv\Scripts\Activate.ps1
```
- Linux / macOS:
```bash
source venv/bin/activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set your OpenAI API key in agents.py:
```bash
OPENAI_API_KEY=your_api_key_here
```

5. Run the main script:
```bash
python agents.py
```

