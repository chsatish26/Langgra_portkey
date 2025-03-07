"""
Credit Assessment System - Main Workflow Orchestrator for SageMaker Studio
"""

from typing import Annotated, Sequence, TypedDict, Optional,Dict,Any
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph
from tools.pdf_reader import PDFReaderTool
from agents.risk_agent import RiskAnalysisAgent
from agents.loan_agent import LoanDecisionAgent
from output.output_handler import SageMakerOutputHandler
from config_loader import ConfigLoader
import logging
from pathlib import Path
import os
import yaml
from datetime import datetime 

# Set up logging for SageMaker Studio
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def get_project_root() -> Path:
    """
    Get the project root directory.
    
    Returns:
        Path: The root directory of the project
    """
    try:
        # Start with the current file's directory
        current_dir = Path(__file__).resolve().parent
        
        # First check if we're in SageMaker Studio
        if 'SAGEMAKER_STUDIO_HOME' in os.environ:
            return Path(os.environ.get('SAGEMAKER_PROJECT_DIR', str(current_dir)))
        
        # Look for common project markers
        while current_dir != current_dir.parent:
            # Check for common project indicators
            if any((current_dir / marker).exists() for marker in ['.git', 'requirements.txt', 'setup.py']):
                return current_dir
            current_dir = current_dir.parent
        
        # If no marker found, return the script's directory
        logger.info(f"No project root markers found, using script directory: {Path(__file__).parent}")
        return Path(__file__).parent
        
    except Exception as e:
        logger.error(f"Error determining project root: {str(e)}")
        # Fallback to the current working directory
        return Path.cwd()

class AgentState(TypedDict):
    """Represents the complete state of the workflow process."""
    messages: Sequence[BaseMessage]
    next: str
    agents_scratchpad: str
    pdf_content: str
    risk_factors: dict
    final_decision: dict
    config: dict  # Added config to state

def find_pdf_file(search_dirs: list[Path]) -> Path:
    """
    Find the credit report PDF file in the given directories.
    
    Args:
        search_dirs: List of directories to search in
        
    Returns:
        Path to the PDF file
        
    Raises:
        FileNotFoundError: If no PDF file is found
    """
    for directory in search_dirs:
        logger.info(f"Searching for PDF in: {directory}")
        try:
            # Ensure directory exists
            if not directory.exists():
                logger.warning(f"Directory does not exist: {directory}")
                continue
                
            # Search for PDF files
            pdf_files = list(directory.glob("*.pdf"))
            if pdf_files:
                logger.info(f"Found PDF file: {pdf_files[0]}")
                return pdf_files[0]
                
        except Exception as e:
            logger.warning(f"Error searching directory {directory}: {str(e)}")
            continue
    
    # If we get here, no PDF was found
    searched_paths = "\n  ".join(str(d) for d in search_dirs)
    error_msg = f"No PDF files found in searched directories:\n  {searched_paths}"
    logger.error(error_msg)
    raise FileNotFoundError(error_msg)

def setup_directories() -> tuple[Path, Path, Path]:
    """
    Set up the necessary directories for input, output, and config.
    
    Returns:
        Tuple of (input_dir, output_dir, config_dir)
    """
    try:
        # First try SageMaker Studio project directory
        project_dir = Path.cwd()
        if 'SAGEMAKER_STUDIO_HOME' in os.environ:
            project_dir = Path(os.environ.get('SAGEMAKER_PROJECT_DIR', str(project_dir)))
        
        # Set up directories
        input_dir = project_dir / "input"
        output_dir = project_dir / "output"
        config_dir = project_dir / "config"
        
        # Create directories if they don't exist
        input_dir.mkdir(exist_ok=True)
        output_dir.mkdir(exist_ok=True)
        config_dir.mkdir(exist_ok=True)
        
        logger.info(f"Using input directory: {input_dir}")
        logger.info(f"Using output directory: {output_dir}")
        logger.info(f"Using config directory: {config_dir}")
        
        return input_dir, output_dir, config_dir
        
    except Exception as e:
        logger.error(f"Error setting up directories: {str(e)}")
        raise

def risk_analysis_node(state: AgentState) -> AgentState:
    """
    Process credit report through risk analysis.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated workflow state
    """
    try:
        # Get task configuration
        task_config = state.get("config", {}).get("tasks", {}).get("research_credit_report_task", {})
        
        # Create risk analysis agent
        config_loader = ConfigLoader("config")
        agent_config = config_loader.get_agent_config("risk_agent")
        agent = RiskAnalysisAgent(config=agent_config)
        
        # Perform analysis
        state["risk_factors"] = agent.analyze(
            pdf_content=state["pdf_content"],
            task_config=task_config
        )
        logger.info("Risk analysis completed successfully")
        return state
        
    except Exception as e:
        logger.error(f"Error in risk analysis: {str(e)}")
        raise

def loan_decision_node(state: AgentState) -> AgentState:
    """
    Generate final loan decision based on risk analysis.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated workflow state
    """
    try:
        # Get task configuration
        task_config = state.get("config", {}).get("tasks", {}).get("loan_assesment_task", {})
        
        # Create loan decision agent
        config_loader = ConfigLoader("config")
        agent_config = config_loader.get_agent_config("loan_agent")
        agent = LoanDecisionAgent(config=agent_config)
        
        # Generate decision
        state["final_decision"] = agent.decide(
            risk_factors=state["risk_factors"],
            task_config=task_config
        )
        logger.info("Loan decision generated successfully")
        return state
        
    except Exception as e:
        logger.error(f"Error in loan decision: {str(e)}")
        raise

def create_workflow() -> StateGraph:
    """
    Create and configure the workflow graph.
    
    Returns:
        Compiled workflow graph
    """
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("analyze_risk", risk_analysis_node)
    workflow.add_node("loan_decision", loan_decision_node)
    
    # Set entry point and edges
    workflow.set_entry_point("analyze_risk")
    workflow = workflow.add_edge("analyze_risk", "loan_decision")
    
    return workflow.compile()

def create_text_output(risk_factors: Dict[str, Any], final_decision: Dict[str, Any]) -> str:
    """
    Create a combined text output from risk factors and final decision.
    
    Args:
        risk_factors: Risk analysis results
        final_decision: Final loan decision
        
    Returns:
        Formatted text output
    """
    text_output = ""
    
    # Add risk analysis text
    text_output += "Risk Analysis Results:\n\n"
    if "text_format" in risk_factors:
        text_output += risk_factors["text_format"]
    else:
        # Fallback to a generic format
        text_output += "**Comprehensive Credit Report Analysis**\n\n"
        for applicant in risk_factors.get("applicants", []):
            personal_info = applicant.get("personal_info", {})
            text_output += f"**Personal Information:**\n"
            text_output += f"- Name: {personal_info.get('name', 'N/A')}\n"
            text_output += f"- Address: {personal_info.get('address', 'N/A')}\n\n"
            # Add more sections as needed
    
    # Add separator
    text_output += "```\n"
    text_output += "==================================================\n\n"
    
    # Add loan decision text
    text_output += "Loan Decision:\n\n"
    if "text_format" in final_decision:
        text_output += final_decision["text_format"]
    else:
        # Fallback to a generic format
        text_output += "**Loan Decision Report**\n\n"
        for decision in final_decision.get("decisions", []):
            text_output += f"**Applicant:** {decision.get('applicant_name', 'N/A')}\n"
            decision_details = decision.get("decision", {})
            text_output += f"**Decision:** {decision_details.get('status', 'N/A')}\n\n"
            # Add rationale if available
            for rationale in decision_details.get("rationale", []):
                text_output += f"{rationale}\n\n"
    
    return text_output

def main():
    """Main execution function for SageMaker Studio environment."""
    try:
        logger.info("Starting credit assessment process in SageMaker Studio")
        # Record start time
        start_time = datetime.now()
        logger.info(f"Process started at: {start_time}")

        # Set up directories
        input_dir, output_dir, config_dir = setup_directories()
        
        # Initialize ConfigLoader with config directory
        config_loader = ConfigLoader(str(config_dir))
        config = config_loader.load_config()
        
        # Debug: Print the loaded configuration
        logger.debug(f"Loaded configuration: {config}")
        
        # Validate configuration
        if not config_loader.validate_config(config):
            raise ValueError("Invalid configuration")
        
        # Initialize agents with configuration
        risk_agent = RiskAnalysisAgent(config=config_loader.get_agent_config('risk_agent'))
        loan_agent = LoanDecisionAgent(config=config_loader.get_agent_config('loan_agent'))
        
        # Debug: Print agent configurations
        logger.debug(f"Risk Agent Config: {config_loader.get_agent_config('risk_agent')}")
        logger.debug(f"Loan Agent Config: {config_loader.get_agent_config('loan_agent')}")
        
        # Look for PDF file
        search_dirs = [
            Path.cwd(),
            input_dir,
            get_project_root(),
            get_project_root() / "input"
        ]
        
        try:
            pdf_path = find_pdf_file(search_dirs)
        except FileNotFoundError as e:
            logger.error(str(e))
            raise
        
        logger.info(f"Processing credit report: {pdf_path}")
        
        # Process credit report with configuration
        final_state = process_credit_report(
            pdf_path=pdf_path,
            config=config,
            risk_agent=risk_agent,
            loan_agent=loan_agent
        )
        
        if final_state is None:
            logger.error("Failed to process credit report")
            return
            
        # Generate outputs
        output_handler = SageMakerOutputHandler(
            output_dir=str(output_dir),
            config=config
        )
        output_handler.save_outputs(final_state)
        
        # Generate direct text output file
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        text_output = create_text_output(
            final_state.get("risk_factors", {}),
            final_state.get("final_decision", {})
        )
        
        # Save text output directly to the expected format
        text_output_path = output_dir / f"credit_report_langgraph_{timestamp}.txt"
        with open(text_output_path, "w") as f:
            f.write(text_output)
            
        logger.info(f"Text output saved to: {text_output_path}")

        # Record end time
        end_time = datetime.now()
        logger.info(f"Process ended at: {end_time}")
        
        # Calculate execution time
        execution_time = end_time - start_time
        logger.info(f"Total execution time: {execution_time}")

        logger.info("Credit assessment process completed successfully")
        
    except Exception as e:
        logger.error(f"Error in main execution: {str(e)}")
        raise

def process_credit_report(
    pdf_path: Path,
    config: dict,
    risk_agent: RiskAnalysisAgent,
    loan_agent: LoanDecisionAgent
) -> Optional[AgentState]:
    """Process a credit report through the entire workflow."""
    try:
        # Initialize workflow
        graph = create_workflow()
        logger.info("Workflow initialized successfully")
        
        # Create initial state with config
        initial_state = AgentState(
            messages=[],
            next="",
            agents_scratchpad="",
            pdf_content="",
            risk_factors={},
            final_decision={},
            config=config
        )
        
        # Read PDF content - corrected method call from _run() to run()
        pdf_tool = PDFReaderTool(pdf_path=str(pdf_path))
        initial_state["pdf_content"] = pdf_tool.run()  # Changed from _run() to run()
        logger.info("PDF content loaded successfully")
        
        # Process through workflow
        final_state = graph.invoke(initial_state)
        logger.info("Workflow completed successfully")
        
        return final_state
        
    except Exception as e:
        logger.error(f"Error processing credit report: {str(e)}")
        return None

if __name__ == "__main__":
    main()