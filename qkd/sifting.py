import numpy as np

def sifting(df):

    print("Initial raw size:", len(df))

    sifted = df[df["matching_basis"] == True]

    alice_bits = sifted["tx_state"].to_numpy(dtype=np.uint8)
    bob_bits = sifted["rx_state"].to_numpy(dtype=np.uint8)

    return alice_bits, bob_bits