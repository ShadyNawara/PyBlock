from collections import OrderedDict

import binascii
import random
import requests
from uuid import uuid4
from time import time
import json
import hashlib

from flask import Flask, request, jsonify, render_template

import Crypto
import Crypto.Random
from Crypto.Hash import SHA
from Crypto.PublicKey import RSA
from Crypto.Signature import PKCS1_v1_5

class Client:
    def __init__(self, nodes, private_key, public_key):
        self.nodes = list(nodes)
        self.private_key = private_key
        self.public_key = public_key

    """
    send transaction to a receipient
    """
    def send(self, payload):
        receipient = random.choice(self.nodes)
        self.value = payload
        r = requests.post('http://'+receipient+'/transactions/new', data={'sender': self.public_key,  'value': payload, 'signature': self.__sign_transaction()})
        return r.status_code
    
    def __to_dict(self):
        return OrderedDict({'sender': self.public_key,
                            'value': self.value})

    """
    Sign transaction with private key
    """
    def __sign_transaction(self):
        private_key = RSA.importKey(binascii.unhexlify(self.private_key))
        signer = PKCS1_v1_5.new(private_key)
        h = SHA.new(str(self.__to_dict()).encode('utf8'))
        return binascii.hexlify(signer.sign(h)).decode('ascii')

class __node():
    def __init__(self, nodes):
        self.nodes = nodes
        #Generate random number to be used as node_id
        self.node_id = str(uuid4()).replace('-', '')
        self.transactions = []
        self.chain = []
        #Create genesis block
        self.create_block(0, '00')     
    
    def registerNodes(self, nodes):
        self.nodes = nodes
    
    def create_block(self, nonce, previous_hash):
        """
        Add a block of transactions to the blockchain
        """
        block = {'block_number': len(self.chain) + 1,
                'timestamp': time(),
                'transactions': self.transactions,
                'nonce': nonce,
                'previous_hash': previous_hash}

        # Reset the current list of transactions
        self.transactions = []

        self.chain.append(block)
        return block

    def submit_transaction(self, sender, value, signature):
        self.updateChain()

        """
        Add a transaction to transactions array if the signature verified
        """
        transaction = OrderedDict({'sender': sender, 
                                    'value': value})

        transaction_verification = self.verify_transaction_signature(sender, signature, transaction)
        if transaction_verification:
            self.transactions.append(transaction)
            len(self.chain) + 1
        else:
            return False
        # We run the proof of work algorithm to get the next proof...
        last_block = self.chain[-1]
        nonce = self.proof_of_work()

        # Forge the new Block by adding it to the chain
        previous_hash = self.hash(last_block)
        self.create_block(nonce, previous_hash)

        # update other nodes
        for node in self.nodes:
            requests.get('http://' + node + '/update')
        return True

    def updateChain(self):
        """
        Resolve conflicts between blockchain's nodes
        by replacing our chain with the longest one in the network.
        """
        neighbours = self.nodes
        new_chain = None
        # We're only looking for chains longer than ours
        max_length = len(self.chain)

        # Grab and verify the chains from all the nodes in our network
        for node in neighbours:
            response = requests.get('http://' + node + '/chain')

            if response.status_code == 200:
                length = response.json()['length']
                chain = response.json()['chain']
                
                # Check if the length is longer and the chain is valid
                if length > max_length and self.valid_chain(chain):
                    max_length = length
                    new_chain = chain

        # Replace our chain if we discovered a new, valid chain longer than ours
        if new_chain:
            self.chain = new_chain
        return True

    def valid_chain(self, chain):
        """
        check if a bockchain is valid
        """
        last_block = chain[0]
        current_index = 1

        while current_index < len(chain):
            block = chain[current_index]
            #print(last_block)
            #print(block)
            #print("\n-----------\n")
            # Check that the hash of the block is correct
            if block['previous_hash'] != self.hash(last_block):
                return False

            # Check that the Proof of Work is correct
            transactions = block['transactions']
            # Need to make sure that the dictionary is ordered. Otherwise we'll get a different hash
            transaction_elements = ['sender', 'value']
            transactions = [OrderedDict((k, transaction[k]) for k in transaction_elements) for transaction in transactions]

            if not self.valid_proof(transactions, block['previous_hash'], block['nonce']):
                return False

            last_block = block
            current_index += 1

        return True

    def valid_proof(self, transactions, last_hash, nonce):
        """
        Check if a hash value satisfies the mining conditions. This function is used within the proof_of_work function.
        """
        guess = (str(transactions)+str(last_hash)+str(nonce)).encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:2] == '0'*2


    def proof_of_work(self):
        """
        Proof of work algorithm
        """
        last_block = self.chain[-1]
        last_hash = self.hash(last_block)

        nonce = 0
        while self.valid_proof(self.transactions, last_hash, nonce) is False:
            nonce += 1

        return nonce

    def hash(self, block):
        """
        Create a SHA-256 hash of a block
        """
        # We must make sure that the Dictionary is Ordered, or we'll have inconsistent hashes
        block_string = json.dumps(block, sort_keys=True).encode()
        
        return hashlib.sha256(block_string).hexdigest()

    def verify_transaction_signature(self, sender, signature, transaction):
        """
        Check that the provided signature corresponds to transaction
        signed by the public key (sender)
        """
        public_key = RSA.importKey(binascii.unhexlify(sender))
        verifier = PKCS1_v1_5.new(public_key)
        h = SHA.new(str(transaction).encode('utf8'))
        result = verifier.verify(h, binascii.unhexlify(signature))
        return result

app = Flask(__name__)
node = __node([])
def Initialize(nodes, port, ip = "0.0.0.0"):
    node.registerNodes(nodes)
    app.run(host=ip, port=port)
    return node

@app.route('/transactions/new', methods=['POST'])
def new_transaction():
    values = request.form
    # Create a new Transaction
    result = node.submit_transaction(values['sender'], values['value'], values['signature'])
    print(node.nodes)
    return jsonify(result), 200

@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': node.chain,
        'length': len(node.chain),
    }
    print (jsonify(response))
    return jsonify(response), 200

@app.route('/transactions/get', methods=['GET'])
def get_transactions():
    #Get transactions from transactions pool
    transactions = node.transactions

    response = {'transactions': transactions}
    return jsonify(response), 200

@app.route('/update', methods=['GET'])
def updateChain():
    response = node.updateChain()
    return jsonify(response), 200