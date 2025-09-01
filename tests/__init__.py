import os
import sys

PROJECT_PATH = os.getcwd()
SOURCE_PATH = os.path.join(PROJECT_PATH, "src/bulle_planning_model")
sys.path.append(SOURCE_PATH)

BACKEND_PATH = os.path.join(PROJECT_PATH, "src/bulle_planning_model")
os.chdir(BACKEND_PATH)
