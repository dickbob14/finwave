from fastapi import FastAPI
app = FastAPI()

@app.get("/")
def ping():
	return {"status": "FinWave Day-0 up!"}
