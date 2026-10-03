import { CircleMarker, MapContainer, Popup, TileLayer, Tooltip } from 'react-leaflet';

type StateCoordinate = {
  name: string;
  lat: number;
  lng: number;
  capital: string;
};

const stateCoordinates: StateCoordinate[] = [
  { name: 'Andhra Pradesh', capital: 'Amaravati', lat: 16.5062, lng: 80.648 },
  { name: 'Arunachal Pradesh', capital: 'Itanagar', lat: 27.0844, lng: 93.6053 },
  { name: 'Assam', capital: 'Dispur', lat: 26.1433, lng: 91.7898 },
  { name: 'Bihar', capital: 'Patna', lat: 25.5941, lng: 85.1376 },
  { name: 'Chhattisgarh', capital: 'Raipur', lat: 21.2514, lng: 81.6296 },
  { name: 'Goa', capital: 'Panaji', lat: 15.4909, lng: 73.8278 },
  { name: 'Gujarat', capital: 'Gandhinagar', lat: 23.2156, lng: 72.6369 },
  { name: 'Haryana', capital: 'Chandigarh', lat: 30.7333, lng: 76.7794 },
  { name: 'Himachal Pradesh', capital: 'Shimla', lat: 31.1048, lng: 77.1734 },
  { name: 'Jharkhand', capital: 'Ranchi', lat: 23.3441, lng: 85.3096 },
  { name: 'Karnataka', capital: 'Bengaluru', lat: 12.9716, lng: 77.5946 },
  { name: 'Kerala', capital: 'Thiruvananthapuram', lat: 8.5241, lng: 76.9366 },
  { name: 'Madhya Pradesh', capital: 'Bhopal', lat: 23.2599, lng: 77.4126 },
  { name: 'Maharashtra', capital: 'Mumbai', lat: 19.076, lng: 72.8777 },
  { name: 'Manipur', capital: 'Imphal', lat: 24.817, lng: 93.9368 },
  { name: 'Meghalaya', capital: 'Shillong', lat: 25.5788, lng: 91.8933 },
  { name: 'Mizoram', capital: 'Aizawl', lat: 23.7271, lng: 92.7176 },
  { name: 'Nagaland', capital: 'Kohima', lat: 25.6751, lng: 94.1086 },
  { name: 'Odisha', capital: 'Bhubaneswar', lat: 20.2961, lng: 85.8245 },
  { name: 'Punjab', capital: 'Chandigarh', lat: 30.7333, lng: 76.7794 },
  { name: 'Rajasthan', capital: 'Jaipur', lat: 26.9124, lng: 75.7873 },
  { name: 'Sikkim', capital: 'Gangtok', lat: 27.3389, lng: 88.6065 },
  { name: 'Tamil Nadu', capital: 'Chennai', lat: 13.0827, lng: 80.2707 },
  { name: 'Telangana', capital: 'Hyderabad', lat: 17.385, lng: 78.4867 },
  { name: 'Tripura', capital: 'Agartala', lat: 23.8315, lng: 91.2868 },
  { name: 'Uttar Pradesh', capital: 'Lucknow', lat: 26.8467, lng: 80.9462 },
  { name: 'Uttarakhand', capital: 'Dehradun', lat: 30.3165, lng: 78.0322 },
  { name: 'West Bengal', capital: 'Kolkata', lat: 22.5726, lng: 88.3639 },
];

export const StateSatelliteMap = () => {
  return (
    <section id="maps" className="w-full bg-zinc-950 text-white px-6 py-12 md:px-12 md:py-16">
      <div className="mx-auto max-w-6xl">
        <h2 className="text-2xl md:text-4xl font-semibold mb-3">State-Level Satellite View</h2>
        <p className="text-zinc-400 mb-6">Satellite map with exact latitude/longitude markers for each Indian state capital.</p>
        <div className="h-[560px] w-full overflow-hidden rounded-2xl border border-zinc-800 shadow-2xl">
          <MapContainer center={[22.5, 79.5]} zoom={5} scrollWheelZoom className="h-full w-full">
            <TileLayer
              attribution='&copy; <a href="https://www.esri.com/">Esri</a>'
              url="https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}"
            />
            {stateCoordinates.map((state) => (
              <CircleMarker
                key={state.name}
                center={[state.lat, state.lng]}
                radius={6}
                pathOptions={{ color: '#f97316', fillColor: '#fb923c', fillOpacity: 0.9 }}
              >
                <Tooltip direction="top" offset={[0, -8]}>{state.name}</Tooltip>
                <Popup>
                  <div className="text-sm">
                    <strong>{state.name}</strong>
                    <br />
                    Capital: {state.capital}
                    <br />
                    Lat: {state.lat}, Lng: {state.lng}
                  </div>
                </Popup>
              </CircleMarker>
            ))}
          </MapContainer>
        </div>
      </div>
    </section>
  );
};
