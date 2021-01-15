Feature: ces
  
    Scenario: setup database
        Given a lambda function for database
        When a message is consumed from action queue for database
        Then create Null checkin in database
        And Publish a message to an SNS topic
        And start waiter for Slack App Queue publisher

    Scenario: update database with user inputs
        Given a lambda function for database update
        When a message is consumed from action queue for database inputs
        Then Update checkin in database with user inputs

    Scenario: update database from predict action
        Given a lambda function to update database
        When a message is consumed from action queue
        Then Update checkin in database with predictions