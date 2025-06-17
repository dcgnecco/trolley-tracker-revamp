#
## Installations
Ensure all of the following are installed before setting up the application:
- Node.js (and npm)
- Python
- Git

## Setup Instructions
1. In a terminal, cd into the folder you want to develop in and clone the repository:
```bash
git clone https://github.com/dcgnecco/trolley-tracker-revamp.git
cd trolley-tracker-revamp
```
2. Install backend dependencies in the `backend` folder and (optionally) create virtual python environment:
```bash (in trolley-tracker-revamp)
cd backend
python -m venv venv        # OPTIONAL
venv\Scripts\activate      # OPTIONAL
pip install -r requirements.txt
```
3. Open a new terminal and install frontend dependencies in the `frontend` folder (keep the backend terminal open):
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
5. Run the backend in the backend terminal:
```bash
python main.py
```
6. Run the frontend in the frontend terminal:
```bash
npm run dev
```
7. View the webpage on the given localhost port (example):
```bash
http://localhost:5173/
```
   
