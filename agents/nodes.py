import json
from typing import Dict
from docx import Document
from agents.prompts import ( 
    STRATEGIC_ANALYSIS_PROMPT, 
    EDITORIAL_INTERROGATOR_PROMPT,
    LATEX_WRITER_PROMPT
)
from core.state import AgentState
from chains.extraction_chain import get_extraction_chain
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from utils.pdf_generator import compile_latex_to_pdf
from dotenv import load_dotenv

load_dotenv()

# 1. INGESTION NODE
def ingestion_node(state: AgentState) -> Dict:
    """
    Handles the raw file input and converts it to text.
    In a real scenario, this links to the Laravel file path.
    """
    file_path = state.get("file_path")
    if not file_path:
        return {"current_step": "error", "messages": [("assistant", "No file provided.")]}
    
    # Simple extension check (integrated from our doc_parser logic)
    # For now, we assume the DocumentParser utility is available
    from utils.doc_parser import DocumentParser
    text = DocumentParser.parse(file_path)
    
    return {
        "doc_text": text, 
        "current_step": "extraction",
        "messages": [("assistant", f"Document {file_path} ingested successfully. Starting extraction...")]
    }

# 2. EXTRACTION NODE (The Resilient Parser)
def extraction_node(state: AgentState) -> Dict:
    """
    Uses the resilient prompt to turn raw text into structured JSON.
    """
    text = state.get("doc_text")
    chain = get_extraction_chain()
    
    # The chain uses the structured output we defined in schema.py
    structured_data = chain.invoke({"text": text})
    
    return {
        "structured_data": {
            "firm_metadata": {
                "id": structured_data.firm_id,
                "name": structured_data.firm_name,
                "practice_area": structured_data.practice_area,
                "location": structured_data.location
            },
            "matters": [m.model_dump() for m in structured_data.matters],
            "narrative": structured_data.narrative_overview
        },
        "current_step": "analysis"
    }

# 3. ANALYSIS NODE (Fase 2 - The Judge)
def analysis_node(state: AgentState) -> Dict:
    """
    High-level Strategic Analyst Node.
    Analyzes extracted data to identify Tiers, Models, and Gaps.
    """
    # Use a high-reasoning model for analysis
    llm = ChatOpenAI(model="gpt-4o", temperature=0)
    
    # Define the input context from previous nodes
    structured_data = state.get("structured_data", {})
    
    # Create the analysis chain
    prompt = ChatPromptTemplate.from_messages([
        ("system", STRATEGIC_ANALYSIS_PROMPT),
        ("human", "Analyze the following structured legal data and determine the strategic positioning: {data}")
    ])
    
    # We use a simple JSON parser or .with_structured_output if you define a Pydantic schema for analysis
    chain = prompt | llm
    
    # Execute analysis
    response = chain.invoke({"data": json.dumps(structured_data)})
    
    # Parse the response content (assuming JSON format from prompt instructions)
    try:
        analysis_json = json.loads(response.content)
    except:
        # Fallback if JSON parsing fails
        analysis_json = {"error": "Analysis failed to format as JSON", "confidence_score": 0}

    confidence = analysis_json.get("confidence_score", 0)

    return {
        "analysis_results": analysis_json,
        "confidence_score": confidence,
        "is_complete": confidence >= 65,
        "current_step": "report" if confidence >= 65 else "interrogate",
        "messages": [("assistant", f"Analysis complete. Confidence: {confidence}%. Proceeding to {('Report' if confidence >= 65 else 'Interrogation')} phase.")]
    }

# 4. INTERROGATOR NODE (Editorial Agent v1)
def interrogator_node(state: AgentState) -> Dict:
    """
    Analyst-Driven Interrogator (Invisible Personalization).
    Translates technical thresholds into professional consulting advice.
    """
    llm = ChatOpenAI(model="gpt-4o", temperature=0.4)
    
    analysis = state.get("analysis_results", {})
    # Note: We keep the score here for the LLM to know how 'far' we are, 
    # but the prompt forbids it from telling the user.
    confidence = state.get("confidence_score", 0) 
    
    internal_brief = {
        "blind_spots": analysis.get("blind_spots", []),
        "tension": analysis.get("tier_viability", {}).get("status"),
        "internal_confidence_level": confidence # LLM uses this to calibrate urgency
    }

    prompt = ChatPromptTemplate.from_messages([
        ("system", EDITORIAL_INTERROGATOR_PROMPT),
        ("placeholder", "{messages}"),
        ("human", f"INTERNAL DATA (DO NOT QUOTE): {json.dumps(internal_brief)}\n\n"
                  f"Engage the user to strengthen the submission's structural evidence.")
    ])
    
    chain = prompt | llm
    response = chain.invoke({"messages": state["messages"]})
    
    return {
        "messages": [response],
        "current_step": "waiting_for_user"
    }

# 5. WRITER NODE (LaTeX Architect)
def writer_node(state: dict) -> dict:
    llm = ChatOpenAI(model="gpt-4o", temperature=0.2)
    firm_name = data.get('firm_metadata', {}).get('name', 'N/A')
    practice_area = data.get('firm_metadata', {}).get('practice_area', 'N/A')
    data = state.get("structured_data", {})
    analysis = state.get("analysis_results", {})
    
    # 1. THE STUNNING FRONT PAGE (Hardcoded for 100% Standardization)
    # This uses TikZ for the color block and geometry for the layout.
    PREAMBLE_AND_FRONT_PAGE = r"""
    \documentclass[11pt,a4paper]{article}
    \usepackage[utf8]{inputenc}
    \usepackage[margin=1in]{geometry}
    \usepackage{xcolor}
    \usepackage{titlesec}
    \usepackage{tcolorbox}
    \usepackage{tikz}
    \usepackage{helvet}
    \renewcommand{\familydefault}{\sfdefault}
    \usepackage{fancyhdr}
    \pagestyle{fancy}
    \fancyhf{}
    \renewcommand{\headrulewidth}{0pt} % No line at the top
    \fancyfoot[L]{\color{gray}\small """ + data['firm_metadata']['name'] + r""" | Confidential}
    \fancyfoot[R]{\color{gray}\small Page \thepage}

    \definecolor{brandnavy}{HTML}{1A237E}
    \definecolor{lightgray}{HTML}{F5F5F5}

    \begin{document}

    % --- FRONT PAGE START ---
    \begin{titlepage}
        \begin{tikzpicture}[remember picture,overlay]
            % Navy Blue Header Block
            \fill[brandnavy] (current page.north west) rectangle ([yshift=-8cm]current page.north east);
        \end{tikzpicture}
        
        \vspace*{1cm}
        \begin{center}
            \color{white}
            {\huge \textbf{RANKPILOT INTELLIGENCE}} \\[0.5cm]
            {\Large \textbf{STRATEGIC DIAGNOSTIC SNAPSHOT™}} \\[2cm]
            
            \begin{tcolorbox}[colback=white, colframe=brandnavy, arc=5pt, width=0.8\textwidth, center]
                \centering
                \color{brandnavy}
                {\Large \textbf{FIRM: """ + data['firm_metadata']['name'] + r"""}} \\[0.2cm]
                {\large Practice Area: """ + data['firm_metadata']['practice_area'] + r"""}
            \end{tcolorbox}
        \end{center}
        
        \vfill
        
        \begin{center}
            \color{brandnavy}
            \textbf{CONFIDENTIAL STRATEGIC ASSESSMENT} \\
            \small Generated on: \today
        \end{center}
    \end{titlepage}
    % --- FRONT PAGE END ---

    \newpage
    """

    CONTENT_START_HEADER = r"""
    % --- CONTENT HEADER ---
    \begin{center}
        {\color{brandnavy}\rule{\linewidth}{2pt}} \\
        \vspace{0.2cm}
        {\Large \textbf{""" + data['firm_metadata']['name'] + r"""}} \\
        {\large \textit{Practice Area: """ + data['firm_metadata']['practice_area'] + r"""}} \\
        \vspace{0.1cm}
        {\color{brandnavy}\rule{\linewidth}{0.8pt}}
    \end{center}
    \vspace{0.5cm}
    """

    # 2. THE AI-GENERATED CONTENT (The "Rest")
    prompt = ChatPromptTemplate.from_messages([
        ("system", LATEX_WRITER_PROMPT),
        ("human", "Data: {data}, Analysis: {analysis}")
    ])
    
    chain = prompt | llm
    response = chain.invoke({
        "data": json.dumps(data),
        "analysis": json.dumps(analysis)
    })
    
    content = response.content.replace("```latex", "").replace("```", "").strip()
    
    # Cleaning the response to ensure no duplicate preambles
    if r"\begin{document}" in content:
        content = content.split(r"\begin{document}")[1].split(r"\end{document}")[0]

    # 3. ASSEMBLY
    final_latex = PREAMBLE_AND_FRONT_PAGE + CONTENT_START_HEADER + content + r"\end{document}"

    # Generate the PDF file
    firm_name = data.get('firm_metadata', {}).get('name', 'Report').replace(" ", "_")
    pdf_path = compile_latex_to_pdf(final_latex, f"outputs/{firm_name}_Snapshot")
    
    return {
        "latex_code": final_latex,
        "pdf_url": pdf_path, # This is what Laravel will link to
        "is_complete": True
    }