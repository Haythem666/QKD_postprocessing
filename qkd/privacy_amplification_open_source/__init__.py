import numpy as np

from .universal_hashing import HashingAlgorithm, MODEL_1


def binary_entropy(p):
	if p <= 0 or p >= 1:
		return 0
	return -p * np.log2(p) - (1 - p) * np.log2(1 - p)