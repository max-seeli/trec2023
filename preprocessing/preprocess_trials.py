from text_normalization import pipeline
import json
from tqdm import tqdm

trials = []

with open("trials.json", "r") as json_file:
    trials = json.load(json_file)

with open("trials_preprocessed.json", "w") as file:
    file.write("[")

for index, trial in tqdm(enumerate(trials)):
    inclusion_criteria = trial['inclusion']
    
    inclusion_criteria_preprocessed = []
    for criterium in inclusion_criteria:
        preprocessed_criteria = pipeline(criterium)
        for preprocessed_criterium in preprocessed_criteria:
            inclusion_criteria_preprocessed.append(preprocessed_criterium)

    exclusion_criteria = trial['exclusion']
    
    exclusion_criteria_preprocessed = []
    for criterium in exclusion_criteria:
        preprocessed_criteria = pipeline(criterium)
        for preprocessed_criterium in preprocessed_criteria:
            exclusion_criteria_preprocessed.append(preprocessed_criterium)

    #move negatives

    exclusion_criteria_unique = []
    inclusion_criteria_unique = []

    for criterium in inclusion_criteria_preprocessed:
        if criterium.startswith("n_"):
            exclusion_criteria_unique.append(criterium[2:])
        else:
            inclusion_criteria_unique.append(criterium)

    for criterium in exclusion_criteria_preprocessed:
        if criterium.startswith("n_"):
            inclusion_criteria_unique.append(criterium[2:])
        else:
            exclusion_criteria_unique.append(criterium)

    #remove duplicates

    inclusion_criteria_unique = dict.fromkeys(inclusion_criteria_unique)
    exclusion_criteria_unique = dict.fromkeys(exclusion_criteria_unique)

    #remove duplicates across criteria

    exclusion_criteria_final = []
    inclusion_criteria_final = []

    exclusion_criteria_final = [item for item in exclusion_criteria_unique if item not in inclusion_criteria_unique]
    inclusion_criteria_final = [item for item in inclusion_criteria_unique if item not in exclusion_criteria_unique]


    preprocessed_trial = {"nct_id": trial['nct_id'],
                    "minimum_age": trial['minimum_age'],
                    "maximum_age": trial['maximum_age'],
                    "gender": trial['gender'],
                    "inclusion": inclusion_criteria_final,
                    "exclusion": exclusion_criteria_final}

    with open("trials_preprocessed.json", "a") as file:
        file.write(json.dumps(preprocessed_trial))

        if not index == len(trials)-1:
            file.write(",")

with open("trials_preprocessed.json", "a") as file:
    file.write("]")
