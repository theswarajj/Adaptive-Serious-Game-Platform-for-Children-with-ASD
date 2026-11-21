import urllib.request
import json

base = 'http://127.0.0.1:8000/api'

def post(url, data):
    req = urllib.request.Request(f'{base}{url}', data=json.dumps(data).encode(), headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def get(url):
    req = urllib.request.Request(f'{base}{url}')
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def run_tests():
    print('1. Testing Teacher Login...')
    t_login = post('/auth/login', {'username': 'teacher', 'password': 'teacher123', 'role': 'teacher'})
    assert t_login['success']
    print('   Teacher Login OK:', t_login['user']['display_name'])

    print('2. Testing Teacher Dashboard...')
    dash = get('/teacher/dashboard')
    print('   Dashboard stats:', dash['stats'])

    print('3. Testing Trigger AI Recommendation for STU-1001...')
    rec_res = post('/recommendations/generate/STU-1001', {})
    assert rec_res['success']
    rec = rec_res['recommendation']
    print('   Generated recommendation:', rec['recommended_game_id'], rec['difficulty'], rec['target_skill'])
    print('   Alternatives:', len(rec.get('alternative_games', [])))

    print('4. Testing Approve Recommendation...')
    rec_id = rec['id']
    appr_res = post(f'/recommendations/{rec_id}/approve', {'teacher_notes': 'Verified and approved'})
    assert appr_res['success']
    print('   Approved OK:', appr_res['message'])

    print('5. Testing Student Assignments...')
    asgs = get('/students/STU-1001/assignments')
    print('   Active assignments for STU-1001:', len(asgs), [a['game_id'] for a in asgs])

    print('6. Testing Parent Home Observation...')
    p_obs = post('/parent/observations', {
        'student_id': 'STU-1001',
        'parent_id': 'parent-user',
        'routine_transitions': 5,
        'communication_attempts': 5,
        'sensory_sensitivity': 2,
        'regulation_strategies': 'Quiet space and favorite puzzle',
        'home_notes': 'Alex completed daily routine without stress and enjoyed pointing game.'
    })
    assert p_obs['success']
    print('   Parent observation saved OK:', p_obs['message'])

    print('7. Testing 10-Section Student Report...')
    rep = get('/reports/student/STU-1001')
    assert 'student' in rep and 'radar_profile' in rep and 'disclaimer' in rep
    print('   Student Report generated OK! Radar:', rep['radar_profile'])

    print('\nALL PLATFORM INTEGRATION TESTS PASSED 100%!')

if __name__ == '__main__':
    run_tests()
