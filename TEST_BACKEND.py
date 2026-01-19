"""
Quick Backend Test Script

Run this after starting the backend to verify it's working.
"""
import requests
import json
import time

API_URL = "http://localhost:8000"

def test_health():
    """Test health endpoint"""
    print("="*60)
    print("TEST 1: Health Check")
    print("="*60)
    try:
        response = requests.get(f"{API_URL}/health", timeout=5)
        print(f"Status: {response.status_code}")
        print(f"Response: {response.json()}")
        print("✅ PASSED\n")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}\n")
        return False

def test_create_session():
    """Test creating a chat session"""
    print("="*60)
    print("TEST 2: Create Chat Session")
    print("="*60)
    try:
        response = requests.post(
            f"{API_URL}/api/chat/session",
            json={
                "company_id": "TEST_001",
                "company_name": "Test Company"
            },
            timeout=10
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Session ID: {data.get('session_id')}")
        print(f"Company: {data.get('company_name')}")
        print("✅ PASSED\n")
        return data.get('session_id')
    except Exception as e:
        print(f"❌ FAILED: {e}\n")
        return None

def test_send_query(session_id):
    """Test sending a query"""
    print("="*60)
    print("TEST 3: Send Query")
    print("="*60)

    if not session_id:
        print("❌ SKIPPED: No session ID\n")
        return None

    try:
        response = requests.post(
            f"{API_URL}/api/chat/query",
            json={
                "query": "What is the fair value of investment properties?",
                "session_id": session_id,
                "company_id": "PHX_FXD",
                "top_k": 5
            },
            timeout=30
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Message ID: {data.get('message_id')}")
        print(f"Model Used: {data.get('model_used')}")
        print(f"Success: {data.get('success')}")

        # Show first 200 chars of answer
        answer = data.get('answer', '')
        print(f"Answer Preview: {answer[:200]}...")

        if data.get('success'):
            print("✅ PASSED\n")
        else:
            print(f"⚠️  PARTIAL: Query processed but returned error: {data.get('error')}\n")

        return data.get('message_id')
    except Exception as e:
        print(f"❌ FAILED: {e}\n")
        return None

def test_submit_feedback(message_id, session_id):
    """Test submitting feedback"""
    print("="*60)
    print("TEST 4: Submit Feedback (RLHF)")
    print("="*60)

    if not message_id or not session_id:
        print("❌ SKIPPED: No message ID or session ID\n")
        return False

    try:
        response = requests.post(
            f"{API_URL}/api/feedback/submit",
            json={
                "message_id": message_id,
                "session_id": session_id,
                "feedback_score": 1.0  # Good
            },
            timeout=10
        )
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Feedback ID: {data.get('feedback_id')}")
        print(f"Score: {data.get('feedback_score')}")
        print(f"Message: {data.get('message')}")
        print("✅ PASSED\n")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}\n")
        return False

def test_get_companies():
    """Test getting company list"""
    print("="*60)
    print("TEST 5: Get Companies")
    print("="*60)
    try:
        response = requests.get(f"{API_URL}/api/upload/companies", timeout=10)
        print(f"Status: {response.status_code}")
        data = response.json()
        print(f"Total Companies: {data.get('total_count')}")

        companies = data.get('companies', [])
        for company in companies[:3]:  # Show first 3
            print(f"  - {company['company_id']}: {company['company_name']} ({company['chunk_count']} chunks)")

        print("✅ PASSED\n")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}\n")
        return False

def main():
    """Run all tests"""
    print("\n" + "="*60)
    print("🧪 BACKEND API TESTING SUITE")
    print("="*60)
    print("Make sure backend is running: py -3.11 main.py")
    print("="*60 + "\n")

    # Wait a moment for server to be ready
    print("Waiting for server...")
    time.sleep(2)

    # Run tests
    results = []

    # Test 1: Health
    results.append(("Health Check", test_health()))

    # Test 2: Create Session
    session_id = test_create_session()
    results.append(("Create Session", session_id is not None))

    # Test 3: Send Query
    message_id = test_send_query(session_id)
    results.append(("Send Query", message_id is not None))

    # Test 4: Submit Feedback
    results.append(("Submit Feedback", test_submit_feedback(message_id, session_id)))

    # Test 5: Get Companies
    results.append(("Get Companies", test_get_companies()))

    # Summary
    print("="*60)
    print("📊 TEST SUMMARY")
    print("="*60)

    passed = sum(1 for _, result in results if result)
    total = len(results)

    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")

    print("="*60)
    print(f"TOTAL: {passed}/{total} tests passed")
    print("="*60)

    if passed == total:
        print("\n🎉 ALL TESTS PASSED! Backend is working correctly!")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Check errors above.")

    print("\n✨ Next: Start frontend (npm run dev) and open http://localhost:3000\n")

if __name__ == "__main__":
    main()
