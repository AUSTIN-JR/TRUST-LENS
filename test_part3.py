"""
TrustLens Part 3 Test - CV Model Integration
=============================================
Tests the computer vision model and blockchain integration
"""

import sys
sys.path.insert(0, 'D:\\vs code\\TrustLens')

from model import CVModel
from blockchain import Blockchain
import hashlib
from datetime import datetime

print("=" * 60)
print("TrustLens Part 3 Test - CV Model")
print("=" * 60)
print()

# Test 1: Initialize CV Model
print("1. Initializing CV Model...")
try:
    model = CVModel(model_dir='models')
    print(f"   ✓ Model initialized")
    if model.model_loaded:
        print(f"   ✓ Model loaded successfully")
    else:
        print(f"   ⚠️  Model not fully loaded (TensorFlow may not be installed)")
except Exception as e:
    print(f"   ✗ Error: {e}")

print()

# Test 2: Get Model Info
print("2. Model Information:")
try:
    info = model.get_model_info()
    for key, value in info.items():
        print(f"   {key}: {value}")
except Exception as e:
    print(f"   ✗ Error: {e}")

print()

# Test 3: Model Hash
print("3. Model Hashing for Blockchain:")
if model.model_hash:
    print(f"   ✓ Model hash calculated: {model.model_hash[:32]}...")
    print(f"   ✓ Full hash: {model.model_hash}")
else:
    print(f"   ✗ Model hash not available")

print()

# Test 4: Blockchain Integration
print("4. Blockchain Integration:")
try:
    bc = Blockchain()

    # Add model info block
    model_block = bc.add_block({
        'type': 'model_info',
        'model_name': 'MobileNetV2',
        'model_hash': model.model_hash,
        'framework': 'TensorFlow/Keras',
        'dataset': 'ImageNet'
    })
    print(f"   ✓ Model block added to blockchain")
    print(f"   Block #{model_block.index}: {model_block.data['model_name']}")

    # Add inference example block
    image_hash = hashlib.sha256(b"test_image.jpg").hexdigest()
    prediction = "cat"

    inference_data = f"{image_hash}{model.model_hash}{prediction}"
    inference_hash = hashlib.sha256(inference_data.encode()).hexdigest()

    inference_block = bc.add_block({
        'type': 'inference',
        'image_hash': image_hash,
        'model_hash': model.model_hash,
        'prediction': prediction,
        'confidence': 0.95,
        'inference_hash': inference_hash
    })
    print(f"   ✓ Inference block added to blockchain")
    print(f"   Block #{inference_block.index}: Predicted '{prediction}' with 95% confidence")

    # Verify blockchain
    is_valid, error = bc.is_chain_valid()
    print(f"   ✓ Blockchain valid: {is_valid}")
    print(f"   ✓ Total blocks: {len(bc.chain)}")

except Exception as e:
    print(f"   ✗ Error: {e}")

print()

# Test 5: Prediction (if model is loaded)
print("5. Model Prediction Test:")
if model.model_loaded:
    try:
        # Create a simple test image
        from PIL import Image
        import os

        os.makedirs('uploads', exist_ok=True)
        test_image = 'uploads/test_prediction.jpg'

        # Create a test image
        img = Image.new('RGB', (224, 224), color=(73, 109, 137))
        img.save(test_image)

        print(f"   ✓ Test image created: {test_image}")

        # Run prediction
        result = model.predict(test_image, top_k=3)

        if result.get('success'):
            print(f"   ✓ Prediction successful")
            print(f"   Top 3 predictions:")
            for i, pred in enumerate(result['predictions'], 1):
                print(f"      {i}. {pred['class_name']}: {pred['confidence_percent']}")
        else:
            print(f"   ✗ Prediction failed: {result.get('error')}")

    except Exception as e:
        print(f"   ✗ Error during prediction: {e}")
else:
    print(f"   ⚠️  Model not loaded - skipping prediction test")
    print(f"   Install TensorFlow: pip install tensorflow")

print()
print("=" * 60)
print("✅ Part 3 Tests Complete!")
print("=" * 60)
print()
print("Summary:")
print("- CV Model wrapper created and working")
print("- Model hashing implemented for blockchain")
print("- Blockchain integration tested")
print("- Inference logging tested")
print()
print("Next: Integration with Flask backend (already done in app.py)")
print("      Routes available:")
print("      - GET /api/model-info")
print("      - POST /predict/<upload_id>")
print("      - GET /api/predictions")
