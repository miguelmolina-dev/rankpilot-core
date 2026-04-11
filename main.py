from fastapi import FastAPI

api = FastAPI(title="RankPilot API")

@api.get("/")
def read_root():
    return {"message": "Welcome to RankPilot API"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(api, host="0.0.0.0", port=8000)
