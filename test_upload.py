import urllib.request, json, sys

# Login
login_data = json.dumps({'email': 'test2@sars.com', 'password': 'test1234'}).encode()
req = urllib.request.Request(
    'http://127.0.0.1:8000/auth/login',
    data=login_data,
    headers={'Content-Type': 'application/json'}
)
with urllib.request.urlopen(req) as r:
    tok = json.loads(r.read())['access_token']
print('Token OK, len:', len(tok))

# Build multipart body
BOUNDARY = 'SARSBOUND42'
pdf_path = r'c:\Users\hp\Downloads\sars_goal1\test_grade_sheet.pdf'
with open(pdf_path, 'rb') as f:
    pdf_data = f.read()

body = (
    ('--' + BOUNDARY + '\r\n').encode() +
    b'Content-Disposition: form-data; name="file"; filename="test_grade_sheet.pdf"\r\n' +
    b'Content-Type: application/pdf\r\n\r\n' +
    pdf_data +
    ('\r\n--' + BOUNDARY + '--\r\n').encode()
)

req2 = urllib.request.Request(
    'http://127.0.0.1:8000/student/upload-marksheet',
    data=body,
    headers={
        'Authorization': 'Bearer ' + tok,
        'Content-Type': 'multipart/form-data; boundary=' + BOUNDARY
    }
)

try:
    with urllib.request.urlopen(req2) as r:
        resp = json.loads(r.read())
    print('Status: 200')
    print(json.dumps(resp, indent=2))
except urllib.error.HTTPError as e:
    err_body = e.read()
    print('HTTP', e.code, err_body.decode())
