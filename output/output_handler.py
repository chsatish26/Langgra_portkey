"""
Output Handler for Credit Assessment System

This module handles the output generation and saving for the credit assessment system.
"""

import os
import json
import logging
from typing import Dict, Any, Optional
from datetime import datetime
from pathlib import Path

logger = logging.getLogger(__name__)

class SageMakerOutputHandler:
    """
    Handles output formatting and saving for SageMaker Studio environment.
    
    Attributes:
        output_dir: Directory to save output files
        config: Output configuration settings
    """
    
    def __init__(self, output_dir: str, config: Dict[str, Any]):
        """
        Initialize the output handler.
        
        Args:
            output_dir: Directory to save output files
            config: Configuration dictionary
        """
        self.output_dir = Path(output_dir)
        self.config = config
        
        # Create output directory if it doesn't exist
        self.output_dir.mkdir(exist_ok=True, parents=True)
        logger.info(f"Output handler initialized with directory: {self.output_dir}")
    
    def save_outputs(self, final_state: Dict[str, Any]) -> None:
        """
        Save outputs in the specified formats.
        
        Args:
            final_state: Final workflow state containing results
        """
        try:
            # Generate timestamp for filenames
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            
            # Extract risk factors and final decision from state
            risk_factors = final_state.get("risk_factors", {})
            final_decision = final_state.get("final_decision", {})
            
            # Format for text output
            if "text" in self.config.get("output", {}).get("save_format", ["text"]):
                self._save_text_output(risk_factors, final_decision, timestamp)
            
            # Format for JSON output
            if "json" in self.config.get("output", {}).get("save_format", ["text"]):
                self._save_json_output(risk_factors, final_decision, timestamp)
                
            logger.info(f"Outputs saved successfully in directory: {self.output_dir}")
            
        except Exception as e:
            logger.error(f"Failed to save outputs: {str(e)}")
            raise
    
    def _save_text_output(self, risk_factors: Dict[str, Any], final_decision: Dict[str, Any], timestamp: str) -> None:
        """
        Save results as formatted text file.
        
        Args:
            risk_factors: Risk analysis results
            final_decision: Final loan decision
            timestamp: Timestamp string for filename
        """
        try:
            # Generate text content
            text_content = self._format_text_report(risk_factors, final_decision)
            
            # Save to file
            output_path = self.output_dir / f"credit_report_langgraph_{timestamp}.txt"
            with open(output_path, "w") as f:
                f.write(text_content)
                
            logger.info(f"Text output saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save text output: {str(e)}")
            raise
    
    def _save_json_output(self, risk_factors: Dict[str, Any], final_decision: Dict[str, Any], timestamp: str) -> None:
        """
        Save results as JSON file.
        
        Args:
            risk_factors: Risk analysis results
            final_decision: Final loan decision
            timestamp: Timestamp string for filename
        """
        try:
            # Combine results
            combined_results = {
                "risk_analysis": risk_factors,
                "loan_decision": final_decision,
                "metadata": {
                    "timestamp": datetime.now().isoformat(),
                    "format_version": "1.0"
                }
            }
            
            # Save to file
            output_path = self.output_dir / f"credit_report_langgraph_{timestamp}.json"
            with open(output_path, "w") as f:
                json.dump(combined_results, f, indent=2)
                
            logger.info(f"JSON output saved to: {output_path}")
            
        except Exception as e:
            logger.error(f"Failed to save JSON output: {str(e)}")
            raise
    
    def _format_text_report(self, risk_factors: Dict[str, Any], final_decision: Dict[str, Any]) -> str:
        """
        Format risk factors and decision into readable text report.
        
        Args:
            risk_factors: Risk analysis results
            final_decision: Final loan decision
            
        Returns:
            Formatted text report
        """
        # Initialize text content
        text_content = ""
        
        # Add risk analysis section
        text_content += "Risk Analysis Results:\n\n"
        
        # Format risk analysis information from applicants
        if "applicants" in risk_factors:
            text_content += "**Comprehensive Credit Report Analysis**\n\n"
            
            for applicant in risk_factors.get("applicants", []):
                # Personal Information
                personal_info = applicant.get("personal_info", {})
                text_content += "**1. Personal Information:**\n"
                text_content += f"   - **Name:** {personal_info.get('name', 'N/A')}\n"
                text_content += f"   - **SSN:** XXX-XX-{personal_info.get('ssn', 'N/A')[-4:] if personal_info.get('ssn') else 'N/A'}\n"
                text_content += f"   - **Address:** {personal_info.get('address', 'N/A')}\n\n"
                
                # Credit History
                credit_history = applicant.get("credit_history", {})
                text_content += "**2. Credit History:**\n"
                text_content += f"   - **Credit Scores:**\n"
                text_content += f"     - Current Score {credit_history.get('credit_score', 'N/A')}\n"
                text_content += f"   - **Payment History:** {credit_history.get('payment_history', 'N/A')}\n"
                text_content += f"   - **Credit Utilization:** {credit_history.get('credit_utilization', 'N/A')}\n\n"
                
                # Debt-Income Analysis
                dti = applicant.get("debt_income_analysis", {})
                text_content += "**3. Debt-Income Analysis:**\n"
                text_content += f"   - **Monthly Income:** ${dti.get('monthly_income', 'N/A')}\n"
                text_content += f"   - **Total Debt:** ${dti.get('total_debt', 'N/A')}\n"
                text_content += f"   - **DTI Ratio:** {dti.get('dti_ratio', 'N/A')}\n\n"
                
                # Employment Stability
                employment = applicant.get("employment_stability", {})
                text_content += "**4. Employment Stability:**\n"
                text_content += f"   - **Current Employer:** {employment.get('current_employer', 'N/A')}\n"
                text_content += f"   - **Years Employed:** {employment.get('years_employed', 'N/A')}\n"
                text_content += f"   - **Employment Type:** {employment.get('employment_type', 'N/A')}\n\n"
                
                # Overall Assessment
                assessment = applicant.get("overall_assessment", {})
                text_content += "**5. Overall Risk Assessment:**\n"
                text_content += f"   - **Risk Level:** {assessment.get('risk_level', 'N/A')}\n"
                
                # Risk Factors
                risk_factors_list = assessment.get("risk_factors", [])
                if risk_factors_list:
                    text_content += "   - **Risk Factors:**\n"
                    for factor in risk_factors_list:
                        text_content += f"     - {factor}\n"
                
                # Recommendations
                recommendations = assessment.get("recommendations", [])
                if recommendations:
                    text_content += "   - **Recommendations:**\n"
                    for rec in recommendations:
                        text_content += f"     - {rec}\n"
                
                text_content += "\n"
        
        # Add conclusion if present in the overall risk analysis
        if "conclusion" in risk_factors:
            text_content += "**Conclusion:**\n"
            text_content += risk_factors["conclusion"] + "\n"
        
        # Add separator
        text_content += "```\n"
        text_content += "==================================================\n\n"
        
        # Add loan decision section
        text_content += "Loan Decision:\n\n"
        
        if "decisions" in final_decision:
            text_content += "**Loan Decision Report**\n\n"
            
            for decision in final_decision.get("decisions", []):
                # Applicant name
                text_content += "**Applicant Information:**\n"
                text_content += f"- **Name:** {decision.get('applicant_name', 'N/A')}\n\n"
                
                # Decision details
                decision_details = decision.get("decision", {})
                
                # Status
                status = decision_details.get("status", "N/A")
                text_content += f"**Decision: {status}**\n\n"
                
                # Loan terms if approved
                if status == "APPROVED" or status == "CONDITIONAL":
                    loan_terms = decision_details.get("loan_terms", {})
                    text_content += "**Loan Terms:**\n"
                    text_content += f"- **Amount:** ${loan_terms.get('amount', 'N/A')}\n"
                    text_content += f"- **Interest Rate:** {loan_terms.get('interest_rate', 'N/A')}%\n"
                    text_content += f"- **Term:** {loan_terms.get('term_months', 'N/A')} months\n\n"
                
                # Conditions if conditional
                conditions = decision_details.get("conditions", [])
                if conditions and (status == "CONDITIONAL" or status == "APPROVED"):
                    text_content += "**Conditions:**\n"
                    for condition in conditions:
                        text_content += f"- {condition}\n"
                    text_content += "\n"
                
                # Rationale for decision
                rationale = decision_details.get("rationale", [])
                if rationale:
                    text_content += "**Justification:**\n"
                    for reason in rationale:
                        text_content += f"{reason}\n\n"
        
        # Add custom message for empty or error results
        if not risk_factors.get("applicants", []) and not final_decision.get("decisions", []):
            text_content += "No detailed credit report information available.\n"
        
        return text_content
