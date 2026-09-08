"""
TrustLens Blockchain Module
===========================
This module implements a simple blockchain for tracking data integrity
in computer vision pipelines.

Author: First-year CSE Student
Date: 2026-09-07
"""

import hashlib
import json
from datetime import datetime


class Block:
    """
    Represents a single block in the blockchain.

    Each block contains:
    - index: Position in the chain (0, 1, 2, ...)
    - timestamp: When the block was created
    - data: Information stored in this block (image hash, model info, etc.)
    - previous_hash: Hash of the previous block (links blocks together)
    - current_hash: This block's unique fingerprint
    """

    def __init__(self, index, timestamp, data, previous_hash):
        """
        Create a new block.

        Args:
            index (int): Position in the blockchain
            timestamp (str): When this block was created
            data (dict): The actual information we're storing
            previous_hash (str): Hash of the previous block
        """
        self.index = index
        self.timestamp = timestamp
        self.data = data
        self.previous_hash = previous_hash
        # Calculate this block's hash when it's created
        self.current_hash = self.calculate_hash()

    def calculate_hash(self):
        """
        Generate a unique SHA-256 hash for this block.

        This hash acts like a fingerprint. If ANY data in the block changes,
        the hash will be completely different, letting us detect tampering.

        Returns:
            str: 64-character hexadecimal hash
        """
        # Combine all block data into one string
        block_string = json.dumps({
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash
        }, sort_keys=True)  # sort_keys ensures consistent ordering

        # Create SHA-256 hash of the string
        return hashlib.sha256(block_string.encode()).hexdigest()

    def to_dict(self):
        """
        Convert block to a dictionary for easy JSON serialization.

        Returns:
            dict: Block data as a dictionary
        """
        return {
            "index": self.index,
            "timestamp": self.timestamp,
            "data": self.data,
            "previous_hash": self.previous_hash,
            "current_hash": self.current_hash
        }


class Blockchain:
    """
    Manages the entire chain of blocks.

    The blockchain is just a list of blocks, where each block points to
    the previous one through its previous_hash. This creates an unbreakable
    chain - if someone modifies an old block, all subsequent blocks become invalid.
    """

    def __init__(self):
        """
        Initialize the blockchain with a genesis block.

        The genesis block is the first block (index 0) and has no previous block,
        so its previous_hash is "0".
        """
        self.chain = []
        # Create the first block in the chain
        self.create_genesis_block()

    def create_genesis_block(self):
        """
        Create the very first block in the blockchain.

        This block is special because it doesn't point to any previous block.
        """
        genesis_block = Block(
            index=0,
            timestamp=datetime.now().isoformat(),
            data={"type": "genesis", "message": "TrustLens Blockchain Initialized"},
            previous_hash="0"
        )
        self.chain.append(genesis_block)

    def get_latest_block(self):
        """
        Get the most recent block in the chain.

        Returns:
            Block: The last block in the chain
        """
        return self.chain[-1]

    def add_block(self, data):
        """
        Add a new block to the blockchain.

        The new block is automatically linked to the previous block through
        the previous_hash field.

        Args:
            data (dict): The information to store in this block

        Returns:
            Block: The newly created block
        """
        # Get the previous block
        previous_block = self.get_latest_block()

        # Create new block
        new_block = Block(
            index=len(self.chain),
            timestamp=datetime.now().isoformat(),
            data=data,
            previous_hash=previous_block.current_hash
        )

        # Add to chain
        self.chain.append(new_block)
        return new_block

    def is_chain_valid(self):
        """
        Verify the entire blockchain is unbroken and unmodified.

        This checks two things for each block:
        1. Does the stored hash match a recalculated hash? (detects data tampering)
        2. Does the previous_hash match the actual previous block's hash? (detects chain breaks)

        Returns:
            tuple: (is_valid (bool), error_message (str or None))
        """
        # Start from block 1 (skip genesis block)
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            # Check 1: Has this block's data been tampered with?
            # Recalculate the hash and compare to stored hash
            if current_block.current_hash != current_block.calculate_hash():
                return False, f"Block {i} has been tampered with (hash mismatch)"

            # Check 2: Does this block properly link to the previous one?
            if current_block.previous_hash != previous_block.current_hash:
                return False, f"Block {i} chain is broken (previous_hash doesn't match)"

        # If we made it through all blocks without issues, chain is valid
        return True, None

    def get_chain_as_dict(self):
        """
        Convert the entire blockchain to a list of dictionaries.

        Useful for saving to a file or sending as JSON.

        Returns:
            list: List of block dictionaries
        """
        return [block.to_dict() for block in self.chain]

    def find_block_by_data(self, key, value):
        """
        Search for a block containing specific data.

        Args:
            key (str): The data field to search in (e.g., "filename")
            value: The value to search for

        Returns:
            Block or None: The matching block, or None if not found
        """
        for block in self.chain:
            if key in block.data and block.data[key] == value:
                return block
        return None


# ============================================================================
# DEMO / TESTING CODE
# ============================================================================

if __name__ == "__main__":
    """
    This code runs when you execute: python blockchain.py
    It demonstrates how the blockchain works and tests tampering detection.
    """

    print("=" * 60)
    print("TrustLens Blockchain Demo")
    print("=" * 60)
    print()

    # Create a new blockchain
    print("1. Creating blockchain...")
    bc = Blockchain()
    print(f"   ✓ Genesis block created (Index: {bc.chain[0].index})")
    print()

    # Add some sample blocks
    print("2. Adding sample blocks...")
    bc.add_block({
        "type": "image_upload",
        "filename": "cat.jpg",
        "hash": "a1b2c3d4e5f6...",
        "uploader": "Alice"
    })
    print("   ✓ Block 1 added: Image upload (cat.jpg)")

    bc.add_block({
        "type": "model_training",
        "model_name": "mobilenet_v2",
        "dataset_hash": "x9y8z7...",
        "accuracy": 0.94
    })
    print("   ✓ Block 2 added: Model training")

    bc.add_block({
        "type": "inference",
        "image_hash": "a1b2c3d4e5f6...",
        "model_hash": "x9y8z7...",
        "prediction": "cat",
        "confidence": 0.98
    })
    print("   ✓ Block 3 added: Inference result")
    print()

    # Display the chain
    print("3. Current blockchain:")
    for block in bc.chain:
        print(f"   Block {block.index}:")
        print(f"      Data: {block.data}")
        print(f"      Hash: {block.current_hash[:16]}...")
        print(f"      Previous: {block.previous_hash[:16]}...")
        print()

    # Verify chain integrity
    print("4. Verifying chain integrity...")
    is_valid, error = bc.is_chain_valid()
    if is_valid:
        print("   ✅ Blockchain is valid! All blocks are intact and properly linked.")
    else:
        print(f"   ❌ Blockchain is invalid: {error}")
    print()

    # Simulate tampering
    print("5. Simulating tampering (modifying block 1 data)...")
    # Change some data in block 1
    bc.chain[1].data["filename"] = "dog.jpg"
    print("   ⚠️  Changed 'cat.jpg' to 'dog.jpg' in block 1")
    print()

    # Verify chain after tampering
    print("6. Verifying chain after tampering...")
    is_valid, error = bc.is_chain_valid()
    if is_valid:
        print("   ✅ Blockchain is valid")
    else:
        print(f"   ❌ Tampering detected! {error}")
    print()

    print("=" * 60)
    print("Demo complete! The blockchain successfully detected tampering.")
    print("=" * 60)
