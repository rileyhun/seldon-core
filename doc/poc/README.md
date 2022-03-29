### Set up Seldon Core on GKE

```bash
export APPLICATION_NAME="seldon-core"
export CLUSTER_NAME="seldon-infra"
export RELEASE="seldon-infra"
export NAMESPACE="seldon-system"
export REGION="us-east1-b"
export PROJECT_ID="dao-aa-poc-uyim"
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
export ENV="dev"
export CLUSTER_DOMAIN="ml"
export POD_IP_CIDR_NAME="${ENV}-${REGION}-k8s-${CLUSTER_DOMAIN}-${ENV}-pods-0"
export SERVICES_IP_CIDR_NAME="${ENV}-${REGION}-k8s-${CLUSTER_DOMAIN}-${ENV}-services-0"
export BIGQUERY_DATASET_USAGE_DB="bq_${ENV}_platform_gke"
export NETWORK="composer"
export SUBNETWORK="composer-us-east1"
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

Install Kiali Virtual Service
```bash
kubectl apply -f istio-resources/kiali-virtualservice.yaml
```

Create Static IP
```bash
gcloud compute addresses create primary-istio-ingress-static-ip --global
gcloud compute addresses create ops-istio-ingress-static-ip --global
```

Create Kubernetes Ingress Object
```bash
kubectl apply -f istio-resources/staging/primary-ingress.yaml
kubectl apply -f istio-resources/staging/ops-ingress.yaml
```

Change Health-check so it points to Status Port of Istio Gateway and request path /healthz/ready

Set up Istio
```bash
kubectl apply -f istio-resources/staging/istio_gateway.yaml
```

Install Seldon Core Using Helm
```bash
helm upgrade --install seldon-core seldon-core-operator \
    --repo https://storage.googleapis.com/seldon-charts \
    --set usageMetrics.enabled=true \
    --namespace ${NAMESPACE} \
    --set istio.enabled=true \
    --values values-staging.yaml
```

Create namespace for running models
```bash
export MODELS_NAMESPACE="ai-for-good"
kubectl create namespace ${MODELS_NAMESPACE}
kubectl label namespace ${MODELS_NAMESPACE} istio-injection=enabled
```

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
kubectl create serviceaccount --namespace ${MODELS_NAMESPACE} seldon-core-user

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
  --member "serviceAccount:${PROJECT_ID}.svc.id.goog[${MODELS_NAMESPACE}/seldon-core-user]" \
  seldon-core-user@${PROJECT_ID}.iam.gserviceaccount.com


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
  --namespace ${MODELS_NAMESPACE}\
  seldon-core-user \
 iam.gke.io/gcp-service-account=seldon-core-user@${PROJECT_ID}.iam.gserviceaccount.com
```

### Setting up Seldon-Core Analytics Chart

Create storage class
```bash
kubectl apply -f analytics-resources/storageclass.yaml
```

Install Analytics Chart
```bash
sed -e "s/REPLACE_PASSWORD/${GRAFANA_PASSWORD}/g" analytics-resources/staging/values.yaml > analytics-resources/staging/tmp-values.yaml
helm upgrade --install seldon-core-analytics seldon-core-analytics \
   --repo https://storage.googleapis.com/seldon-charts \
   --namespace monitoring \
   --values=analytics-resources/staging/tmp-values.yaml
rm analytics-resources/staging/tmp-values.yaml
```

### Install EFK for Logging

TLS Security Handling
```bash
export CA_PASSWD=""
export CERT_PASSWD=""
docker run --name elastic-helm-charts-certs -i -w /app \
${ELASTICSEARCH_IMAGE:-docker.elastic.co/elasticsearch/elasticsearch:7.12.0} \
/bin/sh -c " \
elasticsearch-certutil ca --out /app/elastic-stack-ca.p12 --pass '$CA_PASSWD' && \
elasticsearch-certutil cert --name elasticsearch-master-cert --dns elasticsearch-master,elasticsearch-master-0.elasticsearch-master-headless,elasticsearch-master-1.elasticsearch-master-headless,elasticsearch-2.elasticsearch-master-headless --ca /app/elastic-stack-ca.p12 --pass '$CERT_PASSWD' --ca-pass '$CA_PASSWD' --out /app/elastic-certificates.p12"
cd efk
mkdir certs && docker cp elastic-helm-charts-certs:/app/elastic-stack-ca.p12 certs/
docker cp elastic-helm-charts-certs:/app/elastic-certificates.p12 certs/
docker rm -f elastic-helm-charts-certs
openssl pkcs12 -nodes -passin pass:"$CA_PASSWD" -in certs/elastic-stack-ca.p12 -out certs/elastic-ca.pem
```

Google Secret Manager Handling
```bash
# install K8s external secret
helm install external-secrets external-secrets/kubernetes-external-secrets \
  --values secret-manager/k8s-external-secret-values.yaml

kubectl create secret generic elastic-certificates \
  --from-file=efk/certs/elastic-certificates.p12 \
  --namespace logging
kubectl create secret generic elastic-ca \
  --from-file=efk/certs/elasticsearch-ca.pem \
  --namespace logging
  
envsubst < secret-manager/elastic-credentials-external-secret.yaml | kubectl apply -n logging -f -
envsubst < secret-manager/elastic-ssl-external.yaml | kubectl apply -n logging -f -
envsubst < secret-manager/kiali-credentials-external-secret.yaml | kubectl apply -n istio-system -f -
```

Install Multi-ElasticSearch w/ dedicated master, data, client nodes
```bash
helm upgrade --install es-master \
  --namespace logging \
  --values efk/staging/es-master-values.yaml \
  elastic/elasticsearch
  
helm upgrade --install es-data \
  --namespace logging \
  --values efk/staging/es-data-values.yaml \
  elastic/elasticsearch
  
helm upgrade --install es-client \
  --namespace logging \
  --values efk/staging/es-client-values.yaml \
  elastic/elasticsearch
```

Install Kibana
```bash
# get encryption key 
encryptionkey=$(docker run --rm busybox:1.31.1 /bin/sh -c "< /dev/urandom tr -dc _A-Za-z0-9 | head -c50")
helm upgrade --install kibana --namespace=logging --values=efk/kibana-values.yaml elastic/kibana
```

Install Fluentd
```bash
helm upgrade --install fluentd kokuwa/fluentd-elasticsearch --namespace=logging --values=efk/staging/fluentd-values.yaml
```

#### Knative and Request Logger Set-up

Set variables
```bash
export KNATIVE_SERVING_URL="https://github.com/knative/serving/releases/download"
export SERVING_VERSION="v0.20.0"
export SERVING_BASE_VERSION="v0.20.0"
export KNATIVE_EVENTING_URL="https://github.com/knative/eventing/releases/download"
export EVENTING_VERSION="v0.20.0"
```

Install KNative Serving + Eventing
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

# Install default in-memory channel (not suitable for production)
kubectl apply -f "https://github.com/knative/eventing/releases/download/${EVENTING_VERSION}/in-memory-channel.yaml"

# Install default Broker
kubectl apply -f "https://github.com/knative/eventing/releases/download/${EVENTING_VERSION}/mt-channel-broker.yaml"

# Install Sugar Controller
kubectl apply -f "https://github.com/knative/eventing/releases/download/${EVENTING_VERSION}/eventing-sugar-controller.yaml"
```

Create broker in model namespace
```bash
kubectl label namespace ${MODELS_NAMESPACE} eventing.knative.dev/injection=enabled
```

Build Docker Image
```bash
export IMAGE_TAG="0.1.0"
export IMAGE_NAME="seldon-request-logger"
cd seldon-request-logger
docker build . -t ${IMAGE_NAME}:${IMAGE_TAG}
docker tag ${IMAGE_NAME}:${IMAGE_TAG} gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${IMAGE_TAG}
docker push gcr.io/${PROJECT_ID}/${IMAGE_NAME}:${IMAGE_TAG}
```

Deploy Request Logger
```bash
envsubst < logging/staging/seldon-request-logger.yaml | kubectl apply -n ${MODELS_NAMESPACE} -f -
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

Run Example REST deployment
```bash
kubectl apply -f observability/simplest.yaml -n ai-for-good
kubectl create -f test/deployment_rest.yaml
```

Send Requests
```bash
curl -d '{"data": {"ndarray":[[8.0, 1.0, 5.0]]}}' \
   -X POST http://34.117.89.136/seldon/ai-for-good/tracing-example/api/v1.0/predictions \
   -H "Content-Type: application/json"
```

Port forward Jaeger UI
```bash
kubectl port-forward $(kubectl get pods -l app.kubernetes.io/name=simplest -n ai-for-good -o jsonpath='{.items[0].metadata.name}') 16686:16686 -n ai-for-good
```




