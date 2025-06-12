'use client';

import { useEffect, useRef, useState } from 'react';
import { MapContainer, TileLayer, Marker, Popup, Polyline, useMap } from 'react-leaflet';
import { LatLngExpression } from 'leaflet';
import 'leaflet/dist/leaflet.css';
import { useSearchParams } from 'next/navigation';


const baseURL  = process.env.NEXT_PUBLIC_API_URL;


function MapController({ position }: { position: LatLngExpression }) {
    const map = useMap();
    useEffect(() => {
      if (position) {
        map.setView(position, 10, { animate: true });
      }
    }, [position, map]);
    return null;
  }

// Fix leaflet marker icons inside useEffect
export default function MapPage() {
    const [currentIndex, setCurrentIndex] = useState(0);
    const [stops, setStops] = useState<LatLngExpression[]>([])
    const [route, setRoute] = useState<LatLngExpression[]>([]);
    const [pois, setPois] = useState<any[]>([]);

    const searchParams = useSearchParams();
    
    // used for getting information from server
    const hash = searchParams.get('hash');

  useEffect(() => {
    // Dynamic import to avoid SSR crash

    import('leaflet').then(L => {
        delete L.Icon.Default.prototype._getIconUrl;
  
        L.Icon.Default.mergeOptions({
          iconRetinaUrl: '/marker-icon.png',
          iconUrl: '/marker-icon.png',
          shadowUrl: '/marker-shadow.png',
        });
      });

      fetch(`${baseURL}directions?hash=${hash}`)
      .then(res => res.json())
      .then(data => {
        setRoute(data.features[0].geometry.coordinates.map((coord: number[]) => [coord[1], coord[0]]));
      });

    fetch(`${baseURL}pois?hash=${hash}`)
      .then(res => res.json())
      .then(data => {
        const stopsTemp: LatLngExpression = []
        var currentCoord = [0, 0]
        const poisTemp = data.map((poi: any) => {
            let [currLat, currLon] = currentCoord
            let sourceLat = poi.source_coord[0]
            let sourceLon = poi.source_coord[1]
            if (currLat !== sourceLat || currLon != sourceLon) {
                stopsTemp.push([sourceLat, sourceLon]);
                currentCoord = [sourceLat, sourceLon]
            }
            
            return {
                name: poi.properties.name,
                lat: poi.geometry.coordinates[1],
                lon: poi.geometry.coordinates[0],
                sourceLat: poi.source_coord[0],
                sourceLon: poi.source_coord[1],
                score: poi.score,
                wikipedia: poi.properties.wikipedia,
            }
        })
        setPois(poisTemp)
        setStops(stopsTemp);
      });
  }, []);


  const currentPOI = pois[currentIndex];

  const poiByStop = (stopCoord: LatLngExpression) => {
    const [lat, lon] = stopCoord;
    let filteredPoi = pois.filter((poi) => {
        return lat === poi.sourceLat && lon === poi.sourceLon
    })
    filteredPoi.sort((poi)=>poi.score)
    return filteredPoi;
  }

  return (
    <div style={{display: 'flex', flexDirection: 'row', height: '100vh', width: '100vw'}}>
        <div style={{ width: '50vw' }}>
            <div style={{ height: '95vh'}}>
              <MapContainer 
                center={currentPOI ? [currentPOI.lat, currentPOI.lon] : [35.5, -119]}
                // center={[35.5, -119]} 
                zoom={10} style={{ height: '100%', width: '100%' }}
              >
                <TileLayer 
                    url="https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png"             
                    />
                <Polyline positions={route} color="blue" />
                {currentPOI && stops.length > 0 && <MapController position={stops[currentIndex]} />}
                {pois.map((poi, i) => (
                  <Marker key={i} position={[poi.lat, poi.lon]}>
                    <Popup>
                      <strong>{poi.name}</strong><br />
                      {poi.description}
                    </Popup>
                  </Marker>
                ))}
              </MapContainer>
            </div>
    
          <div style={{ padding: '1rem', textAlign: 'center' }}>
            <button onClick={() => setCurrentIndex(i => Math.max(i - 1, 0))} disabled={currentIndex === 0}>
              ◀ Previous
            </button>
            <span style={{ margin: '0 1rem' }}>
              {currentIndex + 1} / {stops.length}
            </span>
            <button
                id="next-button"
                onClick={() => setCurrentIndex(i => Math.min(i + 1, pois.length - 1))}
                disabled={currentIndex >= stops.length - 1}
            >
              Next ▶
            </button>
          </div>
        </div>
        <div style={{ width: '50vw', padding: '1rem', overflowY: 'auto' }}>
            <h2>Points of Interest</h2>
            {stops.length > 0 && poiByStop(stops[currentIndex]).map((poi, i) => (
              <div key={i} style={{ 
                display: 'flex',
                alignItems: 'flex-start',
                gap: '1rem',
                marginBottom: '1.5rem',
                padding: '1rem',
                border: '1px solid #ccc',
                borderRadius: '8px',
                backgroundColor: '#fff',
                boxShadow: '0 2px 6px rgba(0, 0, 0, 0.05)',
            }}
                >
                {/* <h3>{poi.name}</h3> */}
                {/* Image */}
                {poi.wikipedia?.type == 'standard' && poi.wikipedia?.thumbnail?.source && (
                <img
                src={poi.wikipedia.thumbnail.source}
                alt={poi.name}
                style={{
                  width: '120px',
                  height: '120px',
                  objectFit: 'cover',
                  borderRadius: '6px',
                    }}
                />
                )}
                {/* <h3>{poi.score}</h3> */}
                <div style={{ flex: 1 }}>
                    <h3 style={{ margin: '0 0 0.5rem', fontSize: '1.2rem', color: 'black' }}>{poi.name}</h3>
                    {poi.wikipedia?.type == 'standard' && poi.wikipedia?.extract && (
                        <p style={{ margin: 0, fontSize: '0.9rem', color: '#444' }}>
                        {poi.wikipedia.extract}
                        </p>
                    )}
            {poi.wikipedia?.type == 'standard' && poi.wikipedia?.content_urls?.desktop?.page && (
                <div style={{ marginTop: '0.5rem' }}>
                <a
                    href={poi.wikipedia?.content_urls?.desktop?.page}
                    target="_blank"
                    rel="noopener noreferrer"
                    style={{ fontSize: '0.85rem', color: '#0070f3', textDecoration: 'none' }}
                >
                    📖 Read more on Wikipedia →
                </a>
                </div>
            )}
                </div>
                </div>
            ))}

        </div>
    </div>
    
  );
}