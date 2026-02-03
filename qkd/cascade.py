
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
    

def cascade_iteration(alice_key, bob_key, block_size, permutation=None):
    
    if permutation is not None:
       alice_permuted = alice_key[permutation]
       bob_permuted = bob_key[permutation]
       
    else:
       alice_permuted = alice_key.copy()
       bob_permuted = bob_key.copy()

    corrected_bob_permuted = bob_permuted.copy()   
    leaked_bits = 0
    corrected_errors = 0
    
    for i in range(0, len(alice_key), block_size):
        alice_block = alice_permuted[i:i + block_size]
        bob_block = bob_permuted[i:i + block_size]

        if len(alice_block) < 2:
            continue  # Skip blocks that are too small for error correction
        
        leaked_bits += 1  # Parity bit revealed
        
        if parity(alice_block) != parity(bob_block):
            error_index = binary_search_error(alice_block, bob_block, i)
            corrected_bob_permuted[error_index] ^= 1
            corrected_errors += 1
            
    if permutation is not None:
        corrected_bob = np.empty_like(corrected_bob_permuted)
        corrected_bob[permutation] = corrected_bob_permuted
    else:
        corrected_bob = corrected_bob_permuted
    
        
    return corrected_bob, leaked_bits, corrected_errors


def cascade_error_protocol(alice_key, bob_key, qber, iterations=16):
    
    n = len(alice_key)
    corrected_bob = bob_key.copy()
    
    total_leaked_bits = 0
    total_errors = 0
    
    base_block_size = max(4, int(0.73 / max(qber, 1e-5)))
    
    final_errors = np.sum(alice_key != corrected_bob)

    for it in range(iterations):
        
        block_size = min(n, base_block_size * (2 ** it))

        if it == 0:
            permutation = None
        else:
            permutation = np.random.permutation(n)
            
        corrected_bob, leaked_bits, errors = cascade_iteration(alice_key, corrected_bob, block_size, permutation)
    
        total_leaked_bits += leaked_bits
        total_errors += errors

        final_errors = np.sum(alice_key != corrected_bob)

        if final_errors == 0:
            break
    
    return corrected_bob, total_leaked_bits, total_errors, final_errors