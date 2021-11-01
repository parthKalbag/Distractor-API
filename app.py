from flask import Flask, request
import nltk
from collections import OrderedDict
nltk.download('wordnet')
from nltk.corpus import wordnet as wn
import requests
from sense2vec import Sense2Vec
from summarizer import Summarizer

app = Flask(__name__)

model = Summarizer()
s2v = Sense2Vec().from_disk('s2v_old')
model_name = 'tuner007/pegasus_paraphrase'

def get_wordsense(word):
    word= word.lower()
      
    if len(word.split())>0:
        word = word.replace(" ","_")
    
      
    synsets = wn.synsets(word,'n')
    return synsets[0]
    

@app.route('/api/wordnet', methods=['POST'])
def get_distractors_wordnet():
    word = str(request.args.get('word'))
    syn = get_wordsense(word)
    distractors=[]
    word= word.lower()
    orig_word = word
    if len(word.split())>0:
        word = word.replace(" ","_")
    hypernym = syn.hypernyms()
    if len(hypernym) == 0: 
        return distractors
    for item in hypernym[0].hyponyms():
        name = item.lemmas()[0].name()
        if name == orig_word:
            continue
        name = name.replace("_"," ")
        name = " ".join(w.capitalize() for w in name.split())
        if name is not None and name not in distractors:
            distractors.append({"name": name})
    return {"distractors" : distractors}

@app.route('/api/conceptnet', methods=['POST'])
def get_distractors_conceptnet():
    word = request.args.get('word')
    word = word.lower()
    
    original_word= word
    if (len(word.split())>0):
        word = word.replace(" ","_")
    distractor_list = [] 
    url = "http://api.conceptnet.io/query?node=/c/en/%s/n&rel=/r/PartOf&start=/c/en/%s&limit=5"%(word,word)
    obj = requests.get(url).json()

    for edge in obj['edges']:
        link = edge['end']['term'] 

        url2 = "http://api.conceptnet.io/query?node=%s&rel=/r/PartOf&end=%s&limit=10"%(link,link)
        obj2 = requests.get(url2).json()
        for edge in obj2['edges']:
            word2 = edge['start']['label']
            if word2 not in distractor_list and original_word.lower() not in word2.lower():
                distractor_list.append({"name": word2})
                    
    return {"distractors" : distractor_list}

@app.route('/api/sense2vec', methods=['POST'])
def sense2vec_get_words():
    output = []
    word = request.args.get('word')
    word = word.lower()
    word = word.replace(" ", "_")

    sense = s2v.get_best_sense(word)
    most_similar = s2v.most_similar(sense, n=20)

    for each_word in most_similar:
        append_word = each_word[0].split("|")[0].replace("_", " ").lower()
        if append_word.lower() != word:
            output.append(append_word.title())

    out = list(OrderedDict.fromkeys(output))
    distractor_list = []

    for idx, distractor in enumerate(out):
        if idx == 2:
            return {"distractor": distractor}

@app.route('/api/summary', methods=['POST'])
def summary():
    text = request.args.get('text')
    result = model(text, min_length=60, max_length = 700 , ratio = 0.4)
    summarized_text = ''.join(result)

    return {"summary": summarized_text}

if __name__ == '__main__':
    app.run(port=5000)