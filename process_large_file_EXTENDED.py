"""
Extended process_large_file.py with configurable Privacy Amplification and Parameter Estimation
Supports both Toeplitz and SHA-256 based PA methods
"""

import argparse
import pandas as pd
import numpy as np
import time
from datetime import datetime


from qkd.sifting import sifting
from qkd.parameter_estimation import parameter_estimation
from qkd.cascade_wrapper import cascade_opensource
from qkd.privacy_amplification import toeplitz_hash, binary_entropy as binary_entropy_toeplitz
from qkd.privacy_amplification_open_source import HashingAlgorithm, binary_entropy

# Configuration
QBER_THRESHOLD = 0.11
CHUNK_SIZE = 2_000_000
CASCADE_ALGORITHM = 'yanetal'
PA_METHOD = 'sha256'  # 'sha256' or 'toeplitz'
PE_SAMPLE_RATIO = 0.1  # 10% default


def process_large_file(filepath, chunk_size=CHUNK_SIZE, algorithm=CASCADE_ALGORITHM,
                       pa_method=PA_METHOD, pe_sample=PE_SAMPLE_RATIO):
    """
    Process a large QKD file with configurable parameters.
    
    Args:
        filepath: Path to the CSV file
        chunk_size: Number of rows per chunk
        algorithm: Cascade algorithm to use
        pa_method: Privacy amplification method ('sha256' or 'toeplitz')
        pe_sample: Parameter estimation sample ratio (0.05 to 0.20)
    """

    print("="*70)
    print("  QKD POST-PROCESSING - EXTENDED VERSION")
    print("="*70)
    print(f"File: {filepath}")
    print(f"Chunk size: {chunk_size:,} rows")
    print(f"Algorithm: {algorithm}")
    print(f"PA Method: {pa_method.upper()}")
    print(f"PE Sample: {pe_sample*100:.0f}%")
    print("="*70)

    # Global statistics
    total_raw_bits = 0
    total_sifted_bits = 0
    total_final_keys = 0
    total_leaked_bits = 0
    qber_values = []
    cascade_eff_values = []
    batch_number = 0

    start_time = time.time()
    
    # Read the file in chunks
    print("\nProcessing chunks...")

    for chunk_num, chunk in enumerate(pd.read_csv(filepath, chunksize=chunk_size), start=1):
        
        actual_chunk_size = len(chunk)
        total_raw_bits += actual_chunk_size

        print(f"\nChunk {chunk_num}: {actual_chunk_size:,} rows")
        
        batch_number += 1

        # Sifting
        alice_bits, bob_bits = sifting(chunk)
        total_sifted_bits += len(alice_bits)
            
        print(f"  Sifted: {len(alice_bits):,} bits")
        
        if len(alice_bits) < 10000:
            print(f"  ⚠ Too few bits, skipping")
            continue

        # Parameter Estimation with configurable sample ratio
        np.random.seed(42)
        qber, qber_low, qber_high, alice_key, bob_key = parameter_estimation(
            alice_bits, bob_bits, sample_ratio=pe_sample
        )
        
        qber_values.append(qber)

        print(f"  QBER: {qber*100:.3f}% (CI: [{qber_low*100:.3f}%, {qber_high*100:.3f}%])")
            
        if qber_high > QBER_THRESHOLD:
            print(f"  ❌ ABORT: QBER too high")
            continue

        # Cascade Error Correction
        corrected_bob_key, leaked_bits, final_errors, stats = cascade_opensource(
            alice_key, bob_key, qber, algorithm=algorithm, verbose=False
        )
        
        total_leaked_bits += leaked_bits
        cascade_eff_values.append(stats.realistic_efficiency)

        print(f"  Cascade: {final_errors} errors, {leaked_bits} leaked")

        if final_errors > 0:
            print(f"  ⚠ Errors remain")
            continue
            
        # Privacy Amplification - METHOD SELECTION
        h_qber = binary_entropy(qber_high)
        n = len(alice_key)
        safety_margin = 50

        final_len = int(n - leaked_bits - n * h_qber - safety_margin)
        final_len = max(0, final_len)

        if final_len > 0:
            if pa_method == 'toeplitz':
                # Toeplitz Hashing (slower, theoretical)
                print(f"  PA: Using Toeplitz Matrix...")
                alice_sec, toeplitz_seed = toeplitz_hash(alice_key, final_len)
                bob_sec, _ = toeplitz_hash(corrected_bob_key, final_len, seed=toeplitz_seed)
                
            else:  # sha256 (default)
                # SHA-256 based hashing (faster, practical)
                print(f"  PA: Using SHA-256...")
                output_bytes = max(1, (final_len + 7) // 8)

                alice_hash = HashingAlgorithm(''.join(str(int(bit)) for bit in alice_key))
                alice_bits_pa = alice_hash.shake_256(output_bytes)[:final_len]
                alice_sec = np.fromiter((int(bit) for bit in alice_bits_pa), 
                                       dtype=np.uint8, count=final_len)

                bob_hash = HashingAlgorithm(''.join(str(int(bit)) for bit in corrected_bob_key))
                bob_bits_pa = bob_hash.shake_256(output_bytes)[:final_len]
                bob_sec = np.fromiter((int(bit) for bit in bob_bits_pa), 
                                     dtype=np.uint8, count=final_len)

            # Verify keys match
            if np.array_equal(alice_sec, bob_sec):
                total_final_keys += final_len
                print(f"  ✅ Final key: {final_len:,} bits")
            else:
                print(f"  ❌ PA failed: keys differ")

    elapsed_time = time.time() - start_time

    # Calculate averages
    avg_qber = np.mean(qber_values) if qber_values else 0
    avg_cascade_eff = np.mean(cascade_eff_values) if cascade_eff_values else 0

    print(f"\n{'='*70}")
    print(f"  FINAL STATISTICS")
    print(f"{'='*70}")
    print(f"Total raw bits:      {total_raw_bits:,}")
    print(f"Total sifted bits:   {total_sifted_bits:,}")
    print(f"Total final keys:    {total_final_keys:,} bits")
    print(f"Total leaked:        {total_leaked_bits:,}")
    print(f"Batches processed:   {batch_number}")
    print(f"Average QBER:        {avg_qber*100:.2f}%")
    print(f"Cascade efficiency:  {avg_cascade_eff:.3f}")
    print(f"Elapsed time:        {elapsed_time:.2f} seconds")
    print(f"Overall efficiency:  {total_final_keys/total_raw_bits*100:.2f}%")
    print(f"{'='*70}")

    

if __name__ == "__main__":
    LARGE_FILE = "raw_data/parsed_qkd_data_partial_10M.csv"

    parser = argparse.ArgumentParser(description="QKD post-processing with extended parameters")
    parser.add_argument(
        "--data",
        default=LARGE_FILE,
        help="Path to input CSV dataset"
    )
    parser.add_argument(
        "--algo",
        default=CASCADE_ALGORITHM,
        help="Cascade algorithm (original, yanetal, option7, option8)"
    )
    parser.add_argument(
        "--chunk",
        type=int,
        default=CHUNK_SIZE,
        help="Chunk size in number of rows"
    )
    parser.add_argument(
        "--pa-method",
        default=PA_METHOD,
        choices=['sha256', 'toeplitz'],
        help="Privacy Amplification method (sha256=fast, toeplitz=slow)"
    )
    parser.add_argument(
        "--pe-sample",
        type=float,
        default=PE_SAMPLE_RATIO,
        help="Parameter Estimation sample ratio (0.05 to 0.20)"
    )

    args = parser.parse_args()

    if args.chunk <= 0:
        parser.error("--chunk must be a positive integer")
    
    if not (0.01 <= args.pe_sample <= 0.30):
        parser.error("--pe-sample must be between 0.01 and 0.30")
    
    print("\n🚀 Starting extended processing...\n")
    
    process_large_file(
        args.data, 
        chunk_size=args.chunk, 
        algorithm=args.algo,
        pa_method=args.pa_method,
        pe_sample=args.pe_sample
    )