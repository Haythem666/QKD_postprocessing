import numpy as np

def sifting(df):

    print("Initial raw size:", len(df))

    if 'decoy_level' in df.columns:
        df_signal = df[df['decoy_level'] == 0]
    else:
        df_signal = df
        
    sifted = df_signal[df_signal["matching_basis"] == True]

    alice_bits = sifted["tx_state"].to_numpy(dtype=np.uint8)
    bob_bits = sifted["rx_state"].to_numpy(dtype=np.uint8)

    return alice_bits, bob_bits