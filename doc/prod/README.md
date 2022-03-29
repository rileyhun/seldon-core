## Infrastructure Set-up

### Set up Seldon Core on GKE

```bash
export APPLICATION_NAME="seldon-core"
export CLUSTER_NAME="seldon-infra"
export RELEASE="seldon-infra"
export NAMESPACE="seldon-system"
export REGION="us-east1-b"
export PROJECT_ID="dao-aa-prod-xj8i"
export ISTIO_VERSION=1.7.7
export DISK_TYPE="pd-ssd"
export IMAGE_TYPE="COS"
export MACHINE_TYPE="n1-standard-8"
export DISK_SIZE="100"
export NUM_NODES="3"
export MIN_NODES="2"
export MAX_NODES="100"
export MAX_PODS_NODES="110"
export MASTER_IP_CIDR="172.10.192.0/28"
export LABEL_PROJECT="model-serving"
export DEFAULT_NODE_POOL_LABEL="default"
export ENV="prod"
export CLUSTER_DOMAIN="ml"
export POD_IP_CIDR_NAME="${ENV}-${REGION}-k8s-${CLUSTER_DOMAIN}-${ENV}-pods-0"
export SERVICES_IP_CIDR_NAME="${ENV}-${REGION}-k8s-${CLUSTER_DOMAIN}-${ENV}-services-0"
export BIGQUERY_DATASET_USAGE_DB="bq_${ENV}_platform_gke"
export NETWORK="seldon-prod"
export SUBNETWORK="seldon-prod-us-east1"
export IP_ADDRESS="34.117.74.172"
export SERVICE_ACCOUNT_EMAIL="seldon-core-user@${PROJECT_ID}.iam.gserviceaccount.com"
```

Set GCP Project ID
```bash
gcloud config set project ${PROJECT_ID}
```

Create Service Account
```bash
gcloud iam service-accounts create seldon-core-user --display-name "seldon-core-user"
gcloud iam service-accounts keys create secrets/seldon-core-user-key.json --iam-account seldon-core-user@${PROJECT_ID}.iam.gserviceaccount.com
```

Grant Service Account Permission/Roles
```bash
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
--member serviceAccount:${SERVICE_ACCOUNT_EMAIL} \
--role roles/container.clusterAdmin
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
--member serviceAccount:${SERVICE_ACCOUNT_EMAIL} \
--role roles/monitoring.metricWriter
# gcloud projects add-iam-policy-binding ${PROJECT_ID} \
# --member serviceAccount:${SERVICE_ACCOUNT_EMAIL} \
# --role roles/storage.objectAdmin
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
--member serviceAccount:${SERVICE_ACCOUNT_EMAIL} \
--role roles/logging.logWriter
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
--member serviceAccount:${SERVICE_ACCOUNT_EMAIL} \
--role roles/monitoring.editor
```

<Configure VPC Network for Seldon/Kubeflow & BentoML MLOps framework>

Create K8s cluster
```bash
gcloud container clusters create ${RELEASE} \
--zone ${REGION} \
--machine-type ${MACHINE_TYPE} \
--image-type ${IMAGE_TYPE} \
--disk-type ${DISK_TYPE} \
--disk-size ${DISK_SIZE} \
--scopes bigquery,cloud-platform,cloud-source-repos,compute-rw,gke-default,monitoring,pubsub,storage-rw  \
--num-nodes ${NUM_NODES} \
--min-nodes ${MIN_NODES} \
--max-nodes ${MAX_NODES} \
--max-pods-per-node ${MAX_PODS_NODES} \
--addons HorizontalPodAutoscaling,HttpLoadBalancing, \
--enable-autoupgrade \
--enable-autorepair \
--enable-autoscaling \
--enable-vertical-pod-autoscaling \
--max-surge-upgrade 1 \
--max-unavailable-upgrade 0 \
--no-enable-private-endpoint \
--enable-private-nodes \
--enable-ip-alias \
--network ${NETWORK} \
--subnetwork ${SUBNETWORK} \
--no-enable-master-authorized-networks \
--no-issue-client-certificate \
--no-enable-basic-auth \
--master-ipv4-cidr ${MASTER_IP_CIDR} \
--enable-network-policy \
--enable-master-authorized-networks \
--resource-usage-bigquery-dataset ${BIGQUERY_DATASET_USAGE_DB} \
--enable-network-egress-metering \
--enable-resource-consumption-metering \
--master-authorized-networks 128.107.0.0/16,171.68.0.0/14,173.36.0.0/14,64.100.0.0/16,64.101.0.0/18,64.101.64.0/18,64.101.128.0/18,64.101.192.0/19,64.101.224.0/19,64.102.0.0/16,64.103.0.0/16,64.104.0.0/16,64.68.96.0/19,66.187.208.0/20,72.163.0.0/16,144.254.0.0/16,161.44.0.0/16,198.92.0.0/18,216.128.32.0/19 \
--service-account ${SERVICE_ACCOUNT_EMAIL} \
--tags k8s-${ENV},${APPLICATION_NAME},${CLUSTER_NAME},${REGION}-${ENV},${DEFAULT_NODE_POOL_LABEL} \
--labels data_classification=ciscohighlyconfidential,environment=${ENV},resource_owner=esearch-health-alerts,data_taxonomy=supportdata,application_name=${APPLICATION_NAME},component=k8s,client_components=k8s,network_type=cloudonly,project=${PROJECT_ID},region=${REGION} \
--node-labels data_classification=ciscohighlyconfidential,environment=${ENV},resource_owner=esearch-health-alerts,data_taxonomy=supportdata,application_name=${APPLICATION_NAME},component=k8snode,client_components=k8s,network_type=cloudonly,project=${LABEL_PROJECT},region=${REGION},node_label=${DEFAULT_NODE_POOL_LABEL} \
--enable-stackdriver-kubernetes \
--enable-master-global-access \
--enable-shielded-nodes \
--enable-intra-node-visibility \
--metadata disable-legacy-endpoints=true \
--workload-pool=${PROJECT_ID}.svc.id.goog
```

Connect to GKE cluster
```bash
gcloud container clusters get-credentials ${RELEASE} --region ${REGION}
```

Create clusterrolebinding admin user
```bash
kubectl create clusterrolebinding kube-system-cluster-admin \
    --clusterrole=cluster-admin \
    --serviceaccount=kube-system:default

kubectl create clusterrolebinding cluster-admin-binding \
    --clusterrole cluster-admin \
    --user $(gcloud config get-value core/account)
```

Create Namespace for seldon GKE deployment
```bash
kubectl create namespace ${NAMESPACE}
```

### Istio Configuration

Manual install

```bash
bash istio-resources/install-istio.sh
```

IMPORTANT: Go to Firewall Rules and Locate "Master" for GKE cluster and add port TCP 15017,4443,8443

Install Health Virtual Service 
```bash
kubectl apply -f istio-resources/virtual_service.yaml
```

Patch Istio Ingress Gateway

Create JSON Patch file to make changes to Istio Ingress Gateway
```bash
cat <<EOF > istio-resources/istio-ingress-patch.json
[
  {
	"op": "replace",
	"path": "/spec/type",
	"value": "NodePort"
  },
  {
	"op": "remove",
	"path": "/status"
  }
]
EOF
```

Apply backend-config
```bash
kubectl apply -f istio-resources/backend-config.yaml
```

Apply patch file and add the Istio Ingress Gateway as a backend
```bash
kubectl -n istio-system patch svc istio-ingressgateway \
    --type=json -p="$(cat istio-resources/istio-ingress-patch.json)" \
	--dry-run=true -o yaml | kubectl apply -f -
kubectl annotate svc istio-ingressgateway -n istio-system cloud.google.com/neg='{"exposed_ports": {"80":{}}}' cloud.google.com/backend-config='{"default": "istio-backendconfig"}' --overwrite=true

kubectl -n istio-system patch svc istio-ops-ingressgateway \
    --type=json -p="$(cat istio-resources/istio-ingress-patch.json)" \
	--dry-run=true -o yaml | kubectl apply -f -
kubectl annotate svc istio-ops-ingressgateway -n istio-system cloud.google.com/neg='{"exposed_ports": {"80":{}}}' cloud.google.com/backend-config='{"default": "istio-backendconfig"}' --overwrite=true
```

Create Static IP
```bash
gcloud compute addresses create primary-istio-ingress-static-ip --global
gcloud compute addresses create ops-istio-ingress-static-ip --global
```

Create Kubernetes Ingress Object
```bash
kubectl apply -f istio-resources/primary-ingress.yaml
kubectl apply -f istio-resources/ops-ingress.yaml
```

Change Health-check so it points to Status Port of Istio Gateway and request path /healthz/ready

Set up Istio
```bash
kubectl apply -f istio-resources/istio_gateway.yaml
```

Create Virtual Service for Kiali
```bash
kubectl apply -f istio-resources/kiali-virtualservice.yaml
```

Install Seldon Core Using Helm
```bash
helm upgrade --install seldon-core seldon-core-operator \
    --repo https://storage.googleapis.com/seldon-charts \
    --set usageMetrics.enabled=true \
    --namespace ${NAMESPACE} \
    --set istio.enabled=true \
    --values values-prod.yaml
```

Create namespace for running models
```bash
export MODELS_NAMESPACE="ai-for-good"
kubectl create namespace ${MODELS_NAMESPACE}
kubectl label namespace ${MODELS_NAMESPACE} istio-injection=enabled
```

****
Set up Workload Identity Config

Monitoring Namespace
```bash
kubectl create namespace monitoring
kubectl create namespace logging
```

```bash
gcloud iam service-accounts create secrets-manager-invoker

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:secrets-manager-invoker@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/secretmanager.secretAccessor
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:secrets-manager-invoker@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/secretmanager.viewer
  
kubectl create serviceaccount --namespace logging secretsinvoker
kubectl create serviceaccount --namespace ${MODELS_NAMESPACE} secretsinvoker
kubectl create serviceaccount --namespace default secretsinvoker
kubectl create serviceaccount --namespace istio-system secretsinvoker

gcloud iam service-accounts add-iam-policy-binding \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:${PROJECT_ID}.svc.id.goog[logging/secretsinvoker]" \
  secrets-manager-invoker@${PROJECT_ID}.iam.gserviceaccount.com
gcloud iam service-accounts add-iam-policy-binding \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:${PROJECT_ID}.svc.id.goog[${MODELS_NAMESPACE}/secretsinvoker]" \
  secrets-manager-invoker@${PROJECT_ID}.iam.gserviceaccount.com
gcloud iam service-accounts add-iam-policy-binding \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:${PROJECT_ID}.svc.id.goog[default/secretsinvoker]" \
  secrets-manager-invoker@${PROJECT_ID}.iam.gserviceaccount.com
gcloud iam service-accounts add-iam-policy-binding \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:${PROJECT_ID}.svc.id.goog[istio-system/secretsinvoker]" \
  secrets-manager-invoker@${PROJECT_ID}.iam.gserviceaccount.com


kubectl annotate serviceaccount \
  --namespace logging \
  secretsinvoker \
  iam.gke.io/gcp-service-account=secrets-manager-invoker@${PROJECT_ID}.iam.gserviceaccount.com
kubectl annotate serviceaccount \
  --namespace ${MODELS_NAMESPACE} \
  secretsinvoker \
  iam.gke.io/gcp-service-account=secrets-manager-invoker@${PROJECT_ID}.iam.gserviceaccount.com
kubectl annotate serviceaccount \
  --namespace default\
  secretsinvoker \
 iam.gke.io/gcp-service-account=secrets-manager-invoker@${PROJECT_ID}.iam.gserviceaccount.com
kubectl annotate serviceaccount \
  --namespace istio-system \
  secretsinvoker \
 iam.gke.io/gcp-service-account=secrets-manager-invoker@${PROJECT_ID}.iam.gserviceaccount.com
```

### Metrics and Analytics Chart

Prometheus Installation

Create storage class
```bash
kubectl apply -f analytics-resources/storageclass.yaml
```

Store Service Account as Secret
```bash
gcloud iam service-accounts create thanos-sa
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:thanos-sa@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/storage.objectAdmin
gcloud iam service-accounts keys create secrets/thanos-sa-key.json --iam-account thanos-sa@${PROJECT_ID}.iam.gserviceaccount.com
#kubectl create secret generic thanos-gcs-credentials --from-file=secrets/thanos-sa-key.json --namespace monitoring
```

### Setting up Seldon-Core Monitoring + Observability

#### (a) With Prometheus Operator

Install Thanos
```bash
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update
sed -e "s/PROJECT_ID/${PROJECT_ID}/g" analytics-resources/thanos-prom/objstore-0.yaml > analytics-resources/thanos-prom/objstore-1.yaml
awk '/GCLOUD_SERVICE_KEY/{system("cat secrets/thanos-sa-key.json");next}1' analytics-resources/thanos-prom/objstore-1.yaml > analytics-resources/thanos-prom/objstore.yml
kubectl create secret generic thanos-objstore-secret -n monitoring --from-file=analytics-resources/thanos-prom/objstore.yml --dry-run=client -oyaml > analytics-resources/thanos-prom/thanos_objstore_secret.yaml
kubectl apply -n monitoring -f analytics-resources/thanos-prom/thanos_objstore_secret.yaml
rm analytics-resources/thanos-prom/objstore-1.yaml
rm analytics-resources/thanos-prom/objstore.yml
helm upgrade --install thanos bitnami/thanos \
   --values analytics-resources/thanos-prom/thanos-values.yaml \
   --version 1.1.0 \
   --namespace monitoring
```

Install Prometheus
```bash
helm upgrade --install prometheus-operator bitnami/kube-prometheus \
  --namespace monitoring \
  --values analytics-resources/thanos-prom/prom-operator-values.yaml
 
# apply service monitor
kubectl apply -f analytics-resources/thanos-prom/service-monitor.yaml
```

Install Grafana
```bash
helm upgrade --install grafana bitnami/grafana \
  --set service.type=NodePort \
  --set admin.password=${GRAFANA_PASSWORD} \
  --set admin.user=${GRAFANA_USER} \
  --namespace monitoring \
  --values analytics-resources/thanos-prom/grafana-values.yaml
  
kubectl apply -f analytics-resources/thanos-prom/grafana-virtualservice.yaml
```

#### EFK

Install Elasticsearch Operator. Documentation can be found [here](https://wwwin-github.cisco.com/Data-Analytics/elasticsearch-operator)

Google Secret Manager Handling
```bash
# install K8s external secret
helm upgrade --install external-secrets external-secrets/kubernetes-external-secrets \
  --values secret-manager/k8s-external-secret-values.yaml
  
envsubst < secret-manager/elastic-credentials-external-secret.yaml | kubectl apply -n logging -f -
envsubst < secret-manager/kiali-credentials-external-secret.yaml | kubectl apply -n istio-system -f -
envsubst < secret-manager/jaeger-external-secret.yaml | kubectl apply -n ai-for-good -f -
```

kubectl get ExternalSecrets -n logging

Install Fluentd
```bash
helm upgrade --install fluentd kokuwa/fluentd-elasticsearch --namespace=logging --values=efk/fluentd-values.yaml
```

#### Set variables
```bash
export KNATIVE_SERVING_URL="https://github.com/knative/serving/releases/download"
export SERVING_VERSION="v0.20.0"
export SERVING_BASE_VERSION="v0.20.0"
export KNATIVE_EVENTING_URL="https://github.com/knative/eventing/releases/download"
export EVENTING_VERSION="v0.20.0"
export KGCP_VERSION="v0.21.0"
```

##### Install KNative Serving + Eventing
```bash
kubectl apply -f ${KNATIVE_SERVING_URL}/${SERVING_VERSION}/serving-crds.yaml
kubectl apply -f ${KNATIVE_SERVING_URL}/${SERVING_VERSION}/serving-core.yaml
kubectl apply -f https://github.com/knative-sandbox/net-istio/releases/download/${SERVING_BASE_VERSION}/release.yaml

kubectl apply --filename ${KNATIVE_EVENTING_URL}/${EVENTING_VERSION}/eventing-crds.yaml
kubectl apply --filename ${KNATIVE_EVENTING_URL}/${EVENTING_VERSION}/eventing-core.yaml

kubectl annotate --overwrite -n knative-serving service autoscaler prometheus.io/scrape=true
kubectl annotate --overwrite -n knative-serving service autoscaler prometheus.io/port=9090

kubectl annotate --overwrite -n knative-serving service activator-service prometheus.io/scrape=true
kubectl annotate --overwrite -n knative-serving service activator-service prometheus.io/port=9090

# Install Sugar Controller
kubectl apply -f "https://github.com/knative/eventing/releases/download/${EVENTING_VERSION}/eventing-sugar-controller.yaml"
```

Deploy Request Logger

Build Docker Image
```bash
export IMAGE_TAG="0.1.0"
export IMAGE_NAME="seldon-request-logger"
cd seldon-request-logger
docker build . -t ${IMAGE_NAME}:${IMAGE_TAG}
docker tag ${IMAGE_NAME}:${IMAGE_TAG} gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${IMAGE_TAG}
docker push gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${IMAGE_TAG}

# run docker container
docker run -p 8080:8080 ${IMAGE_NAME}:${IMAGE_TAG} --workers=1
```

Deploy on K8s
```bash
envsubst < logging/seldon-request-logger.yaml | kubectl apply -n ${MODELS_NAMESPACE} -f -
```

Apply trigger
```bash
kubectl apply -f logging/trigger.yaml -n ${MODELS_NAMESPACE}
```

#### Install KNative-GCP
```bash
#kubectl create namespace cloud-run-events
#kubectl apply --filename https://github.com/google/knative-gcp/releases/download/${KGCP_VERSION}/cloud-run-events-pre-install-jobs.yaml

kubectl apply --selector events.cloud.google.com/crd-install=true \
--filename https://github.com/google/knative-gcp/releases/download/${KGCP_VERSION}/cloud-run-events.yaml

kubectl apply --filename https://github.com/google/knative-gcp/releases/download/${KGCP_VERSION}/cloud-run-events.yaml
```

#### Needed for init scripts
```bash
gcloud config set run/cluster ${CLUSTER_NAME}
gcloud config set run/cluster_location ${REGION}
gcloud config set project ${PROJECT_ID}
```

#### Enable workload identity
```bash
curl -s https://raw.githubusercontent.com/google/knative-gcp/master/hack/init_control_plane_gke.sh --output init_control_plane_gke.sh
bash init_control_plane_gke.sh
```

#### Configure Pub/Sub enabled Service Account for Data Plane

```bash
gcloud iam service-accounts create events-sources-gsa
gcloud iam service-accounts create events-broker-gsa

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:events-sources-gsa@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/pubsub.editor
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:events-sources-gsa@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/monitoring.metricWriter
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:events-sources-gsa@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/cloudtrace.agent
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:events-sources-gsa@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/storage.objectAdmin

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:events-broker-gsa@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/pubsub.editor

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:events-broker-gsa@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/monitoring.metricWriter

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:events-broker-gsa@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/cloudtrace.agent

gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:events-broker-gsa@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/storage.objectAdmin
  
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:events-broker-gsa@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/monitoring.editor
  
# Configure Authentication Mechanism for GCP (the data plane)
curl -s https://raw.githubusercontent.com/google/knative-gcp/master/hack/init_data_plane_gke.sh --output init_data_plane_gke.sh
bash init_data_plane_gke.sh
```

#### Authentication Set-up for GCP Broker
```bash
# Bind broker service-account with events-broker-gsa
gcloud iam service-accounts add-iam-policy-binding \
  --role roles/iam.workloadIdentityUser \
  --member serviceAccount:${PROJECT_ID}.svc.id.goog[cloud-run-events/broker] \
  events-broker-gsa@${PROJECT_ID}.iam.gserviceaccount.com
# Annotate the broker
kubectl create serviceaccount broker -n cloud-run-events
kubectl --namespace cloud-run-events annotate serviceaccount broker \
  iam.gke.io/gcp-service-account=events-broker-gsa@${PROJECT_ID}.iam.gserviceaccount.com

kubectl apply -f knative-setup/gcp-broker.yaml -n ${MODELS_NAMESPACE}
```

#### Set-up Service Account for Models
```bash
gcloud iam service-accounts create seldon-model-user
gcloud projects add-iam-policy-binding ${PROJECT_ID} \
  --member=serviceAccount:seldon-model-user@${PROJECT_ID}.iam.gserviceaccount.com \
  --role roles/storage.objectAdmin
  
kubectl create serviceaccount --namespace ${MODELS_NAMESPACE} modeluser

gcloud iam service-accounts add-iam-policy-binding \
  --role roles/iam.workloadIdentityUser \
  --member "serviceAccount:${PROJECT_ID}.svc.id.goog[${MODELS_NAMESPACE}/modeluser]" \
  seldon-model-user@${PROJECT_ID}.iam.gserviceaccount.com

kubectl annotate serviceaccount \
  --namespace ${MODELS_NAMESPACE} \
  modeluser \
  iam.gke.io/gcp-service-account=seldon-model-user@${PROJECT_ID}.iam.gserviceaccount.com
```

#### Install Broker with Pub/Sub Channel
```bash
sed -e "s/PROJECT_ID/${PROJECT_ID}/g" knative-setup/config-br-default-channel.yaml > knative-setup/temp-config-br-default-channel.yaml
kubectl apply -f knative-setup/temp-config-br-default-channel.yaml

# Patch the configmap in the knative-eventing namespace to use the Pub/Sub Channel as the default channel
kubectl patch configmap config-br-defaults -n knative-eventing --patch "$(cat knative-setup/patch-config-br-defaults-with-pubsub.yaml)"

kubectl label namespace ${MODELS_NAMESPACE} knative-eventing-injection=enabled
```

#### Istio Security

Authentication Policy
```bash
envsubst < istio-resources/security/x-mashery-policy.yaml | kubectl apply -f -
```

#### Distributed Tracing

Install Jaeger Operator on K8s

```bash
kubectl create namespace observability
kubectl create -n observability -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/master/deploy/crds/jaegertracing.io_jaegers_crd.yaml
kubectl create -n observability -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/master/deploy/service_account.yaml
kubectl create -n observability -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/master/deploy/role.yaml
kubectl create -n observability -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/master/deploy/role_binding.yaml
kubectl create -n observability -f observability/operator.yaml
# The operator will activate extra features if given cluster-wide permissions.
kubectl create -n observability -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/master/deploy/cluster_role.yaml
kubectl create -n observability -f https://raw.githubusercontent.com/jaegertracing/jaeger-operator/master/deploy/cluster_role_binding.yaml
```

Copy ES TLS Certificates to Namespace
```bash
kubectl get secret gke-eck-es-http-certs-public -o yaml > secrets/gke-eck-http-certs-public.yaml
kubectl apply -f secrets/gke-eck-http-certs-public.yaml -n ai-for-good
```

Create Jaeger Instance
```bash
kubectl apply -f observability/simple-prod-with-volumes.yaml -n ${MODELS_NAMESPACE}
```

Port forward Jaeger UI
```bash
kubectl port-forward svc/simple-prod-query 16686:16686 -n ai-for-good
```
