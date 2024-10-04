# MedAIssist: Medical Research AI Assistant

MedAIssist is an AI-powered medical research assistant that helps healthcare professionals quickly gather and analyze information from various medical sources. It uses advanced language models to process queries, build knowledge bases, and provide insightful responses to medical questions.

## Features

- Build knowledge bases from multiple sources (PubMed, Google Scholar, Wikipedia, etc.)
- Process and analyze PDF documents
- Interactive chat interface for querying the knowledge base
- Prescription image analysis (placeholder functionality)

## Installation

### Prerequisites

- Python 3.8 or higher
- Conda (for managing Python environments)
- Ollama (for running LLaMA 3.2 locally)

### Step 1: Clone the Repository

```bash
git clone https://github.com/yourusername/MedAIssist.git
cd MedAIssist
```

### Step 2: Set Up Conda Environment

```bash
conda create -n medaissist python=3.8
conda activate medaissist
```

### Step 3: Install Python Dependencies

```bash
pip install -r requirements.txt
```

### Step 4: Install and Run Ollama

Follow the instructions on the [Ollama website](https://ollama.ai/) to install Ollama for your operating system.

Once installed, run the Ollama server:

```bash
ollama serve
```

In a new terminal window, pull the LLaMA 3.2 model:

```bash
ollama pull llama2:32b
```

## Getting Started

1. Ensure the Ollama server is running.

2. Start the Flask application:

```bash
python app.py
```

3. Open a web browser and navigate to `http://localhost:5000`.

4. Use the interface to build a knowledge base, ask questions, and analyze medical information.

## Configuration

Edit the `config.py` file to customize settings such as:

- LLM choice (Ollama/LLaMA or Claude)
- API keys for various services
- Maximum token limits
- Enabled data sources

## Contributing

We welcome contributions! Please see our [Contributing Guidelines](CONTRIBUTING.md) for more details.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- LangChain for providing the framework for working with language models
- Ollama for the local LLaMA 3.2 implementation
- All the open-source libraries and tools that made this project possible

## Support

If you encounter any issues or have questions, please file an issue on the GitHub repository.
