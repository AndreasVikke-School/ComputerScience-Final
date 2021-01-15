Feature: predict topic
  
  Scenario: make prediction
    Given a lambda function
    When a message is consumed from a predict topic
    Then Then make a hardcoded prediction
    And publish it to action queue