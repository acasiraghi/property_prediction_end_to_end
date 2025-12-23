import os
from dotenv import load_dotenv
load_dotenv()
from pathlib import Path
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from metaflow import Runner

class Config(BaseModel):
    models: list[str]

class Data(BaseModel):
    rows:  list[dict]

class PayLoad(BaseModel):
    config: Config
    data: Data

app = FastAPI()

@app.post('/predict')
def run_pipeline(payload: PayLoad):
    # TODO: fix relative path with more robust Path object
    property_prediction_dir = Path(os.environ['PROPERTY_PREDICTION_DIR']) 
    with Runner(str(property_prediction_dir / 'property_prediction.py')).run(payload_json_string = payload.model_dump_json()) as running:
        if running.status != 'successful':
            # basic error handling: returns 500 on metaflow failure
            # may be extended to include run_id or other info in details if needed
            raise HTTPException(status_code = 500)
        else:
            results = running.run.data.results_json
    return results