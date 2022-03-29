from seldon_core.seldon_client import SeldonClient
import time
import numpy as np
import requests
import random

# ISTIO_GATEWAY = '34.117.89.136'
# for i in range(1000):
#     sc = SeldonClient(deployment_name="iris-model", namespace="ai-for-good", gateway_endpoint=ISTIO_GATEWAY)
#     r = sc.predict(gateway="istio", transport="rest", payload_type='ndarray', shape=(1,4))
#     print(r)

# for i in range(1000):
#     from seldon_core.seldon_client import SeldonClient
#     sc = SeldonClient(deployment_name="myabtest",namespace="ai-for-good", gateway_endpoint=ISTIO_GATEWAY)
#     r = sc.predict(gateway="istio",transport="rest")
#     assert(r.success==True)
#     print(r)

# for i in range(10000):
#     sc = SeldonClient(deployment_name="model-logs", namespace="seldon", gateway_endpoint=ISTIO_GATEWAY)
#     r = sc.predict(gateway="istio", transport="rest", payload_type='ndarray', data=np.ones((5,)))
#     print(r)
#     assert(r.success==True)
#     time.sleep(5)

# url = 'http://34.117.89.136/seldon/ai-for-good/wines-classifier/api/v1.0/predictions'
# for i, _ in enumerate(range(100)):
#     payload = {'data':
#                 {
#                     "names": ["fixed acidity","volatile acidity","citric acid","residual sugar","chlorides","free sulfur dioxide","total sulfur dioxide","density","pH","sulphates","alcohol"],
#                     "ndarray": [[random.uniform(0, 30) for _ in range(11)]]
#                 }
#               }
#     r = requests.post(
#         url=url,
#         headers={'Content-Type': 'application/json'},
#         json = payload
#         )
#     count = i+1
#     print(count)

# for _ in range(0, 50):
#     r = requests.post(
#         url='http://34.117.89.136/seldon/ai-for-good/spt-bert-model/api/v1.0/predictions',
#         headers={'Content-Type': 'application/json'},
#         json={"text": "Title: Top Manhattan ER doc committed suicide, shaken by coronavirus onslaught"}
#     )
#     print(r.json())

sentences = np.array([["a", "b", "c", "d"]])
result = np.array([[1, 2, 3, 4]])

# data = np.concatenate((sentences, result))
# print(data[0])

# print(result.flatten().tolist())