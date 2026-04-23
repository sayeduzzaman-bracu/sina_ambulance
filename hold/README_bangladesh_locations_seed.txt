Bangladesh Locations Seed Database

Files:
- bangladesh_locations_seed.sqlite
- divisions.csv
- districts.csv
- upazilas.csv
- unions.csv

What this is:
A practical offline seed database for Bangladesh administrative locations.

Coverage:
- 8 divisions
- 64 districts
- 494 upazilas
- 4,540 unions

Important:
This is NOT a full clone of Google Maps. It is a structured administrative location dataset
you can use right now for:
- dropdowns
- autocomplete
- validation
- service-area mapping
- manager dispatch filters

SQLite tables:
1. divisions(id, name_en, name_bn, url)
2. districts(id, division_id, name_en, name_bn, lat, lon, url)
3. upazilas(id, district_id, name_en, name_bn, url)
4. unions(id, upazila_id, name_en, name_bn, url)
5. location_lookup(...)
6. metadata(key, value)

Useful SQL:

-- search by English name
SELECT * FROM location_lookup
WHERE name_en LIKE '%Mirpur%';

-- all districts in Dhaka division
SELECT di.*
FROM districts di
JOIN divisions d ON d.id = di.division_id
WHERE d.name_en = 'Dhaka';

-- all upazilas in Cumilla district
SELECT u.*
FROM upazilas u
JOIN districts d ON d.id = u.district_id
WHERE d.name_en = 'Cumilla';

Suggested use in your app:
- Use division -> district -> upazila dropdowns
- Keep one free-text field for exact address / landmark
- Optionally map only your service districts first

Source:
https://github.com/techno-stupid/places-in-bangladesh
