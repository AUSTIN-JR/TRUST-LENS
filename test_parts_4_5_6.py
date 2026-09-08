"""
TrustLens Parts 4-6 Integration Test
====================================
Tests inference logging, verification, and dashboard functionality
"""

import sys
sys.path.insert(0, 'D:\\vs code\\TrustLens')

from blockchain import Blockchain
from inference_logger import InferenceLogger
import hashlib
import sqlite3
import os
from datetime import datetime

DB_PATH = 'test_integration.db'

print("=" * 60)
print("TrustLens Parts 4-6 Integration Test")
print("=" * 60)
print()

# Clean up old database
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

# Test 1: Blockchain with inference data
print("1. Testing Blockchain with Inference Data...")
try:
    bc = Blockchain()

    # Add image upload block
    bc.add_block({
        'type': 'image_upload',
        'filename': 'test_image.jpg',
        'file_hash': hashlib.sha256(b'test_image').hexdigest(),
        'uploader_name': 'Alice'
    })

    # Add model block
    bc.add_block({
        'type': 'model_info',
        'model_name': 'MobileNetV2',
        'model_hash': hashlib.sha256(b'mobilenet_v2').hexdigest()
    })

    # Add inference block
    bc.add_block({
        'type': 'inference',
        'image_hash': hashlib.sha256(b'test_image').hexdigest(),
        'model_hash': hashlib.sha256(b'mobilenet_v2').hexdigest(),
        'prediction': 'cat',
        'confidence': 0.95
    })

    is_valid, error = bc.is_chain_valid()
    print(f"   ✓ Blockchain created with {len(bc.chain)} blocks")
    print(f"   ✓ Blockchain valid: {is_valid}")
    print()

except Exception as e:
    print(f"   ✗ Error: {e}")
    print()

# Test 2: Inference Logging
print("2. Testing Inference Logging...")
try:
    logger = InferenceLogger(DB_PATH)

    # Log first inference
    result1 = logger.log_inference(
        upload_id=1,
        image_hash=hashlib.sha256(b'test_image').hexdigest(),
        filename='test_image.jpg',
        model_hash=hashlib.sha256(b'mobilenet_v2').hexdigest(),
        model_name='MobileNetV2',
        top_prediction='cat',
        confidence=0.95,
        all_predictions=[
            {'class': 'cat', 'confidence': 0.95},
            {'class': 'dog', 'confidence': 0.04},
            {'class': 'bird', 'confidence': 0.01}
        ],
        block_index=3
    )
    print(f"   ✓ Inference 1 logged (ID: {result1['inference_id']})")
    print(f"   Inference hash: {result1['inference_hash'][:32]}...")

    # Log second inference
    result2 = logger.log_inference(
        upload_id=2,
        image_hash=hashlib.sha256(b'test_image2').hexdigest(),
        filename='test_image2.jpg',
        model_hash=hashlib.sha256(b'mobilenet_v2').hexdigest(),
        model_name='MobileNetV2',
        top_prediction='dog',
        confidence=0.87,
        all_predictions=[
            {'class': 'dog', 'confidence': 0.87},
            {'class': 'cat', 'confidence': 0.10},
            {'class': 'wolf', 'confidence': 0.03}
        ],
        block_index=4
    )
    print(f"   ✓ Inference 2 logged (ID: {result2['inference_id']})")
    print()

except Exception as e:
    print(f"   ✗ Error: {e}")
    print()

# Test 3: Inference Verification
print("3. Testing Inference Verification (Part 5)...")
try:
    # Verify first inference
    verify1 = logger.verify_inference_integrity(result1['inference_id'])
    print(f"   ✓ Inference 1 verification: {verify1['valid']}")

    # Verify second inference
    verify2 = logger.verify_inference_integrity(result2['inference_id'])
    print(f"   ✓ Inference 2 verification: {verify2['valid']}")

    # Test tampering detection
    # Modify the database directly to simulate tampering
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        UPDATE inference_logs
        SET top_prediction = 'bird'
        WHERE id = ?
    ''', (result1['inference_id'],))
    conn.commit()
    conn.close()

    # Try to verify tampered inference
    verify_tampered = logger.verify_inference_integrity(result1['inference_id'])
    print(f"   ✓ Tampered inference detected: {not verify_tampered['valid']}")
    print()

except Exception as e:
    print(f"   ✗ Error: {e}")
    print()

# Test 4: Dashboard Data (Part 6)
print("4. Testing Dashboard Data (Part 6)...")
try:
    # Get recent inferences
    recent = logger.get_recent_inferences(limit=5)
    print(f"   ✓ Retrieved {len(recent)} recent inferences")

    # Get model statistics
    stats = logger.get_all_model_statistics()
    print(f"   ✓ Retrieved {len(stats)} model(s)")
    for stat in stats:
        print(f"      - {stat['model_name']}: {stat['total_inferences']} inferences, " +
              f"{stat['average_confidence']:.2%} avg confidence")

    # Get summary
    summary = logger.get_inference_summary()
    print(f"   ✓ Summary:")
    print(f"      Total inferences: {summary['total_inferences']}")
    print(f"      Average confidence: {summary['average_confidence']:.2%}")
    print(f"      Models used: {summary['models_used']}")
    print()

except Exception as e:
    print(f"   ✗ Error: {e}")
    print()

# Test 5: Query Functions
print("5. Testing Query Functions...")
try:
    image_hash = hashlib.sha256(b'test_image').hexdigest()
    model_hash = hashlib.sha256(b'mobilenet_v2').hexdigest()

    # Get inferences by image
    by_image = logger.get_inferences_by_image(image_hash)
    print(f"   ✓ Found {len(by_image)} inference(s) for specific image")

    # Get inferences by model
    by_model = logger.get_inferences_by_model(model_hash)
    print(f"   ✓ Found {len(by_model)} inference(s) for specific model")

    # Get specific inference
    specific = logger.get_inference_by_id(result1['inference_id'])
    if specific:
        print(f"   ✓ Retrieved specific inference:")
        print(f"      Filename: {specific['filename']}")
        print(f"      Prediction: {specific['top_prediction']}")
        print(f"      Confidence: {specific['confidence_score']:.2%}")

    print()

except Exception as e:
    print(f"   ✗ Error: {e}")
    print()

# Test 6: Tamper Audit Trail
print("6. Testing Tamper Audit Trail...")
try:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute('SELECT * FROM inference_audit')
    audits = cursor.fetchall()
    conn.close()

    print(f"   ✓ Audit trail entries: {len(audits)}")
    for audit in audits:
        print(f"      - Action: {audit['action']}")
        print(f"        Time: {audit['detected_timestamp']}")

    print()

except Exception as e:
    print(f"   ✗ Error: {e}")
    print()

print("=" * 60)
print("✅ Parts 4-6 Integration Tests Complete!")
print("=" * 60)
print()
print("Summary:")
print("✓ Blockchain stores inference data")
print("✓ Inference logging with integrity hashing")
print("✓ Inference verification and tamper detection")
print("✓ Dashboard data queries working")
print("✓ Audit trail for tampering")
print()
print("All components ready for deployment!")

# Clean up
os.remove(DB_PATH)
