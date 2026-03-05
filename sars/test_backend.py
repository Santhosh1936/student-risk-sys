#!/usr/bin/env python
import requests
import json
import time

BASE_URL = "http://127.0.0.1:8000"
time.sleep(3)  # Give server time to reload

print("Testing SARS Goal 1 Endpoints...")
print("=" * 60)

# Test 1: Register student
print("\n[TEST 1] POST /auth/register (student)")
resp = requests.post(f"{BASE_URL}/auth/register", json={
    "email": "student@test.com",
    "password": "test123",
    "role": "student",
    "full_name": "Test Student",
    "roll_number": "20CS001"
})
print(f"Status: {resp.status_code}")
if resp.status_code in [200, 201]:
    print("✓ PASS")
    data = resp.json()
    student_token = None
else:
    print("✗ FAIL:", resp.text[:200])

# Test 2: Register teacher
print("\n[TEST 2] POST /auth/register (teacher)")
resp = requests.post(f"{BASE_URL}/auth/register", json={
    "email": "teacher@test.com",
    "password": "test123",
    "role": "teacher",
    "full_name": "Dr. Test Teacher"
})
print(f"Status: {resp.status_code}")
if resp.status_code in [200, 201]:
    print("✓ PASS")
    teacher_token = None
else:
    print("✗ FAIL:", resp.text[:200])

# Test 3: Login student
print("\n[TEST 3] POST /auth/login (student)")
resp = requests.post(f"{BASE_URL}/auth/login", json={
    "email": "student@test.com",
    "password": "test123"
})
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    data = resp.json()
    student_token = data.get("access_token")
    print(f"✓ PASS - Token received")
else:
    print("✗ FAIL:", resp.text[:200])

# Test 4: Get current user with student token
print("\n[TEST 4] GET /auth/me (with student token)")
if student_token:
    resp = requests.get(f"{BASE_URL}/auth/me", 
                       headers={"Authorization": f"Bearer {student_token}"})
    print(f"Status: {resp.status_code}")
    if resp.status_code == 200:
        print("✓ PASS")
    else:
        print("✗ FAIL:", resp.text[:200])
else:
    print("⊘ SKIPPED (no token)")

# Test 5: RBAC - student trying to access teacher endpoint
print("\n[TEST 5] GET /teacher/students (with student token - should fail)")
if student_token:
    resp = requests.get(f"{BASE_URL}/teacher/students",
                       headers={"Authorization": f"Bearer {student_token}"})
    print(f"Status: {resp.status_code}")
    if resp.status_code == 403:
        print("✓ PASS - Correctly forbidden")
    else:
        print("✗ FAIL: Expected 403, got", resp.status_code)
else:
    print("⊘ SKIPPED")

# Test 6: Health check
print("\n[TEST 6] GET / (health check)")
resp = requests.get(f"{BASE_URL}/")
print(f"Status: {resp.status_code}")
if resp.status_code == 200:
    print("✓ PASS")
else:
    print("✗ FAIL:", resp.text[:200])

print("\n" + "=" * 60)
print("Backend Testing Complete!")
