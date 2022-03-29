### Packaging Python models for Seldon Core using Docker (incl. A/B testing)

Set Variables
```bash
export NAMESPACE="ai-for-good"
```

Retrieve Service Account Key
```bash
gcloud iam service-accounts keys create key.json \
  --iam-account seldon-core-user@${PROJECT_ID}.iam.gserviceaccount.com
```

#### Bert Model

Build Docker image for Bert Model
```bash
docker build . -t ${BERT_IMAGE_NAME}:${BERT_IMAGE_TAG}
```

Submit Docker Image to Google Container Registry
```bash
docker tag ${BERT_IMAGE_NAME}:${BERT_IMAGE_TAG} gcr.io/${PROJECT_ID}/${BERT_IMAGE_NAME}:${BERT_IMAGE_TAG}
docker push gcr.io/${PROJECT_ID}/${BERT_IMAGE_NAME}:${BERT_IMAGE_TAG}
```

#### Rule-Based Model

Build Docker image for Rule-Based Model
```bash
docker build . -t ${RULE_BASED_IMAGE_NAME}:${RULE_BASED_IMAGE_TAG}
```

Submit Docker Image to Google Container Registry
```bash
docker tag ${RULE_BASED_IMAGE_NAME}:${RULE_BASED_IMAGE_TAG} gcr.io/${PROJECT_ID}/${RULE_BASED_IMAGE_NAME}:${RULE_BASED_IMAGE_TAG}
docker push gcr.io/${PROJECT_ID}/${RULE_BASED_IMAGE_NAME}:${RULE_BASED_IMAGE_TAG}
```

Deploy Models (A/B testing) on Seldon using Kubernetes Resource Yaml
```bash

envsubst < spt-model.yaml | kubectl apply -f -
```

#### How to Connect Application to Model in POC environment

Example:
```python
from google.cloud import secretmanager
import json
import requests

# authenticate with Cisco SSO Server
client = secretmanager.SecretManagerServiceClient()
response = client.access_secret_version(
    name="projects/dao-aa-poc-uyim/secrets/seldon-oauth-credentials/versions/latest")
secrets = json.loads(response.payload.data.decode('UTF-8'))
url = "https://cloudsso-test.cisco.com/as/token.oauth2"
payload = 'grant_type=client_credentials&client_id=%s&client_secret=%s' % (
    secrets['test_client_id'], secrets['test_client_secret'])
headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
response = requests.request("POST", url, headers=headers, data=payload)

# retrieve bearer token
access_token = response.json()['access_token']
headers = {'Authorization': 'Bearer %s' % access_token}

# send POST request to Seldon Model
article = "Hello World!"
r = requests.post(url='https://api.cisco.com/api/enterprise-ai/models/ai-for-good/spt-model/api/v1.0/predictions',
                  json={"strData": article},
                  headers=headers
                  )
```


