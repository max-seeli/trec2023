# trec2023
Submission for [TREC (Text Retrieval Conference) Clinical Trials 2023](http://trec-cds.org/2023.html)

## Installation

Download the clinical trial data from the [TREC CDS 2023 Website](http://trec-cds.org/2023.html) and place it in the `data/clinical_trials/raw` folder.
You can use the following script to download the data (takes a few minutes: ~2GB):
  
```bash
bash setup.sh
```

To setup the python environment including the parser from [WojciechKusa/clinical-trials](https://github.com/WojciechKusa/clinical-trials/) you need `gcc` installed (for python-terrier):

Conda:
```bash
conda env create -f environment.yml
conda activate trec2023
```  

Pip:
```bash
pip install -r requirements.txt
```

Either way you need to download the spaCy model for the trial preprocessing:
```bash
python -m spacy download en_core_web_sm
```

Finally to be able to use python-terrier you also need a Java Development Kit (JDK) installed.

# Approaches:

## 1. LLM topic enrichment with two stage lexical retrieval and neural reranking

For this approach we took the provided [topics](http://trec-cds.org/topics2023.xml) containing information about conditions and medications as well as more general information about the patients and enriched their representation using ChatGPT to the format previously used in [TREC CT 2021](http://trec-cds.org/2021.html) and [TREC CT 2022](http://trec-cds.org/2022.html).

Example patient representation from 2022 topics:
```xml
<topics task="2022 TREC Clinical Trials">
  <topic number="-1">
    A 2-year-old boy is brought to the emergency department by his parents for 5 days of high fever
    and irritability. The physical exam reveals conjunctivitis, strawberry tongue, inflammation of
    the hands and feet, desquamation of the skin of the fingers and toes, and cervical
    lymphadenopathy with the smallest node at 1.5 cm. The abdominal exam demonstrates tenderness
    and enlarged liver. Laboratory tests report elevated alanine aminotransferase, white blood cell
    count of 17,580/mm, albumin 2.1 g/dL, C-reactive protein 4.5 mg, erythrocyte sedimentation rate
    60 mm/h, mild normochromic, normocytic anemia, and leukocytes in urine of 20/mL with no bacteria
    identified. The echocardiogram shows moderate dilation of the coronary arteries with possible
    coronary artery aneurysm.
  </topic>
</topics>
```


Example patient representation from 2023 topics:
```xml
<topics task="2023 TREC Clinical Trials">
<topic number="1" template="glaucoma">
    <field name="definitive diagnosis">primary open angle glaucoma</field>
    <field name="intraocular pressure"/>
    <field name="visual field">moderate field damage</field>
    <field name="visual acuity">0.3</field>
    <field name="prior cataract surgery">no</field>
    <field name="prior LASIK surgery">no</field>
    <field name="comorbid ocular diseases">corneal edema</field>
  </topic>
</topics>
```

Example enriched patient representation:
```xml
<topics task="2023 TREC Clinical Trials">
    <topic number="1">
        Patient has been diagnosed with primary open angle glaucoma. The patient's intraocular pressure is a concern and needs monitoring. There is moderate damage observed in the patient's visual field. The visual acuity is recorded at 0.3. The patient has not undergone prior cataract surgery or LASIK surgery. The presence of corneal edema, along with glaucoma, suggests comorbid ocular diseases. The definitive diagnosis is primary open angle glaucoma, and the patient's ocular health requires close attention due to the combination of factors mentioned.
    </topic>
</topics>
```

For the enrichment the following query was used:
```
Please consider this kind of format:

<topic number="40" template="type 2 diabetes">
<field name="definitive diagnosis">yes</field>
<field name="HbA1c">6.3</field>
<field name="glucose">115 fasting blood sugar</field>
<field name="BMI">40</field>
<field name="insulin">no</field>
<field name="metformin">8.5 mL</field>
<field name="other anti-diabetic drugs">no</field>
<field name="diet restrictions">low-calorie</field>
<field name="exercise">no</field>
<field name="ketoacidosis history"/>
<field name="comorbidities">chronic kidney disease</field>
<field name="hospitalization events">never</field>
</topic>

Please convert this into free text. Take this style as an example:

Patient is a 45-year-old man with a history of anaplastic astrocytoma of the spine complicated by severe lower extremity weakness and urinary retention s/p Foley catheter, high-dose steroids, hypertension, and chronic pain. The tumor is located in the T-L spine, unresectable anaplastic astrocytoma s/p radiation. Complicated by progressive lower extremity weakness and urinary retention. Patient initially presented with RLE weakness where his right knee gave out with difficulty walking and right anterior thigh numbness. MRI showed a spinal cord conus mass which was biopsied and found to be anaplastic astrocytoma. Therapy included field radiation t10-l1 followed by 11 cycles of temozolomide 7 days on and 7 days off. This was followed by CPT-11 Weekly x4 with Avastin Q2 weeks/ 2 weeks rest and repeat cycle. 

Do NOT by any terms make up information. Try to stay short.
If the patient's age and gender are not given in the xml format, stay neutral and do not make up age or gender.
```

With the enriched topics we used the approach described in the paper [Effective matching of patients to clinical trials using entity extraction and neural re-ranking](https://www.sciencedirect.com/science/article/pii/S153204642300165X) of Wojciech Kusa et al. 

## 2. Two stage lexical retrieval with model based feature extraction preprocessing

In this approach we used the representation of this years topics directly. In the topics there is a field called __template__ giving a broad overview about the general condition of the patient. With this keyword we pre-selected 2000 trials for each of the 8 different __templates__. 

In the next step we used a combination of BioBERT ([BioBERT-Chemical](https://huggingface.co/alvaroalon2/biobert_chemical_ner) and [BioBERT-Diseases](https://huggingface.co/alvaroalon2/biobert_diseases_ner)), a [negation model](https://huggingface.co/bvanaken/clinical-assertion-negation-bert) spezialized in the medical domain.

Using this we are able to preprocess the trials by extracting features and especially negations from their criteria section.

In the last step we used a lexical retrieval approach to rank the trials based on the preprocessed criteria section.

