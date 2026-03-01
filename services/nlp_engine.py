import spacy

class NLPEngine:
    def __init__(self, model_name="fr_core_news_md"):
        self.nlp = spacy.load(model_name)
    
    def analyze_text(self, text):
        return self.nlp(text)
