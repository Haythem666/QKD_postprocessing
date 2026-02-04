"""
Alice Server - gRPC Service for Cascade Error Correction
Alice répond aux demandes de parité de Bob via le réseau.
"""

import grpc
from concurrent import futures
import numpy as np
import pandas as pd
import sys

# Import des fichiers générés par protoc
# NOTE: Tu devras générer ces fichiers d'abord avec:
# python -m grpc_tools.protoc -I. --python_out=qkd --grpc_python_out=qkd qkd_grpc_cascade.proto
import sys
import os

# Add qkd directory to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'qkd'))

try:
    import qkd_grpc_cascade_pb2
    import qkd_grpc_cascade_pb2_grpc
except ImportError as e:
    print(f"ERROR: gRPC files not found! {e}")
    print("Run: python -m grpc_tools.protoc -I. --python_out=qkd --grpc_python_out=qkd qkd_grpc_cascade.proto")
    sys.exit(1)

from qkd.sifting import sifting
from qkd.parameter_estimation import parameter_estimation
from qkd.cascade_wrapper import Key
from qkd.cascade_open_source.shuffle import Shuffle


class AliceCascadeService(qkd_grpc_cascade_pb2_grpc.CascadeServiceServicer):
    """
    Service gRPC d'Alice.
    Alice possède la clé correcte et répond aux questions de Bob.
    """
    
    def __init__(self, alice_key):
        """
        Args:
            alice_key (Key): La clé d'Alice (objet Key wrapper)
        """
        self.alice_key = alice_key
        self.total_parities_sent = 0
        print(f"[Alice] Initialized with key of {alice_key.get_size()} bits")
    
    def StartReconciliation(self, request, context):
        """Bob démarre une nouvelle session Cascade"""
        print(f"\n[Alice] Starting reconciliation with algorithm: {request.algorithm_name}")
        self.total_parities_sent = 0
        return qkd_grpc_cascade_pb2.Empty()
    
    def AskParities(self, request, context):
        """
        Bob demande les parités de plusieurs blocs.
        Alice calcule et renvoie les parités correctes.
        """
        parities = []
        
        for block_info in request.blocks:
            # Reconstruire le Shuffle à partir de l'ID (convert string back to int)
            shuffle_id = int(block_info.shuffle_id)
            shuffle = Shuffle.create_shuffle_from_identifier(shuffle_id)
            
            # Calculer la parité sur la clé d'Alice
            parity = shuffle.calculate_parity(
                self.alice_key,
                block_info.start_index,
                block_info.end_index
            )
            
            parities.append(parity)
            self.total_parities_sent += 1
        
        print(f"[Alice] Sent {len(parities)} parities (total: {self.total_parities_sent})")
        
        return qkd_grpc_cascade_pb2.ParityResponse(parities=parities)
    
    def EndReconciliation(self, request, context):
        """Bob termine la session Cascade"""
        print(f"[Alice] Reconciliation ended. Total parities sent: {self.total_parities_sent}")
        return qkd_grpc_cascade_pb2.Empty()


def run_alice_server(port=50051, data_file="raw_data/parsed_qkd_data_partial_10000(in).csv"):
    """
    Lance le serveur Alice.
    
    Args:
        port (int): Port d'écoute
        data_file (str): Fichier de données QKD
    """
    
    print("="*70)
    print("  ALICE SERVER - QKD CASCADE gRPC")
    print("="*70)
    
    # 1. Charger les données et faire le sifting
    print(f"\n[Alice] Loading data from {data_file}")
    df = pd.read_csv(data_file)
    
    alice_bits, bob_bits = sifting(df)
    print(f"[Alice] Sifted {len(alice_bits)} bits")
    
    # 2. Parameter Estimation
    qber, qber_low, qber_high, alice_key_bits, bob_key_bits = parameter_estimation(
        alice_bits, bob_bits
    )
    print(f"[Alice] QBER: {qber*100:.2f}%")
    
    # 3. Convertir en objet Key
    alice_key = Key(alice_key_bits)
    
    # 4. Créer le serveur gRPC
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    qkd_grpc_cascade_pb2_grpc.add_CascadeServiceServicer_to_server(
        AliceCascadeService(alice_key), 
        server
    )
    
    server.add_insecure_port(f'[::]:{port}')
    
    # 5. Démarrer le serveur
    server.start()
    
    print(f"\n{'='*70}")
    print(f"[Alice] Server listening on port {port}")
    print(f"{'='*70}")
    print("\nWaiting for Bob to connect...")
    print("Press Ctrl+C to stop\n")
    
    try:
        server.wait_for_termination()
    except KeyboardInterrupt:
        print("\n[Alice] Server stopped by user")
        server.stop(0)


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Alice gRPC Server for QKD")
    parser.add_argument('--port', type=int, default=50051, help='Port to listen on')
    parser.add_argument('--data', type=str, 
                       default="raw_data/parsed_qkd_data_partial_10000(in).csv",
                       help='QKD data file')
    
    args = parser.parse_args()
    
    run_alice_server(port=args.port, data_file=args.data)