import requests

def fetch_prediction(data):
    return requests.post("http://localhost:5000/api/predict", json=data).json()