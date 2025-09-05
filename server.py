from flask import Flask, request, jsonify, render_template_string, redirect, url_for
import time

app = Flask(__name__)

agents = {}
ADMIN_TOKEN = "admin-secret-token"

DASHBOARD_HTML = """
<!DOCTYPE html>
<html>
<head>
  <title>Agent Dashboard</title>
  <style>
    body { font-family: Arial, sans-serif; margin: 20px; }
    table { border-collapse: collapse; width: 100%; }
    th, td { border: 1px solid #ddd; padding: 8px; }
    th { background: #f2f2f2; }
    .small { font-size: 12px; color: #555; }
  </style>
</head>
<body>
  <h2>Registered Agents</h2>
  <table>
    <tr>
      <th>Agent ID</th>
      <th>IP</th>
      <th>Last Seen</th>
      <th>Telemetry</th>
      <th>Action</th>
    </tr>
    {% for aid, info in agents.items() %}
    <tr>
      <td>{{aid}}</td>
      <td>{{info["ip"]}}</td>
      <td>{{"%.1f" % (time.time()-info["last_seen"])}}s ago</td>
      <td>
        <div class="small">
          CPU: {{info["telemetry"].get("cpu")}}%,
          Mem: {{info["telemetry"].get("memory")}}%<br>
          Active App: {{info["telemetry"].get("active_app", "N/A")}}<br>
          <strong>Top Processes:</strong><br>
          {% for p in info["telemetry"].get("top_processes", []) %}
            {{p}}<br>
          {% endfor %}
        </div>
      </td>
      <td>
        <form method="post" action="/send_command" style="display:inline">
          <input type="hidden" name="agent_id" value="{{aid}}">
          <input type="hidden" name="command" value="disable">
          <input type="hidden" name="admin_token" value="{{admin_token}}">
          <button type="submit">Send Disable</button>
        </form>
      </td>
    </tr>
    {% endfor %}
  </table>
  <p><em>NOTE: Refresh page to update telemetry.</em></p>
</body>
</html>
"""

@app.route("/")
def dashboard():
    return render_template_string(DASHBOARD_HTML, agents=agents, time=time, admin_token=ADMIN_TOKEN)

@app.route("/register", methods=["POST"])
def register():
    data = request.json
    agent_id = data.get("agent_id")
    token = data.get("token")
    if not agent_id or not token:
        return jsonify({"error": "agent_id and token required"}), 400
    agents[agent_id] = {
        "last_seen": time.time(),
        "telemetry": {},
        "command": None,
        "token": token,
        "ip": request.remote_addr
    }
    return jsonify({"status": "registered"})

@app.route("/heartbeat", methods=["POST"])
def heartbeat():
    data = request.json
    agent_id = data.get("agent_id")
    token = data.get("token")
    if agent_id not in agents or agents[agent_id]["token"] != token:
        return jsonify({"error": "unauthorized"}), 403
    agents[agent_id]["last_seen"] = time.time()
    agents[agent_id]["telemetry"] = data.get("telemetry", {})
    cmd = agents[agent_id]["command"]
    agents[agent_id]["command"] = None
    return jsonify({"command": cmd})

@app.route("/send_command", methods=["POST"])
def send_command():
    agent_id = request.form.get("agent_id")
    command = request.form.get("command")
    admin_token = request.form.get("admin_token")
    if admin_token != ADMIN_TOKEN:
        return "Forbidden", 403
    if agent_id in agents:
        agents[agent_id]["command"] = command
    return redirect(url_for("dashboard"))

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--port", type=int, default=5000)
    args = parser.parse_args()
    app.run(host="0.0.0.0", port=args.port, debug=True)