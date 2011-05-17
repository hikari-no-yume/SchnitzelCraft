def notch_to_string(notch): # Convert from Notchian to "normal" strings
    return notch.rstrip(" ")
    
def string_to_notch(string):
    return string.ljust(64," ")[:64].encode('ascii','ignore')
