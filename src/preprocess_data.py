import pandas as pd
import sys
from pathlib import Path
from detect_fake_reviews import load_csv




if __name__ == "__main__":
    review_booking = load_csv()
    print(review_booking)


    