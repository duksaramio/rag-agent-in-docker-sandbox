import os
import sys
import logging

# Ensure project root is in python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.s3_client import s3_service
from app.ingestion import ingestion_pipeline

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("seed_gxp_docs")

SAMPLE_DOCS = {
    "SOP-QA-001_Cleanroom_Sanitization.txt": """
STANDARD OPERATING PROCEDURE: Cleanroom Class A/B Sanitization Protocol
SOP ID: SOP-QA-001
Effective Date: 2026-01-15
Department: Quality Assurance & Biomanufacturing

1. PURPOSE & SCOPE
This procedure describes the mandatory cleaning, sanitization, and environmental monitoring protocols for Class A laminar flow hoods and Class B aseptic processing areas.

2. FREQUENCY & AGENTS
- Daily Cleaning: 70% Sterile Isopropyl Alcohol (IPA), filtered through 0.22 μm filter.
- Weekly Rotation: Sporicidal agent (Peracetic Acid 0.2% or Hydrogen Peroxide Vapor 30%) to prevent microbial resistance build-up.
- Contact Time: Minimum 10 minutes wet contact time required for all surfaces.

3. GOWNING REQUIREMENTS
Personnel entering Class B areas must wear sterile non-linting coveralls, triple gloves, sterile face mask, safety goggles, and sterile dedicated footwear.
""",
    "SOP-DEV-042_Deviation_Management.txt": """
STANDARD OPERATING PROCEDURE: Quality Deviation and Root Cause Analysis
SOP ID: SOP-DEV-042
Effective Date: 2025-11-01
Department: Quality Compliance

1. DEVIATION CLASSIFICATION
- Minor Deviation: Does not impact product quality, safety, identity, strength, or purity. Requires resolution within 30 days.
- Major Deviation: Potential impact on critical quality attributes (CQAs). Requires formal Root Cause Analysis (RCA) using 5-Whys or Fishbone diagram within 14 days.
- Critical Deviation: Direct risk to patient safety or regulatory compliance. Immediate quarantine of affected batch, notification to QA Director within 2 hours, and CAPA initiation within 24 hours.

2. CORRECTIVE AND PREVENTIVE ACTION (CAPA)
All Major and Critical deviations require CAPA logging, QA approval, and effectiveness verification after 60 days.
""",
    "VAL-PROT-2026_Sterile_Filter_Validation.txt": """
VALIDATION PROTOCOL: Hydrophobic Air Vent Filter Integrity Testing
Protocol ID: VAL-PROT-2026
Effective Date: 2026-03-10

1. ACCEPTANCE CRITERIA
- Water Intrusion Test (WIT) limit: ≤ 0.75 mL/min at 2500 mbar test pressure.
- Bubble Point Test limit: ≥ 3200 mbar using sterile WFI wetting liquid.

2. PROCEDURE
Perform post-use integrity testing immediately following batch filtration. Any integrity failure mandates immediate batch hold and mandatory sterile re-filtration evaluation.
"""
}

def seed_documents():
    logger.info("Uploading sample GxP documents to RustFS S3 bucket 'gxp-docs'...")
    for filename, content in SAMPLE_DOCS.items():
        s3_service.upload_file(
            file_content=content.encode("utf-8"),
            object_name=filename,
            content_type="text/plain"
        )
    
    logger.info("Triggering ingestion pipeline for uploaded documents...")
    results = ingestion_pipeline.sync_all_documents()
    logger.info(f"Ingestion summary: {results}")
    print("Seed complete! Documents uploaded to RustFS and indexed into Qdrant.")

if __name__ == "__main__":
    seed_documents()
