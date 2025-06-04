import { ScrollArea } from "@/components/ui/scroll-area";
import { Button } from "@/components/ui/button";

export function StopSelector({ stops, selectedStop, onSelect }) {
  return (
    <ScrollArea className="max-h-full pr-2">
      <div className="flex flex-col mt-2">
        {stops.map((stop) => (
            <Button key={stop} variant={selectedStop === stop ? "default" : "outline"}
            onClick={() => onSelect(stop)} className="flex-1 justify-start cursor-pointer" type="button">
                {stop}
            </Button>
        ))}
      </div>
    </ScrollArea>
  );
}