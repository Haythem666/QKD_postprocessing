import numpy as np


def parity(bits):
    return np.sum(bits) % 2

def binary_search_error(alice_block, bob_block, start_index):
    if len(alice_block) == 1:
        return start_index
    
    mid = len(alice_block) // 2

    if (parity(alice_block[:mid]) != parity(bob_block[:mid])):
        return binary_search_error(alice_block[:mid], bob_block[:mid], start_index)
    else:
        return binary_search_error(alice_block[mid:], bob_block[mid:], start_index + mid)
    

def cascade_iteration(alice_key, bob_key, block_size):
    corrected_bob = bob_key.copy()
    leaked_bits = 0
    corrected_errors = 0

    for i in range(0, len(alice_key), block_size):
        alice_block = alice_key[i:i + block_size]
        bob_block = corrected_bob[i:i + block_size]

        leaked_bits += 1  # Parity bit revealed

        if parity(alice_block) != parity(bob_block):
            error_index = binary_search_error(alice_block, bob_block, i)
            corrected_bob[error_index] ^= 1
            corrected_errors += 1
    
    return corrected_bob, leaked_bits, corrected_errors


def cascade_error_protocol(alice_key, bob_key, qber, iterations):
    n = len(alice_key)
    corrected_bob = bob_key.copy()
    
    total_leaked_bits = 0
    total_errors = 0

    base_block_size = int(0.73 / max(qber, 1e-5))

    for it in range(iterations):
        block_size = min(n, base_block_size * (2 ** it))
        corrected_bob, leaked_bits, errors = cascade_iteration(alice_key, corrected_bob, block_size)

        total_leaked_bits += leaked_bits
        total_errors += errors

    return corrected_bob, total_leaked_bits, total_errors