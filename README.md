# gke-hpa-custom-metric-python
how to get horizontal pod autoscaling working in gke via custom metric in Python

to build the docker file

docker build python_hpa:v1 .

replace the <registry_url>/python_hpa:v1 in python-metering.yaml for image_name