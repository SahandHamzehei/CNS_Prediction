import time
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import xgboost as xgb
from sklearn.metrics import (
    mean_squared_error,
    r2_score,
    explained_variance_score,
    mean_absolute_error,
    median_absolute_error,
)
from sklearn.model_selection import train_test_split, GridSearchCV
from sklearn.preprocessing import LabelEncoder



class XGBoostForecaster:
    """
    A class that represents an XGBoost forecaster for predicting CNS deaths.
    """

    def __init__(self, excel_file):
        """
        Initialize the XGBoostForecaster with the given excel file.
        """
        self.sheets_dict = pd.read_excel(excel_file, sheet_name=None)
        self.data = self.prepare_data()
        self.le = LabelEncoder()
        self.data["comune"] = self.le.fit_transform(self.data["comune"])

    def prepare_data(self):
        """
        Prepare the data by concatenating all sheets in the excel file, adding a year column, and rearranging columns.
        """
        data = pd.concat(self.sheets_dict.values(), ignore_index=True)
        data["year"] = data.index // 107
        data = data[["year", "comune", "PM2.5", "PM10", "cns deaths"]]
        return data

    def split_data(self):
        """
        Split the data into train and test sets based on the year.
        """
        self.train_data = self.data[self.data["year"] < 10]
        self.test_data = self.data[self.data["year"] == 10]
        self.X_train = self.train_data[["year", "comune", "PM2.5", "PM10"]]
        self.y_train = self.train_data["cns deaths"]
        self.X_test = self.test_data[["year", "comune", "PM2.5", "PM10"]]
        self.y_test = self.test_data["cns deaths"]

    def train(self):
        """
        Train the XGBoost model using grid search.
        """
        param_grid = {
            "n_estimators": [50, 100, 150, 200],
            "learning_rate": [0.01, 0.05, 0.1, 0.2],
            "max_depth": [2, 3, 4, 5],
            "subsample": [0.7, 0.8, 0.9, 1.0],
            "colsample_bytree": [0.7, 0.8, 0.9, 1.0],
        }

        xgb_model = xgb.XGBRegressor(objective="reg:squarederror", random_state=42)

        grid_search = GridSearchCV(
            estimator=xgb_model,
            param_grid=param_grid,
            cv=5,
            scoring="neg_mean_squared_error",
            verbose=1,
            n_jobs=-1,
        )

        start_time = time.time()

        grid_search.fit(self.X_train, self.y_train)

        self.training_time = time.time() - start_time

        best_params = grid_search.best_params_
        print("Best parameters found: ", best_params)

        self.best_xgb_model = xgb.XGBRegressor(
            objective="reg:squarederror", random_state=42, **best_params
        )

        self.best_xgb_model.fit(self.X_train, self.y_train)

    def predict(self):
        """
        Predict the test data using the trained XGBoost model.
        """
        self.y_pred = self.best_xgb_model.predict(self.X_test)
        self.y_pred = pd.DataFrame(self.y_pred)

    def evaluate(self):
        """
        Evaluate the performance of the XGBoost model.
        """
        self.mse = mean_squared_error(self.y_test, self.y_pred)
        self.rmse = np.sqrt(self.mse)
        self.r2 = r2_score(self.y_test, self.y_pred)
        self.evs = explained_variance_score(self.y_test, self.y_pred)
        self.mae = mean_absolute_error(self.y_test, self.y_pred)
        self.medae = median_absolute_error(self.y_test, self.y_pred)

    def save_predictions(self):
        """
        Save the predictions to a CSV file.
        """
        self.y_pred.to_csv("predictions.csv", index=False)

    def print_evaluation_metrics(self):
        """
        Print the evaluation metrics for the XGBoost model.
        """
        print("Mean Squared Error:", self.mse)
        print("Root Mean Squared Error:", self.rmse)
        print("R2 Score:", self.r2)
        print("Explained Variance Score:", self.evs)
        print("Mean Absolute Error:", self.mae)
        print("Median Absolute Error:", self.medae)
        print("Time to fit the XGBoost model:", self.training_time)


# Usage
forecaster = XGBoostForecaster("main_data_cities_V2.xlsx")
forecaster.split_data()
forecaster.train()
forecaster.predict()
forecaster.evaluate()
forecaster.save_predictions()
forecaster.print_evaluation_metrics()
