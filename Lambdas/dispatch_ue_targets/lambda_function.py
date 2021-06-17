from datetime import datetime
import json


def lambda_handler(event, context):
    now = datetime.utcnow()
    batch_id = now.timestamp()
    with open('targets_ue.json') as json_file:
        targets = json.load(json_file)
    for target in targets:
        target['batch_id'] = batch_id

    return {'statusCode': 200, 'data': targets}
