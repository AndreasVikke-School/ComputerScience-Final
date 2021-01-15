from behave import *
from src.dependencies.requests_provider import get_requests_provider
from src.dependencies.pynamodb_consultant_provider import get_consultants_provider
from src.sign_up_command import register

@given(u'an unregistered consultant')
def step_impl(context):
    context.request = get_requests_provider(test=True)
    context.consultant_model = get_consultants_provider(test=True)
    pass

@when(u'you send /signup Command')
def step_impl(context):
    context.event = {
        "body":{
            "user_id":"xxx",
        }
    }
    pass

@then(u'pull user data and publish to database')
def step_impl(context):
    post = register(context.event, context.request, context.consultant_model)
    assert context.consultant_model.email_index.query.call_count == 1