# 🔍 TRUST-LENS
### *Cryptographically Auditable, Immutable AI Inference Logging Engine via Dedicated Blockchain Architecture*

[![CI/CD Pipeline](https://github.com/AUSTIN-JR/TRUST-LENS/actions/workflows/test.yml/badge.svg)](https://github.com/AUSTIN-JR/TRUST-LENS/actions)
[![Security Policy](https://img.shields.io/badge/Security-Policy-blue.svg)](SECURITY.md)
[![Blockchain Engine](https://img.shields.io/badge/Ledger-Custom%20SHA--256%20Chain-purple.svg)](#blockchain-architecture)
[![ML Framework](https://img.shields.io/badge/ML%20Engine-TensorFlow%20%2F%20MobileNetV2-orange.svg)](https://tensorflow.org)
[![Database](https://img.shields.io/badge/Storage-SQLite3%20WAL-lightgrey.svg)](https://sqlite.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

---

## 📌 Executive Summary & Project Conception

**TRUST-LENS** is an enterprise-grade forensic logging and audit framework that bridges the critical trust deficit in modern artificial intelligence deployments. By binding deep learning computer vision inferences (MobileNetV2) directly to a custom, tamper-evident cryptographic blockchain ledger, TRUST-LENS guarantees an unalterable, mathematically provable record of:

1. Exactly **what input data** the model observed (via canonical SHA-256 image digest).
2. Exactly **which model weights and version** executed the computation (via model binary serialization hash).
3. Exactly **what decision and confidence score** were rendered at the exact microsecond timestamp.

If an adversarial database administrator, malicious insider, or compromised system process tampers with a historical inference record in the database, the cryptographic hash link in the blockchain breaks instantly—flagging the exact block, timestamp, and tampered field.

---

## 🚨 Problem Statement: The Black-Box Accountability Crisis

Modern deep learning systems are increasingly entrusted with life-altering, high-stakes decisions:
* **Autonomous Driving & Robotics:** Object classification determining vehicle braking actions.
* **Healthcare & Medical Diagnostics:** Tumor identification and pathology screening recommendations.
* **Financial Services & Automated Lending:** Creditworthiness evaluation, fraud detection, and transaction blocking.
* **Criminal Justice & Border Biometrics:** Automated facial recognition and predictive risk profiling.

### The Fundamental Flaws in Current Architectures:
1. **Mutable Centralized Logs:** Standard production systems write inference events to traditional relational databases (PostgreSQL, MySQL) or log aggregators (Elasticsearch, CloudWatch). Any user with database administrative privileges (`UPDATE inferences SET prediction='benign' WHERE id=402`) can silently rewrite history following an adverse event.
2. **Post-Incident Model Swapping:** Following an AI failure or bias investigation, organizations can secretly retrain or patch a model and retroactively claim the updated weights were responsible for the decision, with zero external auditability.
3. **Regulatory Non-Compliance:** Emerging compliance mandates (e.g., the **EU AI Act**, **FDA Software as a Medical Device (SaMD)** rules, and **NIST AI Risk Management Framework 1.0**) legally require verifiable, non-repudiable audit trails of autonomous algorithmic determinations.

**TRUST-LENS solves this crisis** by removing decision logs from mutable database tables and sealing them inside cryptographic blocks linked by SHA-256 hash chains.

---

## 🏛️ Core Architectural Pillars

```
                               TRUST-LENS WORKFLOW PIPELINE
                               
   [Raw Input Image]                  [Model Weights / Version]
          │                                      │
          ▼                                      ▼
   [SHA-256 Digest]                       [SHA-256 Digest]
          │                                      │
          └──────────────────┬───────────────────┘
                             │
                             ▼
                 [MobileNetV2 Inference Engine]
                             │
            ┌────────────────┴────────────────┐
            ▼                                 ▼
   [Prediction: Class]             [Confidence Score: 0-1]
            │                                 │
            └────────────────┬────────────────┘
                             │
                             ▼
                  [Inference Logger Engine]
                  - Generates Inference Hash
                  - Inserts Record into trustlens.db
                             │
                             ▼
                    [Blockchain Node]
                  - Pulls Unmined Inference Data
                  - Mines New Block (SHA-256 Proof)
                  - Cryptographically Links to Block (N-1)
                             │
                             ▼
              [Immutable Ledger: Genesis ──► N]
```

### 1. The Custom Blockchain Component (`blockchain.py`)
* **Block Topology:** Every block encapsulates `index`, `timestamp`, `data` (dictionary containing inference hash, image digest, model hash, and predictions), `previous_hash`, and its own calculated `current_hash`.
* **Hash Continuity:** The cryptographic integrity of Block $N$ is directly dependent on the exact bit-level byte stream of Block $N-1$:
  $$\text{Hash}_N = \text{SHA256}(\text{Index}_N \parallel \text{Timestamp}_N \parallel \text{Data}_N \parallel \text{Hash}_{N-1})$$
* **Tamper-Evident Verification:** The chain provides an instantaneous $O(N)$ integrity audit. If even 1 single bit in any historical inference is modified, the downstream hashes diverge catastrophically, immediately isolating the tampering.

### 2. The Machine Learning Engine (`model.py`)
* **Architecture:** MobileNetV2 pretrained on ImageNet (1.4 million labeled images across 1,000 semantic categories).
* **Deterministic Model Fingerprinting:** On initialization, the system calculates a SHA-256 hash across the serialized model architecture and weights. This guarantees that model substitution is impossible without invalidating subsequent blockchain blocks.
* **Inference Pipeline:** Preprocesses raw RGB images into $224 \times 224 \times 3$ normalized tensor arrays, computes softmax probability distributions, and extracts top-$k$ classification results.

### 3. The Forensic Inference Logger (`inference_logger.py`)
* **Atomic Transaction Packaging:** Couples input artifacts, model fingerprints, and model predictions into an immutable JSON payload.
* **Dual Persistence Layer:** High-speed SQLite operational table (`trustlens.db`) for rapid web UI dashboard filtering, backed by the linear cryptographic blockchain for audit verification.

---

## 🤝 The Trust Model: Who Trusts Whom?

```
┌─────────────────┐             ┌─────────────────┐             ┌─────────────────┐
│   REGULATORS    │             │  DATA AUDITORS  │             │   END USERS     │
│ & LEGAL COURTS  │             │ & COMPLIANCE    │             │ & PATIENTS      │
└────────┬────────┘             └────────┬────────┘             └────────┬────────┘
         │                               │                               │
         │ Trust Cryptographic           │ Trust Mathematical            │ Trust Non-
         │ Proof of History              │ Immutability of Logs          │ Repudiation
         ▼                               ▼                               ▼
 ═════════════════════════════════════════════════════════════════════════════════
                         TRUST-LENS IMMUTABLE LEDGER
 ═════════════════════════════════════════════════════════════════════════════════
```

### What TRUST-LENS Formally Establishes:
1. **Proof of Existence:** Proves that an inference event occurred at or before timestamp $T$.
2. **Proof of Input Identity:** Proves that inference $X$ was generated specifically from image $I$, preventing claims that the user submitted a corrupted or modified file.
3. **Proof of Model Lineage:** Proves that model version $M_v$ produced the inference, eliminating silent post-deployment model updates.
4. **Proof of Non-Tampering:** Proves that neither the prediction nor the confidence score has been altered since the block was committed to the ledger.

---

## 🔒 Security Features & Attack Resistance

### 1. Cryptographic Immutability
* **Digest Standard:** Standardized on SHA-256 (256-bit hash length, $2^{128}$ collision resistance).
* **Avalanche Effect:** A 1-bit mutation in any historical inference field changes an average of 128 bits in the block hash, causing an unmistakable mismatch with the `previous_hash` of the succeeding block.

### 2. Resistance to Traditional Attacks
* **Historical Rewriting Attack (Database Insider):** If an adversary modifies a row in `trustlens.db`, the `/api/verify-chain` endpoint recalculates the cryptographic chain from the Genesis Block forward. The database tamper is detected instantly, identifying the corrupted block index.
* **Man-In-The-Middle Logging Injection:** Inferences can only be sealed into the blockchain if the input image hash matches the binary buffer received by the web endpoint.
* **Model Impersonation Attack:** If an unapproved neural network model is loaded, its `model_hash` will fail verification against the trusted model registry stored on-chain.

---

## 💼 Real-World Enterprise Use Cases

### 🏥 Use Case 1: Medical Imaging & Diagnostic Accountability
* **Scenario:** A healthcare network utilizes deep learning to analyze chest X-rays for early signs of pulmonary embolism. A physician discharges a patient based on an AI recommendation classifying the scan as "normal". The patient subsequently suffers a critical complication.
* **The Audit:** Investigators query TRUST-LENS. The blockchain reveals Block #1042 containing the SHA-256 hash of the original DICOM image, the exact model weights version, and the AI's actual prediction. If the model had actually flagged a high probability of embolism and an internal actor altered the hospital database to shield themselves from malpractice liability, the blockchain proves the database was falsified.

### 🚗 Use Case 2: Autonomous Vehicle Sensor Forensics
* **Scenario:** An autonomous vehicle strikes an obstacle. Telemetry logs are subpoenaed to determine whether the perception system misclassified the obstacle or the control actuator failed.
* **The Audit:** TRUST-LENS provides non-repudiable proof of every optical frame classification processed by the perception subsystem during the 30 seconds prior to impact.

### 🏦 Use Case 3: Automated Financial Underwriting & Anti-Bias Auditing
* **Scenario:** A commercial bank deploys a computer vision system to analyze identity credentials and facial micro-expressions for automated personal loan approvals. Regulatory authorities investigate potential algorithmic disparate impact.
* **The Audit:** Regulators audit historical decisions over a 12-month period using the `trustlens.db` audit interface, proving that historical training weights were consistent and unmanipulated during regulatory reviews.

---

## 🛠️ Technical Specifications & API Architecture

### Database Schema (`trustlens.db`)

```sql
CREATE TABLE IF NOT EXISTS inferences (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    timestamp TEXT NOT NULL,
    image_hash TEXT NOT NULL,
    model_name TEXT NOT NULL,
    model_version TEXT NOT NULL,
    model_hash TEXT NOT NULL,
    prediction TEXT NOT NULL,
    confidence REAL NOT NULL,
    inference_hash TEXT UNIQUE NOT NULL,
    block_index INTEGER,
    status TEXT DEFAULT 'pending'
);

CREATE TABLE IF NOT EXISTS blocks (
    block_index INTEGER PRIMARY KEY,
    timestamp TEXT NOT NULL,
    previous_hash TEXT NOT NULL,
    current_hash TEXT NOT NULL,
    data_json TEXT NOT NULL
);
```

### RESTful API Specification

| Endpoint | Method | Payload / Parameters | Description |
| :--- | :--- | :--- | :--- |
| **`/api/predict`** | `POST` | Multipart Form: `image` (binary file) | Runs MobileNetV2 inference, logs metadata, and returns classification + block status. |
| **`/api/blockchain`** | `GET` | None | Returns the full JSON array of all committed blocks from Genesis to tip. |
| **`/api/verify-chain`** | `GET` | None | Executes mathematical recalculation of all hash links; returns `{"valid": true}` or tampering report. |
| **`/api/history`** | `GET` | `?limit=50&offset=0` | Returns recent inference logs with associated blockchain confirmations. |
| **`/api/tamper-test`** | `POST` | `{"block_index": int, "fake_data": str}` | Sandbox simulation endpoint demonstrating real-time tamper detection in action. |

---

## 🎯 Threat Model & Defensive Boundaries

```
ASSETS TO PROTECT:
├── AI Decision Authenticity (Historical Inferences)
├── Neural Model Lineage (Model Architecture & Weight Hashes)
└── Input Image Integrity (Raw Image Hashes)

THREATS MITIGATED:
├── T1: Post-Facto Record Modification (Mitigated by SHA-256 chain links)
├── T2: Model Version Swapping (Mitigated by Model Binary Hashing)
├── T3: Disavowal of Input Artifacts (Mitigated by Input Image Hashing)
└── T4: Silent Database Corruption (Mitigated by Automated Chain Verification)

OUT OF SCOPE:
├── Algorithmic Hallucination / Inherent ML Inaccuracies
├── Physical Host Power Outages / Hardware Faults
└── OS-Level Memory Injection (Rootkit / Kernel Exploit)
```

---

## 🚀 Installation & Local Execution

### Prerequisites
* Python 3.9, 3.10, or 3.11
* `git` version control
* Virtual environment utility (`venv`)

### 1. Clone & Environment Setup
```bash
# Clone the repository
git clone https://github.com/AUSTIN-JR/TRUST-LENS.git
cd TRUST-LENS

# Create and activate virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .\.venv\Scripts\Activate.ps1

# Install core machine learning and web dependencies
pip install --upgrade pip
pip install -r requirements.txt
```

### 2. Initialize Database & Genesis Block
```bash
# Verify model loads and bootstrap initial blockchain state
python -c "from blockchain import Blockchain; bc = Blockchain(); print('Genesis Block Initialized:', bc.chain[0].current_hash)"
```

### 3. Launch the TrustLens Dashboard Server
```bash
# Run the application
python app.py
```
Open **`http://127.0.0.1:5000`** in your browser.

---

## 🧪 Automated Verification & Test Suite

The system includes comprehensive automated testing across core modules:

```bash
# Execute entire test suite
pytest test_part2.py test_part3.py test_parts_4_5_6.py tests/ -v
```

### Test Coverage Architecture:
* **`test_part2.py`:** Blockchain validation, Genesis block generation, hash integrity, block creation, and tampering detection.
* **`test_part3.py`:** MobileNetV2 image preprocessing, prediction normalization, top-5 prediction decoding, and model weight hashing.
* **`test_parts_4_5_6.py`:** SQLite database schema validation, inference logging persistence, atomic transaction integrity, and Flask REST API endpoints.

---

## ☁️ Deployment & Production Infrastructure

TRUST-LENS includes production-ready configuration for zero-friction cloud deployment:

### Render Cloud Configuration (`render.yaml`)
```yaml
services:
  - type: web
    name: trust-lens
    env: python
    buildCommand: pip install -r requirements.txt
    startCommand: gunicorn app:app --workers 2 --timeout 120
    envVars:
      - key: PYTHON_VERSION
        value: 3.10.12
      - key: FLASK_ENV
        value: production
```

---

## 🗺️ Future Engineering Roadmap

- [x] Custom SHA-256 blockchain implementation with Genesis bootstrapping
- [x] MobileNetV2 integration with automated input/model hashing
- [x] SQLite3 dual persistence with real-time tamper detection
- [x] Full RESTful API with interactive web dashboard
- [ ] **Phase 2:** Zero-Knowledge Proofs (zk-SNARKs) to prove inference validity without exposing confidential patient/financial input data
- [ ] **Phase 3:** Multi-node consensus (Raft or lightweight Proof-of-Authority) across multiple auditing hospital/bank nodes
- [ ] **Phase 4:** Hardware Security Module (HSM) signing for model certificates

---

## 🔒 Security Policy

For vulnerability reporting or security auditing details, please review **[SECURITY.md](SECURITY.md)** or contact **`robinaustinj@gmail.com`**.

---

## ⚖️ License & Attribution

Distributed under the **MIT License**. Created by **Austin J Robin (AUSTIN-JR)** for AI accountability, forensic machine learning auditability, and cybersecurity research.