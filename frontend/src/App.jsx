import { Button } from "@/components/ui/button"
import { AlignJustify } from 'lucide-react';
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { RouteToggle } from "@/components/ui/RouteToggle";
import { StopSelector } from "@/components/ui/StopSelector";
import { Map } from "@/components/ui/MAP";
import { useState, useEffect } from "react";

// Stop List Arrays
const northboundStops = [
  "Dorsey Ln/Apache Blvd", "Rural Rd/Apache Blvd", "Paseo Del Saber/Apache Blvd",
  "College Ave/Apache Blvd", "Eleventh St/Mill", "Ninth St/Mill",
  "Sixth St/Mill", "Third St/Mill", "Hayden Ferry", "Marina Heights"
]
const southboundStops = [
  "Marina Heights", "Hayden Ferry", "Tempe Beach Park", "3rd St/Ash Ave",
  "5th St/Ash Ave", "University Dr/Ash Ave", "Ninth St/Mill",
  "Eleventh St/Mill", "College Ave/Apache Blvd", "Paseo Del Saber/Apache Blvd",
  "Rural Rd/Apache Blvd", "Dorsey Ln/Apache Blvd"
]

function App() {
  const API_BASE = "https://ontimetracking-d78eaf6faa9c.herokuapp.com"

  const [isDrawerOpen, setIsDrawerOpen] = useState(false); // Car selection sidebar state; boolean (open or closed)

  const [route, setRoute] = useState("northbound"); // Currently selected route; string, "northbound" or "southbound"
  const [selectedStop, setSelectedStop] = useState("default"); // Currently selected stop name; string
  const stops = route === "northbound" ? northboundStops : southboundStops; // Current list of stops given the selected route; array of strings

  // ***** ETA FETCHING *****
  const [finalETA, setFinalETA] = useState("ETA_PLACEHOLDER"); // Final calcualted ETA; string
  const handleSelectStop = async (stop) => {
    setSelectedStop(stop); // Update the currently selected stop variable

    // Send a request containing the selected stop and route to the backend API
    try {
      const response = await fetch(`${API_BASE}/api/eta`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          stop: stop,
          route: route
        })
      });

      const data = await response.json();
      if (data.error) {
        setFinalETA(data.error); // set error message
      } else if (data.eta_min != null && data.eta_sec != null) {
        setFinalETA(`${data.eta_min} min ${data.eta_sec} sec`); // Convert response to string with minutes and seconds
      } else {
        setFinalETA("ETA not available.");
      }
    
    } catch (error) {
      console.error("Error fetching ETA: ", error);
      setEta("ERROR");
    }
  };

  // ***** TROLLEY LOCATION FETCHING *****
  const [trolleyLocations, setTrolleyLocations] = useState([]); // Stores the location data associated with each trolley, array of {car id, lat, lng}
  const fetchTrolleyLocations = async () => {
      // Send a request to the backend API
      const response = await fetch(`${API_BASE}/api/active_trolley_locations`);
      const data = await response.json();
      console.log(data)
      setTrolleyLocations(data);
  };
  // Fetch the locations upon page loading and every 5 seconds
  useEffect(() => { fetchTrolleyLocations(); }, []);
  useEffect(() => {
      const interval = setInterval(() => {
          fetchTrolleyLocations();
      }, 5000); 
      return () => clearInterval(interval);
  }, []);

  // ***** TROLLEY SELECTING *****
  const [selectedCar, setSelectedCar] = useState(null); // Stores the trolley selected by the user, {car id, lat, lng}
  const selectCar = (carId) => {
    const selected = trolleyLocations.find((car) => car.id === carId);
    //console.log("car id " + carId + " selected")
    setSelectedCar(selected || null);
  };

  // ***** PAGE HTML *****
  return (
    <div className="h-screen flex flex-col">
      {/* Page Header */}
      <header className="bg-gray-100 dark:bg-gray-900 p-2 border-b flex items-center justify-between">
        <h1 className="text-xl font-bold pl-[2%]">Tempe Valley Metro Street Car Tracker</h1>

        {/* Contact and Sidebar buttons */}
        <div className="flex items-center gap-5 pr-[1%]">
          <Button variant="ghost" className="underline cursor-pointer"> Contact Us </Button>
          <Button size="icon" variant="ghost" className="cursor-pointer" onClick={() => setIsDrawerOpen(currentState => !currentState)}>
            <AlignJustify />
          </Button>
        </div>
      </header>

      {/* Page Content */}
      <div className="flex flex-grow overflow-hidden">
        
        {/* Stop Selection Sidebar */}
        <aside className="w-[20%] min-w-60 bg-white dark:bg-zinc-900 p-4 border-r flex flex-col">

          {/* Heading + Route Toggle Button */}
          <div className="pb-4">
            <h1 className="text-xl font-semibold text-center">Select a Stop</h1>
            <hr className="my-1" />
            <div>
              <Label className="py-2 block">ROUTE</Label>
              <RouteToggle value={route} onChange={setRoute} />
            </div>
          </div>

          {/* Stop List */}
          <div className="flex justify-between">
            <Label className="text-sm font-medium">STOPS</Label>
            <Button size="sm" variant="ghost" className="underline cursor-pointer">Use my Location</Button>
          </div>
          <div className="flex-1 overflow-y-auto">
            <StopSelector stops={stops} selectedStop={selectedStop} onSelect={handleSelectStop} />
          </div>

          {/* ETA Card */}
          <div className="pt-4 shadow-xl">
            <Card>
              <CardHeader>
                <CardTitle className="text-center"> ETA to {selectedStop}</CardTitle>
              </CardHeader>
              <CardContent className="text-center flex flex-col">
                <div >
                  {finalETA}
                </div>
              </CardContent>
            </Card>
          </div>
        </aside>
    
        {/* Map Area */}
        <main className="relative flex-grow bg-gray-200 dark:bg-zinc-800">
          
          {/* Street Car info Sidebar */}
          <div className={`absolute top-0 right-0 h-full w-[15%] min-w-50 bg-white dark:bg-zinc-900 shadow-lg transform transition-transform duration-300 z-30
          ${ isDrawerOpen ? "translate-x-0" : "translate-x-full" }`}>

            {/* Heading */}
            <div className="p-4">
              <h1 className="text-xl font-semibold text-center">Street Car Info</h1>
              <hr className="my-1" />
            </div>

            {/* Car selector */}
            <div className="p-4">
              <Label className="py-2 block">CAR</Label>
              <Select onValueChange={selectCar}>
                <SelectTrigger>
                  <SelectValue placeholder="Select a Car">{selectedCar && selectedCar.id}</SelectValue>
                </SelectTrigger>
                <SelectContent>
                  {trolleyLocations.map((car) => (
                    <SelectItem key={car.id} value={car.id}>{car.id}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Route + Upcoming Stops, PLACEHOLDERS FOR NOW */}
            {selectedCar != null && (
              <div>
                <div className="p-4">
                  <Label className="py-2 block">ROUTE</Label>
                  {/* selectedCar.route */}Northbound
                </div>
                <div className="p-4">
                  <Label className="py-2 block">UPCOMING STOPS</Label>
                  <div>{/* selectedCar.nextStops[0] */}Stop 1</div>
                  <div>{/* selectedCar.nextStops[1] */}Stop 2</div>
                  <div>{/* selectedCar.nextStops[2] */}Stop 3</div>
                </div>
              </div>
            )}
          </div>

          {/* Map */}
          <div className="w-full h-full flex items-center justify-center text-gray-500 dark:text-gray-300">
            <Map
              selectedStop={selectedStop} selectedCar={selectedCar}
              routeStops={stops} route={route} trolleyLocations={trolleyLocations}
              onStopMarkerSelect={handleSelectStop} onTrolleyMarkerSelect={selectCar}
            />
          </div>

          {/* Ad/Ticketing Space */}
          <div className="absolute bottom-4 left-1/2 transform -translate-x-1/2 z-50 w-[80%]">
            <div className="bg-white dark:bg-zinc-900 px-6 py-4 h-20">
              <p className="text-sm text-center text-gray-600 dark:text-gray-300">Ticketing Space</p>
            </div>
          </div>
        </main>
      </div>
    </div>
  )
}

export default App