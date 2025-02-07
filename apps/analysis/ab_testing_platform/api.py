from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
import os
import simplejson as json
import numpy as np
import pandas as pd

from ab_testing_platform.pipeline import run_experiment
from ab_testing_platform.lib.utils import parse_group_buckets


async def on_fetch(request, env):
    import asgi

    return await asgi.fetch(app, request, env)


app = FastAPI()

app.mount("/static", StaticFiles(directory="static"), name="static")


@app.get("/", response_class=HTMLResponse)
async def serve_html():
    with open(os.path.join("static", "index.html")) as file:
        html_content = file.read()
    return HTMLResponse(content=html_content, status_code=200)


@app.get("/render-image")
def render_image(file_path: str):
    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")
    return FileResponse(
        file_path, media_type="image/png", filename=os.path.basename(file_path)
    )


@app.post("/run-test/")
async def run_ab_test_api(
    file: UploadFile = File(...),
    test_type: str = Form(...), 
    sequential: bool = Form(False),
    stopping_threshold: float = Form(None)
):
    data = await file.read()
    try:
        user_data = json.loads(data)
    except json.JSONDecodeError:
        return {"error": "Invalid JSON data"}

    # TODO: Bring group buckets into the form
    group_buckets = parse_group_buckets("control:0-50,test1:50-100")
    # TODO: Allow the user to specify alpha, prior_successes, and prior_trials
    test_result = run_experiment(
        user_data=user_data,
        group_buckets=group_buckets,
        method=test_type,
        sequential=sequential,
        stopping_threshold=stopping_threshold
    )

    def convert_to_serializable(obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, pd.DataFrame):
            return obj.to_dict(orient="records")
        elif isinstance(obj, bytes):
            return obj.decode("utf-8")
        elif isinstance(obj, np.bool_):
            return bool(obj)
        elif isinstance(obj, float):
            if np.isnan(obj) or np.isinf(obj):
                return str(obj)
        raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

    test_result_serializable = json.loads(
        json.dumps(test_result, default=convert_to_serializable, ignore_nan=True)
    )

    return JSONResponse(content={"result": test_result_serializable}, status_code=200)
