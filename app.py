import sys
import os

# Add the src/app directory to the system path to allow importing its modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src', 'app'))

# Execute the main streamlit app logic
if __name__ == '__main__':
    os.system('streamlit run src/app/main.py --server.port=7860 --server.address=0.0.0.0')
