import argparse
import json
import codecs
import sys
from client import AgentForgeClient

def main():
    parser = argparse.ArgumentParser(description="Antigravity AgentForge Plugin CLI")
    
    parser.add_argument("--action", help="Action to perform (e.g., analyze_project, heartbeat)")
    parser.add_argument("--data", help="JSON string data payload")
    parser.add_argument("--target", default="supervisor", help="Target agent (supervisor, executor, planner)")
    parser.add_argument("--check-connection", action="store_true", help="Check connectivity to Relay")
    parser.add_argument("--poll", action="store_true", help="Poll for messages")
    parser.add_argument("--wait", type=int, default=0, help="Wait N seconds for a response after sending")
    parser.add_argument("--server", help="Override Relay URL")
    
    parser.add_argument("--init", action="store_true", help="Initialize connection and get Server Persona")
    
    args = parser.parse_args()

    # Initialize Client
    kwargs = {}
    if args.server:
        kwargs['relay_url'] = args.server
    
    client = AgentForgeClient(**kwargs)

    # 0. Initialize / Handshake
    if args.init:
        try:
            # Assumes the web interface is on port 5000 (standard) or we map it
            # For now hardcoding localhost:5000 as per server.py
            import requests
            resp = requests.get("http://localhost:5000/api/status", timeout=2)
            if resp.status_code == 200:
                status = resp.json()
                print(json.dumps(status, indent=2))
                # Explicitly print the system message to stderr for human visibility
                print(f"\n[AgentForge Handshake] {status.get('system_message')}\n", file=sys.stderr)
                sys.exit(0)
            else:
                print(json.dumps({"status": "error", "message": f"Server returned {resp.status_code}"}))
                sys.exit(1)
        except Exception as e:
            print(json.dumps({"status": "error", "message": f"Handshake failed: {str(e)}"}))
            sys.exit(1)

    # 1. Check Connection
    if args.check_connection:
        # Simple health check by trying to poll (or we could add a specific health endpoint if known)
        # Using a harmless poll as check
        try:
            client.session.get(client.relay_url + "/healthz", timeout=2)
            print(json.dumps({"status": "connected", "url": client.relay_url}))
            sys.exit(0)
        except Exception as e:
            print(json.dumps({"status": "disconnected", "error": str(e)}))
            sys.exit(1)

    # 2. Poll only
    if args.poll and not args.action:
        target = args.target if args.target else "chatgpt"
        msgs = client.poll_responses(target_agent=target)
        print(json.dumps(msgs, indent=2))
        sys.exit(0)

    # 3. Send Action
    if args.action:
        data = {}
        if args.data:
            try:
                data = json.loads(args.data)
            except json.JSONDecodeError:
                print(json.dumps({"status": "error", "message": "Invalid JSON in --data"}))
                sys.exit(1)
        
        import time
        start_ts = time.time()
        
        # Send
        result = client.send_command(args.action, data, target_agent=args.target)
        
        if result['status'] == 'error':
            print(json.dumps(result))
            sys.exit(1)
            
        # Optional Wait
        response_msgs = []
        if args.wait > 0:
            print(f"Command sent. Waiting {args.wait}s for response...", file=sys.stderr)
            
            # Determine correct outbox to poll
            # If we target 'supervisor', default reply is 'chatgpt' outbox (supervisor writes there)
            # If we target 'executor', it writes to 'executor' outbox
            poll_target = "chatgpt"
            if args.target == "executor":
                poll_target = "executor"
            elif args.target == "planner":
                poll_target = "planner"

            response_msgs = client.wait_for_response(timeout_seconds=args.wait, min_timestamp=start_ts, target_agent=poll_target)
            
        # Output result
        output = {
            "send_result": result,
            "responses": response_msgs
        }
        print(json.dumps(output, indent=2))

if __name__ == "__main__":
    main()
