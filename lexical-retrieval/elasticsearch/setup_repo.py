from elasticsearch import Elasticsearch
import json
from dataclasses import asdict

client = Elasticsearch(
    "http://localhost:9200/"
)

client.indices.create(index="trials")

from CTnlp.parsers import parse_clinical_trials_from_folder

TRIALS_FOLDER = "../../data/clinical_trials/"
cts = parse_clinical_trials_from_folder(folder_name=TRIALS_FOLDER)
cts = [asdict(ct) for ct in cts]

for ct in cts:
    json_data = json.dumps(ct)
    client.index(index="trials", body=json_data)
