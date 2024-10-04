import os

class Config:
    # LLM Configuration
    LLM_CHOICE = os.environ.get('LLM_CHOICE', 'ollama')
    OLLAMA_MODEL = "llama3.2"  # This specifies LLaMA 3.2
    CLAUDE_MODEL_ID = "anthropic.claude-3-sonnet-20240229-v1:0"
    AWS_REGION = "us-east-1"

     # Increase token limit
    MAX_TOKENS = 4096  # Adjust this value based on your needs and model capabilities
    MAX_RESULTS = 30
    # Google Cloud Vision API Credentials
    GOOGLE_CLOUD_CREDENTIALS_PATH = "/Users/sanjij/work/external_demos/pubmed/ver1/google_cloud_credentials.json"
    os.environ['GOOGLE_APPLICATION_CREDENTIALS'] = GOOGLE_CLOUD_CREDENTIALS_PATH

    # Source Configuration
    ENABLED_SOURCES = ['pubmed', 'google_scholar', 'wikipedia', 'internet']

    # Upload Configuration
    UPLOAD_FOLDER = 'uploads'
    ALLOWED_EXTENSIONS = {'pdf', 'png', 'jpg', 'jpeg'}

    # Vector Store Configuration
    VECTOR_STORE_PATH = 'vector_store'

    # Prompts
    GENERATE_SUMMARY_PROMPT = """
    Based on the following context and the query, provide a structured summary:

    Context: {context}
    Query: {query}

    Please format your response exactly as follows, including the numbers and labels:

    1. Key words: List 5-7 relevant keywords separated by commas
    2. Date range: Specify the range of years covered by the reviewed articles (e.g., 2010-2023)
    3. Type of articles reviewed: List the types of articles (e.g., observational, retrospective, review, meta-analysis, practice guidelines)
    4. Summary: Provide a brief summary of 2-3 sentences
    5. Recommended approach: List 3-5 key recommendations. Start each point with a bullet (•)
    6. Label Information: Include relevant label information if available
    7. References: List 3-5 key references in the format: Author(s). Title. Journal. Year;Volume(Issue):Pages. Start each reference with a bullet (•)

    If there's no information for a section, write "N/A" for that section. Do not include any placeholder text, notes, or instructions in your response.

    Response:
    """



    CHAT_RESPONSE_PROMPT = """
    Based on the provided context and the user's question, generate a response that adheres to the following format:

    Context: {context}
    Question: {question}

    Please structure your response as follows:

    1. Start with a direct answer to the question in 1-2 sentences.

    2. Then, provide a section titled "Key Points:" followed by 2-4 bullet points summarizing the main points of the answer. Each bullet point should:
    • Start with a bullet point (•)
    • Be a single, concise sentence or short paragraph
    • Provide specific, relevant information

    3. Finally, include a section titled "Relevant References:" with 1-3 relevant references from the context. Format each reference as:
    [1] Author(s). Title. Journal. Year;Volume(Issue):Pages.

    If there are no relevant references, use [N/A] instead.

    Do not include any placeholder text or notes in your response. Provide actual content based on the context and question.

    Response:
    """

    @classmethod
    def init_app(cls):
        if not os.path.exists(cls.GOOGLE_CLOUD_CREDENTIALS_PATH):
            print(f"Warning: Google Cloud credentials file not found at {cls.GOOGLE_CLOUD_CREDENTIALS_PATH}")
        else:
            print(f"Google Cloud credentials set to: {cls.GOOGLE_CLOUD_CREDENTIALS_PATH}")

# Call init_app when the config is imported
Config.init_app()