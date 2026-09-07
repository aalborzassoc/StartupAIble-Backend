import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

def run_ai_agent(prompt: str, agent_role: str):
    system_prompt = f"You are an expert {agent_role} working for ParsAIce."
    
    print(f"Sending request to Anthropic (Sonnet 5)...")
    try:
        message = client.messages.create(
            model="claude-sonnet-5",
            max_tokens=4096,
            system=system_prompt,
            messages=[{"role": "user", "content": prompt}]
        )
        
        # FIX: Loop through all blocks and only grab the actual text
        text_content = ""
        for block in message.content:
            if block.type == "text":
                text_content += block.text
                
        return {"content": text_content, "model_used": "claude-sonnet-5"}
        
    except Exception as e:
        print(f"Anthropic Error: {e}")
        raise e