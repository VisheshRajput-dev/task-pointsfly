import fs from 'fs'
import path from 'path'

export interface FlightData {
  airline: string
  flightNumber: string
  departureTime: string
  arrivalTime: string
  duration: string
  cashPrice: string
  pointsPrice: string
}

export function parseIndigoFlights(htmlContent: string): FlightData[] {
  const flights: FlightData[] = []

  const flightItemPattern = /<div class="srp__search-result-list__item"[^>]*>([\s\S]*?)<\/div>\s*<\/div>\s*<\/div>\s*<\/div>\s*<\/div>\s*<\/div>/g

  const flightItems = htmlContent.match(flightItemPattern) || []
  
  for (const item of flightItems) {
    try {
      
      const flightNumberMatch = item.match(/>\s*6E\s+(\d+)/i)
      const flightNumber = flightNumberMatch ? `6E ${flightNumberMatch[1]}` : ''

      const departureTimeMatch = item.match(/<div class="skyplus-text time sh3">(\d{1,2}:\d{2})<\/div>/)
      const departureTime = departureTimeMatch ? departureTimeMatch[1] : ''

      const arrivalTimeMatch = item.match(/<div class="skyplus-text time sh3">(\d{1,2}:\d{2})<\/div>/g)
      const arrivalTime = arrivalTimeMatch && arrivalTimeMatch.length > 1 
        ? arrivalTimeMatch[1].match(/>(\d{1,2}:\d{2})</)?.[1] || ''
        : ''

      const durationMatch = item.match(/(\d+h\s*\d+m|\d+h|\d+m)/i)
      const duration = durationMatch ? durationMatch[1] : ''

      const cashPriceMatch = item.match(/₹([\d,]+)/g)
      const cashPrice = cashPriceMatch && cashPriceMatch.length > 0 
        ? `₹${cashPriceMatch[0].replace('₹', '').trim()}`
        : ''

      const pointsMatch = item.match(/(\d+)\s*(?:points|pts|award)/i) || item.match(/points[:\s]*(\d+)/i)
      const pointsPrice = pointsMatch ? `${pointsMatch[1]} points` : 'N/A'

      if (flightNumber && departureTime && cashPrice) {
        flights.push({
          airline: 'IndiGo',
          flightNumber,
          departureTime,
          arrivalTime: arrivalTime || 'N/A',
          duration: duration || 'N/A',
          cashPrice,
          pointsPrice,
        })
      }
    } catch (error) {
      console.error('Error parsing flight item:', error)
    }
  }
  
  return flights
}

export async function getDelBomFlights(): Promise<FlightData[]> {
  try {
    const filePath = path.join(process.cwd(), 'samples', 'del-bom-indigo.html')
    const htmlContent = fs.readFileSync(filePath, 'utf-8')
    return parseIndigoFlights(htmlContent)
  } catch (error) {
    console.error('Error reading flight data:', error)
    return []
  }
}
