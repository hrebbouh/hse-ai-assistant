import os
import base64
import re
import textwrap
from fpdf import FPDF
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyPDFLoader
from langchain_community.vectorstores import FAISS
from langchain.chains import RetrievalQA
from langchain.tools import Tool

os.environ["OPENAI_API_KEY"] = "" #add the openai key

llm = ChatOpenAI(model="gpt-4o-mini", temperature=0.2)

def encode_image(image_path):
    with open(image_path, "rb") as f:
        return base64.b64encode(f.read()).decode("utf-8") #base64 converts an image to text so it can be used by the llm

# --- Safety Agent ---
def safety_analysis_tool(text: str = None, image_path: str = None) -> str:
    """
    Analyze a workplace hazard (text and/or image) and return structured JSON.
    Fields: type_danger, description, risques, gravite_estimee
    """
    if not text and not image_path:
        return "Error: Provide either text or image_path."

    content = []

    if text:
        content.append({
            "type": "text",
            "text": f"""Tu es un assistant HSE.
Analyse les éléments fournis (texte et/ou image).
Voici une description brute d’un danger : "{text}"
Produis une analyse factuelle et professionnelle.
La sortie doit être concise et structurée en JSON avec les champs :
- type_danger
- description
- risques
- gravite_estimee
Ne propose pas encore de mesures préventives ni de rapport final."""
        })

    if image_path:
        image_base64 = encode_image(image_path)
        content.append({
            "type": "image_url",
            "image_url": {"url": f"data:image/jpeg;base64,{image_base64}"}
        })

    response = llm.invoke([HumanMessage(content=content)])
    return response.content

# --- Wrap as a LangChain Tool ---

# Tool is a LangChain concept:
# Makes a function callable by LangChain agents.
# Stores a name and description, so agents can understand when to use it.

safety_agent_tool = Tool(
    name="SafetyAgent",
    func=safety_analysis_tool,
    description="Analyze text or images of workplace hazards and return a JSON analysis."
)

# --- Compliance Agent (CFST 6508) ---  //is also implementing a rag pipeline
def compliance_checker_tool(agent_output: str, pdf_path: str, company_size: int = 20) -> str:
    """
    Checks workplace hazard compliance based on a PDF (CFST 6508).
    Returns structured answer with:
    - conformity (conforme / non conforme)
    - actions to take
    - reasoning with references to the document
    """

    loader = PyPDFLoader(pdf_path) #reads the pdf
    documents = loader.load() # returns a Document object containing data for each page
    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100) # we need the overlap bcs we need context around the text
    docs = splitter.split_documents(documents) 

    embeddings = OpenAIEmbeddings()
    vectorstore = FAISS.from_documents(docs, embeddings) # vector db of each chunk

    qa_chain = RetrievalQA.from_chain_type(
        llm=llm,
        retriever=vectorstore.as_retriever(search_kwargs={"k": 4}), # return top 4 relevant chunks for each query
        return_source_documents=True
    )

    query = f"""
Analyse la situation suivante selon la directive CFST 6508.
Description du danger: "{agent_output}"
Taille de l'entreprise: {company_size} collaborateurs
Tâches :
1. Identifier dangers particuliers selon annexe 1.
2. Vérifier si spécialistes MSST requis.
3. Expliquer avec passages du document.
4. Avis de conformité (conforme / non conforme / mesures à prendre).
5. Plan d’action priorisé.
"""
    result = qa_chain.invoke(query)
    return result["result"]

compliance_agent_tool = Tool(
    name="ComplianceChecker",
    func=compliance_checker_tool,
    description="Checks a workplace hazard against CFST 6508 PDF and returns compliance advice."
)
# --- HSE Report Generator ---
def generate_hse_report(agent_output, compliance_report, company_name="Entreprise XYZ", llm_model=llm):
    prompt = f"""
Tu es un expert HSE senior.
Rédige un rapport complet et structuré pour {company_name} :
Description du danger : {agent_output}
Rapport de conformité : {compliance_report}
Le rapport doit contenir :
- Résumé exécutif
- Analyse détaillée
- Conformité CFST 6508
- Recommandations et plan d'action priorisé
- Conclusion
Style professionnel, clair, titres et sous-titres.
"""
    response = llm_model.invoke([HumanMessage(content=prompt)]) # invoke : send a query (or messages) to the model and get a response.
    return response.content

def safe_wrap_text(text, width=100):
    wrapped_lines = []
    for line in text.split("\n"):
        line = line.strip()
        if not line:
            wrapped_lines.append("")
            continue
        if " " in line:
            wrapped_lines.extend(textwrap.wrap(line, width=width))
        else:
            wrapped_lines.extend(re.findall(f".{{1,{width}}}", line))
    return wrapped_lines

def export_to_pdf_unicode(text, filename="rapport_hse.pdf", wrap_width=100):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_font("DejaVu", "", "DejaVuSans.ttf")
    pdf.add_font("DejaVu", "B", "DejaVuSans-Bold.ttf")

    pdf.set_font("DejaVu", "B", 20)
    pdf.set_text_color(0, 51, 102)
    pdf.multi_cell(0, 12, "Rapport HSE", align="C")
    pdf.ln(10)

    clean_text = re.sub(r"(#+|\*\*)", "", text)
    lines = safe_wrap_text(clean_text, width=wrap_width)

    for line in lines:
        line = line.strip()
        if re.match(r"^(Résumé Exécutif|Analyse Détaillée|Conformité|Recommandations|Plan d'Action|Conclusion)", line):
            pdf.set_font("DejaVu", "B", 16)
            pdf.set_text_color(0, 51, 102)
            pdf.multi_cell(0, 10, line)
            pdf.ln(2)
            pdf.set_font("DejaVu", "", 12)
            pdf.set_text_color(0, 0, 0)
        elif re.match(r"^\d+\.", line):
            pdf.set_font("DejaVu", "B", 12)
            pdf.multi_cell(0, 8, line)
            pdf.set_font("DejaVu", "", 12)
        elif line.startswith("- "):
            pdf.multi_cell(0, 6, line)
        else:
            pdf.multi_cell(0, 6, line)
        pdf.ln(1)

    pdf.output(filename)
    print(f"Rapport exporté : {filename}")
