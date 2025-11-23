# Flight Scraper & Search Platform

A comprehensive web application for scraping and displaying flight data from multiple airlines. This project combines Python-based web scraping with a modern Next.js frontend to provide real-time flight search capabilities.

## 📋 Table of Contents

- [Project Overview](#project-overview)
- [Airlines Supported](#airlines-supported)
- [How to Run Locally](#how-to-run-locally)
- [Scraping Methodology](#scraping-methodology)
- [Project Structure](#project-structure)
- [Technologies Used](#technologies-used)
- [Requirements](#requirements)

## 🎯 Project Overview

This project is a flight search platform that scrapes flight data from various airline websites and displays it in a user-friendly interface. The system supports both domestic and international flights, with real-time scraping capabilities and fallback mechanisms for reliable data retrieval.

### Key Features

- **Multi-Airline Support**: Scrapes data from IndiGo, SpiceJet, and Etihad Airways
- **Real-time Scraping**: Live data extraction from airline websites
- **Fallback System**: HTML snapshot fallback when live scraping fails
- **Advanced Search**: Parallel scraping for international flights
- **Modern UI**: Beautiful, responsive interface with animations
- **Progress Tracking**: Real-time loading progress with fun facts

## ✈️ Airlines Supported

### Domestic Flights
1. **IndiGo** (`attempt2/`)
   - India's largest airline
   - Routes: Major Indian cities
   - Scraping method: Selenium with undetected-chromedriver

2. **SpiceJet** (`attempt1/`)
   - Low-cost carrier
   - Routes: Domestic Indian routes
   - Scraping method: Playwright with network interception

### International Flights
1. **SpiceJet International** (`attempt1international/`)
   - International routes from India
   - Scraping method: Playwright with network interception

2. **Etihad Airways** (`attempt1etihad/`)
   - International premium carrier
   - Routes: International destinations
   - Scraping method: Selenium with undetected-chromedriver

## 🚀 How to Run Locally

### Prerequisites

- **Python 3.8+** installed
- **Node.js 18+** and npm installed
- **Chrome/Chromium** browser installed (for web scraping)

### Backend Setup (Python Scrapers)

1. **Navigate to scraper directory** (choose one based on airline):
   ```bash
   cd attempt1          # For SpiceJet domestic
   cd attempt2          # For IndiGo
   cd attempt1international  # For SpiceJet international
   cd attempt1etihad    # For Etihad
   ```

2. **Install Python dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Install Playwright browsers** (if using Playwright):
   ```bash
   playwright install chromium
   ```

### Frontend Setup (Next.js)

1. **Navigate to frontend directory**:
   ```bash
   cd frontend/flypoints
   ```

2. **Install Node.js dependencies**:
   ```bash
   npm install
   ```

3. **Run development server**:
   ```bash
   npm run dev
   ```

4. **Open browser**:
   Navigate to `http://localhost:3000`

### Running a Scraper Directly

You can test individual scrapers from the command line:

**SpiceJet (Domestic/International)**:
```bash
cd attempt1  # or attempt1international
python spicejet_scraper_api.py DEL BOM 25-12-2025
```

**IndiGo**:
```bash
cd attempt2
python scraper.py DEL BOM 25-12-2025
```

**Etihad**:
```bash
cd attempt1etihad
python etihad_scraper_api.py DEL DXB 25-12-2025
```

## 🔍 Scraping Methodology

### 🚫 Blockers Encountered & How I Handled Them

While working on the scraping layer, I encountered several challenges due to the way airlines secure their websites. Most major airlines use multiple layers of anti-automation protection, including:

#### 1. **Dynamic DOM + Shadow DOM Layers**

Several airlines don't expose flight data in static HTML. Important elements (inputs, buttons, even prices) are:

- Injected dynamically via client-side JavaScript
- Rendered inside nested components
- Placed inside Shadow DOM containers
- Intentionally delayed or obfuscated

This prevents simple HTML parsing or request-based scraping.

#### 2. **Bot Detection & Browser Fingerprinting**

Airline sites actively detect automation through:

- Headless browser fingerprints
- Navigator / WebDriver property checks
- Mouse/pointer movement monitoring
- Timing and event-behavior analysis
- Real device characteristics (viewport, UA, hardware concurrency)

Multiple attempts were blocked with:

- `403 Forbidden` errors
- Infinite loading loops
- Pages showing "Something went wrong" or redirecting to home

#### 3. **Hidden Search API & Encrypted Payloads**

Some airlines do not send flight data via open JSON APIs. Instead they use:

- Encrypted request payloads
- HMAC-signed tokens
- Hidden API endpoints that require session cookies
- Anti-CSRF tokens refreshed on each request

This made direct API scraping unreliable without reverse engineering.

#### 4. **Bot-Proof Input & Form Submission Flow**

A few airlines:

- Do not allow direct programmatic input into search fields
- Keep form values in hidden reactive states
- Trigger validations on actual UI events (mouseover, focus, blur)
- Block submissions that don't originate from genuine UI interaction

This prevented naïve automation.

### ✅ How I Solved These Issues

To handle these blockers, I iterated through multiple technical approaches, testing different libraries and strategies until I reached a stable, repeatable scraping flow.

#### 1. **Switched to a Fully Controlled Browser Environment (Playwright)**

I used Playwright with:

- Stealth mode tweaks
- Chromium with full GPU/JS execution
- Custom user agents
- Randomized viewport & timezone
- Disabled WebDriver flags

This helped bypass most fingerprinting checks.

#### 2. **Simulated Real Human Interaction**

To satisfy strict UI flow requirements, I added:

- Realistic typing delays
- Mouse movements
- Controlled waiting for network/DOM stabilization
- Explicit event-triggered interactions

This allowed the form to submit successfully without being flagged.

#### 3. **Experimented With Multiple Methods**

Before stabilizing the final scraper, I explored:

- iframe isolation
- Stealth plugins
- Playwright extra
- Undetected Chromium builds
- BeautifulSoup (initially, but dropped due to JS-heavy pages)
- Network interception to detect hidden API activity

Each experiment helped uncover how the airline protected its flow.

#### 4. **Used Local Snapshot Fallbacks When Scraping Was Fully Blocked**

For airlines where:

- JS obfuscation was too heavy
- CAPTCHA triggers were unpredictable
- Anti-bot defenses became unstable under automation

I implemented a static HTML snapshot fallback system.

This ensures:

- Consistent demo
- Predictable results
- Real-world airline results still shown
- Product logic remains intact

#### 5. **Built Retry Logic + Defensive Coding**

Added:

- Timed waits
- Multiple selector strategies
- Graceful error handling
- Incremental scraping retries
- Fallback airline-by-airline

This made the scraper reliable for the demo.

### 📊 Final Summary

Airline scraping is significantly harder than normal website scraping due to multi-layer anti-automation systems. I handled these challenges by:

- Using a real browser automation setup
- Mimicking authentic user behavior
- Debugging network/API flows
- Repeated iteration with different tools
- Implementing a robust fallback mechanism

The final outcome is stable, replicable scraping for IndiGo, SpiceJet (domestic & international), and Etihad, while maintaining a professional fallback path where needed.

### How We Scrape

The project uses different scraping strategies depending on the airline's website architecture:

#### 1. **Network Interception (SpiceJet)**
   - **Tool**: Playwright
   - **Method**: Intercepts network requests to capture API responses
   - **Process**:
     1. Launches headless Chromium browser
     2. Navigates to SpiceJet search URL with parameters
     3. Intercepts and captures JSON API responses
     4. Parses flight data from API responses
     5. Falls back to HTML parsing if API data is incomplete
   - **Advantages**: Fast, reliable, gets structured data directly
   - **Files**: `attempt1/spicejet_scraper.py`, `attempt1international/spicejet_scraper.py`

#### 2. **Browser Automation (IndiGo)**
   - **Tool**: Selenium + undetected-chromedriver
   - **Method**: Automated browser interaction with stealth capabilities
   - **Process**:
     1. Uses undetected-chromedriver to avoid bot detection
     2. Navigates to IndiGo website
     3. Fills search form (origin, destination, date)
     4. Waits for results to load
     5. Parses HTML using BeautifulSoup
   - **Advantages**: Handles dynamic content, bypasses basic bot detection
   - **Files**: `attempt2/scraper.py`

#### 3. **Stealth Browser Automation (Etihad)**
   - **Tool**: Selenium + undetected-chromedriver
   - **Method**: Two-step navigation with stealth browser
   - **Process**:
     1. First navigates to homepage to establish session
     2. Then navigates to search URL
     3. Extracts data from `window.flightData` JavaScript variables
     4. Falls back to BeautifulSoup HTML parsing
   - **Advantages**: Bypasses security systems, handles JavaScript-rendered content
   - **Files**: `attempt1etihad/etihad_scraper.py`

### Data Extraction Flow

1. **Input Normalization**: Converts city names to airport codes
2. **Date Parsing**: Handles multiple date formats (DD-MM-YYYY, YYYY-MM-DD)
3. **Browser Automation**: Launches browser and navigates to search page
4. **Data Capture**: 
   - Network interception (for API-based sites)
   - HTML parsing (for static/dynamic content)
   - JavaScript variable extraction (for client-side data)
5. **Data Processing**: Extracts flight number, times, duration, prices, points
6. **Formatting**: Converts to standardized JSON format
7. **Output**: Returns structured flight data

### Fallback Mechanism

The system includes a robust fallback system:

1. **Primary**: Live scraping from airline websites
2. **Secondary**: HTML snapshot parsing (pre-saved HTML files)
3. **Tertiary**: Error message if both methods fail

HTML snapshots are stored in `frontend/flypoints/samples/` directory.

## 📁 Project Structure

```
try/
├── attempt1/                          # SpiceJet Domestic Scraper
│   ├── spicejet_scraper.py           # Main scraper (Playwright)
│   ├── spicejet_scraper_api.py       # API wrapper for Next.js
│   ├── config.py                     # Configuration settings
│   ├── utils.py                      # Helper functions
│   └── requirements.txt              # Python dependencies
│
├── attempt1international/             # SpiceJet International Scraper
│   ├── spicejet_scraper.py           # Main scraper (Playwright)
│   ├── spicejet_scraper_api.py       # API wrapper
│   ├── config.py
│   ├── utils.py
│   └── requirements.txt
│
├── attempt1etihad/                    # Etihad Airways Scraper
│   ├── etihad_scraper.py             # Main scraper (Selenium)
│   ├── etihad_scraper_api.py         # API wrapper
│   ├── config.py
│   ├── utils.py
│   └── requirements.txt
│
├── attempt2/                          # IndiGo Scraper
│   ├── scraper.py                    # Main scraper (Selenium)
│   ├── config.py
│   ├── utils.py
│   └── requirements.txt
│
└── frontend/
    └── flypoints/                     # Next.js Frontend
        ├── app/
        │   ├── page.tsx               # Main search page
        │   ├── api/
        │   │   └── flights/
        │   │       ├── scrape/       # Domestic API route
        │   │       ├── scrape-international/  # International API route
        │   │       └── scrape-etihad/ # Etihad API route
        │   └── globals.css           # Global styles
        ├── components/
        │   └── ui/                    # UI components (shadcn/ui)
        ├── lib/                       # Utility functions
        ├── samples/                   # HTML snapshot fallback data
        ├── public/                    # Static assets
        ├── package.json               # Node.js dependencies
        └── tsconfig.json              # TypeScript config
```

## 🛠️ Technologies Used

### Backend (Python)

- **Playwright** (`>=1.40.0`): Browser automation with network interception
- **Selenium**: Web browser automation
- **undetected-chromedriver** (`>=3.5.4`): Stealth browser automation
- **BeautifulSoup4** (`>=4.12.0`): HTML parsing
- **lxml** (`>=4.9.0`): XML/HTML parser
- **setuptools** (`>=65.0.0`): Package management

### Frontend (Next.js)

- **Next.js 16.0.3**: React framework
- **React 19.2.0**: UI library
- **TypeScript**: Type-safe JavaScript
- **Tailwind CSS 4**: Utility-first CSS framework
- **shadcn/ui**: UI component library
- **Radix UI**: Accessible component primitives
- **date-fns**: Date manipulation
- **lucide-react**: Icon library

### Key Libraries

- **Playwright**: For SpiceJet scraping (network interception)
- **Selenium + undetected-chromedriver**: For IndiGo and Etihad (stealth browsing)
- **BeautifulSoup**: HTML parsing and data extraction

## 📦 Requirements

### Python Requirements

**Common dependencies** (all scrapers):
```
playwright>=1.40.0
beautifulsoup4>=4.12.0
lxml>=4.9.0
setuptools>=65.0.0
undetected-chromedriver>=3.5.4
```

### Node.js Requirements

See `frontend/flypoints/package.json` for complete list. Key dependencies:
- Next.js 16.0.3
- React 19.2.0
- TypeScript 5
- Tailwind CSS 4

### System Requirements

- **Operating System**: Windows, macOS, or Linux
- **Python**: 3.8 or higher
- **Node.js**: 18.0 or higher
- **Chrome/Chromium**: Latest version (for browser automation)
- **RAM**: Minimum 4GB (8GB recommended)
- **Disk Space**: ~500MB for dependencies

### Browser Requirements

- Chrome/Chromium browser must be installed
- Playwright browsers will be installed automatically via `playwright install`

## 🔧 Configuration

### Scraper Configuration

Each scraper has a `config.py` file with settings:
- `HEADLESS_MODE`: Run browser in headless mode
- `USER_AGENT`: Browser user agent string
- `PAGE_LOAD_TIMEOUT`: Maximum page load wait time
- `AIRPORT_CODES`: City name to airport code mappings

### Frontend Configuration

- API routes are configured in `frontend/flypoints/app/api/flights/`
- Scraper paths are relative to the frontend directory
- Date formats are automatically converted between frontend (YYYY-MM-DD) and scrapers (DD-MM-YYYY)

## 📝 Notes

- **Scraping Time**: Domestic flights take 2-3 minutes, international flights take 3-4 minutes
- **Rate Limiting**: Be mindful of airline website rate limits
- **Legal**: This project is for educational purposes. Ensure compliance with airline website terms of service
- **Fallback Data**: HTML snapshots provide sample data when live scraping fails

## 🤝 Contributing

This is a personal project for educational purposes. Feel free to fork and modify as needed.

## 📄 License

This project is for educational and testing purposes only.

---

**Note**: Always respect website terms of service and use scraping responsibly.

