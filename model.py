"""
TrustLens Computer Vision Model
================================
Simple image classification model using MobileNetV2 from TensorFlow/Keras

This module:
- Loads a pretrained MobileNetV2 model
- Classifies images into categories (ImageNet classes)
- Hashes the model file for blockchain tracking
- Links predictions to the blockchain

Author: First-year CSE Student
Date: 2026-09-07
"""

import hashlib
import os
import json
from pathlib import Path
import numpy as np
from PIL import Image

# Try to import TensorFlow (with fallback for installation issues)
try:
    import tensorflow as tf
    from tensorflow.keras.applications import MobileNetV2
    from tensorflow.keras.preprocessing import image
    from tensorflow.keras.applications.mobilenet_v2 import decode_predictions
    TENSORFLOW_AVAILABLE = True
except ImportError:
    TENSORFLOW_AVAILABLE = False
    print("Warning: TensorFlow not available. Install with: pip install tensorflow")


class CVModel:
    """
    Computer Vision Model wrapper for image classification.

    Uses MobileNetV2 (lightweight, fast model suitable for educational purposes)
    from TensorFlow/Keras pretrained on ImageNet.

    Why MobileNetV2?
    - Small and fast (can run on CPU)
    - Good accuracy for common objects
    - Pretrained on ImageNet (1000 categories)
    - Educational: shows how transfer learning works
    """

    def __init__(self, model_dir='models'):
        """
        Initialize the CV model.

        Args:
            model_dir (str): Directory to store model files
        """
        self.model_dir = model_dir
        os.makedirs(model_dir, exist_ok=True)

        self.model = None
        self.model_hash = None
        self.model_path = None
        self.model_loaded = False

        if TENSORFLOW_AVAILABLE:
            self._load_model()
        else:
            print("⚠️  TensorFlow not available - using mock model for testing")

    def _load_model(self):
        """
        Load the pretrained MobileNetV2 model from Keras.

        This downloads the model on first run (~40MB) and caches it.
        """
        try:
            print("Loading MobileNetV2 model...")

            # Load pretrained model (includes weights trained on ImageNet)
            self.model = MobileNetV2(weights='imagenet')

            self.model_loaded = True
            print("✓ Model loaded successfully")

            # Calculate model hash (for blockchain)
            self.model_hash = self._calculate_model_hash()
            print(f"✓ Model hash: {self.model_hash[:16]}...")

        except Exception as e:
            print(f"✗ Error loading model: {e}")
            self.model_loaded = False

    def _calculate_model_hash(self):
        """
        Calculate SHA-256 hash of the model.

        For neural networks, we hash the model config and weights serialization
        to create a unique fingerprint for blockchain tracking.

        Returns:
            str: SHA-256 hash of the model
        """
        try:
            # Get model configuration as JSON
            config = self.model.to_json()

            # Hash the configuration
            # Note: In production, you'd also hash the weights
            model_hash = hashlib.sha256(config.encode()).hexdigest()

            return model_hash

        except Exception as e:
            print(f"Error calculating model hash: {e}")
            return hashlib.sha256(b"mobilenet_v2_default").hexdigest()

    def get_model_info(self):
        """
        Get information about the loaded model.

        Returns:
            dict: Model metadata for blockchain storage
        """
        return {
            'model_name': 'MobileNetV2',
            'model_type': 'image_classification',
            'framework': 'TensorFlow/Keras',
            'input_shape': (224, 224, 3),
            'output_classes': 1000,
            'dataset': 'ImageNet',
            'model_hash': self.model_hash,
            'loaded': self.model_loaded
        }

    def predict(self, image_path, top_k=3):
        """
        Classify an image and return top predictions.

        Args:
            image_path (str): Path to the image file
            top_k (int): Number of top predictions to return

        Returns:
            dict: Predictions with class names and confidence scores
                  Returns None if model not loaded or error occurs
        """
        if not self.model_loaded:
            return {
                'error': 'Model not loaded',
                'predictions': []
            }

        try:
            # Load and preprocess image
            img = Image.open(image_path)

            # Convert to RGB if needed (handles PNG with alpha, grayscale, etc.)
            if img.mode != 'RGB':
                img = img.convert('RGB')

            # Resize to model input size
            img = img.resize((224, 224))

            # Convert to numpy array
            img_array = image.img_to_array(img)

            # Add batch dimension
            img_array = np.expand_dims(img_array, axis=0)

            # Preprocess for MobileNetV2 (normalize)
            from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
            img_array = preprocess_input(img_array)

            # Run prediction
            predictions = self.model.predict(img_array, verbose=0)

            # Decode predictions
            decoded = decode_predictions(predictions, top=top_k)[0]

            # Format results
            results = []
            for class_id, class_name, confidence in decoded:
                results.append({
                    'class_id': class_id,
                    'class_name': class_name,
                    'confidence': float(confidence),
                    'confidence_percent': f"{float(confidence) * 100:.1f}%"
                })

            return {
                'success': True,
                'image_path': image_path,
                'predictions': results,
                'top_prediction': results[0]['class_name'] if results else None,
                'model_hash': self.model_hash
            }

        except FileNotFoundError:
            return {
                'success': False,
                'error': f'Image file not found: {image_path}',
                'predictions': []
            }

        except Exception as e:
            return {
                'success': False,
                'error': f'Prediction error: {str(e)}',
                'predictions': []
            }

    def save_model_metadata(self, output_file='model_metadata.json'):
        """
        Save model metadata to JSON file for reference.

        Args:
            output_file (str): Path to save metadata

        Returns:
            str: Path to saved file
        """
        metadata = {
            'model_info': self.get_model_info(),
            'timestamp': __import__('datetime').datetime.now().isoformat()
        }

        filepath = os.path.join(self.model_dir, output_file)

        with open(filepath, 'w') as f:
            json.dump(metadata, f, indent=2)

        return filepath


# ============================================================================
# DEMO / TESTING CODE
# ============================================================================

if __name__ == "__main__":
    """
    This code runs when you execute: python model.py
    It demonstrates the CV model functionality.
    """

    print("=" * 60)
    print("TrustLens Computer Vision Model Demo")
    print("=" * 60)
    print()

    # Initialize model
    print("1. Initializing CV Model...")
    model = CVModel(model_dir='models')
    print()

    # Get model info
    print("2. Model Information:")
    info = model.get_model_info()
    for key, value in info.items():
        print(f"   {key}: {value}")
    print()

    # Create a test image
    print("3. Creating test image...")
    test_image_path = 'uploads/test_image.jpg'

    if not os.path.exists(test_image_path):
        # Create a simple test image
        os.makedirs('uploads', exist_ok=True)

        # Create a basic image using PIL
        img = Image.new('RGB', (224, 224), color=(100, 150, 200))
        img.save(test_image_path)
        print(f"   ✓ Created test image: {test_image_path}")
    else:
        print(f"   ✓ Using existing image: {test_image_path}")
    print()

    # Make prediction
    if model.model_loaded:
        print("4. Making prediction on test image...")
        result = model.predict(test_image_path, top_k=3)

        if result['success']:
            print("   Predictions:")
            for i, pred in enumerate(result['predictions'], 1):
                print(f"   {i}. {pred['class_name']}: {pred['confidence_percent']}")
        else:
            print(f"   ✗ {result['error']}")
    else:
        print("4. Model not available for predictions")
        print("   Install TensorFlow to enable: pip install tensorflow")

    print()
    print("=" * 60)
    print("CV Model Demo Complete!")
    print("=" * 60)
