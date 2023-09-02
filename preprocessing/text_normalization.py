import re
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, AutoModelForSequenceClassification, TextClassificationPipeline
import spacy

biobert_disease_tokenizer = AutoTokenizer.from_pretrained("alvaroalon2/biobert_diseases_ner")
biobert_disease_model = AutoModelForTokenClassification.from_pretrained("alvaroalon2/biobert_diseases_ner")

biobert_chemical_tokenizer = AutoTokenizer.from_pretrained("alvaroalon2/biobert_chemical_ner")
biobert_chemical_model = AutoModelForTokenClassification.from_pretrained("alvaroalon2/biobert_chemical_ner")

clinical_negation_tokenizer = AutoTokenizer.from_pretrained("bvanaken/clinical-assertion-negation-bert")
clinical_negation_model = AutoModelForSequenceClassification.from_pretrained("bvanaken/clinical-assertion-negation-bert")

def pipeline(text):

    sentences = split_into_sentences(text)

    extracted_entities = []
    for sentence in sentences:
        extracted_entities.extend(extract_entities(sentence))

    return extracted_entities

def split_into_sentences(text):

    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    return [sent.text for sent in doc.sents]


def extract_entities(text):

    disease_extracted_text = extract_entities_with_model(text, biobert_disease_model, biobert_disease_tokenizer)
    chemical_extracted_text = extract_entities_with_model(disease_extracted_text, biobert_chemical_model, biobert_chemical_tokenizer)
    
    variations = generate_variations(chemical_extracted_text)

    classifier = TextClassificationPipeline(model=clinical_negation_model, tokenizer=clinical_negation_tokenizer)

    final_entities = []

    classifications = classifier(variations)

    for i, sentence_variant in enumerate(variations):

        sentence_variant = sentence_variant.replace("\r", "").replace("\n", "")

        entity = re.search(r'\[entity\].*?\[entity\]', sentence_variant).group(0)
        entity = re.sub(r' +', ' ', entity)
        entity = re.sub(r' *[,\\\'\.\?\!-] *', '_', entity)
    
        entity = entity.replace("[entity]","") \
                    .strip() \
                    .lower() \
                    .replace(" ", "_")

        if classifications[i]['label'] == "ABSENT":
            final_entities.append("n_" + entity)
        else:
            final_entities.append(entity)

    return final_entities

def extract_entities_with_model(text, model, tokenizer):
    
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model.to(device)

    input = tokenizer.encode(text, return_tensors="pt").to(device)
    output = model(input)
    output = output[0].to("cpu")
    predictions = torch.argmax(output, dim=2).squeeze().tolist()
    
    e_start = tokenizer.encode("< ES >", return_tensors="pt")[0].tolist()[1:-1]
    e_end = tokenizer.encode("< EE >", return_tensors="pt")[0].tolist()[1:-1]

    token_ids = input[0].tolist().copy()

    # Find chains of [0, 1] (start inclusive, end exclusive)
    predictions_str = "".join([str(i) for i in predictions])
    pattern = re.compile(f'[01]+')
    chains = [[match.start(), match.end()] for match in pattern.finditer(predictions_str)]
    
    def is_continuation_token(token_id):
        return tokenizer.convert_ids_to_tokens(token_id).startswith("##")

    # Expand Chains
    for chain in chains:
        start_index = chain[0]
        end_index = chain[1]

        # Expand to the left
        while start_index > 0 and (is_continuation_token(token_ids[start_index]) or predictions[start_index - 1] == 1):
            start_index -= 1

        # Expand to the right
        while end_index < len(token_ids) and (is_continuation_token(token_ids[end_index]) or predictions[end_index] == 1):
            end_index += 1

        chain[0] = start_index
        chain[1] = end_index

    # Remove overlapping chains
    non_overlapping_chains = []
    while 0 < len(chains):
        possible_chains = [checked_chain for checked_chain in chains if not (chains[0][0] >= checked_chain[1] or chains[0][1] <= checked_chain[0])]
        lengths = [checked_chain[1] - checked_chain[0] for checked_chain in possible_chains]
        # get index of longest chain
        non_overlapping_chains.append(possible_chains[lengths.index(max(lengths))])
        # remove all chains that overlap with longest chain
        chains = [chain for chain in chains if chain not in possible_chains]

    # Insert start and end tokens (from back to front to not mess up indices)
    for chain in reversed(non_overlapping_chains):
        token_ids = list_list_insertion(token_ids, e_end, chain[1])
        token_ids = list_list_insertion(token_ids, e_start, chain[0])
    
    return tokenizer.decode(token_ids).replace("< ES >", "[entity]").replace("< EE >", "[entity]").replace(" [entity] [SEP] [entity]", "").replace(" [SEP]", "").replace("[CLS] ", "").replace(".", " .").replace(",", " ,").replace("?", " ?").replace("!", " !").replace("'", " ' ").replace("[ ", "[").replace(" ]", "]")

# Retruns a list of sentences with exactly one entity each
def generate_variations(sentence):

    entities = set(re.findall(r'\[entity\].*?\[entity\]', sentence))

    variations = []

    for entity in entities:
        variations.append(remove_other_entity_recognition(sentence, entity).strip())

    return variations

# Removes all entities from a sentence except the one specified by substring
# Substring must be of the form "[entity] ... [entity]"
def remove_other_entity_recognition(sentence, entity):
    
    # If the same entity is mentioned multiple times, the first occurence is chosen
    entity_start = sentence.find(entity) 
    entity_end = entity_start + len(entity)

    result = sentence[:entity_start].replace("[entity] ", "") \
                + sentence[entity_start:entity_end] \
                + sentence[entity_end:].replace("[entity] ", "")

    return result

# Inserts a list elementwise into another list at a specified index
def list_list_insertion(original_list, list_to_insert, index):
    return original_list[:index] + list_to_insert + original_list[index:]
