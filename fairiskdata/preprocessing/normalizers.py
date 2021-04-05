class Normalizers:
    def __init__(self):
        self.min_max_scalers = {}

    def min_max(self, v, min, max):
        return (v - min) / (max - min)

    def get_scalers(self, dataset: dict, entity: str):
        for country_key in dataset.keys():
            if entity in dataset[country_key].keys():
                for score_key in dataset[country_key][entity].keys():

                    # Initialize new score entry
                    if score_key not in self.min_max_scalers.keys():
                        self.min_max_scalers[score_key] = [float('inf'), float('-inf')]

                    if isinstance(dataset[country_key][entity][score_key]["VALUE"][0], float):
                        # Update the maximum value
                        if dataset[country_key][entity][score_key]["VALUE"].values[0] > self.min_max_scalers[score_key][1]:
                            self.min_max_scalers[score_key][1] = dataset[country_key][entity][score_key]["VALUE"].values[0]
                        # Update the minimum value
                        if dataset[country_key][entity][score_key]["VALUE"].values[0] < self.min_max_scalers[score_key][0]:
                            self.min_max_scalers[score_key][0] = dataset[country_key][entity][score_key]["VALUE"].values[0]

        return self.min_max_scalers

    def min_max_scaler_scores(self, dataset: dict):
        subgroup = "SCORES"
        scales = self.get_scalers(dataset, subgroup)

        if len(dataset.keys()) >= 2:  # Normalization does only make sense with at least 2 countries
            for i, country_key in enumerate(dataset.keys()):
                if "SCORES" in list(dataset[country_key].keys()):
                    for score_key in list(dataset[country_key][subgroup]):
                        if isinstance(dataset[country_key][subgroup][score_key]["VALUE"][0], float):
                            dataset[country_key][subgroup][score_key]["VALUE"][0] = self.min_max(
                                dataset[country_key][subgroup][score_key]["VALUE"][0],
                                scales[score_key][0],
                                scales[score_key][1]
                            )
                            dataset[country_key][subgroup][score_key]["ATTR_NAME"] = \
                                "Normalized " + dataset[country_key][subgroup][score_key]["ATTR_NAME"]
                            dataset[country_key][subgroup][score_key]["UNIT"] = \
                                "Normalized " + dataset[country_key][subgroup][score_key]["UNIT"]

                            if score_key in ["CON_HIIK_NP", "CON_HIIK_SN", "MPI", "GII", "GINI"]:
                                dataset[country_key][subgroup][score_key]["VALUE"][0] = 1 - dataset[country_key][subgroup][
                                    score_key]["VALUE"][0]

        return dataset

    def min_max_scaler_indicators(self, dataset: dict):
        subgroup = "INDICATORS"
        scales = self.get_scalers(dataset, subgroup)

        if len(dataset.keys()) >= 2:    # Normalization does only make sense with at least 2 countries
            for i, country_key in enumerate(dataset.keys()):
                if subgroup in list(dataset[country_key].keys()):
                    for score_key in list(dataset[country_key][subgroup]):
                        if isinstance(dataset[country_key][subgroup][score_key]["VALUE"][0], float):
                            dataset[country_key][subgroup][score_key]["VALUE"][0] = self.min_max(
                                dataset[country_key][subgroup][score_key]["VALUE"][0],
                                scales[score_key][0],
                                scales[score_key][1]
                            )
                            dataset[country_key][subgroup][score_key]["ATTR_NAME"] = \
                                "Normalized " + dataset[country_key][subgroup][score_key]["ATTR_NAME"]
                            dataset[country_key][subgroup][score_key]["UNIT"] = \
                                "Normalized " + dataset[country_key][subgroup][score_key]["UNIT"]

        return dataset
