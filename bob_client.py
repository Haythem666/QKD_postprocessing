"""
Bob Client - gRPC Client for Cascade Error Correction
Bob utilise Cascade pour corriger sa clé en demandant des parités à Alice via gRPC.
"""

import numpy as np
import pandas as pd
import sys
import argparse

from qkd.sifting import sifting
from qkd.parameter_estimation import parameter_estimation
from qkd.privacy_amplification import toeplitz_hash, binary_entropy
from qkd.cascade_wrapper import Key
from qkd.cascade_open_source import Reconciliation
from qkd.grpc_classical_channel import gRPCClassicalChannel


QBER_THRESHOLD = 0.11


def run_bob_client(server_address='localhost:50051', 
                   data_file="raw_data/parsed_qkd_data_partial_10000(in).csv",
                   algorithm='yanetal'):
    """
    Lance le client Bob pour la correction d'erreurs avec gRPC.
    
    Args:
        server_address (str): Adresse du serveur Alice
        data_file (str): Fichier de données QKD
        algorithm (str): Algorithme Cascade à utiliser
    """
    
    print("="*70)
    print("  BOB CLIENT - QKD CASCADE gRPC")
    print("="*70)
    
    # 1. Charger les données et faire le sifting
    print(f"\n[Bob] Loading data from {data_file}")
    df = pd.read_csv(data_file)
    
    alice_bits, bob_bits = sifting(df)
    print(f"[Bob] Sifted {len(bob_bits)} bits")
    
    # 2. Parameter Estimation
    qber, qber_low, qber_high, alice_key_bits, bob_key_bits = parameter_estimation(
        alice_bits, bob_bits
    )
    
    print(f"[Bob] QBER: {qber*100:.2f}% (CI: [{qber_low*100:.2f}%, {qber_high*100:.2f}%])")
    
    if qber_high > QBER_THRESHOLD:
        print(f"[Bob] ABORT: QBER too high ({qber_high*100:.2f}% > {QBER_THRESHOLD*100}%)")
        return
    
    # 3. Convertir en objet Key
    bob_key = Key(bob_key_bits)
    
    # 4. Créer le canal gRPC vers Alice
    print(f"\n[Bob] Connecting to Alice at {server_address}...")
    try:
        channel = gRPCClassicalChannel(server_address)
    except Exception as e:
        print(f"[Bob] ERROR: Cannot connect to Alice - {e}")
        print("[Bob] Make sure Alice server is running!")
        return
    
    # 5. Lancer Cascade avec le canal gRPC
    print(f"\n[Bob] Starting Cascade error correction ({algorithm})...")
    print(f"[Bob] Initial errors: {np.sum(alice_key_bits != bob_key_bits)}")
    
    reconciliation = Reconciliation(
        algorithm_name=algorithm,
        classical_channel=channel,  # ← gRPC channel!
        noisy_key=bob_key,
        estimated_bit_error_rate=qber
    )
    
    # Lancer la reconciliation
    reconciled_key = reconciliation.reconcile()
    
    # 6. Résultats
    stats = reconciliation.stats
    leaked_bits = channel.bits_leaked
    corrected_bob = reconciled_key.bits
    final_errors = np.sum(alice_key_bits != corrected_bob)
    
    print(f"\n{'='*70}")
    print(f"  CASCADE RESULTS")
    print(f"{'='*70}")
    print(f"Normal iterations:     {stats.normal_iterations}")
    print(f"Leaked bits:           {leaked_bits}")
    print(f"Final errors:          {final_errors}")
    print(f"Realistic efficiency:  {stats.realistic_efficiency:.3f}")
    print(f"Time:                  {stats.elapsed_real_time:.3f}s")
    
    if final_errors > 0:
        print(f"\n[Bob] WARNING: {final_errors} errors remain after Cascade")
        print("[Bob] Cannot proceed to Privacy Amplification")
        channel.close()
        return
    
    # 7. Privacy Amplification
    print(f"\n[Bob] Starting Privacy Amplification...")
    
    h_qber = binary_entropy(qber_high)
    n = len(bob_key_bits)
    safety_margin = 50
    
    final_key_length = int(n - leaked_bits - n * h_qber - safety_margin)
    final_key_length = max(0, final_key_length)
    
    print(f"[Bob] Final key length: {final_key_length:,} bits")
    
    if final_key_length == 0:
        print("[Bob] ABORT: No secure key can be extracted")
        channel.close()
        return
    
    # Bob fait le hashing (Alice doit faire la même chose de son côté)
    bob_secure_key, toeplitz_seed = toeplitz_hash(corrected_bob, final_key_length)
    
    print(f"[Bob] Generated final secure key of {len(bob_secure_key):,} bits")
    
    # 8. Fermer la connexion
    channel.close()
    
    print(f"\n{'='*70}")
    print(f"  SUCCESS! QKD PROTOCOL COMPLETED")
    print(f"{'='*70}")
    print(f"Overall efficiency: {final_key_length/len(df)*100:.2f}%")
    print(f"{'='*70}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Bob gRPC Client for QKD")
    
    parser.add_argument('--server', type=str, default='localhost:50051',
                       help='Alice server address (default: localhost:50051)')
    parser.add_argument('--data', type=str,
                       default="raw_data/parsed_qkd_data_partial_10000(in).csv",
                       help='QKD data file')
    parser.add_argument('--algorithm', type=str, default='yanetal',
                       choices=['original', 'yanetal', 'option7', 'option8'],
                       help='Cascade algorithm to use')
    
    args = parser.parse_args()
    
    run_bob_client(
        server_address=args.server,
        data_file=args.data,
        algorithm=args.algorithm
    )