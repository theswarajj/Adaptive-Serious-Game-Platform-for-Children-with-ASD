import urllib.request
import json

base = 'http://127.0.0.1:8000/api'

# 1. Test class_cohort_ranking
with urllib.request.urlopen(f'{base}/teacher/dashboard') as resp:
    dash = json.loads(resp.read().decode())
    ranking = dash.get('class_cohort_ranking', [])
    print('Class Ranking length:', len(ranking))
    for r in ranking:
        print(f"Rank #{r['class_rank']}: {r['full_name']} ({r['composite_score']}%) - Tier: {r['cohort_tier']} ({r['badge']}) - Care: {r['support_level']}")
        if r['special_care_flags']:
            print(f"  Alerts: {r['special_care_flags']}")

# 2. Test get parents
with urllib.request.urlopen(f'{base}/teacher/parents') as resp:
    parents = json.loads(resp.read().decode())
    print('\nParents list count:', len(parents))
    for p in parents:
        print(f"Parent: {p['full_name']} (@{p['username']}) -> Linked to {p['student_name']} ({p['relationship']})")

# 3. Test create new parent
req = urllib.request.Request(f'{base}/teacher/parents', data=json.dumps({
    'full_name': 'David Lin',
    'username': 'david_parent',
    'password': 'parent123',
    'student_id': 'STU-1002',
    'relationship': 'Father'
}).encode(), headers={'Content-Type': 'application/json'})
try:
    with urllib.request.urlopen(req) as resp:
        res = json.loads(resp.read().decode())
        print('\nCreated parent successfully:', res)
except Exception as e:
    print('\nParent create response (already created or message):', e)
