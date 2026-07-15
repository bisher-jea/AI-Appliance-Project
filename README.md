# ApplianceIQ
This project is an AI-powered appliance identification system designed for home inspections. Users upload photos of HVAC and water heater nameplates through a web application built with HTML, FastAPI, and SQLite. The system uses gpt 5.4 mini to extract key equipment information, including the manufacturer, model number, and serial number. Based on the extracted brand and serial number, a custom age-decoding engine determines the appliance's manufacture date and calculates its age using manufacturer-specific serial number formats. The results are stored in a database and can be flagged for manual review when information cannot be confidently extracted or decoded. The goal is to automate equipment identification and age estimation, reducing manual effort while improving inspection efficiency and consistency.

## Core Functionalities
- Optical character recognition
- Equipment extraction information
- Brand recognition
- Serial number decoding
- Age calculation
- Data validation
- Manual review flagging
- Database integration
