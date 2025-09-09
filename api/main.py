from fastapi import FastAPI
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
    with Runner('./pipeline/property_prediction.py').run(payload_json_string = payload.model_dump_json()) as running:
        # if running.status == 'failed':
        #     message = f'{running.run} failed:'
        # elif running.status == 'successful':
        #      message = f'{running.run} succeeded:'
        # print(f'{running.run} finished')
        results = running.run.data.results_json
    return results
    #return {'message': message}