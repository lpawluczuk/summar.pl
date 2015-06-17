# summar.pl

Summar is an automatic summarization system developed for the Polish language. The system implements trainable sentence-based extractive summarization technique, which consists in determining most important sentences in document due to their computed salience. Neural networks were used as a machine learning algorithm (Pybrain library, as well as FANN were used).

The system was implemented during work on Master Thesis's in computer science at Feculty of Mathematics and Computer Science, Adam Mickiewicz University. For more innformation and demonstration, see http://summar.pl

More info, as well as simple usage will be added soon.

## summar features

* Automatic Summarization Library written in Python
* corpus-based training using PyBrain or FANN (Fast Artificial Neural Network Library)
* three running modes: summarization, training, evaluation
* uses NERf as a Named Entity Recognition too (see: http://zil.ipipan.waw.pl/Nerf)

## Dependencies

* apt-get install gfortran libopenblas-dev liblapack-dev
* pip install enum34, scipy
* PyBrain (see: http://pybrain.org/docs/)
* FANN (see: http://leenissen.dk/fann/wp/help/installing-fann/)
* FANN Python binding (see: https://github.com/FutureLinkCorporation/fann2)
* PSI-Toolkit (see: http://psi-toolkit.amu.edu.pl/)

## Usage

To run summar 3 files need to be provided: config.ini, used features list and model (model file is not needed during training).  

### Configuration file

```
[General
stoplist = {PATH_TO_STOPLIST FILE}
modeltype = {NN, FANN, Random, First}
length = {SHORT, LONG, MEDIUM}

[Train
trainmethod = {NN, FANN}
dirprocessor = {Wide, Ratio}
dirprocessoroption = {float number}

[Eval
evalmethod = {Strict, Wide}
```

### Features

Example of features file:
```
Feature.TfIdf
Feature.SentInHighestTitle
Feature.SentLength
Feature.SentLocPara
```

**Features list:**
* TfIdf - sum of term frequency -- inverse document frequency value for every word in sentence
* Centrality -arithmetic average of the sentence's similarity to all other sentences in the document 
* SentLocPara - position of a sentence in the paragraph: in the first, second or third of equal parts
* ParaLocSection - position of the paragraph in the document: in the first, second or third of equal parts
* SentSpecialSection - occurrence in a special section such as the beginning (introduction) or ending (conclusion) of document
* Verb - existence of the final verb
* Nouns - number of nouns in sentence
* Pronouns - number of pronouns in sentence    
* SentInHighestPname --- number of Named Entities in the sentence as found by a naive method, recognizing Named Entity as a word starting with capital letter
* NER - number of Named Entities in the sentence as found by NERf Named Entities Recognition tool
* NERTf - sum of each Named Entity frequency in the whole document, occurring in given sentence 
* PersNameNE - number of recognized NE of the "person" type
* OrgNameNE - number of recognized NE of the "organization" type
* PlaceNameNE - number of recognized NE of the "place" type
* DateNE - number of recognized NE of the "date" type
* GeogNameNE  - number of recognized NE of the "geography" type
* TimeNE - number of recognized NE of the "time" type
* SentInHighestTitle - number of words from heading or title in the sentence
* ParaLength -paragraph length: short (up to 1 sentence), average (2--5 sentences) or long (more than 5 sentences)
* SentLength - sentence length: short (up to 7 words), average (7--14 words) or long (more than 14 words)
* AvWordLength - the average of words lengths in sentencse
* SentType - type of the sentences, based on its last punctuation mark: declarative, interrogative or imperative
* MetaInfo - sentences not referring to the document content, i.e.: an information about document's author or photo signatures

### Running

usage: main.py [-h] -r {sum,train,eval} [-f FILE] [-a DIR] [-m MODEL]
               [-g FEATURES] [-t TRAIN_DIR] [-y TEST_DIR] [-z CONFIG]

**Running in summary mode:**

To run in summary mode the following parameters are needed:
* -r sum
* -f - input file
* -m - model file
* -g - features file (must be the same list of features, which was used to train given model file)
* -z - config file (also compatible with model)

**Running in training mode:**

To run in summary mode the following parameters are needed:
* -r train
* -a - input directory with train files (library can read only Polish Summaries Corpus files format (see: http://zil.ipipan.waw.pl/PolishSummariesCorpus))
* -g - features file
* -z - config file


**Running in evaluation mode:**

To run in summary mode the following parameters are needed:
* -r eval
* -m - model file
* -g - features file (must be the same list of features, which was used to train given model file)
* -z - config file (also compatible with model)
* -y - test directory (Polish Summaries Corpus again)
