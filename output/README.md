# Langgraph Portkey Integration

A credit assessment system that integrates Langgraph with Portkey for AI-powered analysis of credit reports and loan decisions.

## Overview

This project implements a workflow for processing credit reports using a graph-based approach with Langgraph. It extracts information from credit report PDFs, analyzes risk factors, and generates loan decision recommendations.

The system uses Portkey as a unified API gateway to access language models like GPT-4o, providing an efficient and cost-effective way to leverage AI capabilities.

## Features

- **PDF Processing**: Extract text content from credit report PDFs
- **Risk Analysis**: Identify key risk factors from credit reports
- **Loan Decision**: Generate comprehensive loan recommendations
- **Workflow Orchestration**: Graph-based workflow using Langgraph
- **Model Integration**: Unified access to language models via Portkey

## Architecture

The system is organized into the following components:

- **Main Workflow**: Orchestrates the complete process
- **Risk Analysis Agent**: Analyzes credit reports for risk factors
- **Loan Decision Agent**: Generates final loan decisions
- **PDF Reader Tool**: Extracts text from PDF documents
- **Model Client**: Manages access to AI models via Portkey
- **Output Handler**: Formats and saves results

## Installation

### Prerequisites

- Python 3.8+
- PyPDF2 or PyMuPDF (for PDF processing)
- Portkey Python SDK

### Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/chsatish26/Langgraph_portkey_Integration.git
   cd Langgraph_portkey_Integration
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure API keys:
   - Update `config/config.yaml` with your Portkey API credentials
   - Update `config/agents.yaml` with agent-specific settings

## Usage

1. Place credit report PDF files in the `input` directory

2. Run the main script:
   ```bash
   python main.py
   ```

3. Access results in the `output` directory:
   - Credit assessment reports in `credit_report_langgraph_{timestamp}.txt`
   - Detailed analysis in JSON format

## Configuration

### Main Configuration (config.yaml)

```yaml
portkey:
  enabled: true
  base_url: "YOUR_PORTKEY_BASE_URL"
  api_key: "YOUR_PORTKEY_API_KEY"
  virtual_key: "YOUR_VIRTUAL_KEY"
  model: "gpt-4o"
  max_tokens: 3000
```

### Agent Configuration (agents.yaml)

```yaml
risk_agent:
  role: Senior Credit Analyst
  goal: >
    Conduct a comprehensive analysis of a provided credit report...
  enabled: true
  # Model access settings...
```

## Output Format

The system generates output files in the following format:

```
Risk Analysis Results:

**Comprehensive Credit Report Analysis**
...

==================================================

Loan Decision:

**Loan Decision Report**
...
```

## Integration with SageMaker

This system is designed to run in AWS SageMaker:

1. Upload the project to a SageMaker Studio notebook
2. Configure directory paths and settings
3. Execute the main workflow

## Extending the System

To add new capabilities:

1. Create new agent modules in the `agents` directory
2. Update the workflow graph in `main.py`
3. Configure the new agents in `config/agents.yaml`

## Troubleshooting

Common issues:

- **PDF Reading Errors**: Ensure PyPDF2 or PyMuPDF is installed
- **API Authentication**: Verify Portkey API credentials
- **Model Response Format**: Check that model responses match expected formats

## License

[Specify your license information here]

## Contributors

- [Your Name/Organization]

## Acknowledgments

- Langgraph project (https://github.com/langchain-ai/langgraph)
- Portkey AI (https://portkey.ai)
