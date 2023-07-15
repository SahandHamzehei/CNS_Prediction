import time
import pandas as pd
import numpy as np
import pmdarima as pm
from sklearn.metrics import (
    mean_squared_error,
    r2_score,
    explained_variance_score,
    mean_absolute_error,
    median_absolute_error,
)



class ARIMAForecaster:
    """
    A class used to forecast CNS deaths using the ARIMA model.
    """

    def __init__(self, excel_file):
        """
        Initializes the ARIMAForecaster with the given Excel file.

        :param excel_file: str, path to the Excel file containing the data.
        """
        self.excel_data = pd.read_excel(excel_file, sheet_name=None)
        self.combined_data = self.prepare_data()

    def prepare_data(self):
        """
        Combines the data from all sheets in the Excel file into a single DataFrame.

        :return: DataFrame, combined data from all sheets.
        """
        data_frames = [
            df.assign(year=int(sheet_name))
            for sheet_name, df in self.excel_data.items()
        ]
        combined_data = pd.concat(data_frames)
        return combined_data

    def split_data(self, train_year=2018, test_year=2019):
        """
        Splits the combined data into training and testing sets based on the provided years.

        :param train_year: int, last year to be included in the training set (inclusive).
        :param test_year: int, year for the testing set.
        """
        self.train_data = self.combined_data[self.combined_data["year"] <= train_year]
        self.test_data = self.combined_data[self.combined_data["year"] == test_year]

    def predict_arima(self, city_data):
        """
        Trains an ARIMA model on the given city data and returns the prediction for the next period.

        :param city_data: DataFrame, data for a specific city.
        :return: float, prediction for the next period.
        """
        city_data = city_data.reset_index(drop=True)
        temp_index = pd.date_range(start="2000-01-01", periods=len(city_data), freq="A")
        city_data = city_data.set_index(temp_index)

        model = pm.auto_arima(
            city_data["cns deaths"],
            seasonal=False,
            stepwise=True,
            suppress_warnings=True,
            trace=False,
            error_action="ignore",
            information_criterion="aic",
        )

        forecast, conf_int = model.predict(n_periods=1, return_conf_int=True)
        return forecast[0]

    def train_and_evaluate(self):
        """
        Trains the ARIMA model for each city in the dataset and evaluates the performance using various metrics.
        """
        predictions = []
        start_time = time.time()
        for comune in self.combined_data["comune"].unique():
            city_train_data = self.train_data[self.train_data["comune"] == comune]
            city_test_data = self.test_data[self.test_data["comune"] == comune]

            if not city_train_data.empty and not city_test_data.empty:
                prediction = self.predict_arima(city_train_data)
                predictions.append(
                    (comune, prediction, city_test_data.iloc[0]["cns deaths"])
                )

        end_time = time.time()
        self.total_time = end_time - start_time
        self.predictions = predictions
        self.calculate_evaluation_metrics(predictions)

    def calculate_evaluation_metrics(self, predictions):
        """
        Calculates evaluation metrics for the ARIMA model predictions.

        :param predictions: list, tuples containing (city, predicted_value, true_value).
        """
        y_true = [p[2] for p in predictions]
        y_pred = [p[1] for p in predictions]

        self.mse = mean_squared_error(y_true, y_pred)
        self.rmse = np.sqrt(self.mse)
        self.r2 = r2_score(y_true, y_pred)
        self.evs = explained_variance_score(y_true, y_pred)
        self.mae = mean_absolute_error(y_true, y_pred)
        self.medae = median_absolute_error(y_true, y_pred)

    def predict_upcoming_year(self, year=2020):
        """
        Predicts the CNS deaths for each city for the given year using the ARIMA model.

        :param year: int, year for which predictions should be made (default: 2020).
        """
        upcoming_year_data = self.combined_data[self.combined_data["year"] == year]
        predictions_upcoming_year = []
        for comune in self.combined_data["comune"].unique():
            city_train_data = self.combined_data[self.combined_data["comune"] == comune]

            if not city_train_data.empty:
                prediction = self.predict_arima(city_train_data)
                predictions_upcoming_year.append((comune, prediction))

        self.save_predictions(predictions_upcoming_year)

    def save_predictions(self, predictions):
        """
        Saves the predictions to a CSV file.

        :param predictions: list, tuples containing (city, predicted_value).
        """
        predictions_df = pd.DataFrame(
            predictions, columns=["comune", "predicted_cns_deaths"]
        )
        predictions_df.to_csv("cns_deaths_predictions_ARIMA.csv", index=False)

    def print_evaluation_metrics(self):
        """
        Prints the evaluation metrics for the ARIMA model.
        """
        print("Mean Squared Error:", self.mse)
        print("Root Mean Squared Error:", self.rmse)
        print("R2 Score:", self.r2)
        print("Explained Variance Score:", self.evs)
        print("Mean Absolute Error:", self.mae)
        print("Median Absolute Error:", self.medae)
        print("Time taken to train the model:", self.total_time, "seconds")


# Usage
forecaster = ARIMAForecaster("main_data_cities_V2.xlsx")
forecaster.split_data()
forecaster.train_and_evaluate()
forecaster.predict_upcoming_year()
forecaster.print_evaluation_metrics()
