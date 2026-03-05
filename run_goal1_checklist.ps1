$base = 'http://127.0.0.1:8000'
$front = 'http://localhost:3000'
$studentEmail = 'student@test.com'
$teacherEmail = 'teacher@test.com'
$studentPass = 'test123'
$teacherPass = 'test123'
$studentToken = $null

function ShowResult($id, $ok, $msg) {
  if ($ok) { Write-Output ("PASS " + $id + " - " + $msg) }
  else { Write-Output ("FAIL " + $id + " - " + $msg) }
}

try {
  $body = @{ email=$studentEmail; password=$studentPass; role='student'; full_name='Test Student'; roll_number='20CS001' } | ConvertTo-Json
  $r = Invoke-WebRequest -Uri "$base/auth/register" -Method POST -ContentType 'application/json' -Body $body -UseBasicParsing -ErrorAction Stop
  ShowResult '[1]' ($r.StatusCode -eq 201) ("/auth/register student status=" + $r.StatusCode)
} catch {
  $code = $_.Exception.Response.StatusCode.value__
  ShowResult '[1]' ($code -eq 400) ("/auth/register student status=" + $code + ' (rerun duplicate acceptable)')
}

try {
  $body = @{ email=$teacherEmail; password=$teacherPass; role='teacher'; full_name='Dr. Test Teacher' } | ConvertTo-Json
  $r = Invoke-WebRequest -Uri "$base/auth/register" -Method POST -ContentType 'application/json' -Body $body -UseBasicParsing -ErrorAction Stop
  ShowResult '[2]' ($r.StatusCode -eq 201) ("/auth/register teacher status=" + $r.StatusCode)
} catch {
  $code = $_.Exception.Response.StatusCode.value__
  ShowResult '[2]' ($code -eq 400) ("/auth/register teacher status=" + $code + ' (rerun duplicate acceptable)')
}

try {
  $body = @{ email=$studentEmail; password=$studentPass } | ConvertTo-Json
  $login = Invoke-RestMethod -Uri "$base/auth/login" -Method POST -ContentType 'application/json' -Body $body -ErrorAction Stop
  $studentToken = $login.access_token
  ShowResult '[3]' (![string]::IsNullOrWhiteSpace($studentToken)) '/auth/login token present'
} catch {
  $code = $_.Exception.Response.StatusCode.value__
  ShowResult '[3]' $false ("/auth/login status=" + $code)
}

if ($studentToken) {
  try {
    $me = Invoke-RestMethod -Uri "$base/auth/me" -Method GET -Headers @{ Authorization = "Bearer $studentToken" } -ErrorAction Stop
    ShowResult '[4]' (($me.email -eq $studentEmail) -and ($me.role -eq 'student')) ("/auth/me email=" + $me.email + ', role=' + $me.role)
  } catch {
    $code = $_.Exception.Response.StatusCode.value__
    ShowResult '[4]' $false ("/auth/me status=" + $code)
  }
} else {
  ShowResult '[4]' $false '/auth/me skipped (no token)'
}

if ($studentToken) {
  try {
    $r = Invoke-WebRequest -Uri "$base/teacher/students" -Method GET -Headers @{ Authorization = "Bearer $studentToken" } -UseBasicParsing -ErrorAction Stop
    ShowResult '[5]' $false ("RBAC unexpected status=" + $r.StatusCode)
  } catch {
    $code = $_.Exception.Response.StatusCode.value__
    ShowResult '[5]' ($code -eq 403) ("RBAC status=" + $code)
  }
} else {
  ShowResult '[5]' $false 'RBAC skipped (no token)'
}

try {
  $f = Invoke-WebRequest -Uri $front -UseBasicParsing -ErrorAction Stop
  ShowResult '[6]' ($f.StatusCode -eq 200) ("frontend status=" + $f.StatusCode)
} catch {
  $code = $_.Exception.Response.StatusCode.value__
  ShowResult '[6]' $false ("frontend status=" + $code)
}
