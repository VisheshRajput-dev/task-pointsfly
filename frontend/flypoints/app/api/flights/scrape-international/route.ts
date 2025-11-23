import { NextResponse } from 'next/server'
import { spawn } from 'child_process'
import path from 'path'
import fs from 'fs'

// Import HTML parsing functions from the existing route
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

  return flights
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

// Get HTML snapshot data for fallback
function getHTMLSnapshotData(from: string, to: string): FlightData[] {
  const routeMap: Record<string, { file: string; airline: 'emirates' | 'spicejet' }> = {
    'DEL-LON': { file: 'International/del-lon- Emirates.html', airline: 'emirates' },
    'DEL-LHR': { file: 'International/del-lon- Emirates.html', airline: 'emirates' }, 
    'LON-DEL': { file: 'International/lon-del-Emirates.html', airline: 'emirates' },
    'LHR-DEL': { file: 'International/lon-del-Emirates.html', airline: 'emirates' }, 
    'DEL-DXB': { file: 'International/del-dxb- Emirates.html', airline: 'emirates' },
    'DXB-DEL': { file: 'International/dxb-del-Emirates.html', airline: 'emirates' },
  }
  
  const routeKey = `${from}-${to}`
  const routeInfo = routeMap[routeKey]
  
  if (!routeInfo) {
    return []
  }
  
  const filePath = path.join(process.cwd(), 'samples', routeInfo.file)
  
  if (!fs.existsSync(filePath)) {
    return []
  }
  
  try {
    const htmlContent = fs.readFileSync(filePath, 'utf-8')
    if (routeInfo.airline === 'emirates') {
      return parseEmiratesFlights(htmlContent)
    }
    return []
  } catch (error) {
    console.error('Error reading HTML snapshot:', error)
    return []
  }
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
  
  const str = numValue.toString()
  const len = str.length
  
  if (len <= 3) {
    return str
  }
  
  let result = str.slice(-3)
  let remaining = str.slice(0, -3)
  
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
    .filter((flight): flight is FlightData => flight !== null) // Remove null entries
}

// Run Python scraper with timeout
function runScraper(origin: string, destination: string, date: string): Promise<any[]> {
  return new Promise((resolve, reject) => {
    // Use the API wrapper script that outputs JSON
    // Path from frontend/flypoints/app/api/flights/scrape-international/route.ts to attempt1international/spicejet_scraper_api.py
    const scraperPath = path.join(process.cwd(), '..', '..', 'attempt1international', 'spicejet_scraper_api.py')
    const pythonCommand = process.platform === 'win32' ? 'python' : 'python3'
    
    const pythonProcess = spawn(pythonCommand, [scraperPath, origin, destination, date], {
      cwd: path.dirname(scraperPath),
      stdio: ['pipe', 'pipe', 'pipe'],
    })

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
              
              if (char === '"' && !escapeNext) {
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
            
            const result = JSON.parse(jsonStr)
            
            if (result.success && result.flights) {
              resolve(result.flights)
            } else if (result.error) {
              reject(new Error(result.error))
            } else {
              resolve([])
            }
          } catch (parseError: any) {
            console.error('Failed to parse scraper output:', parseError.message)
            console.error('Output:', finalStdout.substring(0, 500))
            // Try to parse error from stderr
            try {
              const errorJson = JSON.parse(finalStderr.trim())
              if (errorJson.error) {
                reject(new Error(errorJson.error))
              } else {
                reject(new Error(`Failed to parse scraper output: ${parseError.message}`))
              }
            } catch {
              reject(new Error(`Failed to parse scraper output: ${parseError.message}. Output: ${finalStdout.substring(0, 200)}`))
            }
          }
        } else {
          // Process exited with error code
          try {
            const errorJson = JSON.parse(finalStderr.trim())
            if (errorJson.error) {
              reject(new Error(errorJson.error))
            } else {
              reject(new Error(`Scraper exited with code ${code}`))
            }
          } catch {
            reject(new Error(`Scraper exited with code ${code}. Error: ${finalStderr.substring(0, 200)}`))
          }
        }
      }, 100)
    })
  })
}

export async function GET(request: Request) {
  try {
    const { searchParams } = new URL(request.url)
    const from = searchParams.get('from')
    const to = searchParams.get('to')
    const date = searchParams.get('date')

    if (!from || !to || !date) {
      return NextResponse.json(
        { error: 'Missing required parameters: from, to, date' },
        { status: 400 }
      )
    }

    // Format date as DD-MM-YYYY for the scraper (frontend sends YYYY-MM-DD)
    const dateParts = date.split('-')
    const formattedDate = dateParts.length === 3 
      ? `${dateParts[2]}-${dateParts[1]}-${dateParts[0]}` // DD-MM-YYYY
      : date

    let scrapedFlights: FlightData[] = []
    let fallbackFlights: FlightData[] = []

    try {
      console.log(`Starting international scrape for ${from} -> ${to} on ${formattedDate}`)
      const pythonFlights = await runScraper(from, to, formattedDate)
      
      if (pythonFlights && pythonFlights.length > 0) {
        scrapedFlights = convertToFrontendFormat(pythonFlights)
        console.log(`Successfully scraped ${scrapedFlights.length} international flights`)
      } else {
        console.log('No flights returned from international scraper, trying fallback')
      }
    } catch (error: any) {
      console.error('International scraping failed:', error.message)
    }

    // Always attempt to get HTML snapshot data for fallback
    fallbackFlights = getHTMLSnapshotData(from, to)
    if (fallbackFlights.length > 0) {
      console.log(`Using HTML snapshot fallback: ${fallbackFlights.length} flights`)
    } else {
      console.log('No HTML snapshot fallback data available.')
    }

    // Sort all flights by price (low to high)
    const sortFlights = (flights: FlightData[]) => {
      return [...flights].sort((a, b) => {
        const priceA = parseInt(cleanPrice(a.cashPrice)) || Infinity
        const priceB = parseInt(cleanPrice(b.cashPrice)) || Infinity
        return priceA - priceB
      })
    }

    return NextResponse.json({ 
      scrapedFlights: sortFlights(scrapedFlights), 
      fallbackFlights: sortFlights(fallbackFlights) 
    })
  } catch (error: any) {
    console.error('Error in international scrape API:', error)
    return NextResponse.json(
      { error: 'Failed to fetch flights', details: error.message },
      { status: 500 }
    )
  }
}

