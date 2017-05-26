import random
import numpy as np

# s(st_ratio)
# b(borrowing_amount)
def repay_amount(s = 0, b = 0):
    amount = b * np.dot([s, 1 - s], [np.random.uniform(0.95, 1), np.random.uniform(0.2, 1)])
    return amount

def size_score():
    score = 0
    return score

def relation_score():
    score = 0
    return score

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