import pandas as pd
import numpy as np


from qkd.sifting import sifting
from qkd.parameter_estimation import parameter_estimation
from qkd.privacy_amplification import toeplitz_hash, binary_entropy
from qkd.cascade_wrapper import cascade_opensource


QBER_THRESHOLD = 0.11


def main():
    # Load small dataset
    df = pd.read_csv("raw_data/parsed_qkd_data_partial_10000(in).csv")
    
    # Sifting
    alice_bits, bob_bits = sifting(df)
        
    print("Sifted size:", len(alice_bits))
    
    # Parameter estimation
    qber, qber_low, qber_high, alice_key, bob_key = parameter_estimation(alice_bits, bob_bits)


    if qber_high > QBER_THRESHOLD:
        print("ABORT protocol: QBER too high")
        return
    
    print("\n--- Cascade Error Correction (Open Source) ---")

    # Test all available Cascade algorithms
    algorithms = [
        'original',   # Cascade orig. (4 passes)
        'biconf',     # Cascade mod. (1) - BICONF
        'yanetal',    # Cascade opt. (2) - Yan et al.
        'option3',    # Cascade opt. (3) - 16 passes
        'option4',    # Cascade opt. (4) - reuse
        'option7',    # Cascade opt. (7) - optimized
        'option8'     # Cascade opt. (8) - best
    ]
    
    for algo in algorithms:
        print(f"\n{'='*60}")
        print(f"Testing: {algo}")
        print('='*60)
        corrected_bob_key, leaked_bits, final_errors, stats = cascade_opensource(
            alice_key.copy(), bob_key.copy(), qber, algorithm=algo, verbose=True
        )

        print("Remaining errors:", final_errors)
        print("Leaked bits:", leaked_bits)
        print(f"Efficiency: {stats.realistic_efficiency:.2f}")

        if final_errors == 0:
            print(f"  ✓ Success with {algo}!")
            #break

    if final_errors > 0:
        print(f"\n ABORT: {final_errors} errors remain after Cascade")
        print("Cannot proceed to Privacy Amplification with different keys")
        return
    
    # Privacy amplification using Toeplitz hashing
    h_qber = binary_entropy(qber_high)

    n = len(alice_key)
    safety_margin = 50
    final_key_length = int(
        n
        - leaked_bits
        - n * h_qber
        - safety_margin
    )

    final_key_length = max(0, final_key_length)

    print("\n--- Privacy Amplification ---")
    print("Final secure key length:", final_key_length)

    if final_key_length == 0:
        print("ABORT: No secure key can be extracted")
        return

    alice_secure_key, toeplitz_seed = toeplitz_hash(alice_key, final_key_length)
    bob_secure_key, _ = toeplitz_hash(corrected_bob_key, final_key_length, seed=toeplitz_seed)

    print("Keys identical after PA:", np.array_equal(alice_secure_key, bob_secure_key))


if __name__ == "__main__":
    main()

