import random
import numpy as np
import math

# Aj  : asset of Bank j
# A   : asset of all Bank but j
# I   : indicator
# Sij : size_score of Bank i with Bank j
def size_score(Aj, A, I):
    Sij = math.log(Aj) - np.dot(np.log(A), I) / sum(I)
    return Sij

# pSij :
# Sij  :
# X    :
# eta  :
def relation_score(pSij, X, eta=0.5):
    Sij = pSij + math.log(X) if X > 0 else (1 - eta) * pSij
    return Sij

# weight = [w_1, w_2, ...]
# score  = [s_1, s_2, ...]
def total_score(weight, score):
    score = np.dot(weight, score)
    return score

def lending_decision():
    p = 0
    return p

def lending_amount():
    amount = 0
    return amount