import re
import torch
from transformers import AutoTokenizer, AutoModelForTokenClassification, AutoModelForSequenceClassification, TextClassificationPipeline
import spacy

tokenizer = AutoTokenizer.from_pretrained("alvaroalon2/biobert_diseases_ner")
model = AutoModelForTokenClassification.from_pretrained("alvaroalon2/biobert_diseases_ner")

tokenizer_neg = AutoTokenizer.from_pretrained("bvanaken/clinical-assertion-negation-bert")
model_neg = AutoModelForSequenceClassification.from_pretrained("bvanaken/clinical-assertion-negation-bert")

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
        variations.append(remove_entities_except_substring(sentence, entity))

    #print(variations)

    return variations

def extract_entities(text):
    inputs = tokenizer.encode(text, return_tensors="pt")
    outputs = model(inputs)[0]
    #print(outputs)
    predictions = torch.argmax(outputs, dim=2)
    #print(predictions)
    tokens = tokenizer.convert_ids_to_tokens(inputs[0])
    #print(tokens)

    entities = []
    new_sentence = ""
       
    preds = predictions[0].tolist()
    #print(preds)
    prev = False

    for i in range(len(tokens)):
        label = "[entity]"

        if preds[i] == 0 and not prev:
            entities.append(tokens[i])
            new_sentence = new_sentence + " " + label + " " + tokens[i]
            prev = True
        elif (preds[i] == 1 or tokens[i].startswith("##")) and prev:
            if tokens[i].startswith("##"):
                entities[len(entities)-1] = (entities[len(entities)-1] + tokens[i][2:])
                new_sentence = new_sentence + tokens[i][2:]
            else:
                entities[len(entities)-1] = (entities[len(entities)-1] + " " + tokens[i])
                new_sentence = new_sentence + " " + tokens[i]
        else:
            if prev:
                new_sentence = new_sentence + " " + label
            prev = False
            if tokens[i].startswith("##"):
                new_sentence = new_sentence + tokens[i][2:]
            else:
                new_sentence = new_sentence + " " + tokens[i]
            continue

    if entities == []:
        return entities

    new_sentence = new_sentence.strip().replace("[CLS]", "").replace("[SEP]", "").strip()

    variations = generate_variations(new_sentence)

    if variations == []:
        variations = new_sentence

    #print(new_sentence)

    #print(variations)

    classifier = TextClassificationPipeline(model=model_neg, tokenizer=tokenizer_neg)

    counter = 0;

    for sentence in variations:

        classification = classifier(sentence)

        #print(new_sentence)

        #print(classification)

        #print(entities)

        if "ABSENT" in str(classification):
            entities[counter] = "n_" + entities[counter].lower().replace(" ", "_")
            #entities = ["n_" + item.lower().replace(" ", "_") for item in entities]
        else:
            entities[counter] = entities[counter].lower().replace(" ", "_")
            #entities = [item.lower().replace(" ", "_") for item in entities]

        counter = counter + 1

    return entities

text = "Must not have any allergies, but has diabetes. Patient has no history of leukemia, but does have a history of glaucoma."

texts = split_into_sentences(text)

#print(texts)

extracted_entities = []
for text in texts:
    extracted_entities.extend(extract_entities(text))

print(extracted_entities)
