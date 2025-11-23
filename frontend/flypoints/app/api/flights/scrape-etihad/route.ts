import { NextResponse } from 'next/server'
import { spawn } from 'child_process'
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
      
      // Etihad uses 'price' field
      if (flight.price && flight.price !== 'N/A') {
        const cleaned = cleanPrice(flight.price)
        if (cleaned !== 'N/A') {
          priceValue = parseInt(cleaned) || 0
          cashPrice = priceValue > 0 ? `₹${formatIndianNumber(cleaned)}` : 'N/A'
        }
      }

      // Filter out flights with no price or 0 price
      if (cashPrice === 'N/A' || priceValue === 0) {
        return null
      }

      const pointsPrice = flight.award_points && flight.award_points !== 'N/A'
        ? `${formatIndianNumber(flight.award_points)} points`
        : 'N/A'

      return {
        airline: flight.airline || 'Etihad Airways',
        flightNumber: flight.flight_number || 'N/A',
        departureTime: flight.departure_time || 'N/A',
        arrivalTime: flight.arrival_time || 'N/A',
        duration: flight.duration || 'N/A',
        cashPrice,
        pointsPrice,
      }
    })
    .filter((flight): flight is FlightData => flight !== null) // Remove null entries
}

// Run Python scraper with timeout
function runScraper(origin: string, destination: string, date: string): Promise<any[]> {
  return new Promise((resolve, reject) => {
    // Use the API wrapper script that outputs JSON
    // Path from frontend/flypoints/app/api/flights/scrape-etihad/route.ts to attempt1etihad/etihad_scraper_api.py
    const scraperPath = path.join(process.cwd(), '..', '..', 'attempt1etihad', 'etihad_scraper_api.py')
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
            console.error('Failed to parse Etihad scraper output:', parseError.message)
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

    try {
      console.log(`Starting Etihad scrape for ${from} -> ${to} on ${formattedDate}`)
      const pythonFlights = await runScraper(from, to, formattedDate)
      
      if (pythonFlights && pythonFlights.length > 0) {
        scrapedFlights = convertToFrontendFormat(pythonFlights)
        console.log(`Successfully scraped ${scrapedFlights.length} Etihad flights`)
      } else {
        console.log('No flights returned from Etihad scraper')
      }
    } catch (error: any) {
      console.error('Etihad scraping failed:', error.message)
      // Return empty array on error - frontend will handle it
    }

    // Sort flights by price (low to high)
    const sortFlights = (flights: FlightData[]) => {
      return [...flights].sort((a, b) => {
        const priceA = parseInt(cleanPrice(a.cashPrice)) || Infinity
        const priceB = parseInt(cleanPrice(b.cashPrice)) || Infinity
        return priceA - priceB
      })
    }

    return NextResponse.json({ 
      scrapedFlights: sortFlights(scrapedFlights)
    })
  } catch (error: any) {
    console.error('Error in Etihad scrape API:', error)
    return NextResponse.json(
      { error: 'Failed to fetch Etihad flights', details: error.message },
      { status: 500 }
    )
  }
}

