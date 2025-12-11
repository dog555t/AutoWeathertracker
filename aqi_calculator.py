#!/usr/bin/env python3
"""
AQI Calculator Module

Converts raw PM2.5 and PM10 values to US EPA Air Quality Index (AQI)
Reference: https://www.airnow.gov/aqi/aqi-basics/
"""

import logging

logger = logging.getLogger(__name__)


class AQICalculator:
    """Calculate Air Quality Index from particulate matter measurements"""
    
    # US EPA AQI breakpoints for PM2.5 (µg/m³)
    PM25_BREAKPOINTS = [
        (0.0, 12.0, 0, 50, 'Good', '#00E400'),
        (12.1, 35.4, 51, 100, 'Moderate', '#FFFF00'),
        (35.5, 55.4, 101, 150, 'Unhealthy for Sensitive Groups', '#FF7E00'),
        (55.5, 150.4, 151, 200, 'Unhealthy', '#FF0000'),
        (150.5, 250.4, 201, 300, 'Very Unhealthy', '#8F3F97'),
        (250.5, 350.4, 301, 400, 'Hazardous', '#7E0023'),
        (350.5, 500.4, 401, 500, 'Hazardous', '#7E0023'),
    ]
    
    # US EPA AQI breakpoints for PM10 (µg/m³)
    PM10_BREAKPOINTS = [
        (0, 54, 0, 50, 'Good', '#00E400'),
        (55, 154, 51, 100, 'Moderate', '#FFFF00'),
        (155, 254, 101, 150, 'Unhealthy for Sensitive Groups', '#FF7E00'),
        (255, 354, 151, 200, 'Unhealthy', '#FF0000'),
        (355, 424, 201, 300, 'Very Unhealthy', '#8F3F97'),
        (425, 504, 301, 400, 'Hazardous', '#7E0023'),
        (505, 604, 401, 500, 'Hazardous', '#7E0023'),
    ]
    
    @staticmethod
    def calculate_aqi(pm25=None, pm10=None):
        """
        Calculate AQI from PM2.5 and/or PM10 values
        
        Args:
            pm25: PM2.5 concentration in µg/m³
            pm10: PM10 concentration in µg/m³
            
        Returns:
            Dictionary with AQI value, category, color, and details
        """
        aqi_pm25 = None
        aqi_pm10 = None
        
        if pm25 is not None:
            aqi_pm25 = AQICalculator._calculate_aqi_for_pollutant(
                pm25, AQICalculator.PM25_BREAKPOINTS
            )
        
        if pm10 is not None:
            aqi_pm10 = AQICalculator._calculate_aqi_for_pollutant(
                pm10, AQICalculator.PM10_BREAKPOINTS
            )
        
        # Use the higher AQI value (worst case)
        if aqi_pm25 and aqi_pm10:
            result = aqi_pm25 if aqi_pm25['aqi'] >= aqi_pm10['aqi'] else aqi_pm10
        elif aqi_pm25:
            result = aqi_pm25
        elif aqi_pm10:
            result = aqi_pm10
        else:
            result = {
                'aqi': 0,
                'category': 'Unknown',
                'color': '#CCCCCC',
                'description': 'No data available'
            }
        
        return result
    
    @staticmethod
    def _calculate_aqi_for_pollutant(concentration, breakpoints):
        """
        Calculate AQI for a specific pollutant using EPA formula
        
        Args:
            concentration: Pollutant concentration
            breakpoints: List of breakpoint tuples
            
        Returns:
            Dictionary with AQI information
        """
        # Find the appropriate breakpoint
        for bp_lo, bp_hi, aqi_lo, aqi_hi, category, color in breakpoints:
            if bp_lo <= concentration <= bp_hi:
                # EPA AQI formula: I = [(I_hi - I_lo) / (C_hi - C_lo)] * (C - C_lo) + I_lo
                aqi = ((aqi_hi - aqi_lo) / (bp_hi - bp_lo)) * (concentration - bp_lo) + aqi_lo
                aqi = round(aqi)
                
                return {
                    'aqi': aqi,
                    'category': category,
                    'color': color,
                    'description': AQICalculator._get_description(category)
                }
        
        # If concentration is above the highest breakpoint
        if concentration > breakpoints[-1][1]:
            return {
                'aqi': 500,
                'category': 'Hazardous',
                'color': '#7E0023',
                'description': 'Health warnings of emergency conditions. Everyone is likely to be affected.'
            }
        
        # If concentration is below the lowest breakpoint (should not happen with 0-based scale)
        return {
            'aqi': 0,
            'category': 'Good',
            'color': '#00E400',
            'description': 'Air quality is satisfactory, and air pollution poses little or no risk.'
        }
    
    @staticmethod
    def _get_description(category):
        """Get health message for AQI category"""
        descriptions = {
            'Good': 'Air quality is satisfactory, and air pollution poses little or no risk.',
            'Moderate': 'Air quality is acceptable. However, there may be a risk for some people, particularly those who are unusually sensitive to air pollution.',
            'Unhealthy for Sensitive Groups': 'Members of sensitive groups may experience health effects. The general public is less likely to be affected.',
            'Unhealthy': 'Some members of the general public may experience health effects; members of sensitive groups may experience more serious health effects.',
            'Very Unhealthy': 'Health alert: The risk of health effects is increased for everyone.',
            'Hazardous': 'Health warning of emergency conditions: everyone is more likely to be affected.'
        }
        return descriptions.get(category, 'Unknown air quality status.')
    
    @staticmethod
    def get_aqi_color_for_value(aqi_value):
        """Get color code for a specific AQI value"""
        if aqi_value <= 50:
            return '#00E400'  # Green
        elif aqi_value <= 100:
            return '#FFFF00'  # Yellow
        elif aqi_value <= 150:
            return '#FF7E00'  # Orange
        elif aqi_value <= 200:
            return '#FF0000'  # Red
        elif aqi_value <= 300:
            return '#8F3F97'  # Purple
        else:
            return '#7E0023'  # Maroon
    
    @staticmethod
    def get_recommendation(aqi_value):
        """Get health recommendations based on AQI value"""
        if aqi_value <= 50:
            return "Great day for outdoor activities!"
        elif aqi_value <= 100:
            return "Sensitive individuals should consider limiting prolonged outdoor exertion."
        elif aqi_value <= 150:
            return "Sensitive groups should reduce prolonged outdoor exertion."
        elif aqi_value <= 200:
            return "Everyone should reduce prolonged outdoor exertion."
        elif aqi_value <= 300:
            return "Everyone should avoid prolonged outdoor exertion."
        else:
            return "Everyone should remain indoors and keep activity levels low."


def main():
    """Test the AQI calculator"""
    test_values = [
        (5, 10, "Very clean air"),
        (15, 30, "Typical good air"),
        (45, 80, "Moderate air quality"),
        (80, 150, "Unhealthy for sensitive groups"),
        (180, 280, "Unhealthy air"),
        (300, 450, "Very unhealthy air"),
    ]
    
    print("AQI Calculator Test\n" + "="*50)
    
    for pm25, pm10, description in test_values:
        result = AQICalculator.calculate_aqi(pm25=pm25, pm10=pm10)
        print(f"\n{description}:")
        print(f"  PM2.5: {pm25} µg/m³, PM10: {pm10} µg/m³")
        print(f"  AQI: {result['aqi']}")
        print(f"  Category: {result['category']}")
        print(f"  Color: {result['color']}")
        print(f"  Description: {result['description']}")
        print(f"  Recommendation: {AQICalculator.get_recommendation(result['aqi'])}")


if __name__ == '__main__':
    main()
