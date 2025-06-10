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
2. Install backend dependencies in the `backend` folder (UPDATE WHEN BACKEND IS ADDED, virtual python env?):
```bash (in trolley-tracker-revamp)
cd backend
pip install -r requirements.txt
```
3. Install frontend dependencies in the `frontend` folder:
```bash
cd frontend
npm install
```
4. Add Google Maps API Key by either:
   
   a. Create a Google Maps API key by following [this guide](https://developers.google.com/maps/documentation/javascript/get-api-key). Make sure the key has the **Maps JavaScript API** enabled.

   b. Ask a team member for a preexisting one.

   Then create a `.env` file in the root of the `frontend` folder, and add:
   ```.env
   VITE_GOOGLE_MAPS_API_KEY=your_api_key_here
   ```
5. Run the backend (while in the `backend` folder):
```bash
cd backend
python main.py
```
6. Run the frontend (while in the `frontend` folder):
```bash
cd frontend
npm run dev
```
7. View the webpage on the given localhost port (example):
```bash
http://localhost:5173/
```
   
