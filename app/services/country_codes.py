"""
Country code mapping service for compact geolocation display.
"""

from typing import Dict, Optional


class CountryCodeService:
    """Service for mapping country names to ISO country codes."""
    
    # Mapping of common country names to ISO 3166-1 alpha-2 codes
    COUNTRY_MAPPING = {
        # Major countries
        "Russia": "RU",
        "United States": "US",
        "China": "CN",
        "Germany": "DE",
        "United Kingdom": "GB",
        "France": "FR",
        "Japan": "JP",
        "India": "IN",
        "Brazil": "BR",
        "Canada": "CA",
        "Australia": "AU",
        "Italy": "IT",
        "Spain": "ES",
        "Mexico": "MX",
        "South Korea": "KR",
        "Netherlands": "NL",
        "Turkey": "TR",
        "Saudi Arabia": "SA",
        "Switzerland": "CH",
        "Belgium": "BE",
        "Poland": "PL",
        "Argentina": "AR",
        "Sweden": "SE",
        "Ireland": "IE",
        "Israel": "IL",
        "Austria": "AT",
        "Nigeria": "NG",
        "Norway": "NO",
        "United Arab Emirates": "AE",
        "Egypt": "EG",
        "South Africa": "ZA",
        "Finland": "FI",
        "Denmark": "DK",
        "Chile": "CL",
        "Bangladesh": "BD",
        "Philippines": "PH",
        "Vietnam": "VN",
        "Czech Republic": "CZ",
        "Romania": "RO",
        "New Zealand": "NZ",
        "Peru": "PE",
        "Greece": "GR",
        "Portugal": "PT",
        "Hungary": "HU",
        "Qatar": "QA",
        "Kuwait": "KW",
        "Ukraine": "UA",
        "Morocco": "MA",
        "Slovakia": "SK",
        "Kenya": "KE",
        "Ecuador": "EC",
        "Ethiopia": "ET",
        "Sri Lanka": "LK",
        "Dominican Republic": "DO",
        "Guatemala": "GT",
        "Uruguay": "UY",
        "Croatia": "HR",
        "Bulgaria": "BG",
        "Costa Rica": "CR",
        "Lithuania": "LT",
        "Slovenia": "SI",
        "Latvia": "LV",
        "Estonia": "EE",
        "Serbia": "RS",
        "Lebanon": "LB",
        "Tunisia": "TN",
        "Belarus": "BY",
        "Panama": "PA",
        "Jordan": "JO",
        "Ghana": "GH",
        "Paraguay": "PY",
        "Cambodia": "KH",
        "El Salvador": "SV",
        "Honduras": "HN",
        "Nepal": "NP",
        "Nicaragua": "NI",
        "Moldova": "MD",
        "Albania": "AL",
        "Armenia": "AM",
        "Mongolia": "MN",
        "Jamaica": "JM",
        "Bahrain": "BH",
        "Trinidad and Tobago": "TT",
        "Cyprus": "CY",
        "Luxembourg": "LU",
        "Malta": "MT",
        "Iceland": "IS",
        "Brunei": "BN",
        "Maldives": "MV",
        "Barbados": "BB",
        "Belize": "BZ",
        "Bahamas": "BS",
        "Fiji": "FJ",
        "Vanuatu": "VU",
        "Samoa": "WS",
        "Palau": "PW",
        "Nauru": "NR",
        "Tuvalu": "TV",
        "San Marino": "SM",
        "Monaco": "MC",
        "Liechtenstein": "LI",
        "Andorra": "AD",
        "Vatican City": "VA",
        
        # Common variations and alternative names
        "USA": "US",
        "UK": "GB",
        "Britain": "GB",
        "England": "GB",
        "Scotland": "GB",
        "Wales": "GB",
        "Northern Ireland": "GB",
        "Korea": "KR",
        "South Korea": "KR",
        "North Korea": "KP",
        "UAE": "AE",
        "Czech": "CZ",
        "Czechia": "CZ",
        "Slovak Republic": "SK",
        "Republic of Korea": "KR",
        "Russian Federation": "RU",
        "People's Republic of China": "CN",
        "Republic of China": "TW",
        "Taiwan": "TW",
        "Hong Kong": "HK",
        "Macau": "MO",
        "Singapore": "SG",
        "Malaysia": "MY",
        "Thailand": "TH",
        "Indonesia": "ID",
        "Myanmar": "MM",
        "Burma": "MM",
        "Laos": "LA",
        "Brunei Darussalam": "BN",
        "East Timor": "TL",
        "Timor-Leste": "TL",
        
        # Special cases
        "Local": "Local",
        "Unknown": "??",
        "Private": "Private",
        "": "??",
    }
    
    @classmethod
    def get_country_code(cls, country_name: str) -> str:
        """
        Get ISO country code for a country name.
        
        Args:
            country_name: Full country name
            
        Returns:
            ISO 3166-1 alpha-2 country code or original name if not found
        """
        if not country_name or not isinstance(country_name, str):
            return "??"
            
        # Clean the country name
        country_clean = country_name.strip()
        
        # Direct lookup
        if country_clean in cls.COUNTRY_MAPPING:
            return cls.COUNTRY_MAPPING[country_clean]
            
        # Case-insensitive lookup
        for name, code in cls.COUNTRY_MAPPING.items():
            if name.lower() == country_clean.lower():
                return code
                
        # Partial match for common cases
        country_lower = country_clean.lower()
        if "united states" in country_lower or "america" in country_lower:
            return "US"
        elif "united kingdom" in country_lower or "britain" in country_lower:
            return "GB"
        elif "russia" in country_lower:
            return "RU"
        elif "china" in country_lower:
            return "CN"
        elif "germany" in country_lower:
            return "DE"
        elif "france" in country_lower:
            return "FR"
        elif "japan" in country_lower:
            return "JP"
        elif "india" in country_lower:
            return "IN"
        elif "brazil" in country_lower:
            return "BR"
        elif "canada" in country_lower:
            return "CA"
        elif "australia" in country_lower:
            return "AU"
            
        # If no match found, return first 2 characters uppercase
        if len(country_clean) >= 2:
            return country_clean[:2].upper()
        else:
            return "??"
    
    @classmethod
    def format_location(cls, country: str, city: str) -> str:
        """
        Format location as 'CC/City' for compact display.
        
        Args:
            country: Country name
            city: City name
            
        Returns:
            Formatted location string
        """
        country_code = cls.get_country_code(country)
        
        # Clean city name
        city_clean = city.strip() if city else ""
        
        # Handle special cases
        if country_code == "Local" and city_clean == "Local":
            return "Local/Local"
        elif not city_clean or city_clean.lower() in ["unknown", "", "n/a"]:
            return f"{country_code}/--"
        else:
            # Limit city name length for readability
            if len(city_clean) > 15:
                city_clean = city_clean[:12] + "..."
            return f"{country_code}/{city_clean}"


# Global instance
country_code_service = CountryCodeService()