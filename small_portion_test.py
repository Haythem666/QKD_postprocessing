import pandas as pd
import numpy as np


from qkd.sifting import sifting
from qkd.parameter_estimation import parameter_estimation
from qkd.cascade import cascade_error_protocol


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
    
    # Error correction using Cascade
    corrected_bob_key, leaked_bits, corrected_errors = cascade_error_protocol(alice_key, bob_key, qber)

    remaining_errors = np.sum(alice_key != corrected_bob_key)

    print("\n--- Cascade Error Correction ---")
    print("Corrected errors:", corrected_errors)
    print("Remaining errors:", remaining_errors)
    print("Leaked bits:", leaked_bits)

if __name__ == "__main__":
    main()

