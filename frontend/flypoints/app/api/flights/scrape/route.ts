import { NextResponse } from 'next/server'
import { spawn } from 'child_process'
import path from 'path'
import fs from 'fs'

// Import HTML parsing functions from the existing route
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

// Get HTML snapshot data as fallback
function getHTMLSnapshotData(from: string, to: string): FlightData[] {
  const routeMap: Record<string, { file: string; airline: 'indigo' | 'emirates' }> = {
    'DEL-BOM': { file: 'del-bom-indigo.html', airline: 'indigo' },
    'BOM-DEL': { file: 'bom-delhi-indigo.html', airline: 'indigo' },
    'BLR-BOM': { file: 'blr-bom-indigo.html', airline: 'indigo' },
    'BOM-BLR': { file: 'bom-blr-indigo.html', airline: 'indigo' },
    'BLR-DEL': { file: 'blr-del-indigo.html', airline: 'indigo' },
    'DEL-BLR': { file: 'del-blr-indigo.html', airline: 'indigo' },
  }
  
  const routeKey = `${from}-${to}`
  const routeInfo = routeMap[routeKey]
  
  if (routeInfo) {
    const filePath = path.join(process.cwd(), 'samples', routeInfo.file)
    
    if (fs.existsSync(filePath)) {
      const htmlContent = fs.readFileSync(filePath, 'utf-8')
      if (routeInfo.airline === 'indigo') {
        return parseIndigoFlights(htmlContent)
      }
    }
  }
  
  return []
}

export interface FlightData {
  airline: string
  flightNumber: string
  departureTime: string
  arrivalTime: string
  duration: string
  cashPrice: string
  pointsPrice: string
  spicesaverPrice?: string
  spiceflexPrice?: string
  spicemaxPrice?: string
  spicesaverPoints?: string
  spiceflexPoints?: string
  spicemaxPoints?: string
}


// Helper function to clean price string (handles both ₹ and \u20b9)
function cleanPrice(priceStr: string): string {
  if (!priceStr || priceStr === 'N/A') return 'N/A'
  // Remove ₹ symbol (both Unicode and escaped), commas, and whitespace
  return priceStr.replace(/[₹\u20b9,\s]/g, '')
}

// Format number with Indian number system (commas every 2 digits after first 3)
function formatIndianNumber(num: number | string): string {
  const numStr = typeof num === 'string' ? num.replace(/[^\d]/g, '') : num.toString()
  if (!numStr || numStr === '0') return '0'
  
  const numValue = parseInt(numStr)
  if (isNaN(numValue)) return numStr
  
  // Indian numbering: first comma after 3 digits from right, then every 2 digits
  // Examples: 
  // 8338 → 8,338
  // 123456 → 1,23,456
  // 1234567 → 12,34,567
  // 12345678 → 1,23,45,678
  
  const str = numValue.toString()
  const len = str.length
  
  if (len <= 3) {
    return str
  }
  
  // First 3 digits from right (no comma before them)
  let result = str.slice(-3)
  let remaining = str.slice(0, -3)
  
  // Then add commas every 2 digits
  while (remaining.length > 0) {
    if (remaining.length >= 2) {
      result = remaining.slice(-2) + ',' + result
      remaining = remaining.slice(0, -2)
    } else {
      result = remaining + ',' + result
      remaining = ''
    }
  }
  
  return result
}

// Convert Python scraper output to frontend format
function convertToFrontendFormat(pythonFlights: any[]): FlightData[] {
  return pythonFlights
    .map((flight) => {
      // Use SpiceSaver price as default cash price, or fallback to price_inr
      // JSON.parse will decode \u20b9 to ₹ automatically
      let cashPrice = 'N/A'
      let priceValue = 0
      
      if (flight.spicesaver_price && flight.spicesaver_price !== 'N/A') {
        const cleaned = cleanPrice(flight.spicesaver_price)
        if (cleaned !== 'N/A') {
          priceValue = parseInt(cleaned) || 0
          cashPrice = priceValue > 0 ? `₹${formatIndianNumber(cleaned)}` : 'N/A'
        }
      } else if (flight.price_inr && flight.price_inr !== 'N/A') {
        const cleaned = cleanPrice(flight.price_inr)
        if (cleaned !== 'N/A') {
          priceValue = parseInt(cleaned) || 0
          cashPrice = priceValue > 0 ? `₹${formatIndianNumber(cleaned)}` : 'N/A'
        }
      }

      // Filter out flights with no price or 0 price
      if (cashPrice === 'N/A' || priceValue === 0) {
        return null
      }

      // Format points
      const pointsPrice = flight.spicesaver_points && flight.spicesaver_points !== 'N/A'
        ? `${formatIndianNumber(flight.spicesaver_points)} points`
        : flight.award_points && flight.award_points !== 'N/A'
        ? `${formatIndianNumber(flight.award_points)} points`
        : 'N/A'

      return {
        airline: flight.airline || 'SpiceJet',
        flightNumber: flight.flight_number || 'N/A',
        departureTime: flight.departure_time || 'N/A',
        arrivalTime: flight.arrival_time || 'N/A',
        duration: flight.duration || 'N/A',
        cashPrice,
        pointsPrice,
        spicesaverPrice: flight.spicesaver_price && flight.spicesaver_price !== 'N/A' 
          ? `₹${formatIndianNumber(cleanPrice(flight.spicesaver_price))}` 
          : undefined,
        spiceflexPrice: flight.spiceflex_price && flight.spiceflex_price !== 'N/A' 
          ? `₹${formatIndianNumber(cleanPrice(flight.spiceflex_price))}` 
          : undefined,
        spicemaxPrice: flight.spicemax_price && flight.spicemax_price !== 'N/A' 
          ? `₹${formatIndianNumber(cleanPrice(flight.spicemax_price))}` 
          : undefined,
        spicesaverPoints: flight.spicesaver_points && flight.spicesaver_points !== 'N/A' 
          ? formatIndianNumber(flight.spicesaver_points)
          : undefined,
        spiceflexPoints: flight.spiceflex_points && flight.spiceflex_points !== 'N/A' 
          ? formatIndianNumber(flight.spiceflex_points)
          : undefined,
        spicemaxPoints: flight.spicemax_points && flight.spicemax_points !== 'N/A' 
          ? formatIndianNumber(flight.spicemax_points)
          : undefined,
      }
    })
    .filter((flight): flight is FlightData => flight !== null) // Remove null entries (flights with 0 price)
}

// Run Python scraper with timeout
function runScraper(origin: string, destination: string, date: string): Promise<any[]> {
  return new Promise((resolve, reject) => {
    // Use the API wrapper script that outputs JSON
    // Path from frontend/flypoints/app/api/flights/scrape/route.ts to attempt1/spicejet_scraper_api.py
    // process.cwd() is frontend/flypoints, so we need to go up to root then to attempt1
    const scraperPath = path.join(process.cwd(), '..', '..', 'attempt1', 'spicejet_scraper_api.py')
    const pythonCommand = process.platform === 'win32' ? 'python' : 'python3'
    
    const pythonProcess = spawn(pythonCommand, [scraperPath, origin, destination, date], {
      cwd: path.dirname(scraperPath),
      stdio: ['pipe', 'pipe', 'pipe'],
    })

    let stdout = ''
    let stderr = ''

    let stdoutBuffer = ''
    let stderrBuffer = ''

    pythonProcess.stdout.on('data', (data) => {
      stdoutBuffer += data.toString()
    })

    pythonProcess.stderr.on('data', (data) => {
      stderrBuffer += data.toString()
    })

    // Set 5 minute timeout
    const timeout = setTimeout(() => {
      pythonProcess.kill()
      reject(new Error('Scraping timeout after 5 minutes'))
    }, 5 * 60 * 1000) // 5 minutes

    pythonProcess.on('close', (code) => {
      clearTimeout(timeout)
      
      // Wait a bit more to ensure all data is flushed
      setTimeout(() => {
        const finalStdout = stdoutBuffer
        const finalStderr = stderrBuffer
      
        if (code === 0 || code === null) {
          try {
            // The JSON should be the complete output from stdout
            // Find the JSON object (it starts with { and ends with })
            let jsonStr = finalStdout.trim()
            
            // Remove any leading text before the first {
            const firstBrace = jsonStr.indexOf('{')
            if (firstBrace > 0) {
              jsonStr = jsonStr.substring(firstBrace)
            }
            
            // Find the matching closing brace (handle nested objects and arrays)
            let braceCount = 0
            let bracketCount = 0
            let inString = false
            let escapeNext = false
            let lastBrace = -1
            
            for (let i = 0; i < jsonStr.length; i++) {
              const char = jsonStr[i]
              
              if (escapeNext) {
                escapeNext = false
                continue
              }
              
              if (char === '\\') {
                escapeNext = true
                continue
              }
              
              if (char === '"') {
                inString = !inString
                continue
              }
              
              if (!inString) {
                if (char === '{') braceCount++
                if (char === '}') {
                  braceCount--
                  if (braceCount === 0 && bracketCount === 0) {
                    lastBrace = i
                    break
                  }
                }
                if (char === '[') bracketCount++
                if (char === ']') bracketCount--
              }
            }
            
            if (lastBrace > 0) {
              jsonStr = jsonStr.substring(0, lastBrace + 1)
            }
            
            // Parse the JSON
            const result = JSON.parse(jsonStr)
            if (result.success && result.flights && Array.isArray(result.flights)) {
              console.log(`Successfully parsed ${result.flights.length} flights from scraper`)
              resolve(result.flights)
            } else if (result.error) {
              reject(new Error(result.error))
            } else {
              console.log('No flights in result, returning empty array')
              resolve([])
            }
          } catch (parseError: any) {
            // If JSON parsing fails, check if there's an error message
            if (finalStdout.includes('error') || finalStderr.includes('error')) {
              const errorMatch = finalStdout.match(/"error"\s*:\s*"([^"]+)"/) || finalStderr.match(/"error"\s*:\s*"([^"]+)"/)
              if (errorMatch) {
                reject(new Error(errorMatch[1]))
              } else {
                reject(new Error(`Scraper error: ${finalStderr || finalStdout.substring(0, 500)}`))
              }
            } else {
              // Log the actual error for debugging
              console.error('JSON Parse Error:', parseError.message)
              console.error('Stdout length:', finalStdout.length)
              console.error('Stdout preview:', finalStdout.substring(0, 1000))
              reject(new Error(`Failed to parse scraper output: ${parseError.message}. Output length: ${finalStdout.length}`))
            }
          }
        } else {
          // Check stderr for error JSON
          try {
            const errorMatch = finalStderr.match(/\{[\s\S]*"error"[\s\S]*\}/)
            if (errorMatch) {
              const errorObj = JSON.parse(errorMatch[0])
              reject(new Error(errorObj.error || 'Unknown error'))
            } else {
              reject(new Error(`Scraper exited with code ${code}: ${finalStderr || finalStdout.substring(0, 500)}`))
            }
          } catch {
            reject(new Error(`Scraper exited with code ${code}: ${finalStderr || finalStdout.substring(0, 500)}`))
          }
        }
      }, 200) // Small delay to ensure all data is flushed
    })

    pythonProcess.on('error', (error) => {
      clearTimeout(timeout)
      reject(error)
    })
  })
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const from = searchParams.get('from')
    const to = searchParams.get('to')
    const date = searchParams.get('date') // Format: YYYY-MM-DD

    if (!from || !to || !date) {
      return NextResponse.json(
        { error: 'Missing required parameters: from, to, date' },
        { status: 400 }
      )
    }

    // Convert date format if needed (frontend sends YYYY-MM-DD, scraper expects DD-MM-YYYY)
    const dateParts = date.split('-')
    const formattedDate = `${dateParts[2]}-${dateParts[1]}-${dateParts[0]}` // DD-MM-YYYY

    let scrapedFlights: FlightData[] = []
    let fallbackFlights: FlightData[] = []

    // Always get fallback data (if available)
    fallbackFlights = getHTMLSnapshotData(from, to)

    try {
      // Try to scrape with 5 minute timeout
      console.log(`Starting scrape for ${from} -> ${to} on ${formattedDate}`)
      const pythonFlights = await runScraper(from, to, formattedDate)
      
      if (pythonFlights && pythonFlights.length > 0) {
        scrapedFlights = convertToFrontendFormat(pythonFlights)
        console.log(`Successfully scraped ${scrapedFlights.length} flights`)
      } else {
        console.log('No flights returned from scraper')
      }
    } catch (error: any) {
      console.error('Scraping failed:', error.message)
      // Scraping failed, but we'll still return fallback if available
    }

    // Sort both by price (low to high)
    const sortByPrice = (a: FlightData, b: FlightData) => {
      const priceA = parseInt(a.cashPrice.replace(/[₹,\s]/g, '')) || 999999999
      const priceB = parseInt(b.cashPrice.replace(/[₹,\s]/g, '')) || 999999999
      return priceA - priceB
    }

    scrapedFlights.sort(sortByPrice)
    fallbackFlights.sort(sortByPrice)

    return NextResponse.json({ 
      scrapedFlights,
      fallbackFlights,
      hasScrapedData: scrapedFlights.length > 0,
      hasFallbackData: fallbackFlights.length > 0
    })
  } catch (error: any) {
    console.error('Error in scrape API:', error)
    return NextResponse.json(
      { error: 'Failed to fetch flights', details: error.message },
      { status: 500 }
    )
  }
}

