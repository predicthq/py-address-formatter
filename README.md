# py-address-formatter

## Examples

```python
from address_formatter import format
          
address = format(city='Wellington',
                 road='Pirie Street',
                 house_number=53,
                 suburb='Mount Vic',
                 postcode='6011',
                 country_code='NZ')
```

List of valid address components:
    
    building
    city
    city_district
    continent
    country
    country_code
    country_name
    county
    footway
    hamlet
    house
    house_number
    island
    locality
    neighbourhood
    path
    pedestrian
    postcode
    province
    public_building
    region
    residential
    road
    state
    state_code
    state_district
    street
    street_name
    street_number
    suburb
    town
    village

## Run test

```bash
pip install -r requirements/test.txt
python -m pytest
```
