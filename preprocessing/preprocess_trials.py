from text_normalization import pipeline
import json
from tqdm import tqdm

TRIALS_SOURCE = "data/clinical_trials/trial_pre_selection_16k.json"
PREPROCESSED_TRIALS_TARGET = "data/clinical_trials/trials_preprocessed.json"

trials = []

with open(TRIALS_SOURCE, "r") as json_file:
    trials = json.load(json_file)

trials = trials[:10]

preprocessed_trials = []
for index, trial in tqdm(enumerate(trials), total=len(trials)):
    
    inclusion_criteria = trial['inclusion']
    inclusion_entities = [inclusion_entity for inclusion_criterium in inclusion_criteria for inclusion_entity in pipeline(inclusion_criterium)]
    
    exclusion_criteria = trial['exclusion']
    exclusion_entities = [exclusion_entity for exclusion_criterium in exclusion_criteria for exclusion_entity in pipeline(exclusion_criterium)]

    # Move negated entities to other list
    inclusion_entities_negated = [entity for entity in inclusion_entities if entity.startswith("n_")]
    exclusion_entities_negated = [entity for entity in exclusion_entities if entity.startswith("n_")]

    inclusion_entities = [entity for entity in inclusion_entities if entity not in inclusion_entities_negated]
    inclusion_entities.extend([entity[2:] for entity in exclusion_entities_negated])
    
    exclusion_entities = [entity for entity in exclusion_entities if entity not in exclusion_entities_negated]
    exclusion_entities.extend([entity[2:] for entity in inclusion_entities_negated])

    # Remove duplicates
    inclusion_entities = list(set(inclusion_entities))
    exclusion_entities = list(set(exclusion_entities))

    # Remove entities that are in both lists
    inclusion_entities_final = [entity for entity in inclusion_entities if entity not in exclusion_entities]
    exclusion_entities_final = [entity for entity in exclusion_entities if entity not in inclusion_entities]

    preprocessed_trial = {"nct_id": trial['nct_id'],
                    "minimum_age": trial['minimum_age'],
                    "maximium_age": trial['maximium_age'],
                    "gender": trial['gender'],
                    "inclusion": inclusion_entities_final,
                    "exclusion": exclusion_entities_final}

    preprocessed_trials.append(preprocessed_trial)

with open(PREPROCESSED_TRIALS_TARGET, "w") as file:
    json.dump(preprocessed_trials, file, indent=4)
