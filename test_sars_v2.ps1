$BaseURL = "http://127.0.0.1:8000"
Write-Host "Testing SARS Goal 1"

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
    Write-Host "PASS: Student registered"
    $studentEmail = $resp.email
} catch {
    Write-Host "FAIL: $($_.Exception.Response.StatusCode)"
}

Write-Host "`n[TEST 2] POST /auth/register (Teacher)"
$body2 = @{
    email = "teacher@test.com"
    password = "test123"
    role = "teacher"
    full_name = "Dr. Test Teacher"
} | ConvertTo-Json

try {
    $resp = Invoke-RestMethod -Uri "$BaseURL/auth/register" -Method POST -ContentType "application/json" -Body $body2 -ErrorAction Stop
    Write-Host "PASS: Teacher registered"
} catch {
    Write-Host "FAIL: $($_.Exception.Response.StatusCode)"
}

Write-Host "`n[TEST 3] POST /auth/login (Student)"
$body3 = @{
    email = "student@test.com"
    password = "test123"
} | ConvertTo-Json

try {
    $resp = Invoke-RestMethod -Uri "$BaseURL/auth/login" -Method POST -ContentType "application/json" -Body $body3 -ErrorAction Stop
    Write-Host "PASS: Login successful"
    $studentToken = $resp.access_token
} catch {
    Write-Host "FAIL: $($_.Exception.Response.StatusCode)"
}

Write-Host "`n[TEST 4] GET /auth/me (with student token)"
if ($studentToken) {
    $headers = @{ Authorization = "Bearer $studentToken" }
    try {
        $resp = Invoke-RestMethod -Uri "$BaseURL/auth/me" -Method GET -Headers $headers -ErrorAction Stop
        Write-Host "PASS: Got user profile"
    } catch {
        Write-Host "FAIL: $($_.Exception.Response.StatusCode)"
    }
}

Write-Host "`n[TEST 5] RBAC Test - GET /teacher/students with student token"
if ($studentToken) {
    $headers = @{ Authorization = "Bearer $studentToken" }
    try {
        $resp = Invoke-RestMethod -Uri "$BaseURL/teacher/students" -Method GET -Headers $headers -ErrorAction Stop
        Write-Host "FAIL: Should have been forbidden"
    } catch {
        if ($_.Exception.Response.StatusCode -eq 403) {
            Write-Host "PASS: Correctly forbidden (403)"
        } else {
            Write-Host "FAIL: Got $($_.Exception.Response.StatusCode), expected 403"
        }
    }
}

Write-Host "`nAll tests completed!"
