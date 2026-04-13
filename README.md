# DeepNote Vault

Privacy-first local NotebookLM alternative powered by local LLM. **100% offline. Your data stays on your machine.**

## Features

- 📄 **Document Upload**: Drag & drop PDFs, TXT, Markdown files
- 🔍 **RAG-Powered Search**: Ask questions about your documents using semantic search
- 📝 **Summarization**: Auto-generate summaries of single or multiple documents
- 🔐 **Complete Privacy**: All processing happens locally. No cloud calls.
- ⚡ **Fast Inference**: Works smoothly with consumer hardware (8GB+ RAM)
- 🧠 **Multiple Models**: Support for any Ollama-compatible model

## Quick Start

### Requirements

- Python 3.11+
- [Ollama](https://ollama.ai) (for local LLM inference)
- 8GB+ RAM (recommended for smooth operation)

### Installation

```bash
# Clone the repository
git clone https://github.com/manchinsanshinsales/deepnotevault.git
cd deepnotevault

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -e .

# Run the application
deepnotevault
```

### First Time Setup

1. **Start Ollama** (if not already running)
   ```bash
   ollama serve
   ```

2. **Download Models** (one time)
   ```bash
   ollama pull llama3.2
   ollama pull nomic-embed-text
   ```

3. **Launch DeepNote Vault**
   ```bash
   deepnotevault
   ```

4. **Upload Documents**
   - Drag and drop PDFs, TXT, or Markdown files into the left panel
   - Or use "Browse Files..." button

5. **Ask Questions**
   - Type a question in the chat box
   - Get instant answers with source citations

## Settings

Access **File → Settings** to customize:
- **Ollama Base URL** (default: http://localhost:11434)
- **LLM Model** (default: llama3.2)
- **Embedding Model** (default: nomic-embed-text)
- **Chunk Size** (default: 512 tokens)
- **Chunk Overlap** (default: 64 tokens)
- **Similarity Top K** (default: 4 sources)

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Project Structure

```
deepnotevault/
├── src/deepnotevault/
│   ├── core/              # RAG engine, document processing
│   ├── models/            # Pydantic schemas
│   ├── ui/                # PySide6 UI components
│   ├── workers/           # QThread workers for background tasks
│   └── main.py            # Application entry point
├── tests/                 # Unit tests
└── pyproject.toml         # Project configuration
```

## License

MIT License — See LICENSE for details.

## Credits

Built with LlamaIndex, Ollama, ChromaDB, and PySide6.

---

**Made with ❤️ for privacy-conscious users.**
