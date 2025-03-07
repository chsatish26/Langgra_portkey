"""
Loan Decision Agent for Credit Assessment System

This module implements the loan decision component of the credit assessment system.
It processes risk analysis results to generate final loan decisions using either
Portkey or OpenAI for AI-powered decision making.
"""

import yaml
import json
import logging
from typing import Dict, Any, Optional
from model_client import ModelClient
from datetime import datetime

logger = logging.getLogger(__name__)

class LoanDecisionAgent:
    """
    Agent responsible for making final loan decisions based on risk analysis.
    
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
            self.role = self.config.get('role', 'Senior Loan Officer')
            self.goal = self.config.get('goal', '')
            logger.info("Loan Decision Agent initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize Loan Decision Agent: {str(e)}")
            raise
    
    def decide(self, risk_factors: Dict[str, Any], task_config: Dict[str, Any] = None) -> Dict[str, Any]:
        """
        Generates loan decision based on risk factor analysis.
        
        Args:
            risk_factors: Dictionary containing analyzed risk factors
            task_config: Task-specific configuration
            
        Returns:
            Dictionary containing final loan decision and rationale
        """
        try:
            # Use task description if provided
            if task_config and 'description' in task_config:
                decision_prompt = task_config['description']
            else:
                decision_prompt = (
                    "Based on the risk factors, provide a loan decision. "
                    "Include approval status, loan terms, and detailed rationale."
                )
            
            # Extract applicant names from risk factors if available
            applicant_names = []
            for applicant in risk_factors.get("applicants", []):
                name = applicant.get("personal_info", {}).get("name", "Applicant")
                applicant_names.append(name)
            
            # Format the complete prompt with formatting instructions
            prompt = (
                f"As a {self.role}, {decision_prompt}\n\n"
                f"Risk Analysis Results: {json.dumps(risk_factors, indent=2)}\n\n"
                "Format your response in a way that will be displayed in a text file called 'credit_report_langgraph_timestamp.txt'. "
                "The decision should follow the Risk Analysis Results section and be well-structured with headings. "
                "Include a section titled '**Loan Decision Report**', followed by applicant information, "
                "creditworthiness assessment, risk factors, and recommendation.\n\n"
                "Return a JSON object with this structure:\n"
                '{"decisions": [{'
                f'"applicant_name": "{", ".join(applicant_names) if applicant_names else "Applicant"}", '
                '"decision": {'
                '"status": "APPROVED|DENIED|CONDITIONAL", '
                '"loan_terms": {"amount": "float", "interest_rate": "float", "term_months": "int"}, '
                '"conditions": ["str"], '
                '"rationale": ["str"]}'
                '}], '
                '"text_format": "str"'
                '}'
            )
            
            # Invoke model for decision
            response = self.model_client.invoke_model(
                agent_name="loan_agent",
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
            
            # Parse and validate decision
            try:
                decision_result = json.loads(json_str)
            except json.JSONDecodeError:
                # Look for JSON object pattern if not properly formatted
                start_index = json_str.find("{")
                end_index = json_str.rfind("}")
                if start_index >= 0 and end_index >= 0:
                    json_str = json_str[start_index:end_index+1]
                    decision_result = json.loads(json_str)
                else:
                    raise
            
            # Add metadata
            decision_result["metadata"] = {
                "decision_timestamp": datetime.utcnow().isoformat(),
                "agent_role": self.role,
                "agent_version": "1.0.0"
            }
            
            # Store original text format if needed
            if "text_format" not in decision_result:
                decision_result["text_format"] = self._generate_text_format(decision_result)
            
            logger.info("Successfully generated loan decision")
            return decision_result
            
        except json.JSONDecodeError as e:
            logger.error(f"Failed to parse model response: {str(e)}")
            error_response = {
                "decisions": [{
                    "applicant_name": "Error Parsing",
                    "decision": {
                        "status": "ERROR",
                        "loan_terms": {"amount": 0, "interest_rate": 0, "term_months": 0},
                        "conditions": ["Failed to parse response"],
                        "rationale": ["Error in processing decision"]
                    }
                }],
                "text_format": text_content if 'text_content' in locals() else "Error processing loan decision",
                "metadata": {
                    "error": "Failed to parse response",
                    "details": str(e),
                    "timestamp": datetime.utcnow().isoformat()
                }
            }
            return error_response
            
        except Exception as e:
            logger.error(f"Error during loan decision: {str(e)}")
            raise
    
    def _generate_text_format(self, decision_result: Dict[str, Any]) -> str:
        """
        Generate a text format from the decision result.
        
        Args:
            decision_result: The parsed decision result
            
        Returns:
            Formatted text for output file
        """
        text_output = "**Loan Decision Report**\n\n"
        
        # Process each decision
        for decision in decision_result.get("decisions", []):
            # Applicant information
            text_output += f"**Applicant Information:**\n"
            text_output += f"- **Name:** {decision.get('applicant_name', 'N/A')}\n\n"
            
            # Decision details
            decision_details = decision.get("decision", {})
            
            # Creditworthiness Assessment
            text_output += "**Creditworthiness Assessment:**\n"
            
            # Get rationale to use as assessment if available
            rationale = decision_details.get("rationale", [])
            if rationale:
                for item in rationale[:1]:  # Use first rationale item as assessment
                    text_output += f"{item}\n\n"
            else:
                text_output += "Assessment not available.\n\n"
            
            # Risk Factors section
            text_output += "**Risk Factors:**\n"
            # Use remaining rationale items as risk factors if available
            if len(rationale) > 1:
                for i, item in enumerate(rationale[1:], 1):
                    text_output += f"{i}. **{item.split(':')[0] if ':' in item else 'Factor'}:** "
                    text_output += f"{item.split(':', 1)[1] if ':' in item else item}\n"
            else:
                text_output += "No specific risk factors listed.\n"
            text_output += "\n"
            
            # Recommendation (Decision Status)
            status = decision_details.get("status", "N/A")
            text_output += f"**Recommendation:**\n**Decision: {status}**\n\n"
            
            # Justification
            text_output += "**Justification:**\n"
            if rationale:
                for item in rationale:
                    text_output += f"{item}\n\n"
            else:
                text_output += "No detailed justification available.\n\n"
            
            # Loan Terms if approved or conditional
            if status == "APPROVED" or status == "CONDITIONAL":
                loan_terms = decision_details.get("loan_terms", {})
                text_output += "**Loan Terms:**\n"
                text_output += f"- **Amount:** ${loan_terms.get('amount', 'N/A')}\n"
                text_output += f"- **Interest Rate:** {loan_terms.get('interest_rate', 'N/A')}%\n"
                text_output += f"- **Term:** {loan_terms.get('term_months', 'N/A')} months\n\n"
            
            # Conditions if conditional
            conditions = decision_details.get("conditions", [])
            if conditions and (status == "CONDITIONAL" or status == "APPROVED"):
                text_output += "**Conditions for Approval:**\n"
                for condition in conditions:
                    text_output += f"- {condition}\n"
                text_output += "\n"
        
        # Final note
        text_output += "This structured decision report provides a clear rationale for the " 
        text_output += f"{'approval' if status == 'APPROVED' else 'denial' if status == 'DENIED' else 'conditional approval'} "
        text_output += "of the loan application, based on the comprehensive credit report analysis and identified risk factors."
        
        return text_output