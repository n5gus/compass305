# School Navigator Lite (eMerge AI Hackathon 2026, Education track)

## Goal
Help Miami-Dade families find and compare schools near them, with a map and AI answers that come only from the source data.

## MVP
1. Enter an address and a grade, then see nearby eligible schools on a map and in a list.
2. School detail card that shows its source.
3. Compare 2–3 schools side by side.
4. Ask a question; the AI answers only from the selected records and cites them.

## Stretch
Commute time, Spanish/Creole, state school grades, early learning, Archie.

## Data
- Miami-Dade County GIS: public schools (MD_Emaps layer 25) and private schools (MD_LandInformation layer 56)
- Normalized into schools.json: id, name, type, grade_min, grade_max, lat, lon, address, enrollment, website, source

## API
- GET  /schools?lat&lon&grade&radius_km  returns a list of schools sorted by distance
- GET  /schools/{id}                     returns one school
- POST /ask {question, school_ids}       returns {answer, cited_ids}

## Trust
Every record shows its source and pull date, the AI answers from the given records only, and no personal data is stored.

## Process
Design doc, then API contract, then a working end-to-end slice by 12:00, feature freeze at 3:00, backup video, and submit by 5:50.
