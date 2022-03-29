FROM python:3.7-slim

COPY . /app
WORKDIR /app

RUN pip install -r requirements.txt && \
    python -m spacy download en_core_web_sm

EXPOSE 5000

# Define environment variable
ENV MODEL_NAME SPTRuleBasedModel
ENV SERVICE_TYPE MODEL
ENV PERSISTENCE 0

CMD exec seldon-core-microservice $MODEL_NAME --service-type $SERVICE_TYPE --persistence $PERSISTENCE