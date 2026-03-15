import argparse
import pandas as pd
import numpy as np
import time
from datetime import datetime


from qkd.sifting import sifting
from qkd.parameter_estimation import parameter_estimation
from qkd.cascade_wrapper import cascade_opensource
from qkd.privacy_amplification import binary_entropy
from qkd.privacy_amplification_open_source import HashingAlgorithm

# Configuration
QBER_THRESHOLD = 0.11
CHUNK_SIZE = 2_000_000  # Modified by GUI
CASCADE_ALGORITHM = 'yanetal'  # Modified by GUI


def process_large_file(filepath, chunk_size=CHUNK_SIZE, algorithm=CASCADE_ALGORITHM):

    """
    Process a large QKD file in chunks (streaming).
    
    Args:
        filepath: Path to the CSV file 
    
    Strategy:
        1. Read the file in chunks
        2. Perform sifting as we go
        3. Accumulate sifted bits until we have enough (~50-100K bits)
        4. Run Parameter Estimation + Cascade + PA on the batch
        5. Repeat until the end of the file
    """

    print("="*70)
    print("  QKD POST-PROCESSING - LARGE FILE (STREAMING)")
    print("="*70)
    print(f"File: {filepath}")
    print(f"Chunk size: {chunk_size:,} rows")
    print(f"Algorithm: {algorithm}")
    print("="*70)

    raw_buffer = pd.DataFrame()
    batch_number = 0
    

    # Global statistics
    total_raw_bits = 0
    total_sifted_bits = 0
    total_final_keys = 0

    start_time = time.time()
    
    # Read the file in chunks
    print("\nProcessing chunks...")

    for chunk_num, chunk in enumerate(pd.read_csv(filepath, chunksize=chunk_size), start=1):
        
        chunk_size = len(chunk)
        total_raw_bits += chunk_size

        print(f"\nChunk {chunk_num}: {chunk_size:,} rows (total: {total_raw_bits:,})")
        
        
        raw_buffer = pd.concat([raw_buffer, chunk])

        batch_number += 1
        print(f"\n--- Processing batch {batch_number} ---")

        # Sifting
        alice_bits, bob_bits = sifting(raw_buffer)

        total_sifted_bits += len(alice_bits)
            
        print(f" Sifted: {len(alice_bits):,} bits (buffer: {len(raw_buffer):,})")

        # Parameter Estimation
        qber, qber_low, qber_high, alice_key, bob_key = parameter_estimation(
                alice_bits, bob_bits
        )

        print(f"QBER: {qber*100:.3f}% (CI: [{qber_low*100:.3f}%, {qber_high*100:.3f}%])")
            
        if qber_high > QBER_THRESHOLD:
            print(" ABORT batch: QBER too high")
            raw_buffer = pd.DataFrame()
            continue

        # Cascade Error Correction
        print(f"\nCascade ({algorithm})...")
        corrected_bob_key, leaked_bits, final_errors, stats = cascade_opensource(
            alice_key, bob_key, qber, algorithm=algorithm
        )

        print(f"  Errors: {final_errors}")
        print(f"  Leaked: {leaked_bits}")
        print(f"  Efficiency: {stats.realistic_efficiency:.3f}")

        if final_errors > 0:
            print(" WARNING: Errors remain after Cascade!")
            
        # Privacy Amplification
        h_qber = binary_entropy(qber_high)
        n = len(alice_key)
        safety_margin = 50

        final_len = int(n - leaked_bits - n * h_qber - safety_margin)
        final_len = max(0, final_len)

        if final_len > 0 and final_errors == 0:
            output_bytes = max(1, (final_len + 7) // 8)

            alice_hash = HashingAlgorithm(''.join(str(int(bit)) for bit in alice_key))
            alice_bits = alice_hash.shake_256(output_bytes)[:final_len]
            alice_sec = np.fromiter((int(bit) for bit in alice_bits), dtype=np.uint8, count=final_len)

            bob_hash = HashingAlgorithm(''.join(str(int(bit)) for bit in corrected_bob_key))
            bob_bits = bob_hash.shake_256(output_bytes)[:final_len]
            bob_sec = np.fromiter((int(bit) for bit in bob_bits), dtype=np.uint8, count=final_len)

            if np.array_equal(alice_sec, bob_sec):
                total_final_keys += final_len
                print(f" Final key: {final_len:,} bits")
            else:
                print(" PA failed: keys differ")

            
        # Clear buffer for next batch
        raw_buffer = pd.DataFrame()

    elapsed_time = time.time() - start_time


    print(f"\n{'='*70}")
    print(f"  FINAL STATISTICS")
    print(f"{'='*70}")
    print(f"Total raw bits:      {total_raw_bits:,}")
    print(f"Total sifted bits:   {total_sifted_bits:,}")
    print(f"Total final keys:    {total_final_keys:,} bits")
    print(f"Batches processed:   {batch_number}")
    print(f"Overall efficiency:  {total_final_keys/total_raw_bits*100:.2f}%")
    print(f"{'='*70}")

    

if __name__ == "__main__":
    LARGE_FILE = "raw_data/parsed_qkd_data_partial_10M.csv"  # Modified by GUI

    parser = argparse.ArgumentParser(description="QKD post-processing for large CSV files")
    parser.add_argument(
        "--data",
        default=LARGE_FILE,
        help="Path to input CSV dataset"
    )
    parser.add_argument(
        "--algo",
        default=CASCADE_ALGORITHM,
        help="Cascade algorithm (e.g. original, yanetal, option7, option8)"
    )
    parser.add_argument(
        "--chunk",
        type=int,
        default=CHUNK_SIZE,
        help="Chunk size in number of rows"
    )

    args = parser.parse_args()

    if args.chunk <= 0:
        parser.error("--chunk must be a positive integer")
    
    print("Starting large file processing...")
    print(f"Selected data: {args.data}")
    print(f"Selected algorithm: {args.algo}")
    print(f"Selected chunk size: {args.chunk:,}")
    print()
    
    process_large_file(args.data, chunk_size=args.chunk, algorithm=args.algo)
