"""lambda function on AWS Lambda."""
import boto3
from urllib.parse import unquote_plus
from flow.data_pipeline.data_pipeline import AthenaQuery, delete_obsolete_data, update_baseline
from flow.data_pipeline.query import tags, tables,  network_using_edge
from flow.data_pipeline.query import X_FILTER, EDGE_FILTER, WARMUP_STEPS, HORIZON_STEPS

s3 = boto3.client('s3')
queryEngine = AthenaQuery()


def lambda_handler(event, context):
    """Handle S3 put event on AWS Lambda."""
    records = []
    # do a pre-sweep to handle tasks other than initalizing a query
    for record in event['Records']:
        bucket = record['s3']['bucket']['name']
        key = unquote_plus(record['s3']['object']['key'])
        table = key.split('/')[0]
        if table not in tables:
            continue

        # delete unwanted metadata files
        if (key[-9:] == '.metadata'):
            s3.delete_object(Bucket=bucket, Key=key)
            continue

        # load the partition for newly added table
        query_date = key.split('/')[-3].split('=')[-1]
        partition = key.split('/')[-2].split('=')[-1]
        queryEngine.repair_partition(table, query_date, partition)

        # delete obsolete data
        if table == "leaderboard_chart_agg":
            delete_obsolete_data(s3, key, table)

        # add table that need to start a query to list
        if table in tags.keys():
            records.append((bucket, key, table, query_date, partition))

    # initialize the queries
    start_filter = WARMUP_STEPS
    stop_filter = WARMUP_STEPS + HORIZON_STEPS
    for bucket, key, table, query_date, partition in records:
        source_id = "flow_{}".format(partition.split('_')[1])
        response = s3.head_object(Bucket=bucket, Key=key)
        loc_filter = X_FILTER
        if 'network' in response["Metadata"]:
            if response["Metadata"]['network'] in network_using_edge:
                loc_filter = EDGE_FILTER
            if 'is_baseline' in response['Metadata'] and response['Metadata']['is_baseline'] == 'True':
                update_baseline(s3, response["Metadata"]['network'], source_id)

        query_dict = tags[table]

        # handle different energy models
        if table == "fact_energy_trace":
            energy_model_id = partition.replace(source_id, "")[1:]
            query_dict = tags[energy_model_id]

        # initialize queries and store them at appropriate locations
        for table_name, query_list in query_dict.items():
            for query_name in query_list:
                result_location = 's3://circles.data.pipeline/{}/date={}/partition_name={}_{}'.format(table_name,
                                                                                                      query_date,
                                                                                                      source_id,
                                                                                                      query_name)
                queryEngine.run_query(query_name,
                                      result_location,
                                      query_date,
                                      partition,
                                      loc_filter=loc_filter,
                                      start_filter=start_filter,
                                      stop_filter=stop_filter)
