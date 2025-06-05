from dotenv import load_dotenv

from cp_server.config import ROOT

# Load environment variables from .env file
load_dotenv(ROOT.joinpath(".env"))