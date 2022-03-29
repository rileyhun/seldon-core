#FROM gcr.io/google.com/cloudsdktool/cloud-sdk:alpine
FROM python:3.7-slim

COPY .. /app
WORKDIR /app

RUN apt-get update && apt-get install -y curl && \
    curl https://dl.google.com/dl/cloudsdk/release/google-cloud-sdk.tar.gz > /tmp/google-cloud-sdk.tar.gz && \
    mkdir -p /usr/local/gcloud \
    && tar -C /usr/local/gcloud -xvf /tmp/google-cloud-sdk.tar.gz \
    && /usr/local/gcloud/google-cloud-sdk/install.sh

ENV PATH $PATH:/usr/local/gcloud/google-cloud-sdk/bin

ENV GOOGLE_APPLICATION_CREDENTIALS="seldon-sa-key.json"
RUN gcloud auth activate-service-account --key-file=${GOOGLE_APPLICATION_CREDENTIALS} && \
    gsutil -m cp -r gs://dao-aa-prod-xj8i-spt-model-artifacts/* .
RUN rm ${GOOGLE_APPLICATION_CREDENTIALS}

RUN pip install -r requirements.txt
EXPOSE 5000

# Define environment variable
ENV MODEL_NAME SPTBertModel
ENV SERVICE_TYPE MODEL
ENV PERSISTENCE 0

CMD exec seldon-core-microservice $MODEL_NAME --service-type $SERVICE_TYPE --persistence $PERSISTENCE
