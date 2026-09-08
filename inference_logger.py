"""
TrustLens Inference Logger
==========================
Logs and tracks all model inference operations with blockchain integrity.

This module handles:
- Detailed inference logging
- Confidence score tracking
- Model version tracking
- Inference history queries
- Tamper detection on inference logs

Author: First-year CSE Student
Date: 2026-09-07
"""

import sqlite3
import hashlib
import json
from datetime import datetime
from typing import List, Dict, Optional


class InferenceLogger:
    """
    Manages logging of model inference operations to database and blockchain.

    Each inference creates an audit trail:
    1. Image hash (identifies the input)
    2. Model hash (identifies the model version)
    3. Prediction (the output)
    4. Confidence (how sure the model was)
    5. Inference hash (combines all above for blockchain)
    6. Timestamp (when prediction was made)
    """

    def __init__(self, db_path: str):
        """
        Initialize the inference logger.

        Args:
            db_path (str): Path to SQLite database
        """
        self.db_path = db_path
        self.init_tables()

    def init_tables(self):
        """Create necessary database tables for inference logging."""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Detailed inference logs table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inference_logs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                upload_id INTEGER,
                image_hash TEXT NOT NULL,
                filename TEXT,
                model_hash TEXT NOT NULL,
                model_name TEXT,
                top_prediction TEXT NOT NULL,
                confidence_score REAL NOT NULL,
                all_predictions TEXT,
                inference_hash TEXT UNIQUE NOT NULL,
                block_index INTEGER,
                inference_timestamp TEXT NOT NULL,
                logged_timestamp TEXT NOT NULL,
                FOREIGN KEY(upload_id) REFERENCES uploads(id),
                FOREIGN KEY(block_index) REFERENCES blockchain_blocks(block_index)
            )
        ''')

        # Model inference statistics table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS model_statistics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                model_hash TEXT NOT NULL,
                model_name TEXT,
                total_inferences INTEGER DEFAULT 0,
                average_confidence REAL DEFAULT 0.0,
                last_used_timestamp TEXT,
                updated_timestamp TEXT
            )
        ''')

        # Inference audit trail (for detecting tampering)
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS inference_audit (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                inference_id INTEGER,
                action TEXT,
                original_data TEXT,
                modified_data TEXT,
                detected_timestamp TEXT,
                FOREIGN KEY(inference_id) REFERENCES inference_logs(id)
            )
        ''')

        conn.commit()
        conn.close()

    def log_inference(self,
                     upload_id: int,
                     image_hash: str,
                     filename: str,
                     model_hash: str,
                     model_name: str,
                     top_prediction: str,
                     confidence: float,
                     all_predictions: List[Dict],
                     block_index: Optional[int] = None) -> Dict:
        """
        Log a model inference operation.

        Creates an audit record combining all inference metadata into a
        single verifiable hash for blockchain storage.

        Args:
            upload_id (int): ID of the uploaded image
            image_hash (str): SHA-256 hash of the image
            filename (str): Original filename
            model_hash (str): SHA-256 hash of the model
            model_name (str): Name of the model (e.g., "MobileNetV2")
            top_prediction (str): Top predicted class
            confidence (float): Confidence score (0.0 to 1.0)
            all_predictions (list): All predictions with scores
            block_index (int): Index of blockchain block for this inference

        Returns:
            dict: Inference log entry with metadata
        """
        # Create inference hash (combines image + model + prediction)
        inference_data = f"{image_hash}{model_hash}{top_prediction}{confidence}"
        inference_hash = hashlib.sha256(inference_data.encode()).hexdigest()

        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        try:
            # Insert inference log
            cursor.execute('''
                INSERT INTO inference_logs
                (upload_id, image_hash, filename, model_hash, model_name,
                 top_prediction, confidence_score, all_predictions,
                 inference_hash, block_index, inference_timestamp, logged_timestamp)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                upload_id,
                image_hash,
                filename,
                model_hash,
                model_name,
                top_prediction,
                confidence,
                json.dumps(all_predictions),
                inference_hash,
                block_index,
                datetime.now().isoformat(),
                datetime.now().isoformat()
            ))

            inference_id = cursor.lastrowid

            # Update model statistics
            cursor.execute('''
                SELECT id, total_inferences, average_confidence
                FROM model_statistics
                WHERE model_hash = ?
            ''', (model_hash,))

            stat_row = cursor.fetchone()

            if stat_row:
                stat_id, total, avg_conf = stat_row
                new_total = total + 1
                new_avg = ((avg_conf * total) + confidence) / new_total

                cursor.execute('''
                    UPDATE model_statistics
                    SET total_inferences = ?,
                        average_confidence = ?,
                        last_used_timestamp = ?
                    WHERE id = ?
                ''', (new_total, new_avg, datetime.now().isoformat(), stat_id))
            else:
                cursor.execute('''
                    INSERT INTO model_statistics
                    (model_hash, model_name, total_inferences, average_confidence, last_used_timestamp, updated_timestamp)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    model_hash,
                    model_name,
                    1,
                    confidence,
                    datetime.now().isoformat(),
                    datetime.now().isoformat()
                ))

            conn.commit()

            return {
                'success': True,
                'inference_id': inference_id,
                'inference_hash': inference_hash,
                'logged_timestamp': datetime.now().isoformat()
            }

        except sqlite3.IntegrityError as e:
            return {'success': False, 'error': f'Duplicate inference: {str(e)}'}
        finally:
            conn.close()

    def get_inference_by_id(self, inference_id: int) -> Optional[Dict]:
        """
        Retrieve a specific inference log entry.

        Args:
            inference_id (int): ID of the inference to retrieve

        Returns:
            dict: Inference log entry or None
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM inference_logs WHERE id = ?', (inference_id,))
        result = cursor.fetchone()
        conn.close()

        if result:
            row_dict = dict(result)
            if row_dict['all_predictions']:
                row_dict['all_predictions'] = json.loads(row_dict['all_predictions'])
            return row_dict
        return None

    def get_inferences_by_image(self, image_hash: str) -> List[Dict]:
        """
        Get all inferences performed on a specific image.

        Args:
            image_hash (str): SHA-256 hash of the image

        Returns:
            list: List of inference log entries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            'SELECT * FROM inference_logs WHERE image_hash = ? ORDER BY id DESC',
            (image_hash,)
        )
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        for row in results:
            if row['all_predictions']:
                row['all_predictions'] = json.loads(row['all_predictions'])

        return results

    def get_inferences_by_model(self, model_hash: str) -> List[Dict]:
        """
        Get all inferences performed using a specific model.

        Args:
            model_hash (str): SHA-256 hash of the model

        Returns:
            list: List of inference log entries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            'SELECT * FROM inference_logs WHERE model_hash = ? ORDER BY id DESC',
            (model_hash,)
        )
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        for row in results:
            if row['all_predictions']:
                row['all_predictions'] = json.loads(row['all_predictions'])

        return results

    def get_recent_inferences(self, limit: int = 20) -> List[Dict]:
        """
        Get the most recent inference logs.

        Args:
            limit (int): Maximum number of records to return

        Returns:
            list: Recent inference log entries
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            'SELECT * FROM inference_logs ORDER BY id DESC LIMIT ?',
            (limit,)
        )
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        for row in results:
            if row['all_predictions']:
                row['all_predictions'] = json.loads(row['all_predictions'])

        return results

    def get_model_statistics(self, model_hash: str) -> Optional[Dict]:
        """
        Get statistics for a specific model.

        Args:
            model_hash (str): SHA-256 hash of the model

        Returns:
            dict: Model statistics or None
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            'SELECT * FROM model_statistics WHERE model_hash = ?',
            (model_hash,)
        )
        result = cursor.fetchone()
        conn.close()

        return dict(result) if result else None

    def get_all_model_statistics(self) -> List[Dict]:
        """
        Get statistics for all models used.

        Returns:
            list: Statistics for all models
        """
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute(
            'SELECT * FROM model_statistics ORDER BY total_inferences DESC'
        )
        results = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return results

    def verify_inference_integrity(self, inference_id: int) -> Dict:
        """
        Verify that an inference log hasn't been tampered with.

        Recalculates the inference hash and compares to stored value.

        Args:
            inference_id (int): ID of the inference to verify

        Returns:
            dict: Verification result
        """
        inference = self.get_inference_by_id(inference_id)

        if not inference:
            return {'valid': False, 'error': 'Inference not found'}

        # Recalculate hash
        inference_data = (
            f"{inference['image_hash']}"
            f"{inference['model_hash']}"
            f"{inference['top_prediction']}"
            f"{inference['confidence_score']}"
        )
        calculated_hash = hashlib.sha256(inference_data.encode()).hexdigest()

        # Compare
        is_valid = calculated_hash == inference['inference_hash']

        if not is_valid:
            # Log tampering detection
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            cursor.execute('''
                INSERT INTO inference_audit
                (inference_id, action, original_data, modified_data, detected_timestamp)
                VALUES (?, ?, ?, ?, ?)
            ''', (
                inference_id,
                'TAMPERING_DETECTED',
                inference['inference_hash'],
                calculated_hash,
                datetime.now().isoformat()
            ))

            conn.commit()
            conn.close()

        return {
            'valid': is_valid,
            'inference_id': inference_id,
            'stored_hash': inference['inference_hash'],
            'calculated_hash': calculated_hash,
            'image_hash': inference['image_hash'],
            'model_hash': inference['model_hash'],
            'prediction': inference['top_prediction'],
            'confidence': inference['confidence_score']
        }

    def get_inference_summary(self) -> Dict:
        """
        Get a summary of all inference activity.

        Returns:
            dict: Summary statistics
        """
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Total inferences
        cursor.execute('SELECT COUNT(*) FROM inference_logs')
        total_inferences = cursor.fetchone()[0]

        # Average confidence
        cursor.execute('SELECT AVG(confidence_score) FROM inference_logs')
        avg_confidence = cursor.fetchone()[0] or 0.0

        # Models used
        cursor.execute('SELECT COUNT(*) FROM model_statistics')
        models_used = cursor.fetchone()[0]

        # Most common prediction
        cursor.execute('''
            SELECT top_prediction, COUNT(*) as count
            FROM inference_logs
            GROUP BY top_prediction
            ORDER BY count DESC
            LIMIT 1
        ''')
        most_common = cursor.fetchone()

        conn.close()

        return {
            'total_inferences': total_inferences,
            'average_confidence': round(avg_confidence, 4),
            'models_used': models_used,
            'most_common_prediction': most_common[0] if most_common else None,
            'most_common_count': most_common[1] if most_common else 0
        }


# ============================================================================
# DEMO / TESTING CODE
# ============================================================================

if __name__ == "__main__":
    """
    This code runs when you execute: python inference_logger.py
    It demonstrates inference logging functionality.
    """

    import os

    DB_PATH = 'test_inference.db'

    # Clean up old test database
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

    print("=" * 60)
    print("TrustLens Inference Logger Demo")
    print("=" * 60)
    print()

    # Initialize logger
    print("1. Initializing Inference Logger...")
    logger = InferenceLogger(DB_PATH)
    print("   ✓ Logger initialized")
    print()

    # Log some sample inferences
    print("2. Logging sample inferences...")

    image_hash_1 = hashlib.sha256(b"cat_image.jpg").hexdigest()
    model_hash = hashlib.sha256(b"mobilenet_v2").hexdigest()

    result1 = logger.log_inference(
        upload_id=1,
        image_hash=image_hash_1,
        filename="cat_image.jpg",
        model_hash=model_hash,
        model_name="MobileNetV2",
        top_prediction="cat",
        confidence=0.95,
        all_predictions=[
            {"class": "cat", "confidence": 0.95},
            {"class": "dog", "confidence": 0.03},
            {"class": "bird", "confidence": 0.02}
        ],
        block_index=3
    )
    print(f"   ✓ Inference 1 logged (ID: {result1['inference_id']})")

    result2 = logger.log_inference(
        upload_id=2,
        image_hash=hashlib.sha256(b"dog_image.jpg").hexdigest(),
        filename="dog_image.jpg",
        model_hash=model_hash,
        model_name="MobileNetV2",
        top_prediction="dog",
        confidence=0.87,
        all_predictions=[
            {"class": "dog", "confidence": 0.87},
            {"class": "cat", "confidence": 0.10},
            {"class": "wolf", "confidence": 0.03}
        ],
        block_index=4
    )
    print(f"   ✓ Inference 2 logged (ID: {result2['inference_id']})")
    print()

    # Verify inference integrity
    print("3. Verifying inference integrity...")
    verify_result = logger.verify_inference_integrity(result1['inference_id'])
    print(f"   ✓ Inference valid: {verify_result['valid']}")
    print(f"   Hash match: {verify_result['stored_hash'][:16]}...")
    print()

    # Get recent inferences
    print("4. Recent inferences:")
    recent = logger.get_recent_inferences(limit=5)
    for inf in recent:
        print(f"   - {inf['filename']}: {inf['top_prediction']} ({inf['confidence_score']:.2%})")
    print()

    # Get model statistics
    print("5. Model statistics:")
    stats = logger.get_all_model_statistics()
    for stat in stats:
        print(f"   Model: {stat['model_name']}")
        print(f"      Total inferences: {stat['total_inferences']}")
        print(f"      Average confidence: {stat['average_confidence']:.2%}")
    print()

    # Get summary
    print("6. Inference Summary:")
    summary = logger.get_inference_summary()
    for key, value in summary.items():
        print(f"   {key}: {value}")
    print()

    print("=" * 60)
    print("✅ Inference Logger Demo Complete!")
    print("=" * 60)

    # Clean up
    os.remove(DB_PATH)
