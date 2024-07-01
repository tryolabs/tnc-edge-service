# Notebooks

The notebooks in this repository are used to perform the analysis and create the visualizations for the evaluations in section 3 of the report.

## Description

This repository contains Jupyter notebooks used for various analyses and visualizations related to the project evaluations.  The data is primarily read using `awswrangler` from its previous location in an S3 bucket within the ProductOps AWS account. These paths will need to be updated to reflect the new data locations.

### Directory Structure

- `/data/`: Contains CSV files used in some of the notebooks.
- `/helper_functions/`: Contains `.py` scripts with helper functions for data reading and transformations.
- `/models/`: Contains saved models used in the analysis.

### Prerequisites

These notebooks read in data from the previous location in the productOps AWS account. The notebooks will require updating the data paths to reflect the new data locations. No additional installations are required for the helper functions as they are included in the repository.

## Notebooks Overview


- **`edge_integration_charts.ipynb`**: Creates the waffle charts for Evaluation 4, "Edge Integration".
- **`elog_analysis.ipynb`**: Used for the analysis in Evaluation 12, "eLog-Based Prioritization" and Evaluation 11, "eLog Use Behavior".
- **`key_event_detection.ipynb`**: used for the analysis in Evaluation 10, "Key Event Detections". Reads in the model saved in the `notebooks/models/` directory and uses reviewer notes from `notebooks/data/`.
- **`timeseries_classifier_model.ipynb`**: Trains and evaluates several timeseries classifier models, then saves the best one in the `notebooks/models/` directory.
- **`catchcount_vector.ipynb`**: Analyzes the catch count vector for Evaluation 7, "Catch Count Vector".
- **`tnc-edge-catch-plots.ipynb`**: Explores catch counts (not used for any evaluation).
- **`tnc-edge-data-integration.ipynb`**: Used for Evaluation 4, "Edge Integration", and produces the data file used by `edge_integration_charts.ipynb`.
- **`tnc-edge-gps-speed.ipynb`**: Explores GPS data and produces speed and headings (not used in the evaluations).
- **`tnc-edge-network-uptime.ipynb`**: Used for the analysis of Evaluation 2, "Onboard Network".
- **`tnc-edge-ondeck-ops-df.ipynb`**: Exploratory notebook that queries all Ondeck metadata from AWS Athena.
- **`tnc-edge-system-uptime.ipynb`**: Used for the analysis of Evaluation 1, "EM Systems".
- **`tnc-edge-vectorprocessing.ipynb`**: Used for the analysis of Evaluation 6, "Process Vectors".
- **`tnc_edge_bv_excel_parsing.ipynb`**: Creates the Athena tables from the Excel trip data files provided by BV.

### Usage Instructions

1. **Data Access**: Ensure the data paths in the notebooks are updated to reflect the new locations if the data is no longer in the original S3 bucket.
2. **Helper Functions**: The `elog_analysis.ipynb`, `key_event_detection.ipynb`, `catchcount_vector.ipynb`, and `timeseries_classifier_model.ipynb` notebooks use helper functions from the `helper_functions` directory for data reading and transformations.

