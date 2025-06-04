#
## Installations
Ensure all of the following are installed before setting up the application (UPDATE WHEN BACKEND IS ADDED):
- Node.js (and npm)
- Python
- Git

## Setup Instructions
1. Clone the repository:
```bash
git clone https://github.com/dcgnecco/trolley-tracker-revamp.git
cd trolley-tracker-revamp
```
2. Install backend dependencies in the backend folder (UPDATE WHEN BACKEND IS ADDED, virtual python env?):
```bash
cd backend
pip install -r requirements.txt
```
3. Run the backend (while in the backend folder):
```bash
python main.py
```
4. Install frontend dependencies in the frontend folder:
```bash
cd ..
cd frontend
npm install
```
5. Run the frontend (while in the frontend folder):
```bash
npm run dev
```
6. View the webpage on the given localhost port (example):
```bash
http://localhost:5173/
```
   
