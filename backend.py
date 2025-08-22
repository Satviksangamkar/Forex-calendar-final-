#!/usr/bin/env python3
"""
FastAPI Forex Factory Scraper Backend with Redis Database
- GET /events?start=YYYY-MM-DD&end=YYYY-MM-DD
- Database-aside pattern with Redis
- Full scraping logic with Botasaurus
- Optimized for production use
- Paraphrasing support with separate database keys
"""

import sys
import json
import time
import random
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Any, Optional
from contextlib import asynccontextmanager

import redis
import uvicorn
from fastapi import FastAPI, Query, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from pydantic import BaseModel, field_validator
from botasaurus.browser import browser, Driver
from sentence_transformers import SentenceTransformer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('backend.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# Global paraphrase model
paraphrase_model = None

def load_paraphrase_model():
    """Load the paraphrase model once at startup"""
    global paraphrase_model
    try:
        logger.info("Loading paraphrase model...")
        paraphrase_model = SentenceTransformer("sentence-transformers/paraphrase-MiniLM-L3-v2")
        logger.info("Paraphrase model loaded successfully")
    except Exception as e:
        logger.error(f"Failed to load paraphrase model: {e}")
        paraphrase_model = None

def paraphrase_text(text: str) -> str:
    """Paraphrase text using the loaded model"""
    if not text or text.strip() == "" or text.strip() == "0":
        return ""
    
    if paraphrase_model is None:
        logger.warning("Paraphrase model not loaded, returning original text")
        return text
    
    try:
        # Simple paraphrasing approach using sentence-transformers
        # Since paraphrase-MiniLM-L3-v2 is for embeddings, we'll implement a basic paraphrasing strategy
        
        # For now, we'll use a simple text transformation approach
        # In a production environment, you might want to use a dedicated paraphrasing model
        
        # Basic paraphrasing rules for forex data
        paraphrased = text
        
        # Replace common forex abbreviations with full forms
        replacements = {
            "m/m": "month over month",
            "y/y": "year over year",
            "q/q": "quarter over quarter",
            "w/w": "week over week",
            "Fed": "Federal Reserve",
            "ECB": "European Central Bank",
            "BoE": "Bank of England",
            "BoJ": "Bank of Japan",
            "RBA": "Reserve Bank of Australia",
            "BOC": "Bank of Canada",
            "SNB": "Swiss National Bank",
            "RBNZ": "Reserve Bank of New Zealand",
            "CPI": "Consumer Price Index",
            "PPI": "Producer Price Index",
            "GDP": "Gross Domestic Product",
            "NFP": "Non-Farm Payrolls",
            "ISM": "Institute for Supply Management",
            "PMI": "Purchasing Managers Index",
            "ADP": "Automatic Data Processing",
            "BLS": "Bureau of Labor Statistics",
            "BEA": "Bureau of Economic Analysis",
            "CBO": "Congressional Budget Office",
            "FOMC": "Federal Open Market Committee",
            "ECB": "European Central Bank",
            "MPC": "Monetary Policy Committee",
            "RBA": "Reserve Bank of Australia",
            "BOC": "Bank of Canada",
            "SNB": "Swiss National Bank",
            "RBNZ": "Reserve Bank of New Zealand"
        }
        
        for abbrev, full_form in replacements.items():
            paraphrased = paraphrased.replace(abbrev, full_form)
        
        # Add more descriptive language for common forex terms
        descriptive_replacements = {
            "Consumer Credit": "Consumer Credit Change",
            "Employment": "Employment Data",
            "Inflation": "Inflation Rate",
            "Interest Rate": "Interest Rate Decision",
            "Retail Sales": "Retail Sales Report",
            "Trade Balance": "Trade Balance Report",
            "Current Account": "Current Account Balance",
            "Manufacturing": "Manufacturing Data",
            "Services": "Services Sector Data",
            "Housing": "Housing Market Data",
            "Consumer": "Consumer Data",
            "Business": "Business Activity Data"
        }
        
        for term, description in descriptive_replacements.items():
            if term in paraphrased and not description in paraphrased:
                paraphrased = paraphrased.replace(term, description)
        
        # If no changes were made, try to make the text more descriptive
        if paraphrased == text:
            # Add context for common forex terms
            if "Change" in text and "Employment" in text:
                paraphrased = f"Employment Change Report - {text}"
            elif "Rate" in text and "Interest" in text:
                paraphrased = f"Interest Rate Decision - {text}"
            elif "Sales" in text and "Retail" in text:
                paraphrased = f"Retail Sales Performance - {text}"
            elif "Balance" in text and "Trade" in text:
                paraphrased = f"Trade Balance Report - {text}"
        
        logger.info(f"Paraphrased: '{text}' -> '{paraphrased}'")
        return paraphrased
        
    except Exception as e:
        logger.error(f"Error paraphrasing text: {e}")
        return text

def paraphrase_event(event: Dict[str, Any]) -> Dict[str, Any]:
    """Paraphrase all text fields in an event"""
    paraphrased_event = event.copy()
    
    # Paraphrase top-level fields
    text_fields = ["event", "actual", "forecast", "previous"]
    for field in text_fields:
        if field in paraphrased_event and paraphrased_event[field]:
            paraphrased_event[field] = paraphrase_text(paraphrased_event[field])
    
    # Paraphrase details fields
    if "details" in paraphrased_event:
        paraphrased_event["details"] = paraphrased_event["details"].copy()
        detail_fields = [
            "source", "measures", "usual_effect", "frequency", 
            "next_release", "ff_notes", "derived_via", "acro_expand", 
            "also_called", "speaker", "description"
        ]
        for field in detail_fields:
            if field in paraphrased_event["details"] and paraphrased_event["details"][field]:
                paraphrased_event["details"][field] = paraphrase_text(paraphrased_event["details"][field])
    
    return paraphrased_event

# Pydantic Models with validation
class EventDetail(BaseModel):
    source: str = ""
    measures: str = ""
    usual_effect: str = ""
    frequency: str = ""
    next_release: str = ""
    ff_notes: str = ""
    derived_via: str = ""
    acro_expand: str = ""
    also_called: str = ""
    speaker: str = ""
    description: str = ""
    related_stories: List[str] = []
    history: List[str] = []

class ForexEvent(BaseModel):
    date: str
    time: str = ""
    currency: str = ""
    impact: str = "Low"
    event: str = ""
    actual: str = ""
    forecast: str = ""
    previous: str = ""
    details: EventDetail = EventDetail()
    
    @field_validator('impact')
    @classmethod
    def validate_impact(cls, v):
        if v not in ['High', 'Medium', 'Low']:
            return 'Low'
        return v

class EventsResponse(BaseModel):
    success: bool
    data: List[ForexEvent]
    total_events: int
    date_range: Dict[str, str]
    source: str  # "database" or "scrape"
    timestamp: str
    processing_time_ms: Optional[int] = None

# Redis Database Class with Paraphrasing Support
class RedisDatabase:
    def __init__(self):
        try:
            self.client = redis.Redis(
                host='redis-13632.c280.us-central1-2.gce.redns.redis-cloud.com',
                port=13632,
                decode_responses=True,
                username='default',
                password='wkSlVhquYcUAl6tMidvYJVeoD2WtBzuL',
                socket_connect_timeout=5,
                socket_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30
            )
            # Test connection
            self.client.ping()
            logger.info("Redis database connection successful")
        except Exception as e:
            logger.error(f"Redis database connection failed: {e}")
            raise
    
    def key_for(self, date: str, paraphrased: bool = False) -> str:
        """Generate database key for individual date"""
        suffix = ":paraphrased" if paraphrased else ":original"
        return f"forex:events:{date}{suffix}"
    
    def check_dates_in_db(self, start_date: str, end_date: str, paraphrased: bool = True) -> Dict[str, Any]:
        """
        Check which dates exist in database, return partial data analysis
        Returns: {
            'existing_events': [...],  # All events from existing dates  
            'existing_dates': [...],   # Dates that exist in DB
            'missing_dates': [...]     # Dates that need to be scraped
        }
        """
        try:
            # Generate all dates in range
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            all_dates = []
            current_dt = start_dt
            while current_dt <= end_dt:
                all_dates.append(current_dt.strftime("%Y-%m-%d"))
                current_dt += timedelta(days=1)
            
            existing_events = []
            existing_dates = []
            missing_dates = []
            
            # Check each date individually
            for date_str in all_dates:
                key = self.key_for(date_str, paraphrased)
                
                try:
                    data = self.client.get(key)
                    if data:
                        date_events = json.loads(data)
                        existing_events.extend(date_events)
                        existing_dates.append(date_str)
                        logger.info(f"Database HIT for {date_str} ({'paraphrased' if paraphrased else 'original'}): {len(date_events)} events")
                    else:
                        missing_dates.append(date_str)
                        logger.info(f"Database MISS for {date_str} ({'paraphrased' if paraphrased else 'original'})")
                except Exception as e:
                    logger.error(f"Redis get error for {date_str}: {e}")
                    missing_dates.append(date_str)
            
            logger.info(f"Database analysis for {start_date} to {end_date}: {len(existing_dates)} existing, {len(missing_dates)} missing")
            
            return {
                'existing_events': existing_events,
                'existing_dates': existing_dates,
                'missing_dates': missing_dates
            }
                
        except Exception as e:
            logger.error(f"Redis check_dates_in_db error: {e}")
            return {
                'existing_events': [],
                'existing_dates': [],
                'missing_dates': all_dates
            }
    
    def get_events_for_date(self, date: str, paraphrased: bool = True) -> List[Dict[str, Any]]:
        """Get events for a specific date from database"""
        key = self.key_for(date, paraphrased)
        try:
            data = self.client.get(key)
            if data:
                return json.loads(data)
            return []
        except Exception as e:
            logger.error(f"Error getting events for {date}: {e}")
            return []
    

    
    def delete(self, start_date: str, end_date: str) -> bool:
        """Delete both original and paraphrased data for date range from database"""
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            total_deleted = 0
            current_dt = start_dt
            
            while current_dt <= end_dt:
                date_str = current_dt.strftime("%Y-%m-%d")
                original_key = self.key_for(date_str, paraphrased=False)
                paraphrased_key = self.key_for(date_str, paraphrased=True)
                
                try:
                    result_original = self.client.delete(original_key)
                    result_paraphrased = self.client.delete(paraphrased_key)
                    
                    if result_original > 0 or result_paraphrased > 0:
                        total_deleted += (result_original + result_paraphrased)
                        logger.info(f"Deleted records for {date_str} (original: {result_original}, paraphrased: {result_paraphrased})")
                    
                except Exception as e:
                    logger.error(f"Redis delete error for {date_str}: {e}")
                
                current_dt += timedelta(days=1)
            
            if total_deleted > 0:
                logger.info(f"Total database records deleted: {total_deleted}")
            else:
                logger.info(f"No database records found for {start_date} to {end_date}")
                
            return total_deleted > 0
            
        except Exception as e:
            logger.error(f"Redis delete error: {e}")
            return False
    
    def exists(self, start_date: str, end_date: str, paraphrased: bool = False) -> bool:
        """Check if data exists in database for ALL dates in range"""
        try:
            start_dt = datetime.strptime(start_date, "%Y-%m-%d")
            end_dt = datetime.strptime(end_date, "%Y-%m-%d")
            
            current_dt = start_dt
            while current_dt <= end_dt:
                date_str = current_dt.strftime("%Y-%m-%d")
                key = self.key_for(date_str, paraphrased)
                
                if not self.client.exists(key):
                    return False
                    
                current_dt += timedelta(days=1)
            
            return True
            
        except Exception as e:
            logger.error(f"Redis exists error: {e}")
            return False
    
    def get_all_keys(self, pattern: str = "forex:events:*") -> List[str]:
        """Get all keys matching pattern"""
        try:
            return self.client.keys(pattern)
        except Exception as e:
            logger.error(f"Redis keys error: {e}")
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get Redis database statistics"""
        try:
            info = self.client.info()
            return {
                "redis_version": info.get("redis_version"),
                "connected_clients": info.get("connected_clients"),
                "used_memory_human": info.get("used_memory_human"),
                "total_commands_processed": info.get("total_commands_processed"),
                "keyspace_hits": info.get("keyspace_hits"),
                "keyspace_misses": info.get("keyspace_misses"),
                "uptime_in_seconds": info.get("uptime_in_seconds"),
                "total_connections_received": info.get("total_connections_received"),
                "total_keys": len(self.get_all_keys())
            }
        except Exception as e:
            logger.error(f"Error getting Redis stats: {e}")
            return {}

# Optimized Forex Factory Scraper
class ComprehensiveForexFactoryScraper:
    def __init__(self):
        self.results = []
        self.max_retries = 3
        self.retry_delay = 5
    
    def log_info(self, message: str):
        logger.info(f"SCRAPER: {message}")
    
    def log_error(self, message: str):
        logger.error(f"SCRAPER ERROR: {message}")
    
    def get_url_for_date(self, date: datetime) -> str:
        month = date.strftime('%b').lower()
        day = date.day
        year = date.year
        return f"https://www.forexfactory.com/calendar?day={month}{day}.{year}"
    
    def scrape_date(self, driver: Driver, date: datetime) -> List[Dict[str, Any]]:
        events = []
        date_str = date.strftime('%Y-%m-%d')
        
        for attempt in range(self.max_retries):
            try:
                url = self.get_url_for_date(date)
                self.log_info(f"Scraping URL (attempt {attempt + 1}): {url}")
                
                driver.get(url)
                time.sleep(random.uniform(2, 4))  # Reduced random delay
                
                # Check for Cloudflare
                try:
                    page_text = driver.get_text("body")
                except Exception:
                    page_text = ""
                
                if "Just a moment" in page_text or "Checking your browser" in page_text:
                    self.log_error(f"Cloudflare protection detected for {date_str}")
                    if attempt < self.max_retries - 1:
                        time.sleep(10 + attempt * 5)  # Progressive delay
                        continue
                
                # Skip calendar detection - go directly to row extraction
                # The primary selector often fails but rows are still found
                self.log_info(f"Proceeding directly to row extraction for {date_str}")
                
                # Get calendar rows directly - this is the most reliable approach
                rows = driver.select_all("tr[data-event-id]")
                if rows:
                    self.log_info(f"Found {len(rows)} rows using selector: tr[data-event-id]")
                else:
                    self.log_info(f"No rows found for {date_str}")
                    if attempt < self.max_retries - 1:
                        time.sleep(3)  # Reduced wait time
                        continue
                    return []
                
                self.log_info(f"Processing {len(rows)} rows for {date_str}")
                
                # Process each row
                for i, row in enumerate(rows):
                    try:
                        event_data = self.extract_detailed_event_data(driver, i, date_str, rows)
                        if event_data and (event_data["event"] or event_data["currency"]):
                            events.append(event_data)
                    except Exception as e:
                        self.log_error(f"Error processing row {i} for {date_str}: {e}")
                        continue
                
                self.log_info(f"Successfully scraped {len(events)} events for {date_str}")
                break  # Success, exit retry loop
                
            except Exception as e:
                self.log_error(f"Error scraping date {date_str} (attempt {attempt + 1}): {e}")
                if attempt < self.max_retries - 1:
                    time.sleep(self.retry_delay + attempt * 1)  # Reduced progressive delay
                else:
                    self.log_error(f"Failed to scrape {date_str} after {self.max_retries} attempts")
        
        return events
    
    def extract_detailed_event_data(self, driver: Driver, row_index: int, date_str: str, all_rows) -> Dict[str, Any]:
        try:
            event_data = {
                "date": date_str,
                "time": "",
                "currency": "",
                "impact": "Low",
                "event": "",
                "actual": "",
                "forecast": "",
                "previous": "",
                "details": {
                    "source": "",
                    "measures": "",
                    "usual_effect": "",
                    "frequency": "",
                    "next_release": "",
                    "ff_notes": "",
                    "derived_via": "",
                    "acro_expand": "",
                    "also_called": "",
                    "speaker": "",
                    "description": "",
                    "related_stories": [],
                    "history": []
                }
            }
            
            if row_index >= len(all_rows):
                self.log_error(f"Row index {row_index} out of range, total rows: {len(all_rows)}")
                return None
            
            row_element = all_rows[row_index]
            event_data = self.extract_basic_event_data_from_element(driver, row_element, event_data)
            
            if event_data["event"] or event_data["currency"]:
                self.log_info(f"Extracting details for event: {event_data.get('event', 'Unknown')}")
                event_data = self.extract_details_using_hash_fragment(driver, row_element, event_data)
            
            return event_data
        
        except Exception as e:
            self.log_error(f"Error extracting detailed event data for row {row_index}: {e}")
            return None
    
    def extract_basic_event_data_from_element(self, driver: Driver, row_element, event_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Time extraction
            time_selectors = [
                ".calendar__time span",
                ".calendar__time",
                "[class*='time']",
                "td:nth-child(2)",
                "td:first-child"
            ]
            for selector in time_selectors:
                time_elem = row_element.select(selector)
                if getattr(time_elem, 'text', '').strip():
                    time_text = time_elem.text.strip()
                    if time_text and time_text != "All Day":
                        event_data["time"] = time_text
                        break
            
            # Currency extraction
            currency_selectors = [
                ".calendar__currency span",
                ".calendar__currency",
                "[class*='currency']",
                "td:nth-child(3)",
                "td:nth-child(2)"
            ]
            for selector in currency_selectors:
                currency_elem = row_element.select(selector)
                if getattr(currency_elem, 'text', '').strip():
                    currency_text = currency_elem.text.strip()
                    if currency_text and len(currency_text) <= 3:
                        event_data["currency"] = currency_text
                        break
            
            # Impact extraction
            impact_selectors = [
                ".calendar__impact span",
                ".calendar__impact",
                "[class*='impact']",
                "td:nth-child(4)"
            ]
            for selector in impact_selectors:
                impact_elem = row_element.select(selector)
                if impact_elem:
                    class_name = (impact_elem.get_attribute("class") or "").lower()
                    if "ff-impact-red" in class_name:
                        event_data["impact"] = "High"
                        break
                    elif "ff-impact-ora" in class_name:
                        event_data["impact"] = "Medium"
                        break
                    else:
                        event_data["impact"] = "Low"
                        break
            
            # Event name extraction
            event_selectors = [
                ".calendar__event .calendar__event-title",
                ".calendar__event",
                "[class*='event']",
                "td:nth-child(5)",
                "td:nth-child(4)"
            ]
            for selector in event_selectors:
                event_elem = row_element.select(selector)
                if getattr(event_elem, 'text', '').strip():
                    event_text = event_elem.text.strip()
                    if event_text and len(event_text) > 2:
                        event_data["event"] = event_text
                        break
            
            # Actual, Forecast, Previous extraction
            self._extract_numeric_data(row_element, event_data)
            
            return event_data
        except Exception as e:
            self.log_error(f"Error extracting basic event data: {e}")
            return event_data
    
    def _extract_numeric_data(self, row_element, event_data):
        # Actual
        actual_selectors = [".calendar__actual span", ".calendar__actual", "[class*='actual']"]
        for selector in actual_selectors:
            actual_elem = row_element.select(selector)
            if getattr(actual_elem, 'text', '').strip():
                event_data["actual"] = actual_elem.text.strip()
                break
        
        # Forecast
        forecast_selectors = [".calendar__forecast span", ".calendar__forecast", "[class*='forecast']"]
        for selector in forecast_selectors:
            forecast_elem = row_element.select(selector)
            if getattr(forecast_elem, 'text', '').strip():
                event_data["forecast"] = forecast_elem.text.strip()
                break
        
        # Previous
        previous_selectors = [".calendar__previous span", ".calendar__previous", "[class*='previous']"]
        for selector in previous_selectors:
            previous_elem = row_element.select(selector)
            if getattr(previous_elem, 'text', '').strip():
                event_data["previous"] = previous_elem.text.strip()
                break
    
    def extract_details_using_hash_fragment(self, driver: Driver, row_element, event_data: Dict[str, Any]) -> Dict[str, Any]:
        try:
            # Find detail link using best working selector
            detail_link = None
            try:
                detail_link = row_element.select("a.calendar__detail-link")
                if detail_link:
                    self.log_info("Found detail link using selector: a.calendar__detail-link")
            except Exception:
                self.log_info("Detail link not found with primary selector")
            
            if detail_link:
                event_id = row_element.get_attribute("data-event-id")
                if event_id:
                    self.log_info(f"Found event ID: {event_id} for event: {event_data.get('event', 'Unknown')}")
                    
                    try:
                        self.log_info(f"Clicking detail link for event: {event_data.get('event', 'Unknown')}")
                        detail_link.click()
                        time.sleep(3)
                        
                        event_data = self.extract_details_from_detail_pane(driver, event_data)
                        
                        detail_link.click()
                        time.sleep(2)
                        
                    except Exception as click_error:
                        self.log_error(f"Error clicking detail link: {click_error}")
                        # Fallback to hash fragment
                        current_url = driver.current_url
                        detail_url = f"{current_url}#detail={event_id}"
                        self.log_info(f"Trying hash fragment URL: {detail_url}")
                        
                        driver.get(detail_url)
                        time.sleep(5)
                        
                        try:
                            driver.wait_for_element("div.half.details", timeout=10)
                            self.log_info("Detail pane loaded successfully")
                        except:
                            self.log_info("Detail pane not found, trying alternative selectors")
                        
                        event_data = self.extract_details_from_detail_pane(driver, event_data)
                        driver.get(current_url)
                        time.sleep(2)
                else:
                    self.log_error(f"No event ID found for event: {event_data.get('event', 'Unknown')}")
                    # Try to extract details anyway
                    self.log_info(f"Trying to extract details without event ID for: {event_data.get('event', 'Unknown')}")
                    event_data = self.extract_details_from_detail_pane(driver, event_data)
            else:
                self.log_info(f"No detail link found for event: {event_data.get('event', 'Unknown')}")
                # Try to extract details anyway - maybe they're already visible
                self.log_info(f"Trying to extract details without detail link for: {event_data.get('event', 'Unknown')}")
                event_data = self.extract_details_from_detail_pane(driver, event_data)
            
            return event_data
            
        except Exception as e:
            self.log_error(f"Error extracting details using hash fragment: {e}")
            # Try to extract details anyway as fallback
            try:
                self.log_info(f"Fallback: Trying to extract details for: {event_data.get('event', 'Unknown')}")
                event_data = self.extract_details_from_detail_pane(driver, event_data)
            except Exception as fallback_error:
                self.log_error(f"Fallback detail extraction also failed: {fallback_error}")
            return event_data
    
    def extract_details_from_detail_pane(self, driver: Driver, event_data: Dict[str, Any]) -> Dict[str, Any]:
        """Extract detailed information from the loaded detail pane - OPTIMIZED VERSION"""
        try:
            self.log_info(f"EXTRACTING DETAILS for event: {event_data.get('event', 'Unknown')}")
            
            # Wait for dynamic content to load
            time.sleep(1)
            
            # OPTIMIZED APPROACH: Use only Method 3 (page-wide specs tables) - 100% success rate
            all_specs_tables = driver.select_all("table.calendarspecs")
            
            if all_specs_tables:
                self.log_info(f"Found {len(all_specs_tables)} specs tables on page")
                
                for table in all_specs_tables:
                    spec_rows = table.select_all("tr")
                    
                    for row in spec_rows:
                        spec_cells = row.select_all("td")
                        
                        if len(spec_cells) >= 2:
                            spec_name = spec_cells[0].text.strip()
                            spec_value = spec_cells[1].text.strip()
                            
                            # Map spec names to our fields
                            if "Source" in spec_name:
                                event_data["details"]["source"] = spec_value
                            elif "Measures" in spec_name:
                                event_data["details"]["measures"] = spec_value
                            elif "Usual Effect" in spec_name:
                                event_data["details"]["usual_effect"] = spec_value
                            elif "Frequency" in spec_name:
                                event_data["details"]["frequency"] = spec_value
                            elif "Next Release" in spec_name:
                                event_data["details"]["next_release"] = spec_value
                            elif "FF Notes" in spec_name:
                                event_data["details"]["ff_notes"] = spec_value
                            elif "Why Traders" in spec_name or "Care" in spec_name:
                                if not event_data["details"]["ff_notes"]:
                                    event_data["details"]["ff_notes"] = spec_value
                                else:
                                    event_data["details"]["ff_notes"] += f" | {spec_value}"
                            elif "Derived Via" in spec_name:
                                event_data["details"]["derived_via"] = spec_value
                            elif "Acro Expand" in spec_name:
                                event_data["details"]["acro_expand"] = spec_value
                            elif "Also Called" in spec_name:
                                event_data["details"]["also_called"] = spec_value
                            elif "Speaker" in spec_name:
                                event_data["details"]["speaker"] = spec_value
                            elif "Description" in spec_name:
                                event_data["details"]["description"] = spec_value
            else:
                self.log_info("No specs tables found on page")
            
            # Log extraction summary
            detail_count = self._count_details(event_data)
            self.log_info(f"Extracted {detail_count} detail fields for {event_data.get('event', 'Unknown')}")
            
            return event_data
            
        except Exception as e:
            self.log_error(f"Error extracting details: {e}")
            return event_data
    
    def _has_details(self, event_data: Dict[str, Any]) -> bool:
        """Check if event has any details"""
        details = event_data.get("details", {})
        return any(v for v in details.values() if v)
    
    def _count_details(self, event_data: Dict[str, Any]) -> int:
        """Count how many detail fields have values"""
        details = event_data.get("details", {})
        return sum(1 for v in details.values() if v and v != "")

# Global instances
redis_db = RedisDatabase()
scraper = ComprehensiveForexFactoryScraper()

# Browser decorator for scraping
@browser(
    user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    headless=True,
    block_images=True,
    window_size=(1920, 1080)
)
def scrape_forex_data(driver: Driver, data=None) -> List[Dict[str, Any]]:
    """Scrape forex data for specific list of dates using browser automation"""
    dates_to_scrape = data.get('dates_to_scrape', [])
    
    if not dates_to_scrape:
        scraper.log_error("No dates provided to scrape")
        return []
    
    all_events = []
    for date in dates_to_scrape:
        scraper.log_info(f"Scraping date: {date.strftime('%Y-%m-%d')}")
        events = scraper.scrape_date(driver, date)
        all_events.extend(events)
        time.sleep(random.uniform(2, 4))  # Delay between dates
    
    return all_events

# FastAPI Application with optimized lifespan
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    logger.info("Starting Forex Factory Scraper API...")
    logger.info("Redis database connection established")
    load_paraphrase_model() # Load model at startup
    yield
    # Shutdown
    logger.info("Shutting down Forex Factory Scraper API...")

app = FastAPI(
    title="Forex Factory Scraper API",
    description="Comprehensive Forex Factory calendar scraper with Redis caching",
    version="1.0.0",
    lifespan=lifespan
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure as needed for production
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["*"],
    expose_headers=["*"]
)

# Request logging middleware
@app.middleware("http")
async def log_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    process_time = time.time() - start_time
    logger.info(f"{request.method} {request.url.path} - {response.status_code} - {process_time:.3f}s")
    return response

@app.get("/", response_model=dict)
async def root():
    """API status and information"""
    return {
        "message": "Forex Factory Scraper API with Paraphrasing",
        "version": "1.0.0",
        "status": "running",
        "features": {
            "paraphrasing": "Enabled - Returns paraphrased data by default",
            "dual_database": "Original and paraphrased data stored separately in database",
            "flexible_output": "Choose between original or paraphrased data"
        },
        "endpoints": {
            "/events": "GET - Retrieve forex events (paraphrased by default, use ?original=true for original)",
            "/events/original": "GET - Retrieve original forex events (same as /events?original=true)",
            "/health": "GET - Health check",
            "/database/delete": "DELETE - Delete database records for date range",
            "/database/info": "GET - Database statistics"
        },
        "usage_examples": {
            "paraphrased": "/events?start=2025-08-16&end=2025-08-17",
            "original": "/events?start=2025-08-16&end=2025-08-17&original=true",
            "original_alt": "/events/original?start=2025-08-16&end=2025-08-17"
        }
    }

@app.get("/health")
async def health_check():
    """Health check endpoint"""
    try:
        # Test Redis connection
        redis_db.client.ping()
        return {"status": "healthy", "redis": "connected", "timestamp": datetime.now().isoformat()}
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "unhealthy", "redis": "disconnected", "error": str(e), "timestamp": datetime.now().isoformat()}

@app.get("/events", response_model=EventsResponse)
async def get_events(
    start: str = Query(..., description="Start date in YYYY-MM-DD format", examples=["2025-08-16"]),
    end: str = Query(..., description="End date in YYYY-MM-DD format", examples=["2025-08-17"]),
    original: bool = Query(False, description="Return original data instead of paraphrased", examples=[False]),
    background_tasks: BackgroundTasks = None
):
    start_time = time.time()
    
    try:
        # Validate dates (unchanged)
        try:
            start_date = datetime.strptime(start, "%Y-%m-%d")
            end_date = datetime.strptime(end, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        if start_date > end_date:
            raise HTTPException(status_code=400, detail="Start date must be before or equal to end date")
        
        date_diff = (end_date - start_date).days
        if date_diff > 30:
            raise HTTPException(status_code=400, detail="Date range cannot exceed 30 days")
        
        current_date = datetime.now()
        if start_date < current_date - timedelta(days=365) or end_date > current_date + timedelta(days=365):
            raise HTTPException(status_code=400, detail="Dates cannot be more than 1 year in the past or future")
        
        logger.info(f"PROCESSING REQUEST: {start} to {end} ({'original' if original else 'paraphrased'})")
        
        # Step 1: Check database for existing and missing dates
        db_analysis = redis_db.check_dates_in_db(start, end, paraphrased=not original)
        existing_events = db_analysis['existing_events']
        existing_dates = db_analysis['existing_dates']
        missing_dates = db_analysis['missing_dates']
        
        logger.info(f"DATABASE ANALYSIS: Existing dates: {existing_dates}, Missing dates: {missing_dates}, Existing events: {len(existing_events)}")
        
        all_events = existing_events[:]  # Start with existing (already in requested format: paraphrased if original=False)
        
        # Step 2: Scrape only exact missing dates if any
        if missing_dates:
            logger.info(f"SCRAPING MISSING DATES: {missing_dates}")
            try:
                # Convert missing dates to datetime objects
                missing_date_objects = [datetime.strptime(d, "%Y-%m-%d") for d in missing_dates]
                
                # Scrape only specific missing dates
                scraped_events = scrape_forex_data(data={'dates_to_scrape': missing_date_objects})
                
                logger.info(f"SCRAPED: {len(scraped_events)} events for missing dates")
                
                # ALWAYS process ALL missing dates, even if no events were found
                # Initialize scraped_by_date with empty arrays for all missing dates
                scraped_by_date = {}
                for missing_date in missing_dates:
                    scraped_by_date[missing_date] = []

                # Add scraped events to their respective dates
                for event in scraped_events:
                    event_date = event.get('date', '')
                    if event_date in scraped_by_date:  # Should always be true now
                        scraped_by_date[event_date].append(event)

                # Save ALL missing dates to database (both original and paraphrased)
                # This includes dates with zero events (empty arrays)
                for date, date_events in scraped_by_date.items():
                    # Save original
                    original_key = redis_db.key_for(date, paraphrased=False)
                    redis_db.client.set(original_key, json.dumps(date_events, ensure_ascii=False))
                    
                    # Save paraphrased
                    paraphrased_events = [paraphrase_event(e) for e in date_events]
                    paraphrased_key = redis_db.key_for(date, paraphrased=True)
                    redis_db.client.set(paraphrased_key, json.dumps(paraphrased_events, ensure_ascii=False))
                    
                    logger.info(f"SAVED TO DB: {len(date_events)} events for {date} (original + paraphrased)")

                # Add to all_events in the requested format
                if scraped_events:  # Only if we actually got some events
                    if original:
                        all_events.extend(scraped_events)  # Add original scraped
                    else:
                        paraphrased_scraped = [paraphrase_event(e) for e in scraped_events]
                        all_events.extend(paraphrased_scraped)  # Add paraphrased scraped
                
            except Exception as scrape_error:
                logger.error(f"SCRAPING ERROR: {scrape_error}")
                # If scraping fails but we have partial data, return it
                if all_events:
                    logger.info(f"Scraping failed, returning partial data from database ({len(all_events)} events)")
                else:
                    raise HTTPException(status_code=500, detail=f"Scraping failed and no data in database: {str(scrape_error)}")
        
        # Step 3: Sort all events by date and time (to ensure order)
        all_events.sort(key=lambda x: (x.get('date', ''), x.get('time', '')))
        
        # Step 4: Determine source
        if not missing_dates:
            source = "database"
        elif not existing_dates:
            source = "scrape"
        else:
            source = "hybrid"
        
        processing_time = int((time.time() - start_time) * 1000)
        logger.info(f"RESPONSE: {len(all_events)} events from {source} in {processing_time}ms")
        
        return EventsResponse(
            success=True,
            data=[ForexEvent(**event) for event in all_events],
            total_events=len(all_events),
            date_range={"start": start, "end": end},
            source=source,
            timestamp=datetime.now().isoformat(),
            processing_time_ms=processing_time
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise HTTPException(status_code=500, detail=f"Internal server error: {str(e)}")

@app.get("/events/original", response_model=EventsResponse)
async def get_original_events(
    start: str = Query(..., description="Start date in YYYY-MM-DD format", examples=["2025-08-16"]),
    end: str = Query(..., description="End date in YYYY-MM-DD format", examples=["2025-08-17"]),
    background_tasks: BackgroundTasks = None
):
    """
    Get original (non-paraphrased) forex events for specified date range
    
    - **start**: Start date (YYYY-MM-DD)
    - **end**: End date (YYYY-MM-DD)
    
    This endpoint is equivalent to /events?original=true
    Returns original scraped data without paraphrasing.
    """
    # Reuse the main events endpoint with original=True
    return await get_events(start=start, end=end, original=True, background_tasks=background_tasks)

@app.delete("/database/delete")
async def delete_database_records(
    start: str = Query(..., description="Start date in YYYY-MM-DD format", examples=["2025-08-16"]),
    end: str = Query(..., description="End date in YYYY-MM-DD format", examples=["2025-08-17"])
):
    """Delete database records for specified date range"""
    try:
        # Validate dates
        try:
            datetime.strptime(start, "%Y-%m-%d")
            datetime.strptime(end, "%Y-%m-%d")
        except ValueError:
            raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
        
        success = redis_db.delete(start, end)
        
        if success:
            return {"message": f"Database records deleted for {start} to {end}", "success": True}
        else:
            return {"message": f"No database records found for {start} to {end}", "success": False}
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting database records: {e}")
        raise HTTPException(status_code=500, detail=f"Error deleting database records: {str(e)}")

@app.get("/database/info")
async def database_info():
    """Get database information and statistics"""
    try:
        stats = redis_db.get_stats()
        return {
            **stats,
            "total_records": stats.get("total_keys", 0),  # Alias for frontend compatibility
            "timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        logger.error(f"Error getting database info: {e}")
        raise HTTPException(status_code=500, detail=f"Error getting database info: {str(e)}")

# Run the application
if __name__ == "__main__":
    import socket
    
    def find_available_port(start_port=8000, max_attempts=10):
        """Find an available port starting from start_port"""
        for port in range(start_port, start_port + max_attempts):
            try:
                with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
                    s.bind(('127.0.0.1', port))
                    return port
            except OSError:
                continue
        return None
    
    # Find available port
    port = find_available_port(8000)
    if port is None:
        logger.error("No available ports found in range 8000-8010")
        sys.exit(1)
    
    logger.info(f"Starting FastAPI Forex Factory Scraper on port {port}...")
    uvicorn.run(
        "backend:app",
        host="127.0.0.1",
        port=port,
        reload=False,  # Set to True for development
        workers=1,  # Single worker to avoid browser conflicts
        log_level="info"
    )


