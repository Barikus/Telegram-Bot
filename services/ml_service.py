# services/ml_service.py
from sklearn.svm import LinearSVC
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import json
import logging
from pathlib import Path
from typing import Tuple

logger = logging.getLogger(__name__)

class MLService:
    def __init__(self):
        self.vectorizer = TfidfVectorizer(analyzer='char', ngram_range=(3, 3))
        self.clf = LinearSVC(dual=False, random_state=42)
        self._load_data()

    def _load_data(self):
        try:
            data_path = Path(__file__).parent.parent / "data" / "intents.json"
            with open(data_path, 'r', encoding='utf-8') as f:
                data = json.load(f)

            X = []
            y = []
            for intent, examples in data.items():
                X.extend(examples)
                y.extend([intent] * len(examples))

            self.X = self.vectorizer.fit_transform(X)
            self.clf.fit(self.X, y)
            logger.info("ML model loaded successfully")
        except Exception as e:
            logger.error(f"Failed to load ML model: {e}")
            raise

    def predict_intent(self, text: str) -> Tuple[str, float]:
        try:
            vec = self.vectorizer.transform([text])
            decision = self.clf.decision_function(vec)
            confidence = np.max(decision)
            intent = self.clf.predict(vec)[0]
            return intent, float(confidence)
        except Exception as e:
            logger.error(f"Prediction error: {e}")
            return "unknown", 0.0

ml_service = MLService()