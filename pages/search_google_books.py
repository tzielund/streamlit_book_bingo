import os
import urllib

import requests
import streamlit

API_KEY=os.environ["BOOK_SEARCH_API_KEY"]
DUMMY_COVER="http://books.google.com/books/content?id=cutxHKHYmrMC&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api"

BINGO_CARD={
    "b": {
        "1": "Count your collection",
        "2": "Got it for the cover",
        "3": "Anthology or collection",
        "4": "Stand-alone",
        "5": "Recommended to you"
    },
    "i": {
        "1": "Published in 2022",
        "2": "But it was free...",
        "3": "Gifted Book or ARC",
        "4": "BIPOC author",
        "5": "Long title"
    },
    "n": {
        "1": "Part or a series",
        "2": "DNF",
        "3": "FREE SPACE",
        "4": "Favorite genre",
        "5": "Self or indie published"
    },
    "g": {
        "1": "Debut",
        "2": "Seasonal or holiday theme",
        "3": "Weed a book from your stash",
        "4": "Published before 2020",
        "5": "Retelling or has been retold"
    },
    "o": {
        "1": "A book you've been edging",
        "2": "Signed or special edition",
        "3": "Not your favorite format",
        "4": "Animal on the cover",
        "5": "Made you laff"
    }
}

# Display the card

@streamlit.cache
def search_books(query):
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&key={API_KEY}"
    response = requests.get(url)
    print(response.status_code)
    print(response.text)
    return(response.json())

streamlit.header("Search books")
query_title = streamlit.text_input("Title")
query_author = streamlit.text_input("Author")
if query_author or query_title:
    if query_title:
        title_query = urllib.parse.quote(str(query_title).encode('utf-8'))
    else:
        title_query = ""
    if query_author:
        author_query = urllib.parse.quote(b"inauthor:" + str(query_author).encode('utf-8'))
    else:
        author_query = ""
    query = title_query + "+" + author_query
    result_json = search_books(query)
    if result_json["totalItems"] == 0:
        streamlit.write("No volumes found")
    else:
        print(type(result_json))
        # streamlit.json(result_json)
        items = result_json["items"]
        checkboxes = list()
        for itemnum in range(0,min(len(items),10)):
            item = items[itemnum]
            vol = item["volumeInfo"]
            img,md = streamlit.columns([1,5])
            img.image(vol.get("imageLinks", {}).get("thumbnail",DUMMY_COVER))
            title = vol["title"]
            if vol.get("subtitle",""):
                title += ": " + vol["subtitle"]
            checkboxes.append(md.checkbox(title,key=f"search_result_{len(checkboxes)}"))
            authors = ", ".join(vol["authors"])
            md.text(authors)


