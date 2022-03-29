### Seldon in Production

#### Monitoring with Prometheus & Grafana
- Grafana Dashboards are found [here](https://mlops-dashboard1.cisco.com/grafana/login)
- Login Credentials are found in Google Cloud Secret Manager, under instance name: <i>seldon-grafana-secret</i>

#### Logging with Elasticsearch & Kibana
- Kibana can be accessed [here](https://mlops-dashboard2.cisco.com/)
- Login Credentials are found in Google Cloud Secret Manager, under instance names: <i>seldon-elastic-user</i> and <i>seldon-elastic-secret</i>

#### Connecting Application To Seldon Model
1. Go to API Console [here](apiconsole.cisco.com)
2. Sign in as MLOps user account (MlOps Dev team has the credentials)
3. Go to <i>My Apps & Keys</i> and create new client-id and client-secret for authenticating application to Cisco's SSO Server
4. Examples for sending requests to Seldon Model

Accessing Seldon Model Predictions:

```python
import os
import requests

# authenticate with Cisco SSO Server
url = "https://cloudsso.cisco.com/as/token.oauth2"
payload = 'grant_type=client_credentials&client_id=%s&client_secret=%s' % (
    os.environ['client_id'], os.environ['client_secret'])
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

Accessing Seldon Model Explainability:

```python
import os
import requests
import json
from alibi.api.interfaces import Explanation

url = "https://cloudsso.cisco.com/as/token.oauth2"
payload = 'grant_type=client_credentials&client_id=%s&client_secret=%s' % (
os.environ['client_id'], os.environ['client_secret'])

headers = {
    'Content-Type': 'application/x-www-form-urlencoded'
}

response = requests.request("POST", url, headers=headers, data=payload)
access_token = response.json()['access_token']
headers = {'Authorization': 'Bearer %s' % access_token}

r = requests.post(
    url='https://api.cisco.com/api/enterprise-ai/ai-for-good/income-explainer/default/api/v1.0/explain',
    json={"data": {"ndarray": [[0,1,2,3,4,5,6,7,8,9,10,11]]}},
    headers=headers)

explanation = r.json()
explanationStr = json.dumps(explanation)
explanation = Explanation.from_json(explanationStr)
```

#### Sanity Checks
After deploying your Seldon Models in Production on GCP,
1. Ensure the metrics are being scraped by Prometheus and visualized in the Grafana Dashboard. 
2. Check to see that the logs containing model inputs and outputs are being stored and indexed in ElasticSearch and are visible in Kibana.
