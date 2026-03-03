#!/bin/bash

BASE="http://localhost:8000"

echo "=== Health check ==="
curl -s "$BASE/health"

echo ""
echo "=== Register ==="
REGISTER=$(curl -s -X POST "$BASE/auth/register" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"password123","first_name":"Ada","last_name":"Lovelace"}')
echo "$REGISTER"

echo ""
echo "=== Login ==="
LOGIN=$(curl -s -X POST "$BASE/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","password":"password123"}')
echo "$LOGIN"
TOKEN=$(echo "$LOGIN" | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])" 2>/dev/null)

echo ""
echo "=== Conversations ==="
curl -s "$BASE/conversations" -H "Authorization: Bearer $TOKEN"
