import streamlit

STREETS_WITH_MISLEADING_NAMES = [
    {
        "name": "Rodeo Drive",
        "location": "Beverly Hills",
        "known_for": "Shopping",
        "should_be_known_for": "Cattle"
    },
    {
        "name": "Exchange Avenue",
        "location": "Fort Worth",
        "known_for": "Cattle",
        "should_be_known_for": "Stock Exchange",
    },
    {
        "name": "Wall Street",
        "location": "New York City",
        "known_for": "Stock Exchange",
        "should_be_known_for": "Wall"
    },
    {
        "name": "East Side Gallery",
        "location": "Berlin",
        "known_for": "Wall",
        "should_be_known_for": "Statue"
    },
    {
        "known_for": "Statue",
        "location": "New York City",
        "name": "The Battery",
        "should_be_known_for": "Electricity"
    },

    {
        "name": "Printer's Alley",
        "location": "Nashville",
        "known_for": "Music",
        "should_be_known_for": "Printing"
    },
    {
        "name": "Fleet Street",
        "location": "London",
        "known_for": "Printing",
        "should_be_known_for": "Port"
    },


    {
        "name": "Main Street, USA",
        "location": "Disneyland",
        "known_for": "Castle",
        "should_be_known_for": "Town Square"
    },
    {
        "name": "Penny Lane",
        "location": "Liverpool",
        "known_for": "Bus stop",
        "should_be_known_for": "Toll booth"
    },
    {
        "name": "Holland Tunnel",
        "location": "New York City",
        "known_for": "Toll Booth",
        "should_be_known_for": "Windmill"
    },
    {
        "name": "Ted Williams Tunnel",
        "location": "Boston",
        "known_for": "Toll Booth",
        "should_be_known_for": "Baseball"
    },
    {
        "name": "Bond Street",
        "location": "London",
        "known_for": "Shopping",
        "should_be_known_for": "Espionage"
    },
    {
        "name": "Bletchley Park",
        "location": "Bletchley",
        "known_for": "Espinonage",
        "should_be_known_for": "a park"
    },
    {
        "name": "Milk Street",
        "location": "Boston",
        "known_for": "Ben Franklin",
        "should_be_known_for": "Dairy"
    }

    {
        "name": "Bourbon Street",
        "location": "New Orleans",
        "known_for": "Mardi Gras",
        "should_be_known_for": "Distillery"
    },

    {
        "name": "Carnaby Street",
        "location": "London",
        "known_for": "Shopping",
        "should_be_known_for": "Meat Market"
    },
    {
        "name": "Champs-Élysées",
        "location": "Paris",
        "known_for": "Arch",
        "should_be_known_for": "Field of Flowers"
    },

    {
        "name": "Picadilly",
        "location": "London",
        "known_for": "Shopping",
        "should_be_known_for": "Circus"
    },
    {
        "name": "Water Street",
        "location": "Baraboo, WI",
        "known_for": "Circus",
        "should_be_known_for": "Canal"
    },
    {
        "name": "Singel",
        "location": "Amsterdam",
        "known_for": "Canal",
        "should_be_known_for": "Recording studio"
    },
    {
        "name": "Abbey Road",
        "location": "London",
        "known_for": "Recording studio",
        "should_be_known_for": "a monastery"
    },

    {
        "name": "National Mall",
        "location": "Washington DC",
        "known_for": "Monuments",
        "should_be_known_for": "Shopping"
    },

    {
        "name": "Memorial Drive",
        "location": "St Louis",
        "known_for": "Arch",
        "should_be_known_for": "a cemetery"
    },
    {
        "name": "Boot Hill",
        "location": "Tombstone",
        "known_for": "a cemetery",
        "should_be_known_for": "shoes"
    }
]

place_fillers = set()
for street in STREETS_WITH_MISLEADING_NAMES:
    place_fillers.add(street["location"])

blank_fillers = set()
for street in STREETS_WITH_MISLEADING_NAMES:
    blank_fillers.add(street["known_for"])
    blank_fillers.add(street["should_be_known_for"])

def generate_puzzle_wording(street: dict):
    return f"""{street["name"]} in _________ is known for __________, but should be known for ________."""

streamlit.header("Streets with misleading names")
streamlit.write("The following places are known for one thing, but should be known for something else.")
streamlit.write("Can you fill in the blanks?")
streamlit.write("")
num = 0
for street in STREETS_WITH_MISLEADING_NAMES:
    num += 1
    streamlit.markdown(str(num) + ". " + generate_puzzle_wording(street))
streamlit.write("")
streamlit.write("Blank fillers:")
num = 0
for blank_filler in blank_fillers:
    num += 1
    streamlit.markdown(f"{num}. {blank_filler}")

streamlit.write("Places:")
num = 0
for place_filler in place_fillers:
    num += 1
    streamlit.markdown(f"{num}. {place_filler}")

