"use client"

import { useState, useEffect } from "react"
import { CalendarIcon, Plane, Search, Home as HomeIcon, Globe, ChevronDown, Check, ArrowUpDown, Filter } from "lucide-react"
import { format } from "date-fns"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Calendar } from "@/components/ui/calendar"
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover"
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command"
import { cn } from "@/lib/utils"

// Top 7 busiest airports in India
const domesticAirports = [
  { code: "DEL", city: "Delhi", name: "Indira Gandhi International Airport" },
  { code: "BOM", city: "Mumbai", name: "Chhatrapati Shivaji Maharaj International Airport" },
  { code: "BLR", city: "Bangalore", name: "Kempegowda International Airport" },
    { code: "MAA", city: "Chennai", name: "Chennai International Airport" },
    { code: "CCU", city: "Kolkata", name: "Netaji Subhas Chandra Bose International Airport" },
    { code: "HYD", city: "Hyderabad", name: "Rajiv Gandhi International Airport" },
    { code: "COK", city: "Kochi", name: "Cochin International Airport" },
  ]

  // Top 5 Indian airports for international flights
  const topIndianAirports = [
    { code: "DEL", city: "Delhi", name: "Indira Gandhi International Airport" },
    { code: "BOM", city: "Mumbai", name: "Chhatrapati Shivaji Maharaj International Airport" },
    { code: "BLR", city: "Bangalore", name: "Kempegowda International Airport" },
    { code: "MAA", city: "Chennai", name: "Chennai International Airport" },
    { code: "CCU", city: "Kolkata", name: "Netaji Subhas Chandra Bose International Airport" },
  ]

  // Top 10 world's busiest airports
  const topWorldAirports = [
    { code: "ATL", city: "Atlanta", name: "Hartsfield-Jackson Atlanta International Airport", country: "USA" },
    { code: "DXB", city: "Dubai", name: "Dubai International Airport", country: "UAE" },
    { code: "DOH", city: "Doha", name: "Hamad International Airport", country: "Qatar" },
    { code: "LHR", city: "London", name: "Heathrow Airport", country: "UK" },
    { code: "IST", city: "Istanbul", name: "Istanbul Airport", country: "Turkey" },
    { code: "JFK", city: "New York", name: "John F. Kennedy International Airport", country: "USA" },
    { code: "CDG", city: "Paris", name: "Charles de Gaulle Airport", country: "France" },
    { code: "AMS", city: "Amsterdam", name: "Amsterdam Airport Schiphol", country: "Netherlands" },
    { code: "FRA", city: "Frankfurt", name: "Frankfurt Airport", country: "Germany" },
    { code: "SIN", city: "Singapore", name: "Singapore Changi Airport", country: "Singapore" },
  ]

// Legacy arrays - keeping for backward compatibility but not used
const indianCitiesInternational = [
  { code: "DEL", city: "Delhi", name: "Indira Gandhi International Airport" },
]

const internationalAirports = [
  { code: "LON", city: "London", name: "London (All Airports)" },
  { code: "LHR", city: "London", name: "London Heathrow Airport" },
  { code: "DXB", city: "Dubai", name: "Dubai International Airport" },
]

interface Airport {
  code: string
  city: string
  name: string
}

export default function Home() {
  const [flightType, setFlightType] = useState<string>("domestic")
  const [from, setFrom] = useState<Airport | null>(null)
  const [to, setTo] = useState<Airport | null>(null)
  const [date, setDate] = useState<Date>()
  const [fromOpen, setFromOpen] = useState(false)
  const [toOpen, setToOpen] = useState(false)
  const [flights, setFlights] = useState<any[]>([])
  const [scrapedFlights, setScrapedFlights] = useState<any[]>([])
  const [fallbackFlights, setFallbackFlights] = useState<any[]>([])
  const [loading, setLoading] = useState(false)
  const [showAllFlights, setShowAllFlights] = useState(false)
  const [showAllFallback, setShowAllFallback] = useState(false)
  const [hasSearched, setHasSearched] = useState(false)
  const [sortBy, setSortBy] = useState<'price' | 'duration' | 'departure'>('price')
  const [filterBy, setFilterBy] = useState<'all' | 'direct' | 'connecting'>('all')
  const [advancedSearch, setAdvancedSearch] = useState(false)
  const [etihadFlights, setEtihadFlights] = useState<any[]>([])
  const [airlineFilter, setAirlineFilter] = useState<'all' | 'spicejet' | 'etihad'>('all')
  const [loadingProgress, setLoadingProgress] = useState(0)
  const [currentFunFact, setCurrentFunFact] = useState(0)

  // Fun facts about flights and travel
  const funFacts = [
    "The world's busiest airport is Hartsfield-Jackson Atlanta International Airport, handling over 100 million passengers annually!",
    "The longest commercial flight in the world is Singapore Airlines' route from Singapore to New York, taking over 18 hours!",
    "A Boeing 747 has about 6 million parts, including 171 miles of wiring!",
    "The first commercial flight took off in 1914, carrying a single passenger from St. Petersburg to Tampa, Florida!",
    "Airplanes can fly even if one engine fails - they're designed to be safe with multiple engines!",
    "The speed of sound is about 767 mph at sea level - that's how fast supersonic jets travel!",
    "Pilots and co-pilots must eat different meals to prevent food poisoning from affecting both crew members!",
    "The world's shortest commercial flight is in Scotland - it takes just 47 seconds from Westray to Papa Westray!",
    "Airplane windows have tiny holes at the bottom to regulate air pressure and prevent them from breaking!",
    "The Wright Brothers' first flight in 1903 was shorter than the wingspan of a Boeing 747!"
  ]

  // Rotate fun facts every 8 seconds when loading (slower rotation)
  useEffect(() => {
    if (loading) {
      const funFactInterval = setInterval(() => {
        setCurrentFunFact((prev) => (prev + 1) % funFacts.length)
      }, 8000) // Changed from 3000 to 8000 (8 seconds)
      return () => clearInterval(funFactInterval)
    }
  }, [loading, funFacts.length])

  // Simulate loading progress optimized for actual scraping times
  useEffect(() => {
    if (loading) {
      setLoadingProgress(0)
      
      // Determine target time based on flight type
      const targetTime = flightType === 'domestic' 
        ? 2.5 * 60 * 1000 // 2.5 minutes for domestic
        : 3.5 * 60 * 1000 // 3.5 minutes for international
      
      const startTime = Date.now()
      
      const progressInterval = setInterval(() => {
        const elapsed = Date.now() - startTime
        const progress = Math.min((elapsed / targetTime) * 90, 90) // Cap at 90% until search completes
        
        setLoadingProgress(progress)
      }, 200) // Update every 200ms for smooth progress
      
      return () => clearInterval(progressInterval)
    } else {
      setLoadingProgress(0)
    }
  }, [loading, flightType])

  const getFromAirports = () => {
    let airports
    if (flightType === "domestic") {
      airports = domesticAirports
    } else {
      // For international: top 5 Indian airports + top 10 world airports
      airports = [...topIndianAirports, ...topWorldAirports]
    }
    
    if (to) {
      return airports.filter(airport => airport.code !== to.code)
    }
    return airports
  }

  const getToAirports = () => {
    let airports
    if (flightType === "domestic") {
      airports = domesticAirports
    } else {
      // For international: only world airports (no Indian airports in "To" field)
      airports = topWorldAirports
    }
    
    if (from) {
      return airports.filter(airport => airport.code !== from.code)
    }
    return airports
  }

  const handleFlightTypeChange = () => {
    const newType = flightType === "domestic" ? "international" : "domestic"
    setFlightType(newType)
    setFrom(null)
    setTo(null)
    setDate(undefined)
    setFlights([]) 
    setScrapedFlights([])
    setFallbackFlights([])
    setEtihadFlights([])
    setShowAllFlights(false) 
    setShowAllFallback(false)
    setHasSearched(false) // Reset search status when changing flight type
    setSortBy('price')
    setFilterBy('all')
    setAdvancedSearch(false) // Reset advanced search when changing flight type
    setAirlineFilter('all') // Reset airline filter
  }

  const handleSearch = async () => {
    if (!from || !to || !date) {
      if (!from) {
        alert('Please select your departure airport')
        return
      }
      if (!to) {
        alert('Please select your destination airport')
        return
      }
      if (!date) {
        alert('Please select your travel date')
        return
      }
    }

    if (from.code === to.code) {
      alert('Departure and destination airports cannot be the same. Please select different airports.')
      return
    }

    setLoading(true)
    setLoadingProgress(0)
    setCurrentFunFact(Math.floor(Math.random() * funFacts.length))
    setFlights([])
    setScrapedFlights([])
    setFallbackFlights([])
    setShowAllFlights(false) 
    setShowAllFallback(false)
    setHasSearched(false) // Reset search status 

    try {
      // For domestic flights
      if (flightType === 'domestic') {
        // Format date as YYYY-MM-DD
        const formattedDate = format(date, 'yyyy-MM-dd')
        
        try {
          const response = await fetch(`/api/flights/scrape?from=${from.code}&to=${to.code}&date=${formattedDate}`)
          const data = await response.json()
          
          // Logic: scrapedFlights + fallbackFlights (both if available)
          // 1) SpiceJet data + HTML snapshot data (both shown)
          // 2) If SpiceJet fails, only HTML snapshot data
          // 3) If both fail, fallback msg (handled by processedAllFlights.length === 0)
          const scraped = data.scrapedFlights || []
          const fallback = data.fallbackFlights || []
          
          console.log(`Domestic: Scraped=${scraped.length}, Fallback=${fallback.length}`)
          
          setScrapedFlights(scraped)
          setFallbackFlights(fallback)
          setEtihadFlights([])
          
          // Combine for display: scraped + fallback (both shown together)
          setFlights([...scraped, ...fallback])
        } catch (error) {
          console.error('Error fetching domestic flights:', error)
          setScrapedFlights([])
          setFallbackFlights([])
          setEtihadFlights([])
          setFlights([])
        }
        
        setHasSearched(true)
      } else {
        // For international flights
        const formattedDate = format(date, 'yyyy-MM-dd')
        
        if (advancedSearch) {
          // Advanced Search ON: Etihad + SpiceJet + HTML Snapshot
          const [spicejetResponse, etihadResponse] = await Promise.allSettled([
            fetch(`/api/flights/scrape-international?from=${from.code}&to=${to.code}&date=${formattedDate}`),
            fetch(`/api/flights/scrape-etihad?from=${from.code}&to=${to.code}&date=${formattedDate}`)
          ])
          
          // Process SpiceJet results
          let spicejetScraped: any[] = []
          let spicejetFallback: any[] = []
          
          if (spicejetResponse.status === 'fulfilled') {
            try {
              const spicejetData = await spicejetResponse.value.json()
              spicejetScraped = spicejetData.scrapedFlights || []
              spicejetFallback = spicejetData.fallbackFlights || []
            } catch (error) {
              console.error('Error parsing SpiceJet response:', error)
            }
        } else {
            console.error('SpiceJet scraper failed:', spicejetResponse.reason)
          }
          
          // Process Etihad results
          let etihadFlightsData: any[] = []
          
          if (etihadResponse.status === 'fulfilled') {
            try {
              const etihadData = await etihadResponse.value.json()
              etihadFlightsData = etihadData.scrapedFlights || []
            } catch (error) {
              console.error('Error parsing Etihad response:', error)
            }
          } else {
            console.error('Etihad scraper failed:', etihadResponse.reason)
          }
          
          // Set state
          setScrapedFlights(spicejetScraped)
          setFallbackFlights(spicejetFallback)
          setEtihadFlights(etihadFlightsData)
          
          console.log(`International (Advanced ON): Etihad=${etihadFlightsData.length}, SpiceJet Scraped=${spicejetScraped.length}, SpiceJet Fallback=${spicejetFallback.length}`)
          
          // Combine all: Etihad + SpiceJet scraped + SpiceJet fallback (HTML snapshot)
          // Logic: 
          // 1) Etihad + SpiceJet scraped + HTML snapshot (all shown)
          // 2) If SpiceJet fails, Etihad + HTML snapshot
          // 3) If both fail, only HTML snapshot
          // 4) If everything fails, fallback msg (handled by processedAllFlights.length === 0)
          setFlights([
            ...etihadFlightsData,
            ...spicejetScraped,
            ...spicejetFallback
          ])
        } else {
          // Advanced Search OFF: SpiceJet + HTML Snapshot only
          try {
            const spicejetResponse = await fetch(`/api/flights/scrape-international?from=${from.code}&to=${to.code}&date=${formattedDate}`)
            const spicejetData = await spicejetResponse.json()
            
            const scraped = spicejetData.scrapedFlights || []
            const fallback = spicejetData.fallbackFlights || []
            
            console.log(`International (Advanced OFF): SpiceJet Scraped=${scraped.length}, Fallback=${fallback.length}`)
            
            setScrapedFlights(scraped)
            setFallbackFlights(fallback)
            setEtihadFlights([])
            
            // Combine: SpiceJet scraped + HTML snapshot (both shown together)
            // Logic:
            // 1) SpiceJet international + HTML snapshot (both shown)
            // 2) If SpiceJet fails, only HTML snapshot
            // 3) If both fail, fallback msg (handled by processedAllFlights.length === 0)
            setFlights([...scraped, ...fallback])
          } catch (error) {
            console.error('Error fetching international flights:', error)
            setScrapedFlights([])
            setFallbackFlights([])
            setEtihadFlights([])
            setFlights([])
        }
        }
        
        setHasSearched(true)
      }
    } catch (error) {
      console.error('Error fetching flights:', error)
      alert('Oops! Something went wrong while searching for flights. Please try again.')
    } finally {
      // Complete the progress bar
      setLoadingProgress(100)
      // Wait a moment to show 100%, then hide loading
      setTimeout(() => {
      setLoading(false)
        setLoadingProgress(0)
      }, 800)
    }
  }

  // Helper function to extract price number for sorting
  const getPriceValue = (price: string): number => {
    return parseInt(price.replace(/[₹,\s]/g, '')) || 999999999
  }

  // Helper function to extract duration in minutes for sorting
  const getDurationMinutes = (duration: string): number => {
    const match = duration.match(/(\d+)h\s*(\d+)?m?/i)
    if (match) {
      const hours = parseInt(match[1]) || 0
      const minutes = parseInt(match[2]) || 0
      return hours * 60 + minutes
    }
    return 999999
  }

  // Sort flights based on selected sort option
  const sortFlights = (flightsToSort: any[]) => {
    const sorted = [...flightsToSort]
    switch (sortBy) {
      case 'price':
        sorted.sort((a, b) => getPriceValue(a.cashPrice) - getPriceValue(b.cashPrice))
        break
      case 'duration':
        sorted.sort((a, b) => getDurationMinutes(a.duration) - getDurationMinutes(b.duration))
        break
      case 'departure':
        sorted.sort((a, b) => a.departureTime.localeCompare(b.departureTime))
        break
    }
    return sorted
  }

  // Filter flights by route type and airline
  const filterFlights = (flightsToFilter: any[]) => {
    let filtered = flightsToFilter
    
    // Apply route type filter (direct/connecting)
    if (filterBy === 'direct') {
      filtered = filtered.filter(f => {
        const duration = f.duration || ''
        // Simple heuristic: direct flights usually have shorter durations
        const hours = parseInt(duration.match(/(\d+)h/)?.[1] || '0')
        return hours < 24 && !duration.includes('m') || (duration.match(/\d+h\s*\d+m/) && hours < 24)
      })
    } else if (filterBy === 'connecting') {
      filtered = filtered.filter(f => {
        const duration = f.duration || ''
        const hours = parseInt(duration.match(/(\d+)h/)?.[1] || '0')
        return hours >= 24 || duration.includes('connecting')
      })
    }
    
    // Apply airline filter
    if (airlineFilter === 'spicejet') {
      filtered = filtered.filter(f => 
        f.airline?.toLowerCase().includes('spicejet') || 
        f.airline?.toLowerCase().includes('spice')
      )
    } else if (airlineFilter === 'etihad') {
      filtered = filtered.filter(f => 
        f.airline?.toLowerCase().includes('etihad')
      )
    }
    // 'all' - no airline filter
    
    return filtered
  }

  // Process all flights (scraped, fallback, and Etihad)
  const allFlightsToProcess = [...scrapedFlights, ...fallbackFlights, ...etihadFlights]
  const processedAllFlights = sortFlights(filterFlights(allFlightsToProcess))
  
  // Group flights by airline
  const flightsByAirline = processedAllFlights.reduce((acc, flight) => {
    const airline = flight.airline || 'Unknown'
    if (!acc[airline]) {
      acc[airline] = []
    }
    acc[airline].push(flight)
    return acc
  }, {} as Record<string, any[]>)
  
  // Separate flights by airline for display
  // SpiceJet flights (includes both scraped and fallback SpiceJet flights)
  const spicejetFlights = processedAllFlights.filter(f => 
    f.airline?.toLowerCase().includes('spicejet') || 
    f.airline?.toLowerCase().includes('spice')
  )
  
  // Etihad flights
  const etihadProcessedFlights = processedAllFlights.filter(f => 
    f.airline?.toLowerCase().includes('etihad')
  )
  
  // HTML Snapshot flights (IndiGo for domestic, Emirates for international)
  // These are in fallbackFlights but may have different airline names
  const htmlSnapshotFlights = processedAllFlights.filter(f => 
    fallbackFlights.includes(f) && 
    !f.airline?.toLowerCase().includes('spicejet') && 
    !f.airline?.toLowerCase().includes('spice') &&
    !f.airline?.toLowerCase().includes('etihad')
  )
  
  // Legacy variables for backward compatibility
  const processedScrapedFlights = spicejetFlights.filter(f => scrapedFlights.includes(f))
  const processedFallbackFlights = spicejetFlights.filter(f => fallbackFlights.includes(f))

  // Display logic:
  // - Show all scraped flights
  // - Show 3-4 fallback flights initially, with "Show All" button if more available
  const displayedFallbackFlights = showAllFallback 
    ? processedFallbackFlights 
    : processedFallbackFlights.slice(0, 4)
  const hasMoreFallbackFlights = processedFallbackFlights.length > 4

  return (
    <div className="min-h-screen bg-gradient-to-br from-background via-background to-muted/20 flex items-center justify-center p-4 relative">
      {/* Loading Overlay */}
      {loading && (
        <div className="fixed inset-0 z-50 flex items-center justify-center bg-background/90 backdrop-blur-md">
          <div className="flex flex-col items-center justify-center space-y-10 px-8 max-w-lg text-center">
            {/* Loading Spinner - Centered */}
            <div className="w-32 h-32 flex items-center justify-center mx-auto relative">
              <div className="relative">
                <div className="w-32 h-32 border-4 border-primary/20 border-t-primary rounded-full animate-spin" />
                <div className="absolute inset-0 flex items-center justify-center">
                  <Plane className="w-8 h-8 text-primary animate-pulse" />
                </div>
              </div>
            </div>
            
            {/* Fun Fact - Slower rotation */}
            <div className="space-y-4 min-h-[120px] flex flex-col justify-center">
              <p className="text-xl font-bold bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                ✈️ Did you know?
              </p>
              <p className="text-base text-foreground/80 leading-relaxed px-4 transition-opacity duration-500">
                {funFacts[currentFunFact]}
              </p>
            </div>
            
            {/* Loading Percentage - Enhanced */}
            <div className="space-y-3 w-full max-w-md">
              <div className="flex items-center justify-between text-base font-semibold text-foreground">
                <span className="flex items-center gap-2">
                  <span className="animate-spin">⏳</span>
                  Searching flights...
                </span>
                <span className="text-primary font-bold text-lg">{Math.round(loadingProgress)}%</span>
              </div>
              <div className="w-full h-3 bg-muted/50 rounded-full overflow-hidden shadow-inner">
                <div 
                  className="h-full bg-gradient-to-r from-primary via-primary/90 to-primary/70 rounded-full transition-all duration-500 ease-out relative overflow-hidden"
                  style={{ width: `${loadingProgress}%` }}
                >
                  <div className="absolute inset-0 bg-gradient-to-r from-transparent via-white/20 to-transparent animate-shimmer" />
                </div>
              </div>
              <p className="text-xs text-muted-foreground">
                {flightType === 'domestic' 
                  ? 'This may take 2-3 minutes...' 
                  : 'This may take 3-4 minutes...'}
              </p>
            </div>
          </div>
        </div>
      )}
      
      <div className="w-full max-w-4xl">
        <Card className="border-2 shadow-2xl backdrop-blur-sm bg-card/95 transition-all duration-300 hover:shadow-3xl hover:border-primary/20 hover:scale-[1.01]">
          <CardHeader className="text-center space-y-2 pb-6">
            <div className="flex items-center justify-center gap-2 mb-2">
              <Plane className="h-8 w-8 text-primary" />
              <CardTitle className="text-3xl font-bold bg-gradient-to-r from-primary to-primary/60 bg-clip-text text-transparent">
                Flight Search
              </CardTitle>
            </div>
            <p className="text-muted-foreground text-sm">
              Find the best flights for your journey
            </p>
          </CardHeader>
          <CardContent className="space-y-6">
            {}
            <div className="flex flex-col items-center space-y-4">
              <Label className="text-xs font-medium text-muted-foreground uppercase tracking-wider">
                Flight Type
              </Label>
              <div
                onClick={handleFlightTypeChange}
                className="relative inline-flex items-center rounded-xl bg-muted/40 p-1.5 border border-border/60 cursor-pointer transition-all duration-300 hover:border-primary/40 hover:bg-muted/60 hover:shadow-md group backdrop-blur-sm"
                role="button"
                tabIndex={0}
                onKeyDown={(e) => {
                  if (e.key === "Enter" || e.key === " ") {
                    e.preventDefault()
                    handleFlightTypeChange()
                  }
                }}
              >
                {}
                <div
                  className={cn(
                    "absolute h-11 rounded-lg bg-primary shadow-lg shadow-primary/30 transition-all duration-500 ease-[cubic-bezier(0.4,0,0.2,1)]",
                    "before:absolute before:inset-0 before:rounded-lg before:bg-gradient-to-r before:from-primary before:via-primary/90 before:to-primary",
                    "after:absolute after:inset-0 after:rounded-lg after:bg-gradient-to-br after:from-white/25 after:via-transparent after:to-transparent",
                    flightType === "domestic" 
                      ? "left-1.5 w-[calc(50%-0.375rem)]" 
                      : "left-[calc(50%+0.375rem)] w-[calc(50%-0.375rem)]"
                  )}
                />

                {}
                <div className="relative flex items-center gap-6 px-3">
                  {}
                  <div
                    className={cn(
                      "relative z-10 flex items-center gap-2.5 px-5 py-2.5 transition-all duration-300 min-w-[130px] justify-center",
                      flightType === "domestic"
                        ? "text-primary-foreground"
                        : "text-muted-foreground group-hover:text-foreground/80"
                    )}
                  >
                    <HomeIcon
                      className={cn(
                        "h-5 w-5 transition-all duration-300",
                        flightType === "domestic" 
                          ? "scale-110 text-primary-foreground drop-shadow-sm" 
                          : "scale-100"
                      )}
                    />
                    <span className={cn(
                      "font-semibold text-sm whitespace-nowrap transition-all",
                      flightType === "domestic" && "drop-shadow-sm"
                    )}>
                      Domestic
                    </span>
                  </div>

                  {}
                  <div
                    className={cn(
                      "relative z-10 flex items-center gap-2.5 px-5 py-2.5 transition-all duration-300 min-w-[130px] justify-center",
                      flightType === "international"
                        ? "text-primary-foreground"
                        : "text-muted-foreground group-hover:text-foreground/80"
                    )}
                  >
                    <Globe
                      className={cn(
                        "h-5 w-5 transition-all duration-300",
                        flightType === "international" 
                          ? "scale-110 text-primary-foreground drop-shadow-sm rotate-12" 
                          : "scale-100"
                      )}
                    />
                    <span className={cn(
                      "font-semibold text-sm whitespace-nowrap transition-all",
                      flightType === "international" && "drop-shadow-sm"
                    )}>
                      International
                    </span>
                  </div>
                </div>
              </div>
              
            </div>

            {}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
              {}
              <div className="space-y-2">
                <Label htmlFor="from" className="text-sm font-medium">
                  From
                </Label>
                <Popover open={fromOpen} onOpenChange={setFromOpen}>
                  <PopoverTrigger asChild>
                    <Button
                      id="from"
                      variant="outline"
                      role="combobox"
                      aria-expanded={fromOpen}
                      className={cn(
                        "w-full h-14 justify-between text-left font-normal text-base",
                        "border-2 transition-all duration-200",
                        "hover:border-primary/50 hover:bg-primary/5 hover:shadow-md",
                        "focus:border-primary focus:ring-2 focus:ring-primary/20",
                        "active:scale-[0.98]",
                        !from && "text-muted-foreground",
                        from && "border-primary/30 bg-primary/5"
                      )}
                    >
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <Plane className="h-4 w-4 text-muted-foreground shrink-0" />
                        <span className="truncate">
                          {from ? `${from.code} - ${from.city}` : "Select airport"}
                        </span>
                      </div>
                      <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-[300px] p-0" align="start">
                    <Command>
                      <CommandInput placeholder="Search airport..." />
                      <CommandList>
                        <CommandEmpty>No airport found.</CommandEmpty>
                        <CommandGroup>
                          {getFromAirports().map((airport) => (
                            <CommandItem
                              key={airport.code}
                              value={`${airport.code} ${airport.city} ${airport.name}`}
                              onSelect={() => {
                                
                                if (to && to.code === airport.code) {
                                  setTo(null)
                                  alert('Departure and destination airports cannot be the same. Please select a different destination.')
                                }
                                setFrom(airport)
                                setFromOpen(false)
                              }}
                              className="flex items-center gap-3 cursor-pointer"
                            >
                              <div className="flex items-center gap-3 flex-1">
                                <div className="flex flex-col">
                                  <div className="flex items-center gap-2">
                                    <span className="font-semibold text-sm">{airport.code}</span>
                                    <span className="text-sm text-muted-foreground">-</span>
                                    <span className="text-sm font-medium">{airport.city}</span>
                                  </div>
                                  <span className="text-xs text-muted-foreground mt-0.5">
                                    {airport.name}
                                  </span>
                                </div>
                              </div>
                              <Check
                                className={cn(
                                  "ml-auto h-4 w-4",
                                  from?.code === airport.code ? "opacity-100" : "opacity-0"
                                )}
                              />
                            </CommandItem>
                          ))}
                        </CommandGroup>
                      </CommandList>
                    </Command>
                  </PopoverContent>
                </Popover>
              </div>

              {}
              <div className="space-y-2">
                <Label htmlFor="to" className="text-sm font-medium">
                  To
                </Label>
                <Popover open={toOpen} onOpenChange={setToOpen}>
                  <PopoverTrigger asChild>
                    <Button
                      id="to"
                      variant="outline"
                      role="combobox"
                      aria-expanded={toOpen}
                      className={cn(
                        "w-full h-14 justify-between text-left font-normal text-base",
                        "border-2 transition-all duration-200",
                        "hover:border-primary/50 hover:bg-primary/5 hover:shadow-md",
                        "focus:border-primary focus:ring-2 focus:ring-primary/20",
                        "active:scale-[0.98]",
                        !to && "text-muted-foreground",
                        to && "border-primary/30 bg-primary/5"
                      )}
                    >
                      <div className="flex items-center gap-2 flex-1 min-w-0">
                        <Plane className="h-4 w-4 text-muted-foreground rotate-90 shrink-0" />
                        <span className="truncate">
                          {to ? `${to.code} - ${to.city}` : "Select airport"}
                        </span>
                      </div>
                      <ChevronDown className="ml-2 h-4 w-4 shrink-0 opacity-50" />
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-[300px] p-0" align="start">
                    <Command>
                      <CommandInput placeholder="Search airport..." />
                      <CommandList>
                        <CommandEmpty>No airport found.</CommandEmpty>
                        <CommandGroup>
                          {getToAirports().map((airport) => (
                            <CommandItem
                              key={airport.code}
                              value={`${airport.code} ${airport.city} ${airport.name}`}
                              onSelect={() => {
                                
                                if (from && from.code === airport.code) {
                                  setFrom(null)
                                  alert('Departure and destination airports cannot be the same. Please select a different departure airport.')
                                }
                                setTo(airport)
                                setToOpen(false)
                              }}
                              className="flex items-center gap-3 cursor-pointer"
                            >
                              <div className="flex items-center gap-3 flex-1">
                                <div className="flex flex-col">
                                  <div className="flex items-center gap-2">
                                    <span className="font-semibold text-sm">{airport.code}</span>
                                    <span className="text-sm text-muted-foreground">-</span>
                                    <span className="text-sm font-medium">{airport.city}</span>
                                  </div>
                                  <span className="text-xs text-muted-foreground mt-0.5">
                                    {airport.name}
                                  </span>
                                </div>
                              </div>
                              <Check
                                className={cn(
                                  "ml-auto h-4 w-4",
                                  to?.code === airport.code ? "opacity-100" : "opacity-0"
                                )}
                              />
                            </CommandItem>
                          ))}
                        </CommandGroup>
                      </CommandList>
                    </Command>
                  </PopoverContent>
                </Popover>
              </div>

              {}
              <div className="space-y-2">
                <Label htmlFor="date" className="text-sm font-medium">
                  Date
                </Label>
                <Popover>
                  <PopoverTrigger asChild>
                    <Button
                      id="date"
                      variant="outline"
                      className={cn(
                        "w-full h-14 justify-start text-left font-normal text-base",
                        "border-2 transition-all duration-200",
                        "hover:border-primary/50 hover:bg-primary/5 hover:shadow-md",
                        "focus:border-primary focus:ring-2 focus:ring-primary/20",
                        "active:scale-[0.98]",
                        !date && "text-muted-foreground",
                        date && "border-primary/30 bg-primary/5"
                      )}
                    >
                      <CalendarIcon className="mr-2 h-4 w-4" />
                      {date ? format(date, "PPP") : <span>Pick a date</span>}
                    </Button>
                  </PopoverTrigger>
                  <PopoverContent className="w-auto p-0" align="start">
                    <Calendar
                      mode="single"
                      selected={date}
                      onSelect={setDate}
                      initialFocus
                      disabled={(date) => date < new Date(new Date().setHours(0, 0, 0, 0))}
                    />
                  </PopoverContent>
                </Popover>
              </div>
            </div>

            {/* Search Bar with Checkbox and Button */}
            <div className={cn(
              "flex items-center gap-3",
              flightType === "international" ? "flex-row" : "flex-col"
            )}>
              {/* Advanced Search Checkbox - Only for International */}
              {flightType === "international" && (
                <div className="flex items-center gap-2.5 px-4 py-3 rounded-lg border border-border/60 bg-muted/40 hover:bg-muted/60 hover:border-primary/40 transition-all duration-200">
                  <input
                    type="checkbox"
                    id="advanced-search"
                    checked={advancedSearch}
                    onChange={(e) => setAdvancedSearch(e.target.checked)}
                    className="h-4 w-4 rounded border-2 border-primary/40 text-primary focus:ring-2 focus:ring-primary/20 focus:ring-offset-1 cursor-pointer transition-all duration-200 hover:border-primary/60 checked:bg-primary checked:border-primary"
                  />
                  <label
                    htmlFor="advanced-search"
                    className="text-sm font-medium text-foreground cursor-pointer select-none"
                  >
                    Advanced Search
                  </label>
                </div>
              )}
              
              {/* Search Button */}
            <Button
              onClick={handleSearch}
              size="lg"
              disabled={loading || !from || !to || !date}
                className={cn(
                  flightType === "international" ? "flex-1" : "w-full",
                  "h-14 text-lg font-semibold",
                  "bg-gradient-to-r from-primary via-primary/95 to-primary",
                  "hover:from-primary/95 hover:via-primary hover:to-primary/95",
                  "shadow-md hover:shadow-lg hover:shadow-primary/20",
                  "transition-all duration-200",
                  "disabled:opacity-50 disabled:cursor-not-allowed disabled:hover:shadow-md",
                  "relative overflow-hidden group"
                )}
              >
                <span className="relative z-10 flex items-center justify-center">
                  <Search className={cn(
                    "mr-2 h-5 w-5 transition-transform duration-200",
                    !loading && "group-hover:scale-110"
                  )} />
                  {loading ? (
                    <span className="flex items-center gap-2">
                      <span className="animate-spin h-4 w-4 border-2 border-current border-t-transparent rounded-full"></span>
                      Searching...
                    </span>
                  ) : (
                    "Search Flights"
                  )}
                </span>
            </Button>
            </div>
          </CardContent>
        </Card>

        {}
        {(processedAllFlights.length > 0) && (
          <div className="mt-6 space-y-6">
            {/* Filter and Sort Controls */}
            <div className="flex flex-col gap-4">
              <div className="flex flex-col sm:flex-row gap-4 items-center justify-between">
                <div className="flex items-center gap-2 flex-wrap">
                  <Filter className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Route:</span>
                  <div className="flex gap-2">
                    <Button
                      variant={filterBy === 'all' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setFilterBy('all')}
                    >
                      All
                    </Button>
                    <Button
                      variant={filterBy === 'direct' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setFilterBy('direct')}
                    >
                      Direct
                    </Button>
                    <Button
                      variant={filterBy === 'connecting' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setFilterBy('connecting')}
                    >
                      Connecting
                    </Button>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <ArrowUpDown className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Sort by:</span>
                  <select
                    value={sortBy}
                    onChange={(e) => setSortBy(e.target.value as 'price' | 'duration' | 'departure')}
                    className="px-3 py-1.5 border rounded-md text-sm bg-background"
                  >
                    <option value="price">Price (Low to High)</option>
                    <option value="duration">Duration</option>
                    <option value="departure">Departure Time</option>
                  </select>
                </div>
              </div>
              
              {/* Airline Filter - Only show when advanced search is enabled and multiple airlines exist */}
              {advancedSearch && flightType === 'international' && (spicejetFlights.length > 0 || etihadProcessedFlights.length > 0) && (
                <div className="flex items-center gap-2">
                  <Plane className="h-4 w-4 text-muted-foreground" />
                  <span className="text-sm font-medium">Airline:</span>
                  <div className="flex gap-2">
                    <Button
                      variant={airlineFilter === 'all' ? 'default' : 'outline'}
                      size="sm"
                      onClick={() => setAirlineFilter('all')}
                    >
                      All Airlines
                    </Button>
                    {spicejetFlights.length > 0 && (
                      <Button
                        variant={airlineFilter === 'spicejet' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setAirlineFilter('spicejet')}
                      >
                        SpiceJet ({spicejetFlights.length})
                      </Button>
                    )}
                    {etihadProcessedFlights.length > 0 && (
                      <Button
                        variant={airlineFilter === 'etihad' ? 'default' : 'outline'}
                        size="sm"
                        onClick={() => setAirlineFilter('etihad')}
                      >
                        Etihad ({etihadProcessedFlights.length})
                      </Button>
                    )}
                  </div>
                </div>
              )}
            </div>

            {/* Flights Display - Grouped by Airline */}
            {processedAllFlights.length > 0 && (
              <div className="space-y-6">
                {/* SpiceJet Flights */}
                {spicejetFlights.length > 0 && (airlineFilter === 'all' || airlineFilter === 'spicejet') && (
                  <div className="space-y-5">
                    <h2 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-primary to-primary/70 bg-clip-text text-transparent">
                      SpiceJet Flights ({spicejetFlights.length})
                    </h2>
                    <div className="grid grid-cols-1 gap-5">
                      {spicejetFlights.map((flight, index) => (
                        <Card 
                          key={index} 
                          className="group border-2 border-border/60 shadow-md hover:shadow-2xl hover:border-primary/40 transition-all duration-300 hover:-translate-y-1 bg-card/95 backdrop-blur-sm overflow-hidden relative"
                          style={{
                            animation: `fadeInUp 0.5s ease-out ${index * 0.1}s both`
                          }}
                        >
                          {/* Gradient overlay on hover */}
                          <div className="absolute inset-0 bg-gradient-to-r from-primary/0 via-primary/0 to-primary/0 group-hover:from-primary/5 group-hover:via-primary/3 group-hover:to-primary/5 transition-all duration-300 pointer-events-none" />
                          
                          <CardContent className="p-6 relative z-10">
                            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
                              {/* Left Section - Flight Info */}
                              <div className="flex-1 space-y-5">
                                {/* Airline and Flight Number */}
                                <div className="flex items-center gap-3 flex-wrap">
                                  <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg bg-primary/10 border border-primary/20">
                                    <Plane className="h-5 w-5 text-primary" />
                                    <span className="font-bold text-base text-foreground">{flight.airline}</span>
                                  </div>
                                  <span className="text-muted-foreground/50 text-xl">•</span>
                                  <span className="font-semibold text-lg text-foreground tracking-wide">{flight.flightNumber}</span>
                                </div>

                                {/* Flight Details Grid */}
                                <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
                                  <div className="space-y-1.5">
                                    <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Departure</p>
                                    <p className="font-bold text-2xl text-foreground tracking-tight">{flight.departureTime}</p>
                                    <p className="text-xs text-muted-foreground font-medium">{from?.code}</p>
                                  </div>
                                  <div className="space-y-1.5">
                                    <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Arrival</p>
                                    <p className="font-bold text-2xl text-foreground tracking-tight">{flight.arrivalTime}</p>
                                    <p className="text-xs text-muted-foreground font-medium">{to?.code}</p>
                                  </div>
                                  <div className="space-y-1.5">
                                    <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Duration</p>
                                    <p className="font-bold text-xl text-foreground">{flight.duration}</p>
                                  </div>
                                  <div className="space-y-1.5">
                                    <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Route</p>
                                    <p className="font-semibold text-base text-foreground">{from?.code} → {to?.code}</p>
                                  </div>
                                </div>
                              </div>

                              {/* Right Section - Price and Action */}
                              <div className="flex flex-col lg:items-end gap-4 border-t lg:border-t-0 lg:border-l border-border/40 pt-5 lg:pt-0 lg:pl-6 lg:min-w-[200px]">
                                <div className="text-center lg:text-right space-y-1">
                                  <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Cash Price</p>
                                  <p className="font-bold text-3xl text-primary tracking-tight">{flight.cashPrice}</p>
                                </div>
                                <div className="text-center lg:text-right space-y-1">
                                  <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Points</p>
                                  <p className="font-semibold text-base text-foreground">{flight.pointsPrice}</p>
                                </div>
                                <Button 
                                  className="w-full lg:w-auto mt-2 font-semibold shadow-md hover:shadow-lg transition-all duration-200 hover:scale-105"
                                  size="lg"
                                >
                                  Select Flight
                                </Button>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>
                )}

                {/* Etihad Flights - Only show when advanced search is enabled */}
                {etihadProcessedFlights.length > 0 && (airlineFilter === 'all' || airlineFilter === 'etihad') && (
                  <div className="space-y-5">
                    <h2 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-amber-600 to-amber-500 bg-clip-text text-transparent">
                      Etihad Airways Flights ({etihadProcessedFlights.length})
                    </h2>
                    <div className="grid grid-cols-1 gap-5">
                      {etihadProcessedFlights.map((flight, index) => (
                        <Card 
                          key={`etihad-${index}`} 
                          className="group border-2 border-border/60 shadow-md hover:shadow-2xl hover:border-amber-500/40 transition-all duration-300 hover:-translate-y-1 bg-card/95 backdrop-blur-sm overflow-hidden relative"
                          style={{
                            animation: `fadeInUp 0.5s ease-out ${index * 0.1}s both`
                          }}
                        >
                          {/* Gradient overlay on hover */}
                          <div className="absolute inset-0 bg-gradient-to-r from-amber-500/0 via-amber-500/0 to-amber-500/0 group-hover:from-amber-500/5 group-hover:via-amber-500/3 group-hover:to-amber-500/5 transition-all duration-300 pointer-events-none" />
                          
                          <CardContent className="p-6 relative z-10">
                            <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
                              {/* Left Section - Flight Info */}
                              <div className="flex-1 space-y-5">
                                {/* Airline and Flight Number */}
                                <div className="flex items-center gap-3 flex-wrap">
                                  <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg bg-amber-500/10 border border-amber-500/20">
                                    <Plane className="h-5 w-5 text-amber-600" />
                                    <span className="font-bold text-base text-foreground">{flight.airline}</span>
                                  </div>
                                  <span className="text-muted-foreground/50 text-xl">•</span>
                                  <span className="font-semibold text-lg text-foreground tracking-wide">{flight.flightNumber}</span>
                                </div>

                                {/* Flight Details Grid */}
                                <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
                                  <div className="space-y-1.5">
                                    <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Departure</p>
                                    <p className="font-bold text-2xl text-foreground tracking-tight">{flight.departureTime}</p>
                                    <p className="text-xs text-muted-foreground font-medium">{from?.code}</p>
                                  </div>
                                  <div className="space-y-1.5">
                                    <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Arrival</p>
                                    <p className="font-bold text-2xl text-foreground tracking-tight">{flight.arrivalTime}</p>
                                    <p className="text-xs text-muted-foreground font-medium">{to?.code}</p>
                                  </div>
                                  <div className="space-y-1.5">
                                    <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Duration</p>
                                    <p className="font-bold text-xl text-foreground">{flight.duration}</p>
                                  </div>
                                  <div className="space-y-1.5">
                                    <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Route</p>
                                    <p className="font-semibold text-base text-foreground">{from?.code} → {to?.code}</p>
                                  </div>
                                </div>
                              </div>

                              {/* Right Section - Price and Action */}
                              <div className="flex flex-col lg:items-end gap-4 border-t lg:border-t-0 lg:border-l border-border/40 pt-5 lg:pt-0 lg:pl-6 lg:min-w-[200px]">
                                <div className="text-center lg:text-right space-y-1">
                                  <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Cash Price</p>
                                  <p className="font-bold text-3xl text-amber-600 tracking-tight">{flight.cashPrice}</p>
                                </div>
                                <div className="text-center lg:text-right space-y-1">
                                  <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Points</p>
                                  <p className="font-semibold text-base text-foreground">{flight.pointsPrice}</p>
                                </div>
                                <Button 
                                  className="w-full lg:w-auto mt-2 font-semibold shadow-md hover:shadow-lg transition-all duration-200 hover:scale-105 bg-amber-600 hover:bg-amber-700"
                                  size="lg"
                                >
                                  Select Flight
                                </Button>
                              </div>
                            </div>
                          </CardContent>
                        </Card>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            )}

            {/* HTML Snapshot Flights Section (IndiGo/Emirates) */}
            {htmlSnapshotFlights.length > 0 && (airlineFilter === 'all') && (
              <div className="space-y-5">
                <h2 className="text-2xl font-bold tracking-tight bg-gradient-to-r from-blue-600 to-blue-500 bg-clip-text text-transparent">
                  Sample Flight Data ({htmlSnapshotFlights.length})
                </h2>
                <div className="grid grid-cols-1 gap-5">
                  {htmlSnapshotFlights.map((flight, index) => (
                    <Card 
                      key={`html-${index}`} 
                      className="group border-2 border-border/60 shadow-md hover:shadow-2xl hover:border-blue-500/40 transition-all duration-300 hover:-translate-y-1 bg-card/95 backdrop-blur-sm overflow-hidden relative opacity-90"
                      style={{
                        animation: `fadeInUp 0.5s ease-out ${index * 0.1}s both`
                      }}
                    >
                      <div className="absolute inset-0 bg-gradient-to-r from-blue-500/0 via-blue-500/0 to-blue-500/0 group-hover:from-blue-500/5 group-hover:via-blue-500/3 group-hover:to-blue-500/5 transition-all duration-300 pointer-events-none" />
                      
                      <CardContent className="p-6 relative z-10">
                        <div className="flex flex-col lg:flex-row lg:items-center lg:justify-between gap-6">
                          <div className="flex-1 space-y-5">
                            <div className="flex items-center gap-3 flex-wrap">
                              <div className="flex items-center gap-2.5 px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20">
                                <Plane className="h-5 w-5 text-blue-600" />
                                <span className="font-bold text-base text-foreground">{flight.airline}</span>
                              </div>
                              <span className="text-muted-foreground/50 text-xl">•</span>
                              <span className="font-semibold text-lg text-foreground tracking-wide">{flight.flightNumber}</span>
                            </div>

                            <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
                              <div className="space-y-1.5">
                                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Departure</p>
                                <p className="font-bold text-2xl text-foreground tracking-tight">{flight.departureTime}</p>
                                <p className="text-xs text-muted-foreground font-medium">{from?.code}</p>
                              </div>
                              <div className="space-y-1.5">
                                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Arrival</p>
                                <p className="font-bold text-2xl text-foreground tracking-tight">{flight.arrivalTime}</p>
                                <p className="text-xs text-muted-foreground font-medium">{to?.code}</p>
                              </div>
                              <div className="space-y-1.5">
                                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Duration</p>
                                <p className="font-bold text-xl text-foreground">{flight.duration}</p>
                              </div>
                              <div className="space-y-1.5">
                                <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Route</p>
                                <p className="font-semibold text-base text-foreground">{from?.code} → {to?.code}</p>
                              </div>
                            </div>
                          </div>

                          <div className="flex flex-col lg:items-end gap-4 border-t lg:border-t-0 lg:border-l border-border/40 pt-5 lg:pt-0 lg:pl-6 lg:min-w-[200px]">
                            <div className="text-center lg:text-right space-y-1">
                              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Cash Price</p>
                              <p className="font-bold text-3xl text-blue-600 tracking-tight">{flight.cashPrice}</p>
                            </div>
                            <div className="text-center lg:text-right space-y-1">
                              <p className="text-[10px] font-semibold text-muted-foreground uppercase tracking-wider">Points</p>
                              <p className="font-semibold text-base text-foreground">{flight.pointsPrice}</p>
                            </div>
                            <Button 
                              className="w-full lg:w-auto mt-2 font-semibold shadow-md hover:shadow-lg transition-all duration-200 hover:scale-105 bg-blue-600 hover:bg-blue-700"
                              size="lg"
                            >
                              Select Flight
                            </Button>
                          </div>
                        </div>
                      </CardContent>
                    </Card>
                  ))}
                </div>
              </div>
            )}

            {/* Fallback Flights Section - Legacy support (SpiceJet fallback only) */}
            {processedFallbackFlights.length > 0 && (
              <div className="space-y-4">
                <h2 className="text-xl font-bold">
                  Sample Flight Data ({processedFallbackFlights.length})
            </h2>
            <div className="grid grid-cols-1 gap-4">
                  {displayedFallbackFlights.map((flight, index) => (
                    <Card key={`fallback-${index}`} className="border-2 shadow-lg hover:shadow-xl transition-all opacity-90">
                  <CardContent className="p-6">
                    <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4">
                      <div className="flex-1 space-y-3">
                        <div className="flex items-center gap-4">
                          <div className="flex items-center gap-2">
                            <Plane className="h-5 w-5 text-primary" />
                            <span className="font-bold text-lg">{flight.airline}</span>
                          </div>
                          <span className="text-muted-foreground">|</span>
                          <span className="font-semibold text-lg">{flight.flightNumber}</span>
                        </div>

                        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                          <div>
                            <p className="text-xs text-muted-foreground uppercase mb-1">Departure</p>
                            <p className="font-semibold text-lg">{flight.departureTime}</p>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground uppercase mb-1">Arrival</p>
                            <p className="font-semibold text-lg">{flight.arrivalTime}</p>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground uppercase mb-1">Duration</p>
                            <p className="font-semibold">{flight.duration}</p>
                          </div>
                          <div>
                            <p className="text-xs text-muted-foreground uppercase mb-1">Route</p>
                            <p className="font-semibold">{from?.code} → {to?.code}</p>
                          </div>
                        </div>
                      </div>

                      <div className="flex flex-col md:items-end gap-3 border-t md:border-t-0 md:border-l pt-4 md:pt-0 md:pl-6">
                        <div className="text-center md:text-right">
                          <p className="text-xs text-muted-foreground uppercase mb-1">Cash Price</p>
                          <p className="font-bold text-2xl text-primary">{flight.cashPrice}</p>
                        </div>
                        <div className="text-center md:text-right">
                          <p className="text-xs text-muted-foreground uppercase mb-1">Points Price</p>
                          <p className="font-semibold text-lg">{flight.pointsPrice}</p>
                        </div>
                        <Button className="w-full md:w-auto mt-2">
                          Select Flight
                        </Button>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              ))}
            </div>
            
                {hasMoreFallbackFlights && !showAllFallback && (
                  <div className="flex justify-center mt-4">
                <Button
                      onClick={() => setShowAllFallback(true)}
                  variant="outline"
                  size="lg"
                  className="px-8 py-6 text-base font-semibold"
                >
                      Show All Fallback Flights ({processedFallbackFlights.length - 4} more)
                </Button>
              </div>
            )}
            
                {hasMoreFallbackFlights && showAllFallback && (
                  <div className="flex justify-center mt-4">
                <Button
                      onClick={() => setShowAllFallback(false)}
                  variant="outline"
                  size="lg"
                  className="px-8 py-6 text-base font-semibold"
                >
                  Show Less
                </Button>
                  </div>
                )}
              </div>
            )}
          </div>
        )}

        {processedAllFlights.length === 0 && !loading && hasSearched && from && to && (
          <div className="mt-6 text-center text-muted-foreground">
            <p>No flights found for {from?.code} → {to?.code} on {date ? format(date, "PPP") : "selected date"}.</p>
            <p className="text-sm mt-2">Please try a different route or date.</p>
          </div>
        )}
      </div>
    </div>
  )
}
