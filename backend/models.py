class Trolley():
    def __init__(self, id, lat, lng, direction):
        self.id = id
        self.lat = lat
        self.lng = lng
        self.direction = direction
    
    def to_json(self):
        return {
            "id": self.id,
            "lat": self.lat,
            "lng": self.lng,
            "direction": self.direction
        }