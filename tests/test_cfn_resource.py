# -*- coding:utf-8 -*-
from __future__ import absolute_import

import json

import cfn_resource
import responses


class FakeLambdaContext(object):
    def __init__(self, name='Fake', version='LATEST'):
        self.name = name
        self.version = version

    @property
    def get_remaining_time_in_millis(self):
        return 10000

    @property
    def function_name(self):
        return self.name

    @property
    def function_version(self):
        return self.version

    @property
    def invoked_function_arn(self):
        return 'arn:aws:lambda:123456789012:' + self.name

    @property
    def memory_limit_in_mb(self):
        return 1024

    @property
    def aws_request_id(self):
        return '1234567890'


def wrap_with_nothing(func, base_response=None):
    def wrapper(*args):
        return func(*args)
    return wrapper


base_event = {
    "StackId": (
        "arn:aws:cloudformation:us-east-1:123456789012:stack/SomeStackHere3/d50d1280-a454-11e5-bd51-50e2416294a8"
    ),
    "ResponseURL": (
        "https://cloudformation-custom-resource-response-useast1.s3.amazonaws.com/"
        "arn%3Aaws%3Acloudformation%3Aus-east-1%3A368950843917%3Astack/SomeStackHere3/"
        "d50d1280-a454-11e5-bd51-50e2416294a8%7CFakeThing%7C79abbda7-092e-4534-9602-3ab4cc377807?"
        "AWSAccessKeyId=AKIAJNXHFR7P7YGKLDPQ&Expires=1450321030&Signature=HOCkeEsxMHHQMgnj3kx5gqLyfTU%3D"
    ),
    "ResourceProperties": {
        "OtherThing": "foobar",
        "ServiceToken": "arn:aws:lambda:us-east-1:123456789012:function:PyRsrc",
        "AnotherThing": "2"
    },
    "RequestType": "Delete",
    "ServiceToken": "arn:aws:lambda:us-east-1:123456789012:function:PyRsrc",
    "ResourceType": "Custom::MyResource",
    "PhysicalResourceId": "SomeStackHere3-FakeThing-893YUKO12RFM",
    "RequestId": "79abbda7-092e-4534-9602-3ab4cc377807",
    "LogicalResourceId": "FakeThing"
}

response = {
    "StackId": base_event["StackId"],
    "RequestId": base_event["RequestId"],
    "LogicalResourceId": base_event["LogicalResourceId"],
    "Status": cfn_resource.SUCCESS,
}

# Tests for the wrapper function


@responses.activate
def test_client_code_failure():
    serialized = json.dumps(response)

    responses.add(
        responses.PUT,
        base_event['ResponseURL'],
        json=serialized,
        content_type='application/json',
        match_querystring=True
    )

    rsrc = cfn_resource.Resource()

    @rsrc.delete
    def flaky_function(*args):
        raise KeyError('Oopsie')

    rsrc(base_event.copy(), FakeLambdaContext())

    body = responses.calls[0].request.body
    reply = json.loads(body)

    assert reply['Status'] == cfn_resource.FAILED
    assert reply['StackId'] == base_event['StackId']
    assert reply['Reason'] == "Exception was raised while handling custom resource"


@responses.activate
def test_sends_put_request():
    serialized = json.dumps(response)

    responses.add(
        responses.PUT,
        base_event['ResponseURL'],
        json=serialized,
        content_type='application/json',
        match_querystring=True
    )

    rsrc = cfn_resource.Resource()
    rsrc(base_event.copy(), FakeLambdaContext())

    assert responses.calls[0].request.method == 'PUT'


@responses.activate
def test_wraps_func_noresponse():

    rsrc = cfn_resource.Resource()

    event = base_event.copy()
    event['RequestType'] = 'Create'

    @rsrc.create
    def create(event, context):
        raise cfn_resource.NoResponse()

    resp = rsrc(event, FakeLambdaContext())

    assert resp is None


# Tests for the Resource object and its decorator for wrapping user handlers


def test_wraps_func():
    rsrc = cfn_resource.Resource(wrap_with_nothing)

    @rsrc.delete
    def delete(event, context):
        return {'Status': cfn_resource.FAILED}
    resp = rsrc(base_event.copy(), FakeLambdaContext())
    assert resp['Status'] == 'FAILED'


def test_succeeds_default():
    event = base_event.copy()
    event['PhysicalResourceId'] = 'my-existing-thing'
    event['RequestType'] = 'Update'

    rsrc = cfn_resource.Resource(wrap_with_nothing)
    resp = rsrc(event, FakeLambdaContext())
    assert resp == {
        'Status': 'SUCCESS',
        'PhysicalResourceId': 'my-existing-thing',
        'Reason': 'Life is good, man',
        'Data': {},
    }


def test_double_register():
    rsrc = cfn_resource.Resource(wrap_with_nothing)

    event = base_event.copy()
    event['RequestType'] = 'Update'

    @rsrc.update
    def update(event, context):
        return {'Data': {'called-from': 1}}

    @rsrc.update
    def update_two(event, context):
        return {'Data': {'called-from': 2}}

    resp = rsrc(event, FakeLambdaContext())
    assert resp['Data'] == {'called-from': 2}


def test_no_override():
    rsrc = cfn_resource.Resource(wrap_with_nothing)

    event = base_event.copy()
    event['RequestType'] = 'Create'

    @rsrc.create
    def create(event, context):
        return {'Data': {'called-from': 1}}

    assert create(event, FakeLambdaContext()) == rsrc(event, FakeLambdaContext())
