import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import r2_score, mean_absolute_error
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent.resolve()))


from core.config import DATA_DIR
import pickle
import asyncio
from core.backend.analyzers import v1

async def main():
    with open(DATA_DIR / 'boston_housing_dataset.pkl', 'rb') as rf:
        data_dict = pickle.load(rf)


    data = data_dict['data']
    metadata = data_dict['metadata']

    # === Separate features and target ===
    X = data.drop(columns=['MEDV'])
    y = data['MEDV']

    # === Train/test split ===
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    # === Fit a baseline model ===
    model = RandomForestRegressor(random_state=42, n_estimators=200)
    model.fit(X_train, y_train)

    await v1(
        project_desc='The project is to do housing price prediction',
        model=model,
        data=data,
        metadata=metadata
    )

if __name__ == '__main__':
    asyncio.run(main())