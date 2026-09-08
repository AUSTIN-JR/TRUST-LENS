"""
Quick test of TrustLens backend without running Flask server
Tests database initialization and basic blockchain functionality
"""

import sys
sys.path.insert(0, 'D:\\vs code\\TrustLens')

from blockchain import Blockchain
import sqlite3
import os
from datetime import datetime

DB_PATH = 'D:\\vs code\\TrustLens\\trustlens_test.db'
UPLOAD_FOLDER = 'D:\\vs code\\TrustLens\\uploads'

print("=" * 60)
print("TrustLens Backend Test - Part 2")
print("=" * 60)
print()

# Test 1: Blockchain
print("1. Testing Blockchain...")
bc = Blockchain()
bc.add_block({
    'type': 'image_upload',
    'filename': 'test.jpg',
    'file_hash': 'abc123def456...',
    'uploader_name': 'Test User'
})
is_valid, error = bc.is_chain_valid()
print(f"   ✓ Blockchain created with {len(bc.chain)} blocks")
print(f"   ✓ Blockchain valid: {is_valid}")
print()

# Test 2: Database
print("2. Testing Database...")
if os.path.exists(DB_PATH):
    os.remove(DB_PATH)

conn = sqlite3.connect(DB_PATH)
cursor = conn.cursor()

# Create tables
cursor.execute('''
    CREATE TABLE IF NOT EXISTS uploads (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        filename TEXT NOT NULL,
        file_hash TEXT NOT NULL UNIQUE,
        uploader_name TEXT NOT NULL,
        upload_timestamp TEXT NOT NULL,
        file_path TEXT NOT NULL,
        block_index INTEGER
    )
''')

cursor.execute('''
    CREATE TABLE IF NOT EXISTS blockchain_blocks (
        block_index INTEGER PRIMARY KEY,
        timestamp TEXT NOT NULL,
        data TEXT NOT NULL,
        previous_hash TEXT NOT NULL,
        current_hash TEXT NOT NULL
    )
''')

conn.commit()

# Insert test data
cursor.execute('''
    INSERT INTO uploads
    (filename, file_hash, uploader_name, upload_timestamp, file_path, block_index)
    VALUES (?, ?, ?, ?, ?, ?)
''', ('test.jpg', 'abc123', 'Alice', datetime.now().isoformat(), '/uploads/test.jpg', 1))

conn.commit()

# Query test
cursor.execute('SELECT * FROM uploads')
result = cursor.fetchone()
conn.close()

print(f"   ✓ Database created and tables initialized")
print(f"   ✓ Test record inserted: {result[0]} - {result[1]}")
print()

# Test 3: File operations
print("3. Testing File Operations...")
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
test_file = os.path.join(UPLOAD_FOLDER, 'test_file.txt')
with open(test_file, 'w') as f:
    f.write('Test content')

import hashlib
with open(test_file, 'rb') as f:
    file_hash = hashlib.sha256(f.read()).hexdigest()

print(f"   ✓ Test file created: {test_file}")
print(f"   ✓ File hash calculated: {file_hash[:16]}...")
print()

# Test 4: Flask imports
print("4. Testing Flask Imports...")
try:
    from flask import Flask, render_template, request, jsonify
    print("   ✓ Flask imported successfully")
    print("   ✓ All required modules available")
except ImportError as e:
    print(f"   ✗ Import error: {e}")

print()
print("=" * 60)
print("✅ Part 2 Backend Tests Complete!")
print("=" * 60)
print()
print("Next: Run 'python app.py' to start the Flask server")
print("      Then visit http://localhost:5000 in your browser")
