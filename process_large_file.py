import pandas as pd
import numpy as np
import time
from datetime import datetime


from qkd.sifting import sifting
from qkd.parameter_estimation import parameter_estimation
from qkd.cascade_wrapper import cascade_opensource
from qkd.privacy_amplification import toeplitz_hash, binary_entropy

# Configuration
QBER_THRESHOLD = 0.11
#MAX_ROWS = 100_000  # Limit to first 100K rows with good QBER (<5%)
CHUNK_SIZE = 100_000  # Process in single chunk
CASCADE_ALGORITHM = 'yanetal'  # Options: 'original', 'yanetal', 'option7', 'option8'
BATCH_SIZE_THRESHOLD = 50_000  # Process when buffer reaches 50K bits


def process_large_file(filepath):

    """
    Process a large QKD file in chunks (streaming).
    
    Args:
        filepath: Path to the CSV file 
        output_file: File where results are saved
    
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
    #print(f"Max rows: {MAX_ROWS:,} (good QBER region)")
    print(f"Chunk size: {CHUNK_SIZE:,} rows")
    print(f"Algorithm: {CASCADE_ALGORITHM}")
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

    for chunk_num, chunk in enumerate(pd.read_csv(filepath, chunksize=CHUNK_SIZE), start=1):
        
        chunk_size = len(chunk)
        total_raw_bits += chunk_size

        print(f"\nChunk {chunk_num}: {chunk_size:,} rows (total: {total_raw_bits:,})")
        
        # Stop if we've reached the max rows limit
        #if total_raw_bits >= MAX_ROWS:
        #    print(f"\nReached MAX_ROWS limit ({MAX_ROWS:,}). Stopping chunk reading.")

        chunk.sort_values("qubit_id", inplace=True)
        raw_buffer = pd.concat([raw_buffer, chunk])

        # If the buffer is too large, process it
        if len(raw_buffer) >= BATCH_SIZE_THRESHOLD:
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
            print(f"\nCascade ({CASCADE_ALGORITHM})...")
            corrected_bob_key, leaked_bits, final_errors, stats = cascade_opensource(
                alice_key, bob_key, qber, algorithm=CASCADE_ALGORITHM
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
                alice_sec, seed = toeplitz_hash(alice_key, final_len)
                bob_sec, _ = toeplitz_hash(corrected_bob_key, final_len, seed=seed)

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
    LARGE_FILE = "raw_data/parsed_qkd_data.csv" 
    
    print("Starting large file processing...")
    print()
    
    process_large_file(LARGE_FILE)
