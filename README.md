# Document Metadata Extractor

An AI-powered system for automatically extracting key metadata from rental agreement documents using Google's Gemini AI model. The system can process both text documents (.docx) and scanned images (PNG/JPG) through OCR, making it versatile for various document formats.

## Project Objective

To automate the tedious and error-prone process of manually extracting metadata from rental agreements. This system leverages Large Language Models (LLMs) to intelligently parse document content and extract structured information like agreement values, dates, parties involved, and renewal terms.

## Key Features

- **Multi-format Support**: Processes both .docx files and images (PNG/JPG) using OCR
- **AI-Powered Extraction**: Uses Google Gemini AI for accurate metadata extraction
- **Batch Processing**: Command-line pipeline for processing multiple documents
- **Web API**: RESTful API built with FastAPI for easy integration
- **Web Interface**: User-friendly web UI for document upload and metadata viewing
- **Evaluation Metrics**: Built-in recall computation for model performance assessment
- **Docker Deployment**: Containerized for easy deployment and scaling
- **Sample Documents**: Includes test samples for immediate evaluation

## Problem Solved

**Manual Metadata Extraction Challenges:**
- Time-consuming review of lengthy legal documents
- Human error in data entry and transcription
- Inconsistent formatting across different document types
- Scalability issues when processing large volumes of documents
- Difficulty extracting information from scanned or image-based documents

**Our Solution:**
- Automated extraction with high accuracy using AI
- Consistent output format regardless of input document structure
- Support for both digital and scanned documents
- Batch processing capabilities for efficiency
- RESTful API for seamless integration into existing workflows

## Extracted Metadata Fields

The system extracts the following key metadata from rental agreements:

| Field | Description | Example |
|-------|-------------|---------|
| **Agreement Value** | Monthly rent amount | $2,500 |
| **Agreement Start Date** | When the lease begins | 2024-01-01 |
| **Agreement End Date** | When the lease expires | 2024-12-31 |
| **Renewal Notice (Days)** | Days required for renewal notice | 60 |
| **Party One** | First party (usually landlord) | ABC Properties LLC |
| **Party Two** | Second party (usually tenant) | John Smith |

## How to Build and Install

### Prerequisites
- Python 3.11+
- Google Gemini API key (get from [Google AI Studio](https://makersuite.google.com/app/apikey))
- Tesseract OCR (automatically installed via Docker)

### Local Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd Meta-Data-Extraction-from-Documents-main
   ```

2. **Create virtual environment**
   ```bash
   python -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   Create a `.env` file in the root directory:
   ```
   GEMINI_API_KEY=your_gemini_api_key_here
   GEMINI_API_KEY_2=your_backup_api_key_here  # Optional backup key
   ```

5. **Install Tesseract OCR** (for local OCR processing)
   ```bash
   # macOS
   brew install tesseract

   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr

   # Windows: Download from https://github.com/UB-Mannheim/tesseract/wiki
   ```

## How to Run

### Option 1: Command-Line Pipeline (Batch Processing)

Run the main pipeline for batch processing of documents:

```bash
python main.py
```

**Choose from three modes:**
1. **Validate on training data** - Test accuracy on labeled training samples
2. **Predict on test data** - Generate predictions for unlabeled test documents
3. **Both** - Run validation and prediction

**Sample Output:**
```
Starting Metadata Extraction Pipeline
============================================================

Loading data...
  Training samples: 50
  Columns: ['File Name', 'Agreement Value', 'Agreement Start Date', ...]

Choose mode:
  1. Validate on training data
  2. Predict on test data
  3. Both
Enter (1/2/3): 3

============================================================
 VALIDATION ON TRAINING DATA
============================================================

==================================================
 Processing [1/50]: agreement_001
==================================================
 Step 1: Extracting text...
  Extracted 15432 characters
  Step 2: Building prompt...
   Step 3: Sending to LLM...
  Raw metadata: {...}
  Step 4: Post-processing...
   Cleaned metadata: {'Agreement Value': '$2,500', ...}
```

### Option 2: Web API Server

Start the FastAPI web server:

```bash
# From project root
uvicorn api.app:app --host 0.0.0.0 --port 3000
```

**API Endpoints:**
- `GET /` - Web interface
- `GET /docs` - Interactive API documentation
- `POST /extract` - Upload document and extract metadata
- `GET /samples` - List available sample documents
- `POST /extract-sample` - Extract from sample document
- `GET /health` - Health check

### Option 3: Web Interface

1. Start the server as above
2. Open http://localhost:3000 in your browser
3. Upload a document or select from samples
4. View extracted metadata instantly

#### Troubleshooting Web UI

- Keep the `uvicorn` process running; a terminated server will result in a blank page or connection errors.
- In your browser, use `http://localhost:10000` ("0.0.0.0" is a bind address and not directly reachable).
- If the page still appears blank, open the browser DevTools (Console/Network) and look for network errors such as `ERR_CONNECTION_REFUSED`.
- Make sure no firewall or proxy is blocking port 10000.

### Option 4: Docker Deployment

```bash
# Build the Docker image
docker build -t metadata-extractor .

# Run the container
docker run -p 10000:10000 -e GEMINI_API_KEY=your_key_here metadata-extractor
```

##  Project Structure

```
Meta-Data-Extraction-from-Documents-main/
├── main.py                 # Main batch processing pipeline
├── requirements.txt         # Python dependencies
├── Dockerfile              # Docker configuration
├── render.yaml             # Render deployment config
├── predictions.csv         # Generated predictions output
├── train_predictions.csv   # Training validation results
├── api/
│   └── app.py             # FastAPI web application
├── data/
│   ├── train.csv          # Training labels
│   ├── test.csv           # Test file list
│   ├── train/             # Training documents
│   └── test/              # Test documents
├── src/
│   ├── __init__.py
│   ├── text_extractor.py  # Document text extraction (OCR + docx)
│   ├── prompt_builder.py  # LLM prompt construction
│   ├── llm_client.py      # Google Gemini AI integration
│   ├── post_processor.py  # Response cleaning and formatting
│   └── evaluate.py        # Performance metrics calculation
├── templates/
│   └── index.html         # Web interface template
└── preview/               # Preview images/thumbnails
```

## Technical Architecture

### Data Flow Pipeline

1. **Text Extraction**: Extract text from .docx or OCR from images
2. **Prompt Building**: Construct optimized prompts for the LLM
3. **AI Processing**: Send to Google Gemini for metadata extraction
4. **Post-processing**: Clean and format the AI response
5. **Evaluation**: Compare predictions against ground truth (optional)

### Key Components

- **text_extractor.py**: Handles multiple document formats using python-docx and pytesseract
- **llm_client.py**: Manages Google Gemini API calls with error handling and rate limiting
- **post_processor.py**: Parses JSON responses and handles edge cases
- **evaluate.py**: Computes recall metrics for model assessment

##  Evaluation and Performance

The system includes built-in evaluation capabilities:

```bash
# After running validation mode, check recall scores
# Results saved to train_predictions.csv for analysis
```

**Sample Evaluation Output:**
```
Computing Recall on Training Data...
Field-wise Recall Scores:
- Agreement Value: 0.95
- Agreement Start Date: 0.92
- Agreement End Date: 0.89
- Renewal Notice: 0.87
- Party One: 0.94
- Party Two: 0.91
Overall Average Recall: 0.91
```

## Deployment

### Render (Cloud Deployment)

The project is configured for easy deployment on Render:

1. Connect your GitHub repository to Render
2. Use the `render.yaml` configuration
3. Set environment variables: `GEMINI_API_KEY` and `GEMINI_API_KEY_2`
4. Deploy and get your API endpoint

### Local Docker

```bash
docker build -t metadata-extractor .
docker run -p 10000:10000 --env-file .env metadata-extractor
```

## Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

## Acknowledgments

- Google Gemini AI for powerful language understanding
- Tesseract OCR for image text extraction
- FastAPI for the robust web framework
- Open source community for amazing Python libraries

---

**Ready to extract metadata from your documents? Get started with `python main.py`!**