from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def root():
    return {"message": "Railway Test - SUCCESS!"}

@app.get("/health")  
def health():
    return {"status": "healthy"}