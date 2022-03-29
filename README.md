## Seldon Core

#### Project Description
Seldon Core is a platform that makes it easier and faster to deploy machine learning models and experiments at scale 
in a Production Environment. Seldon offers a cloud native solution that brings together different models built
in different environments and enables Data Scientists from different teams to work in any language or framework. This in
turn allows organizations to scale their model deployments and improvements collaboration between MLOps Engineers and 
Data Scientists.

#### Advantages of Using Seldon
- Deploy models as Real-time REST API or Batch processor
- Re-useable model servers such as Scikit-Learn, MLflow, Tensorflow
- Create custom model servers
- Feedback integration enabling users to send feedback (useful for multi-armed bandit)
- Metrics integration via Prometheus
- Log payload and model responses
- A/B testing
- Explainability
- Monitors changes in the model prediction via Alibi
- Automatically scale and allocate resources to model deployment
- Create complex inference graphs including: chaining multiple models together, combining responses from multiple models 
into single response, transformers, etc.

#### Infrastructure Documentation
* Production installation set-up [here](doc/prod/README.md)
* POC environment set-up [here](doc/poc/README.md)

#### Seldon Model Deployment
- Custom Python Model Deployment with A/B Testing [here](examples/custom-model-deployment-AB-testing/README.md)
- MLOps Prod Documentation [here](examples/prod-access/README.md)

#### Maintainers
Riley Hun, David Meyer, Nivi Mukka