
import sys
import json
import time
from client import AgentForgeClient

# Read the code to document
with open("/home/tommaso/projects/antigravity_integration/client.py", "r") as f:
    code_content = f.read()

prompt = f"""
Please generate Google-style docstrings for all classes and methods in the following Python code. 
Return the full Python code with the docstrings included. Do not change any logic.

CODE:
{code_content}
"""

client = AgentForgeClient()
print("Sending request to Executor...")
result = client.send_command("execute_agent", {"prompt": prompt}, target_agent="executor")
print(f"Send Result: {result}")

if result['status'] == 'error':
    sys.exit(1)

print("Waiting for response (up to 120s)...")
# Executor writes to 'executor' outbox
response = client.wait_for_response(timeout_seconds=120, target_agent="executor")

if response:
    print("Response Received:")
    # The response content is often in the 'content' field of the processed message
    # Executor returns the generated text in the 'result' field of the original payload, 
    # which _process_message puts into 'content'.
    print(json.dumps(response[0]['content'], indent=2))
else:
    print("No response received.")
