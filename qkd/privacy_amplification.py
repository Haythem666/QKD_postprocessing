import numpy as np

def binary_entropy(p):
    if p <= 0 or p >= 1:
        return 0
    return -p * np.log2(p) - (1 - p) * np.log2(1 - p)

def toeplitz_hash(key, output_length, seed=None):

    n = len(key)

    if seed is None:
        seed = np.random.randint(0, 2, n + output_length - 1, dtype=np.uint8)

    # Toeplitz matrix-vector multiplication
    hashed_key = np.zeros(output_length, dtype=np.uint8)

    for i in range(output_length):
        hashed_key[i] = np.sum(seed[i:i + n] & key) % 2

    return hashed_key,seed