from flask import Flask, request
import nltk
nltk.download('wordnet')
from nltk.corpus import wordnet as wn
import requests
app = Flask(__name__)

def get_wordsense(word):
    word= word.lower()
      
    if len(word.split())>0:
        word = word.replace(" ","_")
    
      
    synsets = wn.synsets(word,'n')
    return synsets[0]
    

@app.route('/api/wordnet', methods=['POST'])
def get_distractors_wordnet():
    word = str(request.args.get('word'))
    print(word)
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