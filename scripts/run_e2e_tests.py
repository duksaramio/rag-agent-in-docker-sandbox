import json
import sys
import time
import urllib.request
import urllib.error

BASE_URL = "http://localhost:8000"

def log_pass(name: str, msg: str = ""):
    print(f"✅ [PASS] {name} {msg}")

def log_fail(name: str, msg: str):
    print(f"❌ [FAIL] {name}: {msg}")

def http_get(endpoint: str) -> dict:
    url = f"{BASE_URL}{endpoint}"
    req = urllib.request.Request(url)
    with urllib.request.urlopen(req) as resp:
        data = resp.read().decode('utf-8')
        return json.loads(data)

def http_post(endpoint: str, payload: dict, timeout: int = 60) -> dict:
    url = f"{BASE_URL}{endpoint}"
    data_bytes = json.dumps(payload).encode('utf-8')
    req = urllib.request.Request(
        url,
        data=data_bytes,
        headers={"Content-Type": "application/json"}
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        data = resp.read().decode('utf-8')
        return json.loads(data)

def test_health_and_root():
    print("\n--- Running Test Suite 1: API Health & System Status ---")
    try:
        root_data = http_get("/")
        assert root_data.get("status") == "online", f"Expected online status, got {root_data}"
        log_pass("GET / Status Check", f"({root_data.get('service')})")

        health_data = http_get("/health")
        assert health_data.get("s3_storage") == "ok", f"S3 health failed: {health_data}"
        assert health_data.get("qdrant_db") == "ok", f"Qdrant health failed: {health_data}"
        log_pass("GET /health Connectivity Check", f"(S3: {health_data['s3_storage']}, Qdrant: {health_data['qdrant_db']})")
        return True
    except Exception as e:
        log_fail("Health & System Status Check", str(e))
        return False

def test_documents_listing():
    print("\n--- Running Test Suite 2: Document Storage Verification ---")
    try:
        docs_data = http_get("/documents")
        documents = docs_data.get("documents", [])
        doc_keys = [d["key"] for d in documents]
        
        expected_docs = [
            "SOP-QA-001_Cleanroom_Sanitization.txt",
            "SOP-DEV-042_Deviation_Management.txt",
            "VAL-PROT-2026_Sterile_Filter_Validation.txt",
            "SOP-OOS-015_Out_of_Specification_Investigation.txt",
            "SOP-VAL-088_Computer_System_Validation.txt",
            "SOP-LOG-030_Cold_Chain_Storage_Transport.txt",
            "SOP-EQ-104_HPLC_Equipment_Calibration.txt"
        ]
        
        for expected in expected_docs:
            assert expected in doc_keys, f"Missing document in S3: {expected}"
            
        log_pass("GET /documents Storage Check", f"({len(documents)} objects found in bucket 'gxp-docs')")
        return True
    except Exception as e:
        log_fail("Document Storage Verification", str(e))
        return False

def test_rag_queries():
    print("\n--- Running Test Suite 3: End-to-End RAG Queries & Grounding Verification ---")
    test_cases = [
        {
            "name": "OOS Phase I Investigation Timeline & Re-testing",
            "prompt": "What is the timeline for completing a Phase I OOS laboratory investigation, and what is the maximum number of re-tests allowed?",
            "expected_keywords": ["7", "business days", "5"],
            "expected_sources": ["SOP-OOS-015_Out_of_Specification_Investigation.txt"]
        },
        {
            "name": "21 CFR Part 11 Audit Trail & CSV Re-validation",
            "prompt": "According to the GxP computer system validation SOP, how often must QC analytical audit trails be reviewed, and what is the periodic re-validation frequency?",
            "expected_keywords": ["batch release", "2 years"],
            "expected_sources": ["SOP-VAL-088_Computer_System_Validation.txt"]
        },
        {
            "name": "Cold Chain Storage Temperature Excursion Rules",
            "prompt": "What temperature spike threshold triggers an automated quarantine tag for 2°C to 8°C cold chain storage?",
            "expected_keywords": ["15", "30 minutes"],
            "expected_sources": ["SOP-LOG-030_Cold_Chain_Storage_Transport.txt"]
        },
        {
            "name": "HPLC Equipment Calibration & Pressure Limits",
            "prompt": "What is the retention time precision limit (%RSD) and maximum system pressure limit for HPLC equipment calibration?",
            "expected_keywords": ["1.0%", "300 bar"],
            "expected_sources": ["SOP-EQ-104_HPLC_Equipment_Calibration.txt"]
        },
        {
            "name": "Multi-SOP Cross-Functional Compliance Synthesis",
            "prompt": "Summarize the wet contact time for cleanroom sanitization, the RCA timeframe for major deviations, and the water intrusion test limit for vent filters.",
            "expected_keywords": ["10 minutes", "14 days", "0.75"],
            "expected_sources": [
                "SOP-QA-001_Cleanroom_Sanitization.txt",
                "SOP-DEV-042_Deviation_Management.txt",
                "VAL-PROT-2026_Sterile_Filter_Validation.txt"
            ]
        }
    ]

    all_passed = True
    for idx, tc in enumerate(test_cases, 1):
        print(f"\n[Case {idx}/{len(test_cases)}] {tc['name']}")
        start_time = time.time()
        try:
            res = http_post("/query", {"prompt": tc["prompt"]})
            elapsed = time.time() - start_time
            answer = res.get("answer", "")
            sources = res.get("sources", [])
            confidence = res.get("confidence_level", "")

            print(f"⏱ Response Time: {elapsed:.2f}s | Confidence: {confidence}")
            print(f"📄 Cited Sources: {sources}")
            print(f"💬 Answer Snippet: {answer[:250]}...")

            # Validate answer keywords
            for kw in tc["expected_keywords"]:
                assert kw.lower() in answer.lower(), f"Keyword '{kw}' missing from answer."

            # Validate sources citation (check structured sources list or answer text)
            found_source = any(s in sources for s in tc["expected_sources"]) or any(s in answer for s in tc["expected_sources"])
            assert found_source, f"Expected one of sources {tc['expected_sources']}, but got sources={sources} and answer={answer[:150]}"

            # Validate confidence level
            assert confidence in ["High", "Medium"], f"Unexpected confidence level: {confidence}"

            log_pass(f"Case {idx}: {tc['name']}")
        except Exception as e:
            log_fail(f"Case {idx}: {tc['name']}", str(e))
            all_passed = False

    return all_passed

def main():
    print("=================================================================")
    print("🚀 PYDANTIC AI RAG AGENT - END-TO-END AUTOMATED TEST RUNNER 🚀")
    print("=================================================================")

    h_ok = test_health_and_root()
    d_ok = test_documents_listing()
    q_ok = test_rag_queries()

    print("\n=================================================================")
    if h_ok and d_ok and q_ok:
        print("🎉 ALL END-TO-END TESTS PASSED SUCCESSFULLY! 🎉")
        sys.exit(0)
    else:
        print("❌ SOME END-TO-END TESTS FAILED. CHECK LOGS ABOVE. ❌")
        sys.exit(1)

if __name__ == "__main__":
    main()
