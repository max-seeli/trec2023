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

patients = load_patients("../../data/patients.json")

for patient in patients:
    min_age = patient['age']
    max_age = patient['age']
    gender = patient['gender']
    diagnosis = patient['diagnosis']
    diagnoses = patient['diagnoses']

    if min_age == 'adult' or max_age == 'adult':
        min_age = 18
        max_age = None 

    if gender == None:
        gender = ''

    search_query = {
        "size": 1000,
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": diagnosis
                        }
                    },
                    {
                        "match": {
                            "gender": {
                                "query": f"A {gender}",
                                "operator": "or"
                            }
                        }
                    },
                    {
                        "bool": {
                            "should": [
                                {
                                    "bool": {
                                        "must_not": {
                                            "exists": {
                                                "field": "minimum_age"
                                            }
                                        }
                                    }
                                },
                                {
                                    "bool": {
                                        "must_not": {
                                            "exists": {
                                                "field": "maximum_age"
                                            }
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
                            "minimum_should_match": 2
                        }
                    }
                ]
            }
        }
    }

    search_results = client.search(index="trials", body=search_query)

    for hit in search_results["hits"]["hits"]:
        stored_json_data = hit["_source"]
        #print(stored_json_data)

        #1st inclusion criteria

        relevant = True

        inclusion_criteria = stored_json_data['inclusion']

        for criterium in inclusion_criteria:
            for diag in diagnoses:
                if diag not in criterium or criterium not in diag:
                    relevant = False

        if not relevant:
            print(f"Patient {patient['id']} is not relevant for trial {stored_json_data['nct_id']}.")
            with open("results.txt", 'a') as file:
                file.write(f"Patient {patient['id']} is not relevant for trial {stored_json_data['nct_id']}.\n")
            continue

        #2nd exclusion criteria

        exclusion_criteria = stored_json_data['exclusion']

        for criterium in inclusion_criteria:
            for diag in diagnoses:
                if diag in criterium or criterium in diag:
                    relevant = False

        if not relevant:
            print(f"Patient {patient['id']} is relevant but excluded from trial {stored_json_data['nct_id']}.")
            with open("results.txt", 'a') as file:
                file.write(f"Patient {patient['id']} is relevant but excluded from trial {stored_json_data['nct_id']}.\n")
            continue

        print(f"Patient {patient['id']} is relevant for trial {stored_json_data['nct_id']}.")
        with open("results.txt", 'a') as file:
            if len(inclusion_criteria) == 0 and len(exclusion_criteria) == 0:
                file.write(f"Patient {patient['id']} is relevant for trial {stored_json_data['nct_id']}. ALL EMPTY\n")
            else:
                file.write(f"Patient {patient['id']} is relevant for trial {stored_json_data['nct_id']}.\n")


