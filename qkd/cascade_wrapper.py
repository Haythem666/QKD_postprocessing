"""
Wrapper pour utiliser Cascade open-source avec des numpy arrays.
Ce fichier fait le pont entre ton code (numpy) et le code open-source (classes Key).
"""

import numpy as np
from qkd.cascade_open_source import Reconciliation


class Key:
    """Wrapper pour convertir numpy array en objet Key"""
    
    def __init__(self, bits):
        """
        Args:
            bits: numpy array de 0 et 1
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
    """Simule la communication entre Alice et Bob pour Cascade"""
    
    def __init__(self, alice_key):
        """
        Args:
            alice_key: Objet Key contenant la clé d'Alice
        """
        self.alice_key = alice_key
        self.bits_leaked = 0
    
    def start_reconciliation(self, algorithm_name):
        """Appelé au début de la reconciliation"""
        pass
    
    def ask_parities(self, blocks):
        """
        Alice calcule les parités correctes pour les blocs demandés par Bob.
        
        Args:
            blocks: Liste de Block objects
            
        Returns:
            Liste de parités (0 ou 1)
        """
        parities = []
        for block in blocks:
            # Calculer la parité du bloc dans la clé d'Alice
            parity = block.get_shuffle().calculate_parity(
                self.alice_key, 
                block.get_start_index(), 
                block.get_end_index()
            )
            parities.append(parity)
            self.bits_leaked += 1  # 1 bit de parité révélé
        return parities
    
    def end_reconciliation(self, algorithm_name):
        """Appelé à la fin de la reconciliation"""
        pass


def cascade_opensource(alice_bits, bob_bits, qber, algorithm, verbose=False):
    """
    Utilise Cascade open-source pour corriger les erreurs.
    
    Args:
        alice_bits (np.array): Clé d'Alice (numpy array de uint8)
        bob_bits (np.array): Clé de Bob avec erreurs (numpy array de uint8)
        qber (float): QBER estimé
        algorithm (str): Algorithme à utiliser:
            - 'original': Cascade original (4 passes)
            - 'yanetal': Optimisé (10 passes)
            - 'option7': Très optimisé (14 passes)
            - 'option8': Ultra optimisé (14 passes)
        verbose (bool): Afficher les détails
    
    Returns:
        corrected_bob (np.array): Clé de Bob corrigée
        leaked_bits (int): Nombre de bits révélés
        final_errors (int): Erreurs résiduelles
        stats (Stats): Statistiques détaillées
    """
    # Convertir les numpy arrays en objets Key
    alice_key = Key(alice_bits.copy())
    bob_key = Key(bob_bits.copy())
    
    # Créer le channel de communication
    channel = SimpleClassicalChannel(alice_key)
    
    # Créer la reconciliation
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
    
    # Lancer Cascade
    reconciled_key = reconciliation.reconcile()
    
    # Récupérer les résultats
    stats = reconciliation.stats
    leaked_bits = channel.bits_leaked
    
    # Convertir la clé reconciliée en numpy array
    corrected_bob = reconciled_key.bits
    
    # Calculer les erreurs résiduelles
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