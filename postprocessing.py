import pandas as pd
import numpy as np
import random
import math


SAMPLE_RATIO = 0.1  # 10% sample for parameter estimation
QBER_THRESHOLD = 0.11  # Example QBER threshold
CONFIDENCE_Z = 3 # 99.7% confidence interval
CHUNK_SIZE = 500_000

# Confidence Interval Calculation
def qber_confidence_interval(qber, sample_size, z=CONFIDENCE_Z):
    if sample_size == 0:
        return 0, 0
    
    delta = z * math.sqrt((qber * (1 - qber)) / sample_size)
    lower_bound = max(0, qber - delta)  
    upper_bound = min(1, qber + delta)
    return lower_bound, upper_bound


total_sampled = 0
total_errors = 0


buffer_a = np.empty(0, dtype= np.uint8)
buffer_b = np.empty(0, dtype= np.uint8)


for chunk in pd.read_csv('raw_data/parsed_qkd_data.csv', chunksize=CHUNK_SIZE):

    # Sifting
    sifted = chunk[chunk["matching_basis"] == True]

    a = sifted["tx_state"].to_numpy(dtype=np.uint8)
    b = sifted["rx_state"].to_numpy(dtype=np.uint8)

    buffer_a = np.concatenate([buffer_a, a])
    buffer_b = np.concatenate([buffer_b, b])


    # When buffer is large enough, perform parameter estimation
    if len(buffer_a) >= 50_000:
        sample_size = int(len(buffer_a) * SAMPLE_RATIO)
        sample_idx = np.random.choice(len(buffer_a), sample_size, replace=False) 

        errors = np.sum(buffer_a[sample_idx] != buffer_b[sample_idx])
     
        total_errors += errors
        total_sampled += sample_size

        # Remove sampled bits from buffers
        mask = np.ones(len(buffer_a), dtype=bool)
        mask[sample_idx] = False
        buffer_a = buffer_a[mask]
        buffer_b = buffer_b[mask]


qber = total_errors / total_sampled if total_sampled > 0 else 0
qber_lower, qber_upper = qber_confidence_interval(qber, total_sampled)

print("\n--- Streaming Parameter Estimation ---")
print("Sampled bits:", total_sampled)
print("Estimated QBER:", qber)
print("QBER confidence interval:", (qber_lower, qber_upper))
print("Remaining bits:", len(buffer_a))


print("\n--- Protocol Decision ---")
if qber_upper > QBER_THRESHOLD:
    print("ABORT protocol: QBER too high")
else:
    print("CONTINUE protocol: QBER acceptable")