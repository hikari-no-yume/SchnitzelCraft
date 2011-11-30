import random as _random

def notch_to_string(notch): # Convert from Notchian to "normal" strings
    return notch.rstrip(" ")
    
def string_to_notch(string):
    return string.ljust(64," ")[:64].encode('ascii','ignore')

def generate_salt():
    return ''.join(_random.choice('0123456789abcdefghijklmnopqrstuvwxyz') for i in range(16))
