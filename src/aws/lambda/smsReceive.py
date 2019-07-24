import json
import urllib
import datetime
import boto3

def rfc339DateTime():
    """This gets the current date-time (down to the second) in UTC and returns it
    in RFC 3339 format (the right format) with time zone (of UTC) included."""
    return datetime.datetime.utcnow().isoformat(timespec="seconds") + "Z"


def eventCodeIsValid(eventCode):
    return (len(eventCode) == 3 and eventCode.isascii() and
            eventCode.isalpha() and eventCode.isupper())


def process_request(event, context):
    """This is called by the lambda_handler. It is permitted to raise
    exceptions."""
    parsedBody = urllib.parse.parse_qs(event["body"])
    smsMessageBody = parsedBody["Body"][0]

    parts = smsMessageBody.split()
    if len(parts) > 1:
        eventCode = parts[0]
        participantCode = parts[1]
    else:
        raise Exception(f"Invalid request '{smsMessageBody}'")

    eventCode = eventCode.upper()
    participantCode = participantCode.upper()
    datetime = rfc339DateTime()

    if eventCodeIsValid(eventCode):
        dynamodb = boto3.resource('dynamodb')
        signins_table = dynamodb.Table('attendancetracker-signins')
        signins_table.put_item(Item={
            "eventCode": eventCode,
            "participantCode": participantCode,
            "datetime": datetime,
        })


def lambda_handler(event, context):
    try:
        process_request(event, context)
    except Exception as err:
        return {
            "statusCode": 500,
            "body": f'{{"error":"{sys.exc_info()[0]}","message":"sys.exc_info()[1]"}}'
        }
    else:
        return {
            "statusCode": 201,
            "body": ""
        }
