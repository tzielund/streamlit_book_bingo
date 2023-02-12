import streamlit
import book_bingo_utils
from book_bingo_utils import BINGO, BookBingoCard

creator = "tzielund"
streamlit.write(f"Welcome, {creator}")

streamlit.header("Book Bingo Designer")

card_index = book_bingo_utils.CardIndex()

starter = streamlit.checkbox("Start a new card")
if starter:
    title = streamlit.text_input("Card Title")
    description = streamlit.text_input("Card Description")
    make_it = streamlit.button("Start it!")
    if not make_it:
        streamlit.stop()
    card_index.mint_card(title, creator, description)


my_drafts = card_index.get_my_drafts(creator)
my_draft_titles = list()
my_draft_numbers = range(0,len(my_drafts))
for draft in my_drafts:
    my_draft_titles.append(draft.get_title())

chosen_card_number = streamlit.selectbox("Choose a draft card",
                                         options=my_draft_numbers,
                                         format_func=lambda x:my_draft_titles[x])
chosen_card = my_drafts[chosen_card_number]

# Modify the card title and description
new_title = streamlit.text_input("Card Title", value=chosen_card.get_title())
if new_title:
    (chosen_card.set_title(new_title))
new_desc = streamlit.text_input("Card Title", value=chosen_card.get_description())
if new_desc:
    (chosen_card.set_description(new_desc))

# Entry for challenge and instructions
streamlit.header("Add a challenge to your card")
challenge_text = streamlit.text_input("Challenge text")
instruct_text = streamlit.text_input("Instruction details (optional)")
if challenge_text:
    streamlit.write("Click on the cell below to set that cell's challgenge to this")
else:
    streamlit.write("Type in a new challenge above and you can add to a cell below")

# Heading column for card
cols = streamlit.columns(5,gap="medium")
for col in range(0,5):
    cols[col].title(BINGO[col])
buttonMap = dict()
for row in range(0,5):
    cols = streamlit.columns(5,gap="medium")
    for col in range(0,5):
        cell = BookBingoCard.index_to_cell_code(col, row)
        display_text = chosen_card.get_challenge(cell)
        current_instructions = chosen_card.get_instructions(cell)
        buttonMap[cell] = cols[col].button(
            display_text,
            disabled=not(challenge_text),
            key=f"addButton_{cell}",
            help=current_instructions
        )

for cell in buttonMap.keys():
    if buttonMap[cell]:
        chosen_card.set_challenge(cell, challenge_text, instruct_text)
        streamlit.experimental_rerun()

if not(chosen_card.is_not_fully_specified()):
    publishButton = streamlit.button("Publish it!")
    if publishButton:
        chosen_card.publish()

