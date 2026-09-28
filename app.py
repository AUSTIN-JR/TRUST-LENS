"""
TrustLens Flask Backend
=======================
Web application for tamper detection in computer vision pipelines.

This Flask app handles:
- Image uploads (with SHA-256 hashing)
- Blockchain management (stores all uploads)
- Verification of image integrity
- Dashboard and reporting

Author: First-year CSE Student
Date: 2026-09-07
"""

from flask import Flask, render_template, request, jsonify, send_file
import hashlib
import os
import sqlite3
from datetime import datetime
from pathlib import Path
import json
from blockchain import Blockchain
from model import CVModel
from inference_logger import InferenceLogger
import threading
import time

# ============================================================================
# FLASK APP SETUP
# ============================================================================

app = Flask(__name__)

# Configuration
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
DB_PATH = os.path.join(os.path.dirname(__file__), 'trustlens.db')
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'bmp'}

# Create uploads folder if it doesn't exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Database lock for thread-safe access
db_lock = threading.Lock()

# Initialize blockchain (global - will persist during app session)
blockchain = Blockchain()

# Initialize CV model (global)
cv_model = None
model_hash_stored = False

# Initialize inference logger
inference_logger = InferenceLogger(DB_PATH)

# ============================================================================
# DATABASE FUNCTIONS
# ============================================================================

def init_db():
    """
    Initialize SQLite database with required tables.
    Uses WAL mode for better concurrent access handling.
    """
    with db_lock:
        conn = sqlite3.connect(DB_PATH, timeout=30.0)
        conn.execute('PRAGMA journal_mode=WAL')
        conn.execute('PRAGMA busy_timeout=30000')
        cursor = conn.cursor()

        # Table for storing upload records
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS uploads (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                file_hash TEXT NOT NULL UNIQUE,
                uploader_name TEXT NOT NULL,
                upload_timestamp TEXT NOT NULL,
                file_path TEXT NOT NULL,
                block_index INTEGER,
                FOREIGN KEY(block_index) REFERENCES blockchain_blocks(block_index)
            )
        ''')

        # Table for storing blockchain blocks
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS blockchain_blocks (
                block_index INTEGER PRIMARY KEY,
                timestamp TEXT NOT NULL,
                data TEXT NOT NULL,
                previous_hash TEXT NOT NULL,
                current_hash TEXT NOT NULL
            )
        ''')

        # Table for tracking tampering alerts
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS tamper_alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                filename TEXT NOT NULL,
                original_hash TEXT NOT NULL,
                current_hash TEXT NOT NULL,
                detected_timestamp TEXT NOT NULL,
                status TEXT
            )
        ''')

        conn.commit()
        conn.close()


def save_block_to_db(block):
    """
    Save a blockchain block to the database with timeout handling.
    Uses WAL mode and increased timeout for concurrent access.
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with db_lock:
                conn = sqlite3.connect(DB_PATH, timeout=30.0)
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('PRAGMA busy_timeout=30000')
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO blockchain_blocks
                    (block_index, timestamp, data, previous_hash, current_hash)
                    VALUES (?, ?, ?, ?, ?)
                ''', (
                    block.index,
                    block.timestamp,
                    json.dumps(block.data),
                    block.previous_hash,
                    block.current_hash
                ))

                conn.commit()
                conn.close()
                return True
        except sqlite3.OperationalError as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
            else:
                raise
    return False


def save_upload_record(filename, file_hash, uploader_name, file_path, block_index):
    """
    Save an upload record to the database with timeout handling.
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with db_lock:
                conn = sqlite3.connect(DB_PATH, timeout=30.0)
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('PRAGMA busy_timeout=30000')
                cursor = conn.cursor()

                cursor.execute('''
                    INSERT INTO uploads
                    (filename, file_hash, uploader_name, upload_timestamp, file_path, block_index)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (
                    filename,
                    file_hash,
                    uploader_name,
                    datetime.now().isoformat(),
                    file_path,
                    block_index
                ))

                conn.commit()
                conn.close()
                return True
        except sqlite3.OperationalError as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
            else:
                raise
    return False


def get_all_uploads():
    """
    Retrieve all uploaded images from the database.
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with db_lock:
                conn = sqlite3.connect(DB_PATH, timeout=30.0)
                conn.row_factory = sqlite3.Row
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('PRAGMA busy_timeout=30000')
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM uploads ORDER BY id DESC')
                uploads = [dict(row) for row in cursor.fetchall()]

                conn.close()
                return uploads
        except sqlite3.OperationalError as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
            else:
                return []
    return []


def get_upload_by_hash(file_hash):
    """
    Find an upload record by its SHA-256 hash.
    """
    max_retries = 3
    for attempt in range(max_retries):
        try:
            with db_lock:
                conn = sqlite3.connect(DB_PATH, timeout=30.0)
                conn.row_factory = sqlite3.Row
                conn.execute('PRAGMA journal_mode=WAL')
                conn.execute('PRAGMA busy_timeout=30000')
                cursor = conn.cursor()

                cursor.execute('SELECT * FROM uploads WHERE file_hash = ?', (file_hash,))
                result = cursor.fetchone()
                conn.close()

                return dict(result) if result else None
        except sqlite3.OperationalError as e:
            if attempt < max_retries - 1:
                time.sleep(0.5)
            else:
                return None
    return None


# ============================================================================
# FILE HASHING FUNCTIONS
# ============================================================================

def calculate_file_hash(filepath):
    """
    Calculate SHA-256 hash of a file.

    This hash serves as the file's unique fingerprint. If the file is modified
    even slightly, this hash will be completely different.

    Args:
        filepath (str): Path to the file

    Returns:
        str: 64-character hexadecimal SHA-256 hash
    """
    sha256_hash = hashlib.sha256()

    # Read file in chunks (memory efficient for large files)
    with open(filepath, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)

    return sha256_hash.hexdigest()


def allowed_file(filename):
    """
    Check if uploaded file has an allowed extension.

    Args:
        filename (str): Name of the file

    Returns:
        bool: True if extension is allowed
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================================
# ROUTES - IMAGE UPLOAD
# ============================================================================

@app.route('/')
def index():
    """
    Render the main upload page.
    """
    return render_template('index.html')


@app.route('/upload', methods=['POST'])
def upload_image():
    """
    Handle image upload and add to blockchain.

    Steps:
    1. Validate file upload
    2. Save file to uploads folder
    3. Calculate SHA-256 hash
    4. Add block to blockchain
    5. Store record in database

    Returns:
        JSON response with upload status
    """
    try:
        # Check if file was provided
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['file']
        uploader_name = request.form.get('uploader_name', 'Anonymous')

        # Check if file has a name
        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        # Check file extension
        if not allowed_file(file.filename):
            return jsonify({
                'success': False,
                'error': f'File type not allowed. Allowed: {", ".join(ALLOWED_EXTENSIONS)}'
            }), 400

        # Save file with unique name to avoid conflicts
        import uuid
        unique_filename = f"{uuid.uuid4()}_{file.filename}"
        file_path = os.path.join(UPLOAD_FOLDER, unique_filename)

        # Ensure directory exists
        os.makedirs(UPLOAD_FOLDER, exist_ok=True)
        file.save(file_path)

        # Calculate file hash
        file_hash = calculate_file_hash(file_path)

        # Check if this file already exists in blockchain
        existing = get_upload_by_hash(file_hash)
        if existing:
            # Clean up the file we just saved
            try:
                os.remove(file_path)
            except:
                pass
            return jsonify({
                'success': False,
                'error': 'This file has already been uploaded',
                'previous_upload': existing['upload_timestamp']
            }), 400

        # Create blockchain block
        block_data = {
            'type': 'image_upload',
            'filename': file.filename,
            'file_hash': file_hash,
            'uploader_name': uploader_name,
            'upload_timestamp': datetime.now().isoformat()
        }

        new_block = blockchain.add_block(block_data)

        # Save block to database
        save_block_to_db(new_block)

        # Save upload record
        save_upload_record(file.filename, file_hash, uploader_name, file_path, new_block.index)

        return jsonify({
            'success': True,
            'message': f'File uploaded successfully',
            'filename': file.filename,
            'file_hash': file_hash,
            'block_index': new_block.index,
            'block_hash': new_block.current_hash
        }), 200

    except Exception as e:
        import traceback
        print(f"Upload error: {str(e)}")
        print(traceback.format_exc())
        return jsonify({'success': False, 'error': f'Upload failed: {str(e)}'}), 500


# ============================================================================
# ROUTES - IMAGE LISTING
# ============================================================================

@app.route('/api/uploads')
def get_uploads():
    """
    Get list of all uploaded images as JSON.

    Returns:
        JSON with list of uploads and blockchain status
    """
    try:
        uploads = get_all_uploads()

        # Add blockchain verification status
        is_valid, error = blockchain.is_chain_valid()

        return jsonify({
            'success': True,
            'uploads': uploads,
            'blockchain_valid': is_valid,
            'blockchain_error': error,
            'total_blocks': len(blockchain.chain),
            'total_uploads': len(uploads)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/gallery')
def gallery():
    """
    Render the gallery page showing all uploaded images.
    """
    return render_template('index.html')


# ============================================================================
# ROUTES - BLOCKCHAIN INFO
# ============================================================================

@app.route('/api/blockchain')
def get_blockchain_info():
    """
    Get full blockchain state as JSON.

    Returns:
        JSON with complete blockchain data
    """
    try:
        is_valid, error = blockchain.is_chain_valid()

        return jsonify({
            'success': True,
            'chain': blockchain.get_chain_as_dict(),
            'total_blocks': len(blockchain.chain),
            'is_valid': is_valid,
            'error': error
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/dashboard')
def dashboard():
    """
    Render the dashboard page.
    """
    return render_template('dashboard.html')


# ============================================================================
# ROUTES - VERIFICATION
# ============================================================================

@app.route('/verify')
def verify_page():
    """
    Render the verification page.
    """
    return render_template('verify.html')


@app.route('/verify-upload', methods=['POST'])
def verify_upload():
    """
    Verify integrity of an uploaded file.

    Steps:
    1. Receive file
    2. Calculate its hash
    3. Compare to blockchain record
    4. Report if file is unaltered or tampered

    Returns:
        JSON with verification result
    """
    try:
        if 'file' not in request.files:
            return jsonify({'success': False, 'error': 'No file provided'}), 400

        file = request.files['file']

        if file.filename == '':
            return jsonify({'success': False, 'error': 'No file selected'}), 400

        # Save to temporary location
        temp_path = os.path.join(UPLOAD_FOLDER, f'temp_{file.filename}')
        file.save(temp_path)

        # Calculate hash
        current_hash = calculate_file_hash(temp_path)

        # Clean up temp file
        os.remove(temp_path)

        # Look up in database
        upload_record = get_upload_by_hash(current_hash)

        if upload_record:
            return jsonify({
                'success': True,
                'verified': True,
                'message': '✅ Verified - Unaltered',
                'filename': upload_record['filename'],
                'original_hash': upload_record['file_hash'],
                'current_hash': current_hash,
                'uploader': upload_record['uploader_name'],
                'upload_time': upload_record['upload_timestamp'],
                'block_index': upload_record['block_index']
            }), 200
        else:
            return jsonify({
                'success': True,
                'verified': False,
                'message': '⚠️ Tampering Detected',
                'current_hash': current_hash,
                'error': 'This file hash does not match any record in the blockchain'
            }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROUTES - DEMO / TESTING
# ============================================================================

@app.route('/api/tamper-demo/<filename>', methods=['POST'])
def tamper_demo(filename):
    """
    Simulate tampering for demonstration purposes.

    This modifies a stored file slightly so it becomes detectable as tampered.
    DEMO ONLY - not for production use!

    Args:
        filename (str): Name of file to tamper with

    Returns:
        JSON response
    """
    try:
        file_path = os.path.join(UPLOAD_FOLDER, filename)

        if not os.path.exists(file_path):
            return jsonify({'success': False, 'error': 'File not found'}), 404

        # Read file
        with open(file_path, 'rb') as f:
            content = f.read()

        # Modify slightly (change last byte)
        modified = content[:-1] + bytes([(content[-1] + 1) % 256])

        # Write back
        with open(file_path, 'wb') as f:
            f.write(modified)

        # Calculate new hash
        new_hash = calculate_file_hash(file_path)

        return jsonify({
            'success': True,
            'message': 'File tampered for demo purposes',
            'new_hash': new_hash
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROUTES - MODEL INFERENCE
# ============================================================================

@app.route('/api/model-info')
def get_model_info():
    """
    Get information about the loaded CV model.

    Returns:
        JSON with model metadata
    """
    try:
        global cv_model

        if cv_model is None:
            cv_model = CVModel()

        info = cv_model.get_model_info()

        return jsonify({
            'success': True,
            'model_info': info
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/predict/<int:upload_id>', methods=['POST'])
def predict_image(upload_id):
    """
    Run inference on an uploaded image and add result to blockchain.

    Steps:
    1. Get image from uploads by ID
    2. Run model prediction
    3. Log inference with integrity tracking
    4. Add inference block to blockchain
    5. Store in inference logger

    Args:
        upload_id (int): ID of the uploaded image

    Returns:
        JSON with prediction results
    """
    try:
        global cv_model, model_hash_stored

        # Get upload record
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('SELECT * FROM uploads WHERE id = ?', (upload_id,))
        upload = cursor.fetchone()
        conn.close()

        if not upload:
            return jsonify({'success': False, 'error': 'Upload not found'}), 404

        # Initialize model if needed
        if cv_model is None:
            cv_model = CVModel()

        # Store model hash in blockchain once
        if not model_hash_stored and cv_model.model_hash:
            model_block = blockchain.add_block({
                'type': 'model_info',
                'model_name': 'MobileNetV2',
                'model_hash': cv_model.model_hash,
                'framework': 'TensorFlow/Keras',
                'dataset': 'ImageNet',
                'dataset_hash': hashlib.sha256(b"ImageNet").hexdigest()
            })
            save_block_to_db(model_block)
            model_hash_stored = True

        # Run prediction
        file_path = upload['file_path']
        prediction_result = cv_model.predict(file_path, top_k=3)

        if not prediction_result.get('success', False):
            return jsonify({
                'success': False,
                'error': prediction_result.get('error', 'Prediction failed')
            }), 500

        # Get prediction data
        top_prediction = prediction_result['predictions'][0]['class_name']
        confidence = prediction_result['predictions'][0]['confidence']

        # Add inference block to blockchain
        inference_block = blockchain.add_block({
            'type': 'inference',
            'image_filename': upload['filename'],
            'image_hash': upload['file_hash'],
            'model_hash': cv_model.model_hash,
            'top_prediction': top_prediction,
            'confidence': confidence,
            'timestamp': datetime.now().isoformat()
        })

        save_block_to_db(inference_block)

        # Log inference with integrity tracking
        log_result = inference_logger.log_inference(
            upload_id=upload_id,
            image_hash=upload['file_hash'],
            filename=upload['filename'],
            model_hash=cv_model.model_hash,
            model_name='MobileNetV2',
            top_prediction=top_prediction,
            confidence=confidence,
            all_predictions=prediction_result['predictions'],
            block_index=inference_block.index
        )

        if not log_result['success']:
            return jsonify({
                'success': False,
                'error': f'Logging failed: {log_result.get("error")}'
            }), 500

        return jsonify({
            'success': True,
            'upload_id': upload_id,
            'filename': upload['filename'],
            'predictions': prediction_result['predictions'],
            'top_prediction': top_prediction,
            'confidence': confidence,
            'inference_id': log_result['inference_id'],
            'inference_hash': log_result['inference_hash'],
            'block_index': inference_block.index,
            'block_hash': inference_block.current_hash,
            'message': f'Prediction: {top_prediction}'
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500



@app.route('/api/predictions')
def get_predictions():
    """
    Get all predictions made by the model.

    Returns:
        JSON with list of predictions
    """
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()

        cursor.execute('''
            SELECT predictions.*, uploads.filename, uploads.file_hash
            FROM predictions
            LEFT JOIN uploads ON predictions.upload_id = uploads.id
            ORDER BY predictions.id DESC
        ''')

        predictions = [dict(row) for row in cursor.fetchall()]
        conn.close()

        return jsonify({
            'success': True,
            'predictions': predictions,
            'total_predictions': len(predictions)
        }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ROUTES - INFERENCE LOGGING & VERIFICATION
# ============================================================================

@app.route('/api/inference-logs')
def get_inference_logs():
    """
    Get recent inference logs.

    Returns:
        JSON with inference history
    """
    try:
        limit = request.args.get('limit', 20, type=int)
        recent = inference_logger.get_recent_inferences(limit=limit)

        return jsonify({
            'success': True,
            'inferences': recent,
            'total': len(recent)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/inference-logs/<int:inference_id>')
def get_inference_log(inference_id):
    """
    Get a specific inference log entry.

    Args:
        inference_id (int): ID of the inference

    Returns:
        JSON with inference details
    """
    try:
        inference = inference_logger.get_inference_by_id(inference_id)

        if not inference:
            return jsonify({'success': False, 'error': 'Inference not found'}), 404

        return jsonify({
            'success': True,
            'inference': inference
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/verify-inference/<int:inference_id>')
def verify_inference(inference_id):
    """
    Verify integrity of an inference log entry.

    Recalculates the inference hash and compares to stored value.
    Detects if any inference data was modified.

    Args:
        inference_id (int): ID of the inference to verify

    Returns:
        JSON with verification result
    """
    try:
        verification = inference_logger.verify_inference_integrity(inference_id)

        if verification['valid']:
            return jsonify({
                'success': True,
                'verified': True,
                'message': '✅ Inference Verified - Unaltered',
                'inference_id': inference_id,
                'stored_hash': verification['stored_hash'],
                'calculated_hash': verification['calculated_hash']
            }), 200
        else:
            return jsonify({
                'success': True,
                'verified': False,
                'message': '⚠️ Inference Tampering Detected',
                'inference_id': inference_id,
                'stored_hash': verification['stored_hash'],
                'calculated_hash': verification['calculated_hash'],
                'error': 'Inference hash mismatch - data may have been modified'
            }), 200

    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/model-statistics')
def get_model_stats():
    """
    Get statistics for all models used.

    Returns:
        JSON with model usage statistics
    """
    try:
        stats = inference_logger.get_all_model_statistics()
        summary = inference_logger.get_inference_summary()

        return jsonify({
            'success': True,
            'models': stats,
            'summary': summary
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/inferences-by-image/<image_hash>')
def get_inferences_by_image(image_hash):
    """
    Get all inferences for a specific image.

    Args:
        image_hash (str): SHA-256 hash of the image

    Returns:
        JSON with all predictions for that image
    """
    try:
        inferences = inference_logger.get_inferences_by_image(image_hash)

        return jsonify({
            'success': True,
            'image_hash': image_hash,
            'inferences': inferences,
            'total': len(inferences)
        }), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


# ============================================================================
# ERROR HANDLERS
# ============================================================================


@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors."""
    return jsonify({'success': False, 'error': 'Page not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors."""
    return jsonify({'success': False, 'error': 'Internal server error'}), 500


# ============================================================================
# APP STARTUP
# ============================================================================

if __name__ == '__main__':
    # Initialize database
    init_db()

    print("=" * 60)
    print("TrustLens Starting Up")
    print("=" * 60)
    print(f"Upload folder: {UPLOAD_FOLDER}")
    print(f"Database: {DB_PATH}")
    print(f"Blockchain blocks: {len(blockchain.chain)}")
    print()
    print("TrustLens is accessible at:")
    print("  - Local: http://localhost:5000")
    print("  - Network: http://<your-ip>:5000")
    print("=" * 60)

    # Start Flask app in debug mode - accessible on network
    app.run(debug=True, host='0.0.0.0', port=5000)
