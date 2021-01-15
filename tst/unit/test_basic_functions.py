# pylint: disable=E0401,C0413
"""
This unittest file to test the file basic_functions
"""
import sys
sys.path.append('../../src')
import unittest
import modules.basic_functions as function

class TestBasicFunctions(unittest.TestCase):
    '''This is a test suite for funtions in file basic_functions'''
    def test_add(self):
        '''Test on add method from function file'''
        result = function.add(10, 5)
        self.assertEqual(result, 15)
