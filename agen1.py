import requests, time, uuid, psutil

try:
    import pygetwindow as gw  # to get active window title
except ImportError:
    gw = None

SERVER_URL = "http://127.0.0.1:5050"
AGENT_ID = f"agent-{uuid.uuid4().hex[:8]}"
AGENT_TOKEN = "secret123"

def get_active_window():
    if gw:
        try:
            win = gw.getActiveWindow()
            if win:
                return win.title[:40]  # limit to 40 chars
        except Exception:
            return "Unknown"
    return "N/A"

def get_telemetry():
    cpu = psutil.cpu_percent()
    mem = psutil.virtual_memory().percent
    active_app = get_active_window()

    processes = []
    for p in psutil.process_iter(["pid", "name", "cpu_percent", "memory_percent"]):
        try:
            info = p.info
            # Replace None with 0.0
            info["cpu_percent"] = info.get("cpu_percent") or 0.0
            info["memory_percent"] = info.get("memory_percent") or 0.0
            processes.append(info)
        except Exception:
            pass

    top_by_cpu = sorted(processes, key=lambda x: x["cpu_percent"], reverse=True)[:3]
    top_by_mem = sorted(processes, key=lambda x: x["memory_percent"], reverse=True)[:2]

    top_processes = [f"{p['name']} (CPU {p['cpu_percent']}%)" for p in top_by_cpu] + \
                    [f"{p['name']} (Mem {p['memory_percent']:.1f}%)" for p in top_by_mem]

    return {
        "cpu": cpu,
        "memory": mem,
        "active_app": active_app,
        "top_processes": top_processes
    }

def main():
    print(f"Agent starting with id: {AGENT_ID}")
    try:
        r = requests.post(f"{SERVER_URL}/register",
                          json={"agent_id": AGENT_ID, "token": AGENT_TOKEN},
                          timeout=5)
        print("Register response:", r.status_code, r.text)
    except Exception as e:
        print("Registration failed:", e)
        return

    while True:
        telemetry = get_telemetry()
        try:
            r = requests.post(f"{SERVER_URL}/heartbeat",
                              json={"agent_id": AGENT_ID,
                                    "token": AGENT_TOKEN,
                                    "telemetry": telemetry},
                              timeout=5)
            if r.status_code == 200:
                cmd = r.json().get("command")
                if cmd == "disable":
                    print("Agent disabled by server. Exiting.")
                    break
            else:
                print("Heartbeat failed:", r.status_code, r.text)
        except Exception as e:
            print("Heartbeat error:", e)
        time.sleep(5)

if __name__ == "__main__":
    main()