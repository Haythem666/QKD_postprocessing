"""
Alice Server - gRPC Service for Cascade Error Correction (CHUNKED VERSION)
Processes large CSV files in chunks to avoid memory issues.
"""

import grpc
from concurrent import futures
import numpy as np
import pandas as pd
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'qkd'))

try:
    import qkd_grpc_cascade_pb2
    import qkd_grpc_cascade_pb2_grpc
except ImportError as e:
    print(f"ERROR: gRPC files not found! {e}")
    print("Run: python -m grpc_tools.protoc -I. --python_out=qkd --grpc_python_out=qkd qkd_grpc_cascade.proto")
    sys.exit(1)

from qkd.parameter_estimation import parameter_estimation
from qkd.sifting import sifting
from qkd.cascade_wrapper import Key
from qkd.cascade_open_source.shuffle import Shuffle


def sifting_chunked(csv_file, chunk_size=1_000_000):
    """
    Sift data by reading CSV in chunks to avoid memory overflow.
    
    Args:
        csv_file: Path to CSV file
        chunk_size: Number of rows to process at once
        
    Returns:
        alice_bits, bob_bits as numpy arrays
    """
    print(f"[Alice] Reading CSV in chunks of {chunk_size:,} rows...")
    
    alice_list = []
    bob_list = []
    total_rows = 0
    sifted_count = 0
    
    for chunk_num, chunk in enumerate(pd.read_csv(csv_file, chunksize=chunk_size), start=1):
        total_rows += len(chunk)

        alice_bits, bob_bits = sifting(chunk)

        if len(alice_bits) > 0:
            alice_list.append(alice_bits)
            bob_list.append(bob_bits)
            sifted_count += len(alice_bits)
        
        if chunk_num % 10 == 0:
            print(f"  Processed {total_rows:,} rows, sifted {sifted_count:,} bits so far...")
    
    # Concatenate all chunks
    alice_bits = np.concatenate(alice_list)
    bob_bits = np.concatenate(bob_list)
    
    print(f"[Alice] Total: {total_rows:,} rows → {len(alice_bits):,} sifted bits")
    
    return alice_bits, bob_bits


class AliceCascadeService(qkd_grpc_cascade_pb2_grpc.CascadeServiceServicer):
    """Alice's gRPC service."""
    
    def __init__(self, alice_key):
        self.alice_key = alice_key
        self.total_parities_sent = 0
        print(f"[Alice] Initialized with key of {alice_key.get_size():,} bits")
    
    def StartReconciliation(self, request, context):
        print(f"\n[Alice] Starting reconciliation with algorithm: {request.algorithm_name}")
        self.total_parities_sent = 0
        return qkd_grpc_cascade_pb2.Empty()
    
    def AskParities(self, request, context):
        parities = []
        
        for block_info in request.blocks:
            shuffle_id = int(block_info.shuffle_id)
            shuffle = Shuffle.create_shuffle_from_identifier(shuffle_id)
            
            parity = shuffle.calculate_parity(
                self.alice_key,
                block_info.start_index,
                block_info.end_index
            )
            
            parities.append(parity)
            self.total_parities_sent += 1
        
        if self.total_parities_sent % 100 == 0:
            print(f"[Alice] Sent {self.total_parities_sent:,} parities so far...")
        
        return qkd_grpc_cascade_pb2.ParityResponse(parities=parities)
    
    def EndReconciliation(self, request, context):
        print(f"[Alice] Reconciliation ended. Total parities sent: {self.total_parities_sent:,}")
        return qkd_grpc_cascade_pb2.Empty()


def run_alice_server(port=50051, data_file="raw_data/parsed_qkd_data.csv", 
                     chunk_size=1_000_000):
    """
    Start Alice server with chunked processing.
    
    Args:
        port: Listening port
        data_file: QKD data file
        chunk_size: CSV chunk size for reading
    """
    
    print("="*70)
    print("  ALICE SERVER - QKD CASCADE gRPC (CHUNKED)")
    print("="*70)
    
    # 1. Load data with chunked sifting
    print(f"\n[Alice] Loading data from {data_file}")
    alice_bits, bob_bits = sifting_chunked(data_file, chunk_size=chunk_size)

    
    np.random.seed(42)
    
    # 2. Parameter Estimation
    print(f"\n[Alice] Running Parameter Estimation...")
    qber, qber_low, qber_high, alice_key_bits, bob_key_bits = parameter_estimation(
        alice_bits, bob_bits
    )
    print(f"[Alice] QBER: {qber*100:.2f}% (CI: [{qber_low*100:.2f}%, {qber_high*100:.2f}%])")
    print(f"[Alice] Key after PE: {len(alice_key_bits):,} bits")
    
    # 3. Convert to Key object
    alice_key = Key(alice_key_bits)
    
    # 4. Create gRPC server
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))
    
    qkd_grpc_cascade_pb2_grpc.add_CascadeServiceServicer_to_server(
        AliceCascadeService(alice_key), 
        server
    )
    
    server.add_insecure_port(f'[::]:{port}')
    
    # 5. Start server
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
    
    parser = argparse.ArgumentParser(description="Alice gRPC Server for QKD (Chunked)")
    parser.add_argument('--port', type=int, default=50051, help='Port to listen on')
    parser.add_argument('--data', type=str, 
                       default="raw_data/parsed_qkd_data_partial_10000(in).csv",
                       help='QKD data file')
    parser.add_argument('--chunk-size', type=int, default=1_000_000,
                       help='CSV chunk size')
    
    args = parser.parse_args()
    
    run_alice_server(
        port=args.port, 
        data_file=args.data,
        chunk_size=args.chunk_size
    )