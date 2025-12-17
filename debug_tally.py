from tally_manager import TallyClient

client = TallyClient()
print("Fetching User Info...")
try:
    me = client.get_me()
    print("User Info:")
    import json

    print(json.dumps(me, indent=2))

    # Also try to print logic for workspace
    ws_id = None
    if "workspaces" in me and me["workspaces"]:
        ws_id = me["workspaces"][0]["id"]
    elif "id" in me:
        ws_id = me["id"]
    print(f"Detected Workspace ID: {ws_id}")

except Exception as e:
    print(f"Error: {e}")
