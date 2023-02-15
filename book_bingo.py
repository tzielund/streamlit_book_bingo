import streamlit

import book_bingo_utils
from book_bingo_utils import STATUS_OPTIONS, STATUS_FINISHED, STATUS_IN_PROGRESS, STATUS_NOT_STARTED
from PIL import Image

streamlit.title("Book Bingo!")

streamlit.header("Welcome to Book Bingo")

# streamlit.text_input("Who are you?")
# streamlit.text_input("What's your password",type="password")
player="tzielund"

card_index = book_bingo_utils.CardIndex()

playable_cards = card_index.get_published_cards()
playable_titles = list()
playable_numbers = range(0,len(playable_cards))
for card in playable_cards:
    playable_titles.append(card.get_title())

chosen_card_number = streamlit.selectbox("Choose a playable card",
                                         options=playable_numbers,
                                         format_func=lambda x:playable_titles[x])
chosen_card = playable_cards[chosen_card_number]
progress = book_bingo_utils.BookBingoPlayerProgress(player, chosen_card)

# Heading column for card
cols = streamlit.columns(5,gap="medium")
for col in range(0,5):
    cols[col].title(book_bingo_utils.BINGO[col])
buttonMap = dict()
disableOthers = False
for row in range(0,5):
    streamlit.markdown("---")
    cols = streamlit.columns(5,gap="medium")
    for col in range(0,5):
        cell = book_bingo_utils.BookBingoCard.index_to_cell_code(col, row)
        display_image = progress.get_cell_image(cell)
        hover_text = progress.get_cell_title_and_author(cell)
        status = progress.get_cell_status(cell)
        display_text = chosen_card.get_challenge(cell)
        current_instructions = chosen_card.get_instructions(cell)
        if display_image:
            # image = Image.open(display_image)
            # new_image = image.resize((125, 162))
            cols[col].image(display_image, caption=hover_text)
        else:
            cols[col].image(book_bingo_utils.BLANK_COVER, "Click to select")
        buttonMap[cell] = cols[col].checkbox(
            display_text,
            key=f"addButton_{cell}",
            help=current_instructions,
            disabled=disableOthers
        )
        if buttonMap[cell]:
            disableOthers=True
        if status:
            cols[col].write(status)

selected_cell = None
for cell in buttonMap.keys():
    if buttonMap[cell] and not selected_cell:
        selected_cell = cell
if not selected_cell:
    streamlit.write("Select a challenge above to proceed")
    streamlit.stop()

streamlit.header(f"Book details for challenge {selected_cell}")
streamlit.write(f"Challenge: {chosen_card.get_challenge(selected_cell)}")
given_title = progress.get_cell_title(selected_cell)
given_author = progress.get_cell_author(selected_cell)
given_image = progress.get_cell_image(selected_cell)
given_status = progress.get_cell_status(selected_cell)
if given_status:
    given_status_index = STATUS_OPTIONS.index(given_status)
else:
    given_status_index = 0

title_typed = streamlit.text_input("Title", given_title)
author_typed = streamlit.text_input("Author(s)", given_author)
image_url_typed = streamlit.text_input("Image URL", given_image)
current_status = streamlit.selectbox("Reading status", options=STATUS_OPTIONS, index=given_status_index)
grid_enabled = title_typed and author_typed
if not grid_enabled:
    streamlit.write("Enter a title and/or author to continue")
    streamlit.stop()
saveit = streamlit.button("Save")
if saveit:
    progress.set_cell_progress(selected_cell, title_typed,author_typed,
                               image_url_typed, current_status)
    streamlit.experimental_rerun()


streamlit.header("Search books")
if author_typed or title_typed:
    result_json = book_bingo_utils.search_books(author_typed, title_typed)
    if result_json["totalItems"] == 0:
        streamlit.write("No volumes found")
    else:
        # streamlit.json(result_json)
        items = result_json["items"]
        useItButtons = dict()
        useItData = dict()
        for itemnum in range(0,min(len(items),10)):
            item = items[itemnum]
            vol = item["volumeInfo"]
            img,md = streamlit.columns([1,5])
            imageUrl = vol.get("imageLinks", {}).get("thumbnail", book_bingo_utils.BLANK_COVER)
            img.image(imageUrl)
            title = vol["title"]
            if vol.get("subtitle",""):
                title += ": " + vol["subtitle"]
            md.markdown(f"[{title}]({vol.get('canonicalVolumeLink','')})")
            authors = ", ".join(vol["authors"])
            md.text(authors)
            useItButtons[itemnum] = md.button("Use this one", key=f"useItButton{itemnum}")
            useItData[itemnum] = {
                "title": title,
                "author": authors,
                "image": imageUrl
            }

for useItButtonNum in useItButtons:
    if useItButtons[useItButtonNum]:
        useItem = useItData[useItButtonNum]
        progress.set_cell_progress(selected_cell, useItem["title"],useItem["author"],
                                   useItem["image"], current_status)
        streamlit.experimental_rerun()




