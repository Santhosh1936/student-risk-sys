# Test SARS Goal 1
$BaseURL = "http://127.0.0.1:8000"

Write-Host "Testing SARS Goal 1 ====================================" -ForegroundColor Cyan

# Test 1: Register Student
Write-Host "`n[TEST 1] POST /auth/register (Student)"
$body1 = @{
    email = "student@test.com"
    password = "test123"
    role = "student"
    full_name = "Test Student"
    roll_number = "20CS001"
} | ConvertTo-Json

try {
    $resp = Invoke-RestMethod -Uri "$BaseURL/auth/register" -Method POST -ContentType "application/json" -Body $body1 -ErrorAction Stop
    Write-Host "✓ PASS (201)" -ForegroundColor Green
    $studentEmail = $resp.email
} catch {
    Write-Host "✗ FAIL: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
}

# Test 2: Register Teacher
Write-Host "`n[TEST 2] POST /auth/register (Teacher)"
$body2 = @{
    email = "teacher@test.com"
    password = "test123"
    role = "teacher"
    full_name = "Dr. Test Teacher"
} | ConvertTo-Json

try {
    $resp = Invoke-RestMethod -Uri "$BaseURL/auth/register" -Method POST -ContentType "application/json" -Body $body2 -ErrorAction Stop
    Write-Host "✓ PASS (201)" -ForegroundColor Green
} catch {
    Write-Host "✗ FAIL: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
}

# Test 3: Login Student
Write-Host "`n[TEST 3] POST /auth/login (Student)"
$body3 = @{
    email = "student@test.com"
    password = "test123"
} | ConvertTo-Json

try {
    $resp = Invoke-RestMethod -Uri "$BaseURL/auth/login" -Method POST -ContentType "application/json" -Body $body3 -ErrorAction Stop
    Write-Host "✓ PASS (200)" -ForegroundColor Green
    $studentToken = $resp.access_token
    Write-Host "Token obtained: $($resp.user_id)"
} catch {
    Write-Host "✗ FAIL: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
}

# Test 4: Get Current User
Write-Host "`n[TEST 4] GET /auth/me (with student token)"
if ($studentToken) {
    $headers = @{ Authorization = "Bearer $studentToken" }
    try {
        $resp = Invoke-RestMethod -Uri "$BaseURL/auth/me" -Method GET -Headers $headers -ErrorAction Stop
        Write-Host "✓ PASS (200)" -ForegroundColor Green
        Write-Host "User: $($resp.email) ($($resp.role))"
    } catch {
        Write-Host "✗ FAIL: $($_.Exception.Response.StatusCode)" -ForegroundColor Red
    }
} else {
    Write-Host "⊘ SKIPPED (no token)" -ForegroundColor Yellow
}

# Test 5: RBAC Test
Write-Host "`n[TEST 5] GET /teacher/students (with student token - should fail)"
if ($studentToken) {
    $headers = @{ Authorization = "Bearer $studentToken" }
    try {
        $resp = Invoke-RestMethod -Uri "$BaseURL/teacher/students" -Method GET -Headers $headers -ErrorAction Stop
        Write-Host "✗ FAIL - Should have been forbidden" -ForegroundColor Red
    } catch {
        if ($_.Exception.Response.StatusCode -eq 403) {
            Write-Host "✓ PASS (403 Forbidden)" -ForegroundColor Green
        } else {
            Write-Host "✗ FAIL: Got $($_.Exception.Response.StatusCode), expected 403" -ForegroundColor Red
        }
    }
} else {
    Write-Host "⊘ SKIPPED" -ForegroundColor Yellow
}

Write-Host "`nAll tests completed!" -ForegroundColor Cyan
