
import sys
import json
import time
from client import AgentForgeClient

# Read the code to test
with open("/home/tommaso/projects/antigravity_integration/client.py", "r") as f:
    code_content = f.read()

prompt = f"""
Please generate a comprehensive `pytest` unit test file for the following Python code.
Use `unittest.mock` to mock `requests` and avoid real network calls.
Cover `send_command`, `poll_responses`, and `wait_for_response`.
Test success and failure scenarios (e.g., connection error, 500 error).

CODE:
{code_content}

Return ONLY the Python code for the test file.
"""

client = AgentForgeClient()
print("Sending test generation request to Executor...")
result = client.send_command("execute_agent", {"prompt": prompt}, target_agent="executor")
print(f"Send Result: {result}")

if result['status'] == 'error':
    sys.exit(1)

print("Waiting for response (up to 300s)...")
# Executor writes to 'executor' outbox
response = client.wait_for_response(timeout_seconds=300, target_agent="executor")

if response:
    print("Response Received:")
    # The response content is often in the 'content' field of the processed message
    print(json.dumps(response[0]['content'], indent=2))
else:
    print("No response received.")
