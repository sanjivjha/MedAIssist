import os
from flask import Flask, request, jsonify, send_from_directory, render_template
from werkzeug.utils import secure_filename
import importlib
from config import Config
from langchain.chains import ConversationalRetrievalChain, LLMChain
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate
from langchain.prompts import ChatPromptTemplate
from langchain.schema.runnable import RunnablePassthrough
from langchain.schema.output_parser import StrOutputParser
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.text_splitter import CharacterTextSplitter
from langchain.schema import Document
import PyPDF2
import re
import logging

app = Flask(__name__, static_url_path='/static', static_folder='static')
app.config.from_object(Config)

# Set up logging
logging.basicConfig(level=logging.INFO)

# Ensure upload directory exists
app.config['UPLOAD_FOLDER'] = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

# Initialize LLM
if Config.LLM_CHOICE == 'ollama':
    from langchain_ollama import ChatOllama
    llm = ChatOllama(model=Config.OLLAMA_MODEL, max_tokens=Config.MAX_TOKENS, temperature=0)
elif Config.LLM_CHOICE == 'claude':
    import boto3
    from langchain_aws import ChatBedrock
    bedrock_client = boto3.client(service_name='bedrock-runtime', region_name=Config.AWS_REGION)
    llm = ChatBedrock(
        model_id=Config.CLAUDE_MODEL_ID, 
        client=bedrock_client,
        model_kwargs={"max_tokens_to_sample": Config.MAX_TOKENS}
    )
else:
    raise ValueError(f"Unsupported LLM choice: {Config.LLM_CHOICE}")

# Initialize conversation chain
conversation_chain = None

# Pluggable source handlers
source_handlers = {}

def load_source_handlers():
    for source in Config.ENABLED_SOURCES:
        try:
            module = importlib.import_module(f"sources.{source}_handler")
            handler_name = ''.join(word.capitalize() for word in source.split('_')) + 'Handler'
            source_handlers[source] = getattr(module, handler_name)()
        except ImportError:
            app.logger.warning(f"Handler for source '{source}' not found.")
        except AttributeError as e:
            app.logger.error(f"Error loading handler for source '{source}': {e}")

load_source_handlers()

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in Config.ALLOWED_EXTENSIONS

def parse_summary(summary_text):
    sections = {
        'Key words': r'Key words:(.*?)(?=\n\d\.)',
        'Date range': r'Date range:(.*?)(?=\n\d\.)',
        'Type of articles reviewed': r'Type of articles reviewed:(.*?)(?=\n\d\.)',
        'Summary': r'Summary:(.*?)(?=\n\d\.)',
        'Recommended approach': r'Recommended approach:(.*?)(?=\n\d\.)',
        'Label Information': r'Label Information:(.*?)(?=\n\d\.)',
        'References': r'References:(.*?)$'
    }
    
    parsed = {}
    for key, pattern in sections.items():
        match = re.search(pattern, summary_text, re.DOTALL)
        if match:
            content = match.group(1).strip()
            if key in ['Recommended approach', 'References']:
                parsed[key] = [item.strip() for item in re.split(r'\s*•\s*', content) if item.strip()]
            else:
                parsed[key] = content
    
    return parsed

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/build_kb', methods=['POST'])
def build_knowledge_base():
    try:
        query = request.form.get('query')
        sources = request.form.getlist('sources')
        
        documents = []
        articles_reviewed = 0
        
        # Process PDF if uploaded
        if 'pdf' in request.files:
            pdf_file = request.files['pdf']
            if pdf_file and allowed_file(pdf_file.filename):
                filename = secure_filename(pdf_file.filename)
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
                
                # Save the file
                pdf_file.save(filepath)
                app.logger.info(f"File saved to {filepath}")
                
                # Extract text from PDF
                try:
                    with open(filepath, 'rb') as file:
                        reader = PyPDF2.PdfReader(file)
                        for i, page in enumerate(reader.pages):
                            text = page.extract_text()
                            documents.append(Document(page_content=text, metadata={"source": "pdf", "page": i+1}))
                    articles_reviewed += 1  # Count the PDF as one article
                    app.logger.info(f"Processed 1 PDF with {len(reader.pages)} pages")
                except Exception as e:
                    app.logger.error(f"Error processing PDF: {str(e)}")
                    return jsonify(error=f"Error processing PDF: {str(e)}"), 500
            else:
                app.logger.warning("Invalid file or file type")
        else:
            app.logger.info("No PDF file uploaded")

        # Fetch data from selected sources
        for source in sources:
            if source in source_handlers:
                try:
                    source_docs = source_handlers[source].fetch_data(query)
                    documents.extend([Document(page_content=doc, metadata={"source": source}) for doc in source_docs])
                    articles_reviewed += len(source_docs)  # Count articles from each source
                    app.logger.info(f"Retrieved {len(source_docs)} documents from {source}")
                except Exception as e:
                    app.logger.error(f"Error fetching data from {source}: {str(e)}")
            else:
                app.logger.warning(f"No handler available for source '{source}'")
        
        app.logger.info(f"Total documents retrieved: {len(documents)}")
        app.logger.info(f"Total articles reviewed: {articles_reviewed}")

        if not documents:
            return jsonify({
                "message": "No relevant documents found",
                "summary": "Unable to generate summary due to lack of relevant documents.",
                "articles_reviewed": 0
            }), 200
        
        # Create vector store
        text_splitter = CharacterTextSplitter(chunk_size=1000, chunk_overlap=0)
        split_docs = text_splitter.split_documents(documents)
        embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
        vector_store = FAISS.from_documents(split_docs, embeddings)
        vector_store.save_local(Config.VECTOR_STORE_PATH)
        
        # Generate summary
        summary_prompt = ChatPromptTemplate.from_template(Config.GENERATE_SUMMARY_PROMPT)
        summary_chain = summary_prompt | llm | StrOutputParser()
        retriever = vector_store.as_retriever()
        relevant_docs = retriever.invoke(query)
        summary = summary_chain.invoke({"context": "\n".join([doc.page_content for doc in relevant_docs]), "query": query})

        # Truncate summary if it exceeds MAX_TOKENS
        if len(summary.split()) > Config.MAX_TOKENS:
            summary = ' '.join(summary.split()[:Config.MAX_TOKENS]) + '...'
        
        # Parse the summary
        parsed_summary = parse_summary(summary)
        
        # Parse the summary
        parsed_summary = parse_summary(summary)
        
        formatted_summary = f"""
        <h2>Summary</h2>
        <p><strong>Query:</strong> {query}</p>
        <p><strong>Key words:</strong> {parsed_summary.get('Key words', 'N/A')}</p>
        <p><strong>Date range:</strong> {parsed_summary.get('Date range', 'N/A')}</p>
        <p><strong>Number of articles reviewed:</strong> {articles_reviewed}</p>
        <p><strong>Type of articles reviewed:</strong> {parsed_summary.get('Type of articles reviewed', 'N/A')}</p>
        
        <h3>Response:</h3>
        <p>Dear Dr.,</p>
        <p>{parsed_summary.get('Summary', 'N/A')}</p>
        
        <h3>Recommended approach:</h3>
        <ul>
        {"".join(f"<li>{rec.strip()}</li>" for rec in parsed_summary.get('Recommended approach', []) if rec.strip())}
        </ul>
        
        <h3>Label Information:</h3>
        <p>{parsed_summary.get('Label Information', 'N/A')}</p>
        
        <p><em>The information mentioned above may be outside of the current label indication for Product X in [country] and has been provided following an unsolicited request for information from a treating physician. Company ABC is providing this information as a scientific service further to an unsolicited request and not in a promotional context.</em></p>
        """

        # Always include the References section, even if it's empty
        formatted_summary += """
        <h3>References:</h3>
        <ol>
        """
        if parsed_summary.get('References'):
            formatted_summary += "".join(f"<li>{ref.strip()}</li>" for ref in parsed_summary['References'] if ref.strip() and ref.strip() != '[N/A]')
        else:
            formatted_summary += "<li>No references available</li>"
        formatted_summary += "</ol>"
        
        # Initialize conversation chain
        global conversation_chain
        chat_prompt = ChatPromptTemplate.from_template(Config.CHAT_RESPONSE_PROMPT)
        conversation_chain = RunnablePassthrough.assign(context=lambda x: retriever.invoke(x["question"])) | chat_prompt | llm | StrOutputParser()
        
        return jsonify({
            "message": "Knowledge base built successfully",
            "summary": formatted_summary,
            "articles_reviewed": articles_reviewed
        }), 200
    except Exception as e:
        app.logger.error(f"Error in build_knowledge_base: {str(e)}")
        return jsonify(error=f"An error occurred while building the knowledge base: {str(e)}"), 500
    
@app.route('/api/chat', methods=['POST'])
def chat():
    if not conversation_chain:
        return jsonify({"error": "Knowledge base not built yet"}), 400
    
    user_message = request.json.get('message')
    if not user_message:
        return jsonify({"error": "No message provided"}), 400
    
    try:
        # Generate response
        answer = conversation_chain.invoke({"question": user_message})
        
        # Truncate response if it exceeds MAX_TOKENS
        if len(answer.split()) > Config.MAX_TOKENS:
            answer = ' '.join(answer.split()[:Config.MAX_TOKENS]) + '...'
        
        # Parse and format the response
        formatted_response = ""
        sections = answer.split('\n\n')
        
        for section in sections:
            if section.startswith("Direct Answer:"):
                formatted_response += f"<p>{section.replace('Direct Answer:', '').strip()}</p>"
            elif section.startswith("Key Points:"):
                formatted_response += "<h3>Key Points:</h3><ul>"
                points = [point.strip() for point in section.split('•')[1:] if point.strip()]
                for point in points:
                    formatted_response += f"<li>{point}</li>\n"
                formatted_response += "</ul>"
            elif section.startswith("Relevant References:"):
                formatted_response += "<h3>Relevant References:</h3><ol>"
                references = [ref.strip() for ref in section.split('\n')[1:] if ref.strip() and ref.strip() != '[N/A]']
                if references:
                    for ref in references:
                        formatted_response += f"<li>{ref}</li>"
                else:
                    formatted_response += "<li>No relevant references available</li>"
                formatted_response += "</ol>"
            else:
                formatted_response += f"<p>{section}</p>"

        return jsonify({"response": formatted_response}), 200
    except Exception as e:
        app.logger.error(f"Error in chat: {str(e)}")
        return jsonify(error="An error occurred while processing your message. Please try again."), 500
    
if __name__ == '__main__':
    app.run(debug=True)