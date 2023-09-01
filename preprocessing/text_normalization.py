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

def split_into_sentences(text):
    nlp = spacy.load("en_core_web_sm")
    doc = nlp(text)
    sentences = [sent.text for sent in doc.sents]
    return sentences

def remove_entities_except_substring(sentence, substring):
    placeholder = "[entity]"
    parts = sentence.split(substring)

    for i in range(len(parts)):
        if placeholder in parts[i]:
            parts[i] = parts[i].replace(" " + placeholder, "")

    result = substring.join(parts)
    return result

def generate_variations(sentence):
    entities = re.findall(r'\[entity\].*?\[entity\]', sentence)

    #print(entities)

    num_entities = len(entities)
    variations = []

    for entity in entities:
        variations.append(remove_entities_except_substring(sentence, entity).strip())

    #print(variations)

    return variations

def extract_entities(text):

    disease_extracted_text = extract_entities_with_model(text, biobert_disease_model, biobert_disease_tokenizer)
    chemical_extracted_text = extract_entities_with_model(disease_extracted_text, biobert_chemical_model, biobert_chemical_tokenizer)
    
    variations = generate_variations(chemical_extracted_text)

    if variations == []:
        variations = [chemical_extracted_text]

    #print(new_sentence)

    #print(new_chem_sentence)

    #print(variations)

    classifier = TextClassificationPipeline(model=clinical_negation_model, tokenizer=clinical_negation_tokenizer)

    final_entities = []

    for sentence in variations:

        classification = classifier(sentence)

        #print(new_sentence)

        #print(classification)

        #print(entities)

        sentence = sentence.replace("\r", "").replace("\n", "")

        #print(sentence)

        if "ABSENT" in str(classification):
            search = re.findall(r'\[entity\].*?\[entity\]', sentence)
            if len(search) == 0:
                continue
            entity = search[0].replace("[entity]","").strip()
            final_entities.append("n_" + entity.lower().replace(" ", "_"))
            #entities = ["n_" + item.lower().replace(" ", "_") for item in entities]
        else:
            search = re.findall(r'\[entity\].*?\[entity\]', sentence)
            if len(search) == 0:
                continue
            entity = search[0].replace("[entity]","").strip()
            final_entity = entity.lower().replace(" ", "_").replace("#_#_", "")
            final_entity = final_entity.replace("_-_", "-").replace("_/_", "/").replace("_,_", ",_").replace("_.","").replace("_._", ".").replace("_'_", "'")
            if not (final_entity == "" or final_entity == ","):
                final_entities.append(final_entity)
            #entities = [item.lower().replace(" ", "_") for item in entities]

    return final_entities

def pipeline(text):
    texts = split_into_sentences(text)

    extracted_entities = []
    for text in texts:
        extracted_entities.extend(extract_entities(text))

    #print(extracted_entities)
    return extracted_entities


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

    chains = []

    # Find chains of [0, 1] (start inclusive, end exclusive)
    i = 0
    while i < len(predictions):
        if predictions[i] in [0, 1]:
            j = i + 1
            for j in range(i+1, len(predictions)):
                if predictions[j] not in [0, 1]:
                    break
            chains.append([i, j])
            i = j
        else:
            i += 1 

    # Expand Chains
    for chain in chains:
        if tokenizer.convert_ids_to_tokens(token_ids[chain[0]]).startswith("##"):
            i = chain[0] - 1
            while i >= 0 and tokenizer.convert_ids_to_tokens(token_ids[i]).startswith("##"):
                i -= 1
            chain[0] = i
        if chain[1] < len(token_ids) and tokenizer.convert_ids_to_tokens(token_ids[chain[1]]).startswith("##"):
            print("yes")
            i = chain[1] + 1
            while i < len(token_ids) and (tokenizer.convert_ids_to_tokens(token_ids[i]).startswith("##") or predictions[i] == 1):
                i += 1
            chain[1] = i

    # Remove overlapping chains
    i = 0
    while i < len(chains):
        j = i + 1
        while j < len(chains):
            if chains[j][0] in range(chains[i][0], chains[i][1]) or chains[j][1] - 1 in range(chains[i][0], chains[i][1]):
                # Pop shorter chain
                if chains[j][1] - chains[j][0] > chains[i][1] - chains[i][0]:
                    chains.pop(i)
                    i -= 1
                    break
                else:
                    chains.pop(j)
            else:
                j += 1
        i += 1

    # Insert start and end tokens (from back to front to not mess up indices)
    for chain in reversed(chains):
        token_ids = list_list_insertion(token_ids, e_end, chain[1])
        token_ids = list_list_insertion(token_ids, e_start, chain[0])

    return tokenizer.decode(token_ids).replace("< ES >", "[entity]").replace("< EE >", "[entity]").replace(" [entity] [SEP] [entity]", "").replace(" [SEP]", "").replace("[CLS] ", "").replace(".", " .").replace(",", " ,").replace("?", " ?").replace("!", " !").replace("'", " ' ").replace("[ ", "[").replace(" ]", "]")

def list_list_insertion(original_list, list_to_insert, index):
    return original_list[:index] + list_to_insert + original_list[index:]
