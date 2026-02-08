"""
Wrapper to use open-source Cascade with numpy arrays.
This file bridges your numpy-based code and the open-source code (Key classes).
"""

import numpy as np
from qkd.cascade_open_source import Reconciliation


class Key:
    """Wrapper to convert numpy arrays into a Key object"""
    
    def __init__(self, bits):
        """
        Args:
            bits: numpy array of 0s and 1s
        """
        self.bits = bits
    
    def get_size(self):
        return len(self.bits)
    
    def get_bit(self, index):
        return int(self.bits[index])
    
    def set_bit(self, index, value):
        self.bits[index] = value
    
    def flip_bit(self, index):
        self.bits[index] ^= 1


class SimpleClassicalChannel:
    """Simulates the communication between Alice and Bob for Cascade"""
    
    def __init__(self, alice_key):
        """
        Args:
            alice_key: Key object containing Alice's key
        """
        self.alice_key = alice_key
        self.bits_leaked = 0
    
    def start_reconciliation(self, algorithm_name):
        """Called at the start of reconciliation"""
        pass
    
    def ask_parities(self, blocks):
        """
        Alice computes the correct parities for the blocks requested by Bob.
        
        Args:
            blocks: list of Block objects
            
        Returns:
            list of parities (0 or 1)
        """
        parities = []
        for block in blocks:
            # Compute the block parity in Alice's key
            parity = block.get_shuffle().calculate_parity(
                self.alice_key, 
                block.get_start_index(), 
                block.get_end_index()
            )
            parities.append(parity)
            self.bits_leaked += 1  # 1 parity bit revealed
        return parities
    
    def end_reconciliation(self, algorithm_name):
        """Called at the end of reconciliation"""
        pass


def cascade_opensource(alice_bits, bob_bits, qber, algorithm, verbose=True):
    """
    Use open-source Cascade to correct errors.
    
    Args:
        alice_bits (np.array): Alice's key (numpy array of uint8)
        bob_bits (np.array): Bob's key with errors (numpy array of uint8)
        qber (float): Estimated QBER
        algorithm (str): Algorithm to use:
            - 'original': Cascade original (4 passes)
            - 'yanetal': Optimized (10 passes)
            - 'option7': Highly optimized (14 passes)
            - 'option8': Ultra optimized (14 passes)
        verbose (bool): Show detailed logs
    
    Returns:
        corrected_bob (np.array): Corrected Bob key
        leaked_bits (int): Number of revealed bits
        final_errors (int): Residual errors
        stats (Stats): Detailed statistics
    """
    # Convert numpy arrays to Key objects
    alice_key = Key(alice_bits.copy())
    bob_key = Key(bob_bits.copy())
    
    # Create the communication channel
    channel = SimpleClassicalChannel(alice_key)
    
    # Create the reconciliation
    reconciliation = Reconciliation(
        algorithm_name=algorithm,
        classical_channel=channel,
        noisy_key=bob_key,
        estimated_bit_error_rate=qber
    )
    
    if verbose:
        print(f"\n=== Cascade Open-Source ({algorithm}) ===")
        print(f"Initial errors: {np.sum(alice_bits != bob_bits)}")
        print(f"Estimated QBER: {qber*100:.3f}%")
    
    # Run Cascade
    reconciled_key = reconciliation.reconcile()
    
    # Retrieve results
    stats = reconciliation.stats
    leaked_bits = channel.bits_leaked
    
    # Convert reconciled key to numpy array
    corrected_bob = reconciled_key.bits
    
    # Compute residual errors
    final_errors = np.sum(alice_bits != corrected_bob)
    
    if verbose:
        print(f"\nResults:")
        print(f"  Normal iterations: {stats.normal_iterations}")
        print(f"  BICONF iterations: {stats.biconf_iterations}")
        print(f"  Leaked bits: {leaked_bits}")
        print(f"  Final errors: {final_errors}")
        print(f"  Realistic efficiency: {stats.realistic_efficiency:.3f}")
        print(f"  Time: {stats.elapsed_real_time:.3f}s")
    
    return corrected_bob, leaked_bits, final_errors, stats