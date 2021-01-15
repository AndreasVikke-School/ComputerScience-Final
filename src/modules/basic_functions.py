# pylint: disable=C0103
"""
This is a file to test with unittest
"""

def add(x, y):
    '''Add Function'''
    return x + y

def subtract(x, y):
    '''Subtract Function'''
    return x - y

def multiply(x, y):
    '''Multiply Function'''
    return x * y

def divide(x, y):
    '''Divide Function'''
    if y == 0:
        raise ValueError('Can not devide by zero!')
    return x / y
