from elasticsearch import Elasticsearch
import json
from dataclasses import asdict

def load_patients(path):
    with open(path, 'r') as json_file:
        data = json.load(json_file)
        return data

client = Elasticsearch(
    "http://localhost:9200/"
)

patients = load_patients("../../../data/patients/patients_preprocessed.json")

for patient in patients:
    min_age = patient['age']
    max_age = patient['age']
    gender = patient['gender']
    diagnoses = patient['diagnoses']
    topic_id = patient['id']

    if min_age == 'adult' or max_age == 'adult':
        min_age = 18
        max_age = None

    if gender == None:
        gender = 'M F'

    diagnoses_query = ' '.join(diagnoses)

    search_query = {
    "size": 1000,
    "query": {
        "bool": {
            "must": [
                {
                    "match": {
                        "gender": {
                            "query": f"A {gender}",
                            "operator": "or",
                            "boost": 2
                        }
                    }
                },
                {
                    "range": {
                        "minimum_age": {
                            "lte": min_age,
                            "boost": 2
                        }
                    }
                },
                {
                    "range": {
                        "maximum_age": {
                            "gte": max_age,
                            "boost": 2
                        }
                    }
                }
            ],
            "must_not": [
                {
                    "match": {
                        "exclusion": {
                            "query": diagnoses_query,
                            "operator": "OR",
                            "fuzziness": "AUTO",
                            "fuzzy_transpositions": True,
                            "lenient": True,
                            "zero_terms_query": "NONE",
                            "auto_generate_synonyms_phrase_query": True
                        }
                    }
                }
            ],
            "should": [
                {
                    "match": {
                        "inclusion": {
                            "query": diagnoses_query,
                            "operator": "OR",
                            "fuzziness": "AUTO",
                            "fuzzy_transpositions": True,
                            "lenient": True,
                            "zero_terms_query": "NONE",
                            "auto_generate_synonyms_phrase_query": True
                        }
                    }
                }
            ],
            "adjust_pure_negative": True,
            "boost": 1.0
        }
    }
}

    search_results = client.search(index="trials", body=search_query)

    print(f"Found a total of {search_results['hits']['total']['value']} results.")

    for hit in search_results["hits"]["hits"]:
        min_score = search_results['hits']['hits'][0]['_score']
        max_score = search_results['hits']['hits'][0]['_score']

        for hit in search_results['hits']['hits']:
            score = hit['_score']
            if score < min_score:
                min_score = score
            if score > max_score:
                max_score = score

    rank = 1

    for hit in search_results["hits"]["hits"]:

        stored_json_data = hit["_source"]
        #print(stored_json_data)
        score = hit['_score']
        nct_id = stored_json_data['nct_id']

        if max_score - min_score == 0:
            confidence_score = 0
        else:
            confidence_score = (score - min_score) / (max_score - min_score)

        with open("results.txt", "a") as file:
            file.write(f"{topic_id} Q0 {nct_id} {rank} {confidence_score} elastic-pre\n")

        rank += 1
