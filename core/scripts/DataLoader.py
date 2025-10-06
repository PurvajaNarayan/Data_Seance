import re
import requests
import pandas as pd
import pickle 
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.parent.resolve()))

from core.config import DATA_DIR

if __name__ == '__main__':
    URL = "https://lib.stat.cmu.edu/datasets/boston"

    # 1) Fetch raw text from StatLib
    resp = requests.get(URL, timeout=30)
    resp.raise_for_status()
    text = resp.text

    # 2) Parse numbers only (the file has a prose header; data are numeric-only lines)
    num_lines = []
    for line in text.splitlines():
        tokens = line.strip().split()
        # keep the line if ALL tokens look like numbers (ints/floats/scientific)
        if tokens and all(re.match(r"^[+-]?(\d+(\.\d*)?|\.\d+)([eE][+-]?\d+)?$", t) for t in tokens):
            num_lines.append(line)

    # Flatten all numbers in order, then reshape into 14 columns (506 rows x 14 features/target)
    nums = []
    for line in num_lines:
        nums.extend([float(t) for t in line.split()])

    if len(nums) % 14 != 0:
        raise ValueError(f"Unexpected data length {len(nums)}; not divisible by 14.")

    data = pd.DataFrame(
        [nums[i:i+14] for i in range(0, len(nums), 14)],
        columns=[
            "CRIM", "ZN", "INDUS", "CHAS", "NOX", "RM", "AGE",
            "DIS", "RAD", "TAX", "PTRATIO", "B", "LSTAT", "MEDV"
        ]
    )

    # 3) Column metadata (from the StatLib/Delve descriptions)
    metadata = {
        "CRIM":   "per capita crime rate by town",
        "ZN":     "proportion of residential land zoned for lots over 25,000 sq.ft.",
        "INDUS":  "proportion of non-retail business acres per town",
        "CHAS":   "Charles River dummy (1 if tract bounds river; 0 otherwise)",
        "NOX":    "nitric oxides concentration (parts per 10 million)",
        "RM":     "average number of rooms per dwelling",
        "AGE":    "proportion of owner-occupied units built prior to 1940",
        "DIS":    "weighted distances to five Boston employment centres",
        "RAD":    "index of accessibility to radial highways",
        "TAX":    "full-value property-tax rate per $10,000",
        "PTRATIO":"pupil–teacher ratio by town",
        "B":      "1000*(Bk - 0.63)^2 where Bk is proportion of people of African American descent",
        "LSTAT":  "% lower status of the population",
        "MEDV":   "Median value of owner-occupied homes in $1000's (target)"
    }


    data_dict = {
        'data' : data,
        'metadata' : metadata
    }

    with open(DATA_DIR / 'boston_housing_dataset.pkl', 'wb') as wf:
        pickle.dump(data_dict, wf)
