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
""",
    "SOP-OOS-015_Out_of_Specification_Investigation.txt": """
STANDARD OPERATING PROCEDURE: Out-of-Specification (OOS) Laboratory Investigation
SOP ID: SOP-OOS-015
Effective Date: 2026-02-01
Department: Quality Control Analytical Laboratory

1. PURPOSE & SCOPE
This SOP defines the mandatory procedure for evaluating and documenting any Out-of-Specification (OOS) analytical test result obtained during release or stability testing of active pharmaceutical ingredients (APIs) and finished drug products.

2. PHASE I: LABORATORY INVESTIGATION
- Must be completed within 7 business days of the initial initial OOS result discovery.
- Instrument logs, calibration status, reagent purity, and sample preparation steps must be audited before hypothesis testing.
- Re-testing Protocol: Re-testing requires prior written approval from the QC Manager. Maximum of 5 re-tests allowed per affected sample lot with documented scientific rationale.

3. PHASE II: CROSS-FUNCTIONAL INVESTIGATION & DISPOSITION
If Phase I does not uncover a clear laboratory error, initiate Phase II cross-functional manufacturing investigation within 24 hours. Material disposition requires Quality Assurance Director final signature.
""",
    "SOP-VAL-088_Computer_System_Validation.txt": """
STANDARD OPERATING PROCEDURE: Computer System Validation (CSV) & 21 CFR Part 11 Compliance
SOP ID: SOP-VAL-088
Effective Date: 2026-04-12
Department: IT Quality & Automation

1. GAMP 5 RISK CATEGORIZATION
- Category 3: Non-configured software (Off-the-shelf utilities). Validation requires vendor qualification and installation verification.
- Category 4: Configured software (LIMS, QMS, SCADA). Requires Functional Specification (FS), User Acceptance Testing (UAT), and Traceability Matrix.
- Category 5: Custom software (In-house algorithms & Pydantic AI microservices). Requires full lifecycle validation (DQ, IQ, OQ, PQ) and code security analysis.

2. 21 CFR PART 11 AUDIT TRAIL REVIEW
- Audit trails must be enabled 24/7 and stored in tamper-proof S3/WORM storage.
- QC analytical audit trails must be reviewed prior to batch release. General GxP system audit trails must undergo formal review monthly.
- Periodic System Re-validation: All Category 4 and 5 computerized systems must undergo formal periodic re-validation every 2 years.
""",
    "SOP-LOG-030_Cold_Chain_Storage_Transport.txt": """
STANDARD OPERATING PROCEDURE: Cold Chain Storage, Temperature Monitoring, and Excursion Management
SOP ID: SOP-LOG-030
Effective Date: 2026-01-20
Department: Supply Chain & Cold Chain Logistics

1. TEMPERATURE SPECIFICATIONS
- Refrigerated Storage (2°C to 8°C): Calibrated continuous dual-sensor data loggers recording at 5-minute intervals.
- Frozen Storage (-20°C ± 5°C): Monitored via centralized building management system (BMS).
- Ultra-Low Storage (-80°C ± 10°C): Dry ice shipments with validated thermal insulated shippers (min 96-hour temperature hold).

2. TEMPERATURE EXCURSION PROTOCOL
- Any temperature spike above 15°C lasting > 30 minutes, or any freezing event (< 0°C) for 2°C–8°C biologics requires immediate automated quarantine tag in ERP.
- Material must remain quarantined until QA performs thermal stability evaluation and releases disposition decision.
""",
    "SOP-EQ-104_HPLC_Equipment_Calibration.txt": """
STANDARD OPERATING PROCEDURE: High-Performance Liquid Chromatography (HPLC) Operation & Calibration
SOP ID: SOP-EQ-104
Effective Date: 2025-12-15
Department: Quality Control Analytics

1. PREVENTIVE MAINTENANCE & CALIBRATION
- Detector Wavelength & Flow Rate Calibration: Performed quarterly or after major pump component replacement.
- Retention Time Precision Limit: %RSD ≤ 1.0% across 6 replicate injections of analytical reference standard.
- Peak Area Precision Limit: %RSD ≤ 1.5% for active ingredient quantitation assays.

2. OPERATIONAL SAFETY LIMITS
- Maximum System Pressure: 300 bar for standard analytical columns; system autoswitch off triggered at 320 bar.
- Mobile phase degasser vacuum must maintain pressure below 50 mbar during acquisition.
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
