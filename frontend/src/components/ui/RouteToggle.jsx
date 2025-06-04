import { ToggleGroup, ToggleGroupItem } from "@/components/ui/toggle-group";
import { useState } from "react";

export function RouteToggle({ value, onChange }) {
  return (
    <ToggleGroup type="single" variant="outline" className="w-full" value={value}
    onValueChange={(val) => { if (val) onChange(val); }}>
      <ToggleGroupItem value="northbound" className={`flex-1 px-4 py-2 
          data-[state=on]:bg-black data-[state=on]:text-white
          data-[state=on]:border-black cursor-pointer`}>
        Northbound
      </ToggleGroupItem>
      <ToggleGroupItem value="southbound" className={`flex-1 px-4 py-2
          data-[state=on]:bg-black data-[state=on]:text-white
          data-[state=on]:border-black cursor-pointer`}>
        Southbound
      </ToggleGroupItem>
    </ToggleGroup>
  );
}