Feature: Slack Slash Command

    Scenario: a user wants to register with slash Command
        Given an unregistered consultant
        When you send /signup Command
        Then pull user data and publish to database
