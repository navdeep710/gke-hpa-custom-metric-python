import os
import traceback
from functools import partial, lru_cache

import requests
from google.cloud import monitoring_v3
import time
from apscheduler.schedulers.background import BackgroundScheduler


def initialize_metric_client():
    global client
    client = monitoring_v3.MetricServiceClient()


@lru_cache(maxsize=2)
def get_project_id():
    response = requests.get("http://metadata.google.internal/computeMetadata/v1/project/project-id",headers={"Metadata-Flavor": "Google"})
    return response.content.decode('utf-8')


@lru_cache(maxsize=2)
def get_cluster_name():
    response = requests.get("http://metadata.google.internal/computeMetadata/v1/instance/attributes/cluster-name",headers={"Metadata-Flavor": "Google"})
    return response.content.decode('utf-8')

@lru_cache(maxsize=2)
def get_zone():
    response = requests.get("http://metadata.google.internal/computeMetadata/v1/instance/zone",headers={"Metadata-Flavor": "Google"})
    response = response.content.decode('utf-8')
    return response.split("/")[-1]


def write_time_series(metric_name,value):
    try:
        # [START monitoring_write_timeseries]
        client = monitoring_v3.MetricServiceClient()
        project_name = client.project_path(get_project_id())

        series = monitoring_v3.types.TimeSeries()
        series.metric.type = f'custom.googleapis.com/{metric_name}'
        series.resource.type = 'gke_container'
        series.resource.labels['project_id'] = get_project_id()
        series.resource.labels['zone'] = get_zone()
        series.resource.labels['cluster_name'] = get_cluster_name()
        series.resource.labels['container_name'] = ""
        series.resource.labels['pod_id'] = os.getenv("POD_ID")
        series.resource.labels['namespace_id'] = "default"
        series.resource.labels['instance_id'] = ""
        point = series.points.add()
        point.value.int64_value = value
        now = time.time()
        point.interval.end_time.seconds = int(now)
        point.interval.end_time.nanos = int(
            (now - point.interval.end_time.seconds) * 10**9)
        client.create_time_series(project_name, [series])
        # [END monitoring_write_timeseries]
    except Exception as e:
        print("dont worry and carry on")

def get_driver_metrics():
    response = requests.get("http://localhost:9000/api/get_num_drivers")
    json = response.json()
    print(json)
    return int(json['num_drivers'])

def fire_metric(metric,metrics_getter):
    write_time_series(metric,metrics_getter())


if __name__ == '__main__':
    mint = 0
    while True:
        write_time_series("test_metric",mint)
        time.sleep(60)
        print("writing the value")
        mint += 1

#uncomment below if you want a service
# if __name__ == '__main__':
#     scheduler = BackgroundScheduler()
#     scheduler.add_job(partial(fire_metric,"num_drivers_per_pod",get_driver_metrics), 'interval', seconds=60)
#     scheduler.start()
#
#     try:
#         # This is here to simulate application activity (which keeps the main thread alive).
#         while True:
#             time.sleep(10)
#     except (KeyboardInterrupt, SystemExit):
#         # Not strictly necessary if daemonic mode is enabled but should be done if possible
#         scheduler.shutdown()


