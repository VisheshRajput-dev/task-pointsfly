import { NextResponse } from 'next/server'
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

function parseEmiratesFlights(htmlContent: string): FlightData[] {
  const flights: FlightData[] = []

  const flightNumberRegex = /EK\s*(\d{3,4})/gi
  const flightMatches: Array<{ number: string; index: number; context: string }> = []
  
  let match
  while ((match = flightNumberRegex.exec(htmlContent)) !== null) {
    const start = Math.max(0, match.index - 1500)
    const end = Math.min(htmlContent.length, match.index + 3000)
    const context = htmlContent.substring(start, end)
    
    flightMatches.push({
      number: `EK ${match[1]}`,
      index: match.index,
      context,
    })
  }

  const seenFlights = new Set<string>()
  
  for (const flightMatch of flightMatches) {
    const flightNumber = flightMatch.number

    if (seenFlights.has(flightNumber)) continue
    
    try {
      const context = flightMatch.context

      const timeMatches = context.match(/(\d{1,2}):(\d{2})/g) || []
      const uniqueTimes = [...new Set(timeMatches)]
      const departureTime = uniqueTimes[0] || ''
      const arrivalTime = uniqueTimes[1] || uniqueTimes[0] || ''

      const inrPriceMatch = context.match(/INR\s*([\d,]+)/i)
      const gbpPriceMatch = context.match(/GBP\s*([\d,]+)/i)
      const aedPriceMatch = context.match(/AED\s*([\d,]+)/i)
      
      let cashPrice = ''
      if (inrPriceMatch) {
        
        cashPrice = `₹${inrPriceMatch[1]}`
      } else if (gbpPriceMatch) {
        
        const gbpAmount = parseFloat(gbpPriceMatch[1].replace(/,/g, ''))
        const inrAmount = Math.round(gbpAmount * 117.30)
        cashPrice = `₹${inrAmount.toLocaleString('en-IN')}`
      } else if (aedPriceMatch) {
        
        const aedAmount = parseFloat(aedPriceMatch[1].replace(/,/g, ''))
        const inrAmount = Math.round(aedAmount * 24.41)
        cashPrice = `₹${inrAmount.toLocaleString('en-IN')}`
      }

      const durationMatch = context.match(/(\d+)\s*(?:h|hours?|hrs?)\s*(\d+)?\s*(?:m|mins?|minutes?)/i) ||
                           context.match(/(\d+)\s*(?:h|hours?|hrs?)/i)
      let duration = ''
      if (durationMatch) {
        if (durationMatch[2]) {
          duration = `${durationMatch[1]}h ${durationMatch[2]}m`
        } else {
          duration = `${durationMatch[1]}h`
        }
      }

      const pointsMatch = context.match(/(\d+)\s*(?:Skywards\s*)?(?:miles|points|pts)/i) ||
                         context.match(/miles[:\s]*(\d+)/i)
      const pointsPrice = pointsMatch ? `${pointsMatch[1]} miles` : 'N/A'

      if (flightNumber && (departureTime || cashPrice)) {
        seenFlights.add(flightNumber)
        
        flights.push({
          airline: 'Emirates',
          flightNumber,
          departureTime: departureTime || 'N/A',
          arrivalTime: arrivalTime || 'N/A',
          duration: duration || 'N/A',
          cashPrice: cashPrice || 'N/A',
          pointsPrice,
        })
      }
    } catch (error) {
      console.error('Error parsing Emirates flight item:', error)
    }
  }

  flights.sort((a, b) => {
    const priceA = parseInt(a.cashPrice.replace(/[₹,\s]/g, '')) || 999999999
    const priceB = parseInt(b.cashPrice.replace(/[₹,\s]/g, '')) || 999999999
    return priceA - priceB
  })
  
  return flights
}

function parseIndigoFlights(htmlContent: string): FlightData[] {
  const flights: FlightData[] = []

  const flightItemRegex = /<div[^>]*class="srp__search-result-list__item"[^>]*>([\s\S]*?)(?=<div[^>]*class="srp__search-result-list__item"|<\/div>\s*<\/div>\s*<\/div>\s*<\/div>\s*<\/div>\s*<\/div>\s*<div class="at-static-srp-banner"|$)/g
  
  let match
  while ((match = flightItemRegex.exec(htmlContent)) !== null) {
    const flightItem = match[1]
    
    try {
      
      const flightNumberMatch = flightItem.match(/<div[^>]*class="[^"]*flight-number[^"]*"[^>]*>[\s\S]*?6E\s+(\d+)/i) ||
                                flightItem.match(/6E\s+(\d+)/i)
      const flightNumber = flightNumberMatch ? `6E ${flightNumberMatch[1]}` : ''
      
      if (!flightNumber) continue

      const departureMatch = flightItem.match(/<div[^>]*class="[^"]*flight-details__flight-departure[^"]*"[^>]*>[\s\S]*?<div[^>]*class="[^"]*time[^"]*sh3[^"]*"[^>]*>(\d{1,2}:\d{2})<\/div>/i)
      const departureTime = departureMatch ? departureMatch[1] : ''

      const arrivalMatch = flightItem.match(/<div[^>]*class="[^"]*flight-details__flight-arrival[^"]*"[^>]*>[\s\S]*?<div[^>]*class="[^"]*time[^"]*sh3[^"]*"[^>]*>(\d{1,2}:\d{2})<\/div>/i)
      const arrivalTime = arrivalMatch ? arrivalMatch[1] : ''

      const durationMatch = flightItem.match(/<div[^>]*class="[^"]*journey-lap[^"]*"[^>]*>[\s\S]*?<div[^>]*class="[^"]*text-color[^"]*body-small-regular[^"]*"[^>]*>(\d+h\s*\d+m|\d+h|\d+\s*hrs?\s*\d+\s*mins?)<\/div>/i)
      const duration = durationMatch ? durationMatch[1].trim() : ''

      const economyPriceMatch = flightItem.match(/<div[^>]*class="[^"]*economy-class-item[^"]*"[^>]*>[\s\S]*?<div[^>]*class="[^"]*selected-fare__fare-price[^"]*"[^>]*>₹([\d,]+)/i)
      const economyPrice = economyPriceMatch ? `₹${economyPriceMatch[1]}` : ''

      const businessPriceMatch = flightItem.match(/<div[^>]*class="[^"]*business-class-item[^"]*"[^>]*>[\s\S]*?<div[^>]*class="[^"]*selected-fare__fare-price[^"]*"[^>]*>₹([\d,]+)/i)
      const businessPrice = businessPriceMatch ? `₹${businessPriceMatch[1]}` : ''

      const cashPrice = economyPrice || businessPrice || ''

      const pointsMatch = flightItem.match(/(\d+)\s*(?:IndiGo\s+BluChips|points|pts)/i)
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

  flights.sort((a, b) => {
    
    const priceA = parseInt(a.cashPrice.replace(/[₹,]/g, '')) || 0
    const priceB = parseInt(b.cashPrice.replace(/[₹,]/g, '')) || 0
    return priceA - priceB
  })
  
  return flights
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const from = searchParams.get('from')
    const to = searchParams.get('to')

    const routeMap: Record<string, { file: string; airline: 'indigo' | 'emirates' }> = {
      
      'DEL-BOM': { file: 'del-bom-indigo.html', airline: 'indigo' },
      'BOM-DEL': { file: 'bom-delhi-indigo.html', airline: 'indigo' },
      'BLR-BOM': { file: 'blr-bom-indigo.html', airline: 'indigo' },
      'BOM-BLR': { file: 'bom-blr-indigo.html', airline: 'indigo' },
      'BLR-DEL': { file: 'blr-del-indigo.html', airline: 'indigo' },
      'DEL-BLR': { file: 'del-blr-indigo.html', airline: 'indigo' },
      
      'DEL-LON': { file: 'International/del-lon- Emirates.html', airline: 'emirates' },
      'DEL-LHR': { file: 'International/del-lon- Emirates.html', airline: 'emirates' }, 
      'LON-DEL': { file: 'International/lon-del-Emirates.html', airline: 'emirates' },
      'LHR-DEL': { file: 'International/lon-del-Emirates.html', airline: 'emirates' }, 
      'DEL-DXB': { file: 'International/del-dxb- Emirates.html', airline: 'emirates' },
      'DXB-DEL': { file: 'International/dxb-del-Emirates.html', airline: 'emirates' },
    }
    
    const routeKey = `${from}-${to}`
    const routeInfo = routeMap[routeKey]
    
    if (routeInfo) {
      const filePath = path.join(process.cwd(), 'samples', routeInfo.file)
      
      if (!fs.existsSync(filePath)) {
        return NextResponse.json({ error: `Flight data file not found: ${routeInfo.file}` }, { status: 404 })
      }
      
      const htmlContent = fs.readFileSync(filePath, 'utf-8')
      const flights = routeInfo.airline === 'emirates' 
        ? parseEmiratesFlights(htmlContent)
        : parseIndigoFlights(htmlContent)
      
      return NextResponse.json({ flights })
    }
    
    return NextResponse.json({ flights: [] })
  } catch (error) {
    console.error('Error fetching flights:', error)
    return NextResponse.json({ error: 'Failed to fetch flights' }, { status: 500 })
  }
}
