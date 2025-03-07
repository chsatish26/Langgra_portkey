"""
Risk Analysis Agent for Credit Assessment System

This module implements the risk analysis component of the credit assessment system.
It processes credit reports to generate structured risk assessments using either
Portkey or OpenAI for AI-powered analysis.
"""

import yaml
import json
import logging
from typing import Dict, Any, Optional
from model_client import ModelClient
from datetime import datetime

logger = logging.getLogger(__name__)

class RiskAnalysisAgent:
    """
    Agent responsible for analyzing credit reports and identifying risk factors.
    
    Attributes:
        model_client: Flexible model client for LLM access
        config: Agent configuration dictionary
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the agent with model client and configuration.
        
        Args:
            config: Configuration dictionary
        """
        try:
            self.config = config
            self.model_client = ModelClient(config=self.config)
            self.role = self.config.get('role', 'Senior Credit Analyst')
            self.goal = self.config.get('goal', '')
            logger.info("Risk Analysis Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Risk Analysis Agent: {str(e)}")
            raise
    
    def analyze(self, pdf_content: str, task_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Analyzes credit report content to identify risk factors.
        
        Args:
            pdf_content: Raw text content from credit report PDF
            task_config: Task-specific configuration
            
        Returns:
            Dictionary containing structured risk analysis results
        """
        try:
            # Use task description if provided
            if task_config and 'description' in task_config:
                analysis_prompt = task_config['description']
            else:
                analysis_prompt = (
                    "Analyze the credit report and provide a risk assessment in JSON format. "
                    "Include credit history, DTI ratio, employment stability, and other risk factors."
                )
            
            # Format the complete prompt with instructions for proper text formatting
            prompt = (
                f"As a {self.role}, {analysis_prompt}\n\n"
                f"Credit Report Content: {pdf_content}\n\n"
                "Format your response in a way that will be displayed in a text file called 'credit_report_langgraph_timestamp.txt'. "
                "The report should be well-structured with headings and sections, following this format: "
                "1. Start with '**Comprehensive Credit Report Analysis**' "
                "2. Include sections for Personal Information, Credit History, Debt-Income Analysis, Employment Stability, and Overall Risk Assessment "
                "3. Conclude with an overall assessment paragraph\n\n"
                "Return a JSON object that contains all this formatted information with this structure:\n"
                '{"applicants": [{'
                '"personal_info": {"name": "str", "ssn": "str", "address": "str"}, '
                '"credit_history": {"credit_score": "int", "payment_history": "str", "credit_utilization": "float"}, '
                '"debt_income_analysis": {"monthly_income": "float", "total_debt": "float", "dti_ratio": "float"}, '
                '"employment_stability": {"current_employer": "str", "years_employed": "float", "employment_type": "str"}, '
                '"overall_assessment": {"risk_level": "str", "risk_factors": ["str"], "recommendations": ["str"]}'
                '}], '
                '"conclusion": "str", '
                '"text_format": "str" '
                '}'
            )

            # Invoke model for analysis
            response = self.model_client.invoke_model(
                agent_name="risk_agent",
                messages=[{"role": "user", "content": prompt}]
            )
            
            # Extract and parse response
            text_content = response['content'][0]['text']
            json_str = text_content.strip()
            
            # Try to extract JSON from code blocks if present
            if "```json" in json_str:
                start_index = json_str.find("```json") + 7
                end_index = json_str.find("```", start_index)
                json_str = json_str[start_index:end_index].strip()
            elif "```" in json_str:
                start_index = json_str.find("```") + 3
                end_index = json_str.find("```", start_index)
                json_str = json_str[start_index:end_index].strip()
                
            # Parse and validate response
            try:
                analysis_result = json.loads(json_str)
            except json.JSONDecodeError:
                # Look for JSON object pattern if not properly formatted
                start_index = json_str.find("{")
                end_index = json_str.rfind("}")
                if start_index >= 0 and end_index >= 0:
                    json_str = json_str[start_index:end_index+1]
                    analysis_result = json.loads(json_str)
                else:
                    raise
            
            # Add metadata
            analysis_result["metadata"] = {
                "analysis_timestamp": datetime.utcnow().isoformat(),
                "agent_role": self.role,
                "agent_version": "1.0.0"
            }
            
            # Store original text format if needed
            if "text_format" not in analysis_result:
                analysis_result["text_format"] = self._generate_text_format(analysis_result)
            
            logger.info("Successfully completed risk analysis")
            return analysis_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse model response: {str(e)}")
            error_response = {
                "applicants": [{
                    "personal_info": {"name": "Error Parsing", "ssn": "N/A", "address": "N/A"},
                    "credit_history": {"credit_score": 0, "payment_history": "Error", "credit_utilization": 0},
                    "debt_income_analysis": {"monthly_income": 0, "total_debt": 0, "dti_ratio": 0},
                    "employment_stability": {"current_employer": "Error", "years_employed": 0, "employment_type": "Error"},
                    "overall_assessment": {"risk_level": "Error", "risk_factors": ["Failed to parse response"], "recommendations": []}
                }],
                "conclusion": "Failed to parse model response. Please check logs for details.",
                "text_format": text_content if 'text_content' in locals() else "Error processing credit report"
            }
            return error_response
            
        except Exception as e:
            logger.error(f"Error during risk analysis: {str(e)}")
            raise
    
    def _generate_text_format(self, analysis_result: Dict[str, Any]) -> str:
        """
        Generate a text format from the analysis result.
        
        Args:
            analysis_result: The parsed analysis result
            
        Returns:
            Formatted text for output file
        """
        text_output = "**Comprehensive Credit Report Analysis**\n\n"
        
        # Process each applicant
        for i, applicant in enumerate(analysis_result.get("applicants", [])):
            personal = applicant.get("personal_info", {})
            text_output += f"**1. Personal Information:**\n"
            text_output += f"   - **Name:** {personal.get('name', 'N/A')}\n"
            # Mask SSN except last 4 digits
            ssn = personal.get('ssn', 'XXX-XX-0000')
            if len(ssn) >= 4:
                masked_ssn = f"XXX-XX-{ssn[-4:]}"
            else:
                masked_ssn = "XXX-XX-XXXX"
            text_output += f"   - **SSN:** {masked_ssn}\n"
            text_output += f"   - **Address:** {personal.get('address', 'N/A')}\n\n"
            
            # Credit History
            credit = applicant.get("credit_history", {})
            text_output += f"**2. Credit History:**\n"
            text_output += f"   - **Credit Score:** {credit.get('credit_score', 'N/A')}\n"
            text_output += f"   - **Payment History:** {credit.get('payment_history', 'N/A')}\n"
            text_output += f"   - **Credit Utilization:** {credit.get('credit_utilization', 'N/A')}\n\n"
            
            # Debt-Income Analysis
            dti = applicant.get("debt_income_analysis", {})
            text_output += f"**3. Debt-Income Analysis:**\n"
            text_output += f"   - **Monthly Income:** ${dti.get('monthly_income', 'N/A')}\n"
            text_output += f"   - **Total Debt:** ${dti.get('total_debt', 'N/A')}\n"
            text_output += f"   - **DTI Ratio:** {dti.get('dti_ratio', 'N/A')}\n\n"
            
            # Employment Stability
            emp = applicant.get("employment_stability", {})
            text_output += f"**4. Employment Stability:**\n"
            text_output += f"   - **Current Employer:** {emp.get('current_employer', 'N/A')}\n"
            text_output += f"   - **Years Employed:** {emp.get('years_employed', 'N/A')}\n"
            text_output += f"   - **Employment Type:** {emp.get('employment_type', 'N/A')}\n\n"
            
            # Overall Assessment
            assess = applicant.get("overall_assessment", {})
            text_output += f"**5. Overall Risk Assessment:**\n"
            text_output += f"   - **Risk Level:** {assess.get('risk_level', 'N/A')}\n"
            
            # Risk Factors
            risks = assess.get("risk_factors", [])
            if risks:
                text_output += "   - **Risk Factors:**\n"
                for risk in risks:
                    text_output += f"     - {risk}\n"
            
            # Recommendations
            recs = assess.get("recommendations", [])
            if recs:
                text_output += "   - **Recommendations:**\n"
                for rec in recs:
                    text_output += f"     - {rec}\n"
            
            # Add separator between applicants if needed
            if i < len(analysis_result.get("applicants", [])) - 1:
                text_output += "\n---\n\n"
        
        # Conclusion
        if "conclusion" in analysis_result:
            text_output += "\n**Conclusion:**\n"
            text_output += analysis_result["conclusion"] + "\n"
        
        return text_output