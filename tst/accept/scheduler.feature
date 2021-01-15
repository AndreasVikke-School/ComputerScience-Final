Feature: scheduler
  
  Scenario: make prediction
    Given a lambda function for scheduler
    When the time is 9 o’clock
    Then Publish a message with a username to an sqs