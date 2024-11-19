import json
import logging
import os
import requests
from typing import List, Dict, Union
#from dotenv import load_dotenv

class TextGenerationHandler:
    def __init__(self, config_path: str = "kobold_config.json"):
        """Initialize the text generation handler with configuration."""
        # Load environment variables
        #load_dotenv()
        
        # Set up endpoints from environment variables
        self.monolith_endpoint = 'http://192.168.0.6:8051'
        
        # Load base configuration
        self.config_path = config_path
        self.base_config = self.load_config()
        
        # Load system prompt
        self.system_prompt = '''# Role and Context
You are a specialized AI Research News Analyst with expertise in breaking down complex technical papers into clear, impactful summaries. Your goal is to help readers quickly understand both the technical contribution and broader significance of research papers.

# Primary Analysis Framework

## WHAT (Technical Contribution)
Analyze and explain:
- Core innovation or method introduced
- Key technical approaches used
- Primary results or findings
- Technical improvements over existing methods
- Implementation details or requirements

## WHY (Impact and Significance)
Evaluate and explain:
- Problem being solved and its importance
- Potential applications and use cases
- Impact on the field and related domains
- Benefits compared to existing solutions
- Future implications and opportunities

## Real-world Context
Consider:
- Industry applications
- Societal implications
- Ethical considerations
- Economic impact
- Integration challenges

# Output Format
Please provide your analysis in the following structure:

WHAT:
[2-3 sentences explaining the technical contribution in clear, accessible language]

WHY:
[2-3 sentences explaining the broader impact and importance]

CONTEXT:
[1-2 sentences on real-world implications]

# Style Guidelines
- Use clear, jargon-free language while maintaining technical accuracy
- Focus on concrete examples and specific impacts
- Maintain objectivity while highlighting significance
- Avoid speculation beyond what's supported by the paper
- Keep total response length to 150-200 words'''

    def load_config(self) -> Dict:
        """Load the Kobold configuration from JSON file."""
        try:
            with open(self.config_path, 'r') as f:
                return json.load(f)
        except Exception as e:
            logging.error(f"Error loading config: {e}")
            return self._get_default_config()


##this specific config is written koboldcpp using a gemma2 type LLM
##this would need to be changed for claude or GPT
## but thats overkill almost any computer can run  gemma2 at a single user speed

    def _get_default_config(self) -> Dict:
        """Return default configuration if config file is not found."""
        return {
            "n": 1,
            "max_context_length": 4096,
            "max_length": 250,
            "rep_pen": 1.07,
            "temperature": 0.7,
            "top_p": 0.92,
            "top_k": 100,
            "top_a": 0,
            "typical": 1,
            "tfs": 1,
            "rep_pen_range": 320,
            "rep_pen_slope": 0.7,
            "sampler_order": [6, 0, 1, 3, 4, 2, 5],
            "memory": "",
            "trim_stop": True,
            "min_p": 0,
            "stop_sequence": ["<end_of_turn>\n<start_of_turn>user", "<end_of_turn>\n<start_of_turn>model"]
        }

    def split_into_messages(self, text: str, chunk_size: int = 4000) -> List[str]:
        """Split long text into smaller chunks."""
        return [text[i:i+chunk_size] for i in range(0, len(text), chunk_size)]

    def generate_text(self, user_message: str) -> Dict[str, Union[List[str], bool, str]]:
        """Generate text response based on user message."""
        try:
            # Prepare the prompt
            prompt = self.base_config.copy()
            prompt["max_length"] = 480
            prompt["temperature"] = 0.75
            prompt["memory"] = self.system_prompt
            prompt["prompt"] = f"<start_of_turn>user\n{user_message}<end_of_turn>\n<start_of_turn>model\n"


## this would need to be adjusted for claude or GPT 
            # Make API request
            response = requests.post(
                f"{self.monolith_endpoint}/api/v1/generate",
                json=prompt
            )

            if response.status_code == 200:
                results = response.json().get('results', [])
                if results:
                    text = results[0].get('text', '').replace("  ", " ")
                    text = text.replace('<0x0A>', '\n')
                    response_texts = self.split_into_messages(text)
                    
                    return {
                        "success": True,
                        "messages": response_texts,
                        "error": None
                    }
                
                return {
                    "success": False,
                    "messages": ["No results generated from the API."],
                    "error": "Empty results"
                }

            return {
                "success": False,
                "messages": [f"API request failed with status code: {response.status_code}"],
                "error": f"Status code: {response.status_code}"
            }

        except Exception as e:
            logging.error(f"Error generating text: {e}")
            return {
                "success": False,
                "messages": ["An error occurred while processing your request."],
                "error": str(e)
            }

# Usage example:
def main():
    handler = TextGenerationHandler()
    result = handler.generate_text("Explain the importance of transformer architectures in NLP.")
    
    if result["success"]:
        for message in result["messages"]:
            print(message)
            print("-" * 80)
    else:
        print(f"Error: {result['error']}")
        for message in result["messages"]:
            print(message)

if __name__ == "__main__":
    main()