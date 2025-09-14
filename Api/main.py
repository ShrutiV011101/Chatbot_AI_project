import uvicorn
from fastapi.routing import Mount
from fastapi.staticfiles import StaticFiles
from fastapi import FastAPI
from app.Routes.chatRoutes import chatRouter
from fastapi.middleware.cors import CORSMiddleware
from app.extractEnvVariables import PORT

    
# FastAPI app
app = FastAPI(
    title="Chatbot API",
    routes=[Mount("/static", app=StaticFiles(directory="./static"), name="static")]
)
        

# Include router
app.include_router(chatRouter)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=int(PORT), reload=True)