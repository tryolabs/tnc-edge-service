import boto3
import time
from datetime import datetime
from dateutil.parser import parse as dateparse

athena = boto3.client('athena')

custommetrics = boto3.client('cloudwatch')


def has_query_succeeded(execution_id):
    state = "RUNNING"
    max_execution = 5

    while max_execution > 0 and state in ["RUNNING", "QUEUED"]:
        max_execution -= 1
        response = athena.get_query_execution(QueryExecutionId=execution_id)
        if (
            "QueryExecution" in response
            and "Status" in response["QueryExecution"]
            and "State" in response["QueryExecution"]["Status"]
        ):
            state = response["QueryExecution"]["Status"]["State"]
            if state == "SUCCEEDED":
                return True

        time.sleep(30)

    return False

def gen_put_metric_requests(vector_id, value_timestamp_pairs):
    request = None
    for (value, timestamp) in value_timestamp_pairs:


        if request is None:
            request = {'Namespace': 'tnc_edge_brancol_v1', 'MetricData': []}
        request['MetricData'].append({
            'MetricName': 'vector_{}'.format(vector_id),
            'Value': value,
            'Timestamp': timestamp,
        })
        if len(request['MetricData']) >= 1000:
            yield request
            request = None
    if request:
        yield request


def main():
    # 5. Query Athena table
    query = f"SELECT vector_id, score, datetime from tnc_edge.brancol_v1_tests"
    response = athena.start_query_execution(
        QueryString=query,
        ResultConfiguration={"OutputLocation": "s3://51-gema-dev-athena/"}
    )

    execution_id = response["QueryExecutionId"]
    print(f"Get Num Rows execution id: {execution_id}")

    query_status = has_query_succeeded(execution_id=execution_id)
    print(f"Query state: {query_status}")

    paginator = athena.get_paginator('get_query_results')
    page_iterator = paginator.paginate(
        QueryExecutionId=execution_id
    )

    def gen_results():
        for page in page_iterator:
            if len(page['ResultSet']['Rows']) > 1:
                for row in page['ResultSet']['Rows'][1:]:
                    yield row
    
    grouped = {}
    for row in gen_results():
        vector_id = row['Data'][0]['VarCharValue'] 
        if vector_id not in grouped.keys():
            grouped[vector_id] = []
        value = row['Data'][1].get('VarCharValue') 
        try:
            value = float(value)
        except:
            continue
        timestamp = row['Data'][2].get('VarCharValue')
        if timestamp is None:
            continue

        timestamp = dateparse(timestamp)
        if timestamp <= dateparse('2023-10-20 23:00:00Z'):
            continue
        grouped[vector_id].append( (value, timestamp) )
    
    for (vector_id, value_timestamp_pairs) in grouped.items():
        if int(vector_id) == 3:
            continue
        # metric_name = 'tnc_edge_brancol_v1_vector_{}'.format(vector_id)
        for request in gen_put_metric_requests(vector_id=vector_id, value_timestamp_pairs=value_timestamp_pairs):
            print('putting {} values on ')
            response = custommetrics.put_metric_data(**request)
            print(response)



if __name__ == "__main__":
    main()
