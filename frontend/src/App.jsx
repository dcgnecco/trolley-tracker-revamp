import { Button } from "@/components/ui/button"
import { AlignJustify } from 'lucide-react';
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select"
import { RouteToggle } from "@/components/ui/RouteToggle";
import { StopSelector } from "@/components/ui/StopSelector";
import { Map } from "@/components/ui/MAP";
import { useState, useEffect } from "react";

// Stop List Arrays, WOULD GET THESE FROM BACKEND(?)
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
  // Route selection variable
  const [route, setRoute] = useState("northbound");

  // Stop selection variables
  const [selectedStop, setSelectedStop] = useState("default");
  const stops = route === "northbound" ? northboundStops : southboundStops;

  // ETA variables
  const [finalETA, setFinalETA] = useState("ETA_PLACEHOLDER");

  const handleSelectStop = async (stop) => {
    setSelectedStop(stop);
    
    try {
      const response = await fetch("http://127.0.0.1:5000/api/eta", {
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
        setFinalETA(`${data.eta_min} min ${data.eta_sec} sec`);
      } else {
        setFinalETA("ETA not available.");
      }
    
    } catch (error) {
      console.error("Error fetching ETA:", error);
      setEta("ERROR");
    }
  };

  // Car variables, GET FROM BACKEND
  const [selectedCar, setSelectedCar] = useState(null);
  const availableCars = [
    { carName: "Car 1", route: "Northbound", nextStops: ["Stop 1", "Stop 2", "Stop 3"]},
    { carName: "Car 2", route: "Southbound", nextStops: ["Stop 4", "Stop 5", ""]}
  ];
  const selectCar = (carName) => {
    const selected = availableCars.find((car) => car.carName === carName);
    setSelectedCar(selected || null);
  };

  // Drawer state variable
  const [isDrawerOpen, setIsDrawerOpen] = useState(false);

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
                  <SelectValue placeholder="Select a Car" />
                </SelectTrigger>
                <SelectContent>
                  {availableCars.map((car) => (
                    <SelectItem key={car.carName} value={car.carName}>{car.carName}</SelectItem>
                  ))}
                </SelectContent>
              </Select>
            </div>

            {/* Route + Upcoming Stops */}
            {selectedCar != null && (
              <div>
                <div className="p-4">
                  <Label className="py-2 block">ROUTE</Label>
                  {selectedCar.route}
                </div>
                <div className="p-4">
                  <Label className="py-2 block">UPCOMING STOPS</Label>
                  <div>{selectedCar.nextStops[0]}</div>
                  <div>{selectedCar.nextStops[1]}</div>
                  <div>{selectedCar.nextStops[2]}</div>
                </div>
              </div>
            )}
          </div>

          {/* Map */}
          <div className="w-full h-full flex items-center justify-center text-gray-500 dark:text-gray-300">
            <Map selectedStop={selectedStop} routeStops={stops} route={route}/>
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