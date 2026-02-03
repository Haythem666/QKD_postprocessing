import numpy as np
import math


CONFIDENCE_Z = 3 # 99.7% confidence interval
SAMPLE_RATIO = 0.1 # 10% sample for parameter estimation



def qber_confidence_interval(qber, n, z=CONFIDENCE_Z):
    if n == 0:
        return 0, 0
    delta = z * math.sqrt((qber * (1 - qber)) / n)
    return max(0, qber - delta), min(1, qber + delta)


def parameter_estimation(alice_bits, bob_bits, sample_ratio=SAMPLE_RATIO):

    sample_size = int(len(alice_bits) * sample_ratio)
    sample_idx = np.random.choice(len(alice_bits), sample_size, replace=False)

    errors = np.sum(alice_bits[sample_idx] != bob_bits[sample_idx])
    qber = errors / sample_size

    qber_low, qber_high = qber_confidence_interval(qber, sample_size)

    # Remove revealed bits
    mask = np.ones(len(alice_bits), dtype=bool)
    mask[sample_idx] = False

    a_key = alice_bits[mask]
    b_key = bob_bits[mask]


    print("\n--- Parameter Estimation ---")
    print("Sample size:", sample_size)
    print("Estimated QBER:", qber)
    print("QBER confidence interval:", (qber_low, qber_high))
    print("Remaining key length:", len(a_key))


    return qber, qber_low, qber_high, a_key, b_key