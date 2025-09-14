import os

import dotenv
dotenv.load_dotenv()


api_key = os.getenv("OPENAI_API_KEY")
PORT = os.getenv("PORT")
