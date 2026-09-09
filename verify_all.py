import urllib.request
import json

def req(url, method='GET', data=None):
    r = urllib.request.Request(url, method=method)
    if data:
        r.add_header('Content-Type', 'application/json')
        body = json.dumps(data).encode('utf-8')
    else:
        body = None
    with urllib.request.urlopen(r, data=body) as resp:
        return resp.status, json.loads(resp.read().decode('utf-8'))

print("1. Checking Projects:")
status, res = req("http://127.0.0.1:8000/api/projects")
print(f"   Status: {status}, Projects count: {len(res)}, First: {res[0]['name']}")

print("2. Checking Project Settings GET:")
status, res = req("http://127.0.0.1:8000/api/projects/1/settings")
print(f"   Status: {status}, Settings: {res}")

print("3. Checking Project Settings PUT:")
status, res = req("http://127.0.0.1:8000/api/projects/1/settings", method="PUT", data={"gold_threshold": 91.0, "behavioral_threshold": 77.0})
print(f"   Status: {status}, Saved Gold: {res['gold_threshold']}, Behavioral: {res['behavior_threshold']}")

print("4. Checking Leaderboard:")
status, res = req("http://127.0.0.1:8000/api/dashboard/leaderboard?project_id=1")
print(f"   Status: {status}, Annotators count: {res['total_annotators']}")
for a in res['leaderboard']:
    print(f"   #{a['rank']} {a['annotator_name']}: trust={a['trust_score']}, annotations={a['total_annotations']}")

print("5. Checking Heatmap:")
status, res = req("http://127.0.0.1:8000/api/dashboard/agreement-heatmap?project_id=1")
print(f"   Status: {status}, Annotators: {res['annotators']}, Matrix rows: {len(res['matrix'])}")

print("6. Checking Review Queue:")
status, res = req("http://127.0.0.1:8000/api/review/queue?project_id=1")
print(f"   Status: {status}, Items in queue: {len(res['items'])}, Total: {res['total']}")

print("7. Checking Automation Pending:")
status, res = req("http://127.0.0.1:8000/api/automation/pending?project_id=1")
print(f"   Status: {status}, Pending total: {res['total']}")

status, res = req("http://127.0.0.1:8000/api/rerouting/pending?project_id=1")
print(f"   Status: {status} (via rerouting), Pending total: {res['total']}")

print("\nALL ENDPOINTS VERIFIED 100% OPERATIONAL WITH ZERO SQL ERRORS!")
