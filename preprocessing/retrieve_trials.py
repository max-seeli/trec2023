#from text_normalization import pipeline
from elasticsearch import Elasticsearch
import json
from dataclasses import asdict

client = Elasticsearch(
    "http://localhost:9200/"
)

diagnoses = ["glaucoma", "anxiety", "COPD", "breast cancer", "COVID-19", "rheumatoid arthritis", "sickle cell anemia", "type 2 diabetes"]
#diagnoses = ["glaucoma", "anxiety"]

entries = []
uids = set()

for diagnosis in diagnoses:
    
    search_query = {
        "size": 1000,
        "query": {
            "bool": {
                "must": [
                    {
                        "query_string": {
                            "query": diagnosis
                        }
                    }
                ]
            }
        }
    }

    search_results = client.search(index="trials", body=search_query)

    with open("trials.json", "w") as file:
        file.write("[")

    hit_list = search_results["hits"]["hits"]

    for index, hit in enumerate(hit_list):
        stored_json_data = hit["_source"]

        uid = stored_json_data['nct_id']

        if uid in uids:
            print("Trial {stored_json_data['nct_id']} already found.")
        else:
            trial = {
                    "minimum_age": stored_json_data['minimum_age'],
                    "maximum_age": stored_json_data['maximum_age'],
                    "gender": stored_json_data['gender'],
                    "inclusion": stored_json_data['inclusion'],
                    "exclusion": stored_json_data['exclusion'],
                    "nct_id": stored_json_data['nct_id']
                    }

            with open("trials.json", "a") as file:
                file.write(json.dumps(trial))
                if not (index == len(hit_list)-1 and diagnosis in "type 2 diabetes"):
                    file.write(",")
                else:
                    print("Hit last entry")

            """
            inclusion_criteria = stored_json_data['inclusion']
            
            inclusion_criteria_preprocessed = []
            for criterium in inclusion_criteria:
                preprocessed_criteria = pipeline(criterium)
                for preprocessed_criterium in preprocessed_criteria:
                    inclusion_criteria_preprocessed.append(preprocessed_criterium)

            exclusion_criteria = stored_json_data['exclusion']
            
            exclusion_criteria_preprocessed = []
            for criterium in exclusion_criteria:
                preprocessed_criteria = pipeline(criterium)
                for preprocessed_criterium in preprocessed_criteria:
                    exclusion_criteria_preprocessed.append(preprocessed_criterium)

            entries.append({"nct_id": stored_json_data['nct_id'],
                            "inclusion": inclusion_criteria_preprocessed,
                            "exclusion": exclusion_criteria_preprocessed})
            """
#print(entries)

with open("trials.json", "a") as file:
    file.write("]")

print("Finished extracting trials to JSON")


