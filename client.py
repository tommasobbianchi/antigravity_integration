import requests
import json
import logging
import base64
import time

# Configuration
# Default to AgentForge Relay address, but allow override via environment or init
RELAY_URL = "http://100.111.236.92:5101/agentforge" 
INBOX_ENDPOINT = f"{RELAY_URL}/inbox/supervisor"
OUTBOX_ENDPOINT = f"{RELAY_URL}/outbox/chatgpt"

logger = logging.getLogger("AntigravitySupervisorClient")
logging.basicConfig(level=logging.INFO)

class AgentForgeClient:
    def __init__(self, relay_url=RELAY_URL):
        self.relay_url = relay_url
        self.inbox_endpoint = f"{relay_url}/inbox/supervisor"
        self.outbox_endpoint = f"{relay_url}/outbox/chatgpt"
        self.session = requests.Session()

    def send_command(self, action, data=None, target_agent="supervisor"):
        """
        Sends a command to the AgentForge inbox.
        :param action: The action string
        :param data: Dictionary containing payload data
        :param target_agent: The agent inbox to target (default: supervisor)
        """
        if data is None:
            data = {}
        
        endpoint = f"{self.relay_url}/inbox/{target_agent}"
        
        # Construct the operative JSON payload as defined in system.md
        payload = {
            "sender": "chatgpt", # Identification for routing
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

    def poll_responses(self, limit=10, timeout=5, min_timestamp=0, target_agent="chatgpt"):
        """
        Polls the AgentForge outbox for messages from the supervisor/GPT.
        :param limit: Max number of messages to process (not strictly enforced by API but good for client limits)
        :param timeout: Timeout for the HTTP request
        :param min_timestamp: Ignore messages older than this timestamp
        :param target_agent: The agent outbox to pool (e.g. chatgpt, executor)
        :return: List of processed message dictionaries
        """
        endpoint = f"{self.relay_url}/outbox/{target_agent}"
        try:
            response = self.session.get(endpoint, timeout=timeout)
            if response.status_code == 200:
                data = response.json()
                # API format: {"messages": [...]} or just a list? 
                # Based on previous analysis, it likely returns a list or a wrapper.
                # Let's assume standard behavior from supervisor_client.py analysis:
                messages = data.get("messages", [])
                
                processed_msgs = []
                for msg in messages:
                    # Filter by timestamp if provided
                    if msg.get("timestamp", 0) < min_timestamp:
                        continue

                    processed = self._process_message(msg)
                    if processed:
                        processed_msgs.append(processed)
                        if len(processed_msgs) >= limit:
                            break
                
                return processed_msgs
            else:
                logger.warning(f"Failed to poll outbox. Status: {response.status_code}")
                return []
        except requests.exceptions.ConnectionError:
            logger.warning("Connection refused while polling.")
            return []
        except Exception as e:
            logger.error(f"Error polling responses: {e}")
            return []

    def _process_message(self, msg):
        """
        Processes a raw message from the outbox, handling base64 decoding if needed.
        """
        try:
            # Check for chunked payload structure
            payload_chunk = msg.get('payload_chunk', {})
            content = payload_chunk.get('content', '')
            is_base64 = payload_chunk.get('is_base64', False)
            
            decoded_data = content
            
            # Auto-decode base64 if flagged
            if is_base64 and content:
                try:
                    decoded = base64.b64decode(content).decode('utf-8')
                    # Try parsing as JSON if it looks like one
                    try:
                        decoded_data = json.loads(decoded)
                    except json.JSONDecodeError:
                        decoded_data = decoded
                except Exception as e:
                    logger.error(f"Base64 decoding error: {e}")
                    decoded_data = f"[Decode Error] {content}"

            return {
                "id": msg.get("id"),
                "timestamp": msg.get("timestamp"),
                "sender": msg.get("sender"),
                "action": msg.get("action"), # Sometimes actions are at top level
                "content": decoded_data,
                "raw_payload": msg # Keep raw just in case
            }
                
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return None

    def wait_for_response(self, action_id=None, timeout_seconds=30, min_timestamp=0, target_agent="chatgpt"):
        """
        Helper to poll until a response is received or timeout occurs.
        """
        start_time = time.time()
        while (time.time() - start_time) < timeout_seconds:
            msgs = self.poll_responses(min_timestamp=min_timestamp, target_agent=target_agent)
            if msgs:
                return msgs
            time.sleep(1)
        return []
