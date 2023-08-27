from elasticsearch import Elasticsearch
import json
from dataclasses import asdict

client = Elasticsearch(
    "http://localhost:9200/"
)

#client.indices.create(index="trials")

TRIALS = "../../../data/clinical_trials/trials_preprocessed_beauty.json"

with open(TRIALS, "r") as file:
    cts = json.load(file)

for ct in cts:
    json_data = json.dumps(ct)
    client.index(index="trials", body=json_data)
