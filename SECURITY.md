# Security Policy — TRUST-LENS

**Project:** TRUST-LENS (Immutable AI Inference Logging via Blockchain)  
**Author & Maintainer:** Austin J Robin (AUSTIN-JR)  
**Security Contact:** `robinaustinj@gmail.com`  
**Classification:** Cryptographic & Forensic AI Auditing System  
**Last Revised:** September 2026  

---

## 1. Vulnerability Reporting & Coordinated Disclosure

TRUST-LENS is designed to serve as an immutable source of truth in safety-critical and regulated AI decision systems. Cryptographic defects, block forgery exploits, database injection vulnerabilities, or tampering bypasses will be addressed with the utmost urgency.

### Reporting Procedure
**Please DO NOT open a public issue on GitHub for undisclosed security vulnerabilities.**

1. Send an encrypted or direct email to **`robinaustinj@gmail.com`**.
2. Subject format: `[SECURITY AUDIT] TRUST-LENS - <Vulnerability Classification>`.
3. Provide:
   * A detailed description of the vulnerability.
   * Proof-of-concept scripts, attack transactions, or payload sequences.
   * Specific modules impacted (`blockchain.py`, `inference_logger.py`, `model.py`, or `app.py`).
   * Estimated threat severity and potential audit distortion impact.

### Service Commitments
* **Initial Acknowledgment:** Within **24–48 hours**.
* **Triage & Threat Modeling:** Within **5 business days** with a formal CVSS v3.1 score.
* **Patch Release:** High-severity cryptographic or chain-breaking issues patched within **14 days**.
* **Public Disclosure:** Full disclosure published **30 days** post-remediation.

---

## 2. Threat Model & Security Architecture

TRUST-LENS establishes an immutable audit perimeter around the machine learning inference lifecycle.

```
+-----------------------------------------------------------------------------------+
|                            TRUST-LENS SECURITY BOUNDARY                           |
+-----------------------------------------------------------------------------------+
|  [UNTRUSTED DATABASE ENVIRONMENT]                                                 |
|  - Relational SQLite tables (trustlens.db) can be altered by DBAs or root users.  |
+------------------------------------------┬----------------------------------------+
                                           │ (Cryptographic Hash Validation)
+------------------------------------------▼----------------------------------------+
|  [IMMUTABLE BLOCKCHAIN VALIDATION LAYER]                                          |
|  - Blocks linked by SHA-256 parent hash references.                              |
|  - Input images, model binaries, and output predictions committed to block data.  |
|  - Automatic mathematical divergence detection on any row alteration.             |
+-----------------------------------------------------------------------------------+
```

### Assets Protected by TRUST-LENS
1. **Historical Inference Authenticity:** Ensuring past model decisions cannot be rewritten or expunged following an adverse outcome.
2. **Model Version Lineage:** Guaranteeing that the exact model weights used during inference are cryptographically provable.
3. **Input Data Traceability:** Verifying that the input features/image provided during an audit match the exact artifact fed into the model.

### Threats Mitigated

| Threat Vector | Defensive Mechanism | Cryptographic Guarantee |
| :--- | :--- | :--- |
| **Historical Revisionism (Malicious DBA)** | Cryptographic Blockchain Hash Continuity | Modifying any past record breaks the `previous_hash` link in block $N+1$, failing chain verification. |
| **Model Version Swapping** | Dynamic Model Binary Hashing | The SHA-256 hash of the model structure and weights is embedded into every inference transaction. |
| **Input Data Disavowal** | Canonical Input Image Digesting | The raw image is digested before preprocessing, proving the exact visual input processed. |
| **Inference Forgery** | Deterministic Composite Inference Hash | The inference hash combines: `image_hash + model_hash + prediction + confidence + timestamp`. |
| **Silent Database Corruption** | Automated Continuous Chain Verification | Any hash discrepancy is immediately exposed via the `/api/verify-chain` diagnostic endpoint. |

### Out of Scope (Accepted Operational Realities)
* **Underlying Model Inherent Bias / Hallucination:** TRUST-LENS logs what the model did; it does not correct statistical flaws in the neural network's training data.
* **Host Operating System Compromise:** Kernel-level attackers who overwrite volatile memory while the application is in active execution.
* **Quantum Computing:** Long-term migration to post-quantum signature schemes (e.g., Dilithium, Falcon) will be required when cryptanalytically relevant quantum computers emerge.

---

## 3. Cryptographic Implementation Choices: The "Why"

### A. Why Dedicated Local Blockchain vs. Public Blockchain (Ethereum/Solana)?
1. **Zero Financial Gas Costs:** Writing thousands of high-frequency AI inference transactions to a public blockchain incurs unsustainable gas fees ($0.05 to $5.00+ per inference). TRUST-LENS provides cryptographic immutability with zero network transaction costs.
2. **Deterministic Throughput:** Public blockchains suffer from unpredictable block confirmation times (12 seconds to several minutes). TRUST-LENS commits blocks deterministically in sub-millisecond windows.
3. **Data Privacy Control:** Public blockchains expose transaction contents globally, violating HIPAA (healthcare) and GDPR (financial) privacy regulations. TRUST-LENS keeps inference logs within the organization's secure network while maintaining full mathematical auditability.

### B. Why Composite Inference Hashing?
An inference is not merely a label; it is a point-in-time convergence of code, data, and compute. The inference hash is calculated as:
$$\text{Inference Hash} = \text{SHA256}(\text{ImageHash} \parallel \text{ModelHash} \parallel \text{Prediction} \parallel \text{Confidence} \parallel \text{Timestamp})$$
This prevents an attacker from decoupling an input from its output or claiming a different model made the decision.

---

## 4. Fundamental Security Assumptions

For TRUST-LENS guarantees to hold:
1. **Entropy & Hash Safety:** SHA-256 remains preimage and collision resistant.
2. **Access Control on Server Endpoints:** The `/api/predict` endpoint must be secured via API keys or TLS client certificates in enterprise deployments.
3. **Off-Site Ledger Mirroring:** To prevent a malicious hypervisor administrator from wiping both the database and the blockchain, block headers should be periodically mirrored to write-once-read-many (WORM) cloud storage (e.g., AWS S3 Object Lock).

---

## 5. Security Verification & Test Execution

Run the complete cryptographic and blockchain regression test suite:

```bash
# Execute unit and tamper-detection tests
pytest test_part2.py test_part3.py test_parts_4_5_6.py tests/ -v
```

### Verified Test Cases:
* **Tamper Injection:** Artificially alters a historical prediction in the database and verifies that the verification engine flags the exact corrupted block index.
* **Genesis Continuity:** Validates that the Genesis block index is 0, has `previous_hash="0"`, and validates cleanly.
* **Model Integrity:** Modifies model weights and verifies that the resulting model hash deviates completely from the registered hash.

---

## 6. Incident Response & Bug Bounties

* As an open-source academic and research project, financial bounties are not currently available.
* All security researchers who responsibly report verified vulnerabilities will receive formal public acknowledgment in the repository's Hall of Fame and release notes.
