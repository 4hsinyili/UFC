import boto3
import datetime
import pprint
from collections import defaultdict


class StatesMetricInfo():
    def __init__(self, cloudwatch):
        self.cloudwatch = cloudwatch

    def get_states_data(self, end_time, start_time):
        cloudwatch = self.cloudwatch
        response = cloudwatch.get_metric_data(
            MetricDataQueries=[
                {
                    'Id': 'm1',
                    'MetricStat': {
                        'Metric': {
                            'Namespace': 'AWS/States',
                            'MetricName': 'ExecutionsSucceeded',
                            'Dimensions': [
                                {
                                    'Name': 'StateMachineArn',
                                    'Value': 'arn:aws:states:ap-northeast-1:713960092195:stateMachine:ufc_stepfunction'
                                },
                            ]
                        },
                        'Period': 3600,
                        'Stat': 'Sum',
                    },
                },
            ],
            StartTime=start_time,
            EndTime=end_time,
        )
        return response

    def parse_states_data(self, response):
        data = False
        if response['MetricDataResults'][0]['StatusCode'] == 'Complete':
            timestamps = response['MetricDataResults'][0]['Timestamps']
            values = response['MetricDataResults'][0]['Values']
            data = {timestamps[i].strftime('%Y-%m-%d %H:%M:%S'): int(values[i]) for i in range(len(timestamps))}
        return data

    def main(self, end_time, start_time):
        step_function_metrics_raw = self.get_states_data(end_time, start_time)
        step_function_metrics = self.parse_states_data(step_function_metrics_raw)
        return step_function_metrics


class LambdaMetricInfo():
    def __init__(self, cloudwatch):
        self.cloudwatch = cloudwatch
        self.metric_names = ['Duration']
        self.lambda_names = ['get_ue_list', 'get_fp_list', 'get_ue_detail', 'get_fp_detail']

    def get_lambda_static(self, metric_name, lambda_name, end_time, start_time):
        cloudwatch = self.cloudwatch
        if metric_name == 'Duration':
            statics = ['Average']
        else:
            statics = ['Sum']
        response = cloudwatch.get_metric_statistics(
            Namespace='AWS/Lambda',
            MetricName=metric_name,
            Dimensions=[
                {
                    'Name': 'FunctionName',
                    'Value': lambda_name
                }
            ],
            Period=3600,
            Statistics=statics,
            StartTime=start_time,
            EndTime=end_time,
        )
        return response

    def parse_lambda_static(self, response, metric_name):
        datapoints = response['Datapoints']
        data = False
        if len(datapoints) > 0:
            data = {}
            for point in datapoints:
                if metric_name == 'Duration':
                    point_vlaue = int(point['Average']) / 1000
                else:
                    point_vlaue = int(point['Sum'])
                point_datetime = point['Timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                data_point = {point_datetime: point_vlaue}
                data.update(data_point)
        return data

    def main(self, end_time, start_time):
        lambda_metrics = defaultdict(dict)
        for metric_name in self.metric_names:
            for lambda_name in self.lambda_names:
                lambda_metric_raw = self.get_lambda_static(metric_name, lambda_name, end_time, start_time)
                lambda_metric = self.parse_lambda_static(lambda_metric_raw, metric_name)
                lambda_metrics[metric_name][lambda_name] = lambda_metric
        return lambda_metrics


class CustomMetric():
    def __init__(self, cloudwatch):
        self.cloudwatch = cloudwatch

    def put_data(self):
        cloudwatch = self.cloudwatch
        response = cloudwatch.put_metric_data(
            Namespace='Test',  # 要放到哪一個 Namespace ，最好是自創
            MetricData=[
                {
                    'MetricName': 'AWS/Lambda',  # Namespace 自創的話，這個最好也自創
                    'Dimensions': [
                        {
                            'Name': 'test_dimension_name',
                            'Value': 'test_dimension_value'
                        },
                    ],
                    'Timestamp': datetime.utcnow(),
                    'Value': 10,
                },
            ]
        )
        print(response)


if __name__ == '__main__':
    cloudwatch = boto3.client('cloudwatch')

    end_time = datetime.datetime.combine(datetime.datetime.today().date(), datetime.time.min)
    states_metric = StatesMetricInfo(cloudwatch)
    lambda_metric = LambdaMetricInfo(cloudwatch)
    states_metric_info = states_metric.main(end_time)
    lambda_metric_info = lambda_metric.main(end_time)

    pprint.pprint(states_metric_info)
    pprint.pprint(lambda_metric_info)
