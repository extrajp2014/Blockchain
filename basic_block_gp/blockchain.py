import hashlib
import json
from time import time
from uuid import uuid4

from flask import Flask, jsonify, request

class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # Create the genesis block
        self.new_block(previous_hash=1, proof=100)

    def new_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain
        A block should have:
        * Index
        * Timestamp
        * List of current transactions
        * The proof used to mine this block
        * The hash of the previous block
        :param proof: <int> The proof given by the Proof of Work algorithm
        :param previous_hash: (Optional) <str> Hash of previous Block
        :return: <dict> New Block
        """

        block = {
            'index': len(self.chain) + 1,
            'proof': proof,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'previous_hash': previous_hash,
        }

        # Reset the current list of transactions
        self.current_transactions = []
        # Append the chain to the block
        self.chain.append(block)
        # Return the new block
        return block

    def hash(self, block):
        """
        Creates a SHA-256 hash of a Block
        :param block": <dict> Block
        "return": <str>
        """

        # Use json.dumps to convert json into a string
        # Use hashlib.sha256 to create a hash
        # It requires a `bytes-like` object, which is what
        # .encode() does.
        # It converts the Python string into a byte string.
        # We must make sure that the Dictionary is Ordered,
        # or we'll have inconsistent hashes

        # Create the block_string
        block_str = json.dumps(block, sort_keys=True)
        str_bytes = block_str.encode()

        # Hash this string using sha256
        hash_obj = hashlib.sha256(str_bytes)
        hash_str = hash_obj.hexdigest()
        # By itself, the sha256 function returns the hash in a raw string
        # that will likely include escaped characters.
        # This can be hard to read, but .hexdigest() converts the
        # hash to a string of hexadecimal characters, which is
        # easier to work with and understand

        # Return the hashed block string in hexadecimal format
        return hash_str

    @property
    def last_block(self):
        return self.chain[-1]

    @staticmethod
    def valid_proof(block_string, proof):
        """
        Validates the Proof:  Does hash(block_string, proof) contain 3
        leading zeroes?  Return true if the proof is valid
        :param block_string: <string> The stringified block to use to
        check in combination with `proof`
        :param proof: <int?> The value that when combined with the
        stringified previous block results in a hash that has the
        correct number of leading zeroes.
        :return: True if the resulting hash is a valid proof, False otherwise
        """
        guess = f'{block_string}{proof}'.encode()

        # return True or False
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:6] == '000000'

    def new_transaction(self, sender, recipient, amount):
        transaction = {"sender": sender, "recipient": recipient, "amount": amount}
        self.current_transactions.append(transaction)
        return self.last_block["index"] + 1

# Instantiate our Node
app = Flask(__name__)

# Generate a globally unique address for this node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate the Blockchain
blockchain = Blockchain()


@app.route('/mine', methods=['POST'])
def mine():
    data = request.get_json()

    req_params = ['proof', 'id']
    if not all(k in data for k in req_params):
        response = {
            'message': 'Missing required fields.'
        }
        return jsonify(response), 400

    proof_sent = data['proof']

    blk_str = json.dumps(blockchain.last_block, sort_keys=True)

    is_proof_valid = blockchain.valid_proof(blk_str, proof_sent)
    recipient_id = data["id"]

    if is_proof_valid:
        previous_hash = blockchain.hash(blockchain.last_block)
        new_blk = blockchain.new_block(proof_sent, previous_hash)
        blockchain.new_transaction(sender="0", recipient=recipient_id, amount=1)
        
        response = {
            "message": "Congratulation! New block is found",
            "index": new_blk["index"],
            "transactions": new_blk["transactions"],
            "proof": new_blk["proof"],
            "previous_hash": new_blk["previous_hash"]
        }
        return jsonify(response), 200
    else:
        return jsonify({'message': 'Invalid Proof. Unsuccessful Try again.'}), 200

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        # Return the chain and its current length
        'chain': blockchain.chain,
        'chain_length': len(blockchain.chain)
    }
    return jsonify(response), 200


@app.route('/last_block', methods=['GET'])
def last_block_in_chain():
    # last block in chain
    last_block = blockchain.chain[-1]
    response = {
        'last_block': last_block
    }
    return jsonify(response), 200


# Run the program on port 5000
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)