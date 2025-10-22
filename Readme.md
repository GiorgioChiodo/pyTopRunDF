# pyTopRunDF

A model to simulate the potential deposition of a debris flow.

## Features

-   Monte Carlo simulation for deposition modeling.
-   Hillshade generation from DEM data.
-   Dockerized environment for consistent execution.

## Requirements

-   Python 3.8 or higher
-   pip (Python package manager)

## How to Run

### Step 1: Clone the Repository

First, clone this repository to your local machine:

``` bash
git clone <https://github.com/schidli/pyTopRunDF.git>

cd pyTopRunDF
```

### Step 2: Create a Virtual Environment

Create a virtual environment to isolate the dependencies:

``` bash
python -m venv pytoprundf
```

Activate the virtual environment

-   on Windows:

``` bash
pytoprundf\Scripts\activate
```

-   on MacOS/Linux:

``` bash
source pytoprundf\Scripts\activate
```

### Step 3: Install Dependencies

Install the required Python packages using the requirements.txt file:

``` bash
pip install -r requirements.txt
```

### Step 4: Run the Script

Run the main script:

``` bash
python TopRunDF.py
```

### Step 5: View the Results

The script will generate output files (e.g., depo.asc) and display a plot of the results. Check the output directory for the generated files.

Project Structure:

```         
TopRunDF.py: Main script for the simulation.
RandomSingleFlow.py: External Python file for random walk logic.
input.csv: Input data file.
requirements.txt: Python dependencies.
/DEM/topofan.asc: Input digital terrain model (DTM)
```
