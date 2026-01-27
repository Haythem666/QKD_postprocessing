import random 

N = 1000  # Number of bits
noise_prob = 0.05
sample_ratio = 0.1  # 10% of sifted key revealed

# Simulate Alice's bit and basis choices
def alice_bits_and_bases(N):
    alice_bits = [random.randint(0, 1) for _ in range(N)]
    alice_bases = [random.choice(['Z', 'X']) for _ in range(N)]
    return alice_bits, alice_bases

# Bob chooses bases and measures bits (with noise)
def bob_measurements(alice_bits,alice_bases, noise_prob):
    N = len(alice_bits)
    bob_bases = [random.choice(['Z', 'X']) for _ in range(N)]
    bob_bits = []

    for i in range(N):
        if bob_bases[i] == alice_bases[i]:
            measured_bit = alice_bits[i]
        else:     
            measured_bit = random.randint(0, 1)
        
        # Introduce noise
        if random.random() < noise_prob:
            measured_bit = 1 - measured_bit

        bob_bits.append(measured_bit)
    
    return bob_bases, bob_bits

# Sifting process: Keep bits where bases match
def sift_keys(alice_bits, alice_bases, bob_bits, bob_bases):
    sifted_key_alice = []
    sifted_key_bob = []

    for i in range(len(alice_bits)):
        if alice_bases[i] == bob_bases[i]:
            sifted_key_alice.append(alice_bits[i])
            sifted_key_bob.append(bob_bits[i])
    
    return sifted_key_alice, sifted_key_bob

# Parameter Estimation
def parameter_estimation(sifted_key_alice, sifted_key_bob, sample_ratio):
    sifted_length = len(sifted_key_alice)
    sample_size = int(sifted_length * sample_ratio)

    # Randomly select indices for sampling
    sample_indices = random.sample(range(sifted_length), sample_size)

    # Count errors in the sample
    sample_errors = 0
    for i in sample_indices:
        if sifted_key_alice[i] != sifted_key_bob[i]:
            sample_errors += 1

    estimated_qber = sample_errors / sample_size if sample_size > 0 else 0

    # Remove revealed bits from the sifted keys
    for index in sorted(sample_indices, reverse=True):
        del sifted_key_alice[index]
        del sifted_key_bob[index]
    
    return estimated_qber, sifted_key_alice, sifted_key_bob

# Error Correction (block method)
# If parity mismatch discard the whole block
def error_correction_discard(alice_key, bob_key, block_size):
    corrected_bob_key = []
    corrected_alice_key = []
    leaked_bits = 0

    key_length = len(alice_key)

    for i in range(0,key_length, block_size):

        alice_block = alice_key[i:i+block_size]
        bob_block = bob_key[i:i+block_size]
        
        if len(alice_block) < block_size:
            break  # Ignore incomplete block at the end

        alice_parity = sum(alice_block) % 2
        bob_parity = sum(bob_block) % 2

        leaked_bits += 1  # One bit of information leaked per block
        
        if alice_parity == bob_parity:
            corrected_bob_key.extend(bob_block)
            corrected_alice_key.extend(alice_block)
        else:
            # Discard the block
            continue


    return corrected_alice_key,corrected_bob_key, leaked_bits



def count_errors(key1, key2):
    errors = 0
    for a, b in zip(key1, key2):
        if a != b:
            errors += 1
    return errors

# Privacy Amplification (hashing using a random binary matrix)
def privacy_amplification(key, final_length, seed):
    random.seed(seed)
    
    # Créer une matrice de hachage aléatoire (final_length x len(key))
    hash_matrix = [[random.randint(0, 1) for _ in range(len(key))] 
                   for _ in range(final_length)]
    
    # Chaque bit final = XOR (modulo 2) de plusieurs bits de la clé
    hashed_key = []
    for row in hash_matrix:
        bit = sum(key[i] * row[i] for i in range(len(key))) % 2
        hashed_key.append(bit)
    
    return hashed_key



# Main simulation
def main():
    alice_bits, alice_bases = alice_bits_and_bases(N)
    bob_bases, bob_bits = bob_measurements(alice_bits, alice_bases, noise_prob)
    sifted_key_alice, sifted_key_bob = sift_keys(alice_bits, alice_bases, bob_bits, bob_bases)
    qber, final_key_alice, final_key_bob = parameter_estimation(sifted_key_alice, sifted_key_bob, sample_ratio)

    # Error Correction
    block_size = 8
    errors_before = count_errors(final_key_alice, final_key_bob)
    corrected_key_alice, corrected_key_bob, leaked_bits = error_correction_discard(final_key_alice, final_key_bob, block_size)
    errors_after = count_errors(corrected_key_alice, corrected_key_bob)

    # Privacy Amplification
    seed = 42  # public seed
    final_key_length = max(0, len(corrected_key_alice) - leaked_bits)

    secure_key_alice = privacy_amplification(corrected_key_alice, final_key_length, seed)
    secure_key_bob = privacy_amplification(corrected_key_bob, final_key_length, seed)

    print("Errors before correction:", errors_before)
    print("Errors after correction: ", errors_after)
    print("Leaked parity bits:", leaked_bits)

    print("Estimated QBER:", qber)
    print("Final key length (Alice):", len(final_key_alice))
    print("Final key length (Bob):", len(corrected_key_bob))

    print("Final secure key length:", final_key_length)
    print("Keys identical after PA:", secure_key_alice == secure_key_bob)

if __name__ == "__main__":
    main()



