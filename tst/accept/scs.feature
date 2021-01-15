Feature: scs

   Scenario: consume from sqs and publish to slack
     Given a lambda function connected to an sqs
     When a message is consumed from a queue
     Then Combine message and template
     And Publish template to slack
