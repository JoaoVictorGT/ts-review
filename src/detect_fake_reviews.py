import pandas as pd
import sys
from pathlib import Path

CURRENT_DIR = Path(__file__).resolve().parent

# Subir un nivel y entrar en data
DATA_DIR = CURRENT_DIR.parent / "data"

def load_csv():
    """
    Functions to load the data 
    """
    review_data = pd.read_csv(f"{DATA_DIR}/reviews.csv", sep=',')
    return review_data



if __name__=="__main__":
    review_data = load_csv()
    print(review_data)