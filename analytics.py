import asyncio
import os
from time import time
import numpy as np
import random

"""
Analytics
"""

class Analytics:
    __instance = None  # Singleton instance
    ucb_counter = dict()
    ucb_counter[0] = [1, 1]
    ucb_counter[1] = [1, 1]
    ucb_counter[2] = [1, 1]
    epsilon = 0.3
    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super(Analytics, cls).__new__(cls)
        return cls.__instance

    def update_table(self, inst):
        self.ucb_counter[inst][0] += 1
    
    def get_rec(self):
        max_val = -10
        max_item = 0
        for i in range(3):
            num_m = self.ucb_counter[i][1]
            times_m = self.ucb_counter[i][0]
            avg_m = float(times_m) / float(num_m)
            if avg_m > max_val:
                max_val = avg_m
                max_item = i
        if random.random() < self.epsilon:
            max_item = random.randint(0,2)
        self.ucb_counter[max_item][1] += 1
        return max_item
    
    def get_stats(self):
        new = dict()
        for i in range(3):
            num_m = self.ucb_counter[i][1]
            times_m = self.ucb_counter[i][0]
            avg_m = float(times_m) / float(num_m)
            new["a" + str(i)] = str(avg_m)
        return new


