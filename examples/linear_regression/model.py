import numpy as np
import pandas as pd
from sklearn.linear_model import LinearRegression

class LinearModel:
    def __init__(self, layer_args=None,):
        self.csv = layer_args["csv"]
        self.reg = None

    def train(self, args, ):
        df = pd.read_csv(self.csv, sep=';')

        x_cols = [
            "fixed acidity",
            "volatile acidity",
            "citric acid",
            "residual sugar",
            "chlorides",
            "free sulfur dioxide",
            "total sulfur dioxide",
            "density",
            "pH",
            "sulphates",
            "alcohol",
        ]

        
        y_cols = ["quality"]

        X = pd.DataFrame(df, columns=x_cols)
        y = pd.DataFrame(df, columns=y_cols)

        self.reg = LinearRegression().fit(X, y)
        print(self.reg.coef_)

        print(self.reg.intercept_)
        return self.reg.score(X, y)

    def predict(self, X):
        x_cols = [
            "fixed acidity",
            "volatile acidity",
            "citric acid",
            "residual sugar",
            "chlorides",
            "free sulfur dioxide",
            "total sulfur dioxide",
            "density",
            "pH",
            "sulphates",
            "alcohol",
        ]

        X = [X[key] for key in x_cols]

        return self.reg.predict([X]).tolist()
