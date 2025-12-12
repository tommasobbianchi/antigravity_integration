
import sys
import json
import time
from client import AgentForgeClient

# Simplified code: just the send_command method to test
code_content = """
    def send_command(self, action, data=None, target_agent="supervisor"):
        if data is None:
            data = {}
        
        endpoint = f"{self.relay_url}/inbox/{target_agent}"
        
        payload = {
            "sender": "chatgpt",
            "payload": {
                "action": action,
                "data": data
            }
        }
        
        try:
            logger.info(f"Sending action: {action} to {endpoint}")
            response = self.session.post(endpoint, json=payload, timeout=5)
            
            if response.status_code in [200, 201]:
                return {"status": "success", "message": "Command sent successfully"}
            else:
                return {
                    "status": "error", 
                    "message": f"HTTP {response.status_code}: {response.text}"
                }
        except requests.exceptions.ConnectionError:
            return {"status": "error", "message": "Connection refused. Is AgentForge Relay running?"}
        except Exception as e:
            logger.error(f"Error sending command: {e}")
            return {"status": "error", "message": str(e)}
"""

prompt = f"""
Generate a `pytest` unit test for the `send_command` method shown below.
Use `unittest.mock` to mock `self.session.post`.
Mock success (200) and failure (500, ConnectionError) cases.

CODE:
{code_content}

Return ONLY the Python code.
"""

client = AgentForgeClient()
print("Sending SIMPLE test generation request to Executor...")
result = client.send_command("execute_agent", {"prompt": prompt}, target_agent="executor")
print(f"Send Result: {result}")

if result['status'] == 'error':
    sys.exit(1)

print("Waiting for response (up to 300s)...")
response = client.wait_for_response(timeout_seconds=300, target_agent="executor")

if response:
    print("Response Received:")
    print(json.dumps(response[0]['content'], indent=2))
else:
    print("No response received.")
