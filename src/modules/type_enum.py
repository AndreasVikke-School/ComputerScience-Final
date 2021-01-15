"""
    Enum for Types of AWS messages
    :license: MIT
"""
import enum

class Types(enum.Enum):
    '''Enum for SQS Types'''
    none = 99
    Scheduled = 1
    Predict = 2
    Prediction = 3
    Slack = 4
    UserInput = 5
    Scheduled_Reminder = 6
    Slack_Reminder = 7
    Consultant_Update = 8
    Project_Create = 9
