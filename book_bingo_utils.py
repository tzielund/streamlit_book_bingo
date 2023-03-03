"""Model classes for book bingo."""

import json
import os
import urllib
from hashlib import blake2b
from pathlib import Path
from typing import Any, Dict, Tuple, List

import requests
import streamlit

CARD_DIR = "cards/"
INDEX_FILE = f"{CARD_DIR}index.json"
BINGO = "BINGO"
PLAYER_DIR = "players/"
DIRECTION_ASC = "asc"
DIRECTION_DESC = "desc"
STATUS_NOT_STARTED = "not started"
STATUS_IN_PROGRESS = "in progress"
STATUS_FINISHED = "finished"
STATUS_OPTIONS = [STATUS_NOT_STARTED,STATUS_IN_PROGRESS,STATUS_FINISHED]
API_KEY=os.environ.get("BOOK_SEARCH_API_KEY","key not available")
DUMMY_COVER="http://books.google.com/books/content?id=cutxHKHYmrMC&printsec=frontcover&img=1&zoom=1&edge=curl&source=gbs_api"
BLANK_COVER="data:image/jpeg;base64,/9j/4AAQSkZJRgABAQAAAQABAAD/2wCEAAkGBwgHBgkIBwgKCgkLDRYPDQwMDRsUFRAWIB0iIiAdHx8kKDQsJCYxJx8fLT0tMTU3Ojo6Iys/RD84QzQ5OjcBCgoKDQwNGg8PGjclHyU3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3Nzc3N//AABEIAKIAfQMBIgACEQEDEQH/xAAXAAEBAQEAAAAAAAAAAAAAAAAAAwIH/8QAGhABAAMBAQEAAAAAAAAAAAAAAAEDcTEyIf/EABQBAQAAAAAAAAAAAAAAAAAAAAD/xAAUEQEAAAAAAAAAAAAAAAAAAAAA/9oADAMBAAIRAxEAPwDttPmdUTp8zqgAAAAAAAAAAAAAAJ0+Z1ROnk6oAAAAAAAAAAAAAACdPmdUYq5OtgAAAAAAAAAAAAAAxVydbTq5OqAAAAAAAAAAAAAAAxVydbTqn5OqAAAAAAAAAAAAAAAnTydUTp5OqAAAAAAAAAAAAAAAxVydbTp5OqAAAAAAAAAAAAAAAnVydUTp8zqgAAAAAAAAAAAAAAJ0+Z1ROnzOqAAAAAAAAAAAAAAAnT5nVE6eTqgAAAAAAAAAAAAAAJ08nVAAAAAAAAAAAAAAAB//2Q=="
# DUMMY_COVER="https://encrypted-tbn0.gstatic.com/images?q=tbn:ANd9GcTgpZvIJxl4LvMxW--xCyE3v9bmKkjpVl-vbarWt8U0A-qIxhaarSULh55IUr_TyDPkTPc&usqp=CAU"

class BookBingoException(Exception):
    """Used to indicate errors of logic in Book Bingo model."""
    pass

class BookBingoCard:
    """Model of a book bingo card design."""

    CHALLENGES = "challenges"
    INSTRUCTIONS = "instructions"
    STATUS_DRAFT = "draft"
    STATUS_PUBLISHED = "published"
    STATUS_ARCHIVED = "archived"

    @classmethod
    def mint_card(cls, title, description, creator) -> str:
        """Given the starting pieces, mint a new card file and return the filename."""
        wrapper = dict()
        wrapper["title"] = title
        wrapper["description"] = description
        wrapper["creator"] = creator
        wrapper["status"] = cls.STATUS_DRAFT
        h = blake2b(digest_size=20)
        h.update(f"{title} by {creator}".encode('utf8'))
        filename = f"{CARD_DIR}{h.hexdigest()}.json"
        wrapper["filename"] = filename
        with open(filename, 'w') as OUT:
            OUT.write(json.dumps(wrapper, indent=4))
        return filename

    @classmethod
    def index_to_cell_code(cls, col:int, row:int) -> str:
        """Returns the cell code for a given row and column (eg 0, 1 is B2)."""
        # force range
        col = max(0,min(4,col))
        row = max(0,min(4,row))
        colchar = BINGO[col]
        rowchar = str(row+1)
        return f"{colchar}{rowchar}"

    @classmethod
    def cell_code_to_index(cls, cellCode:str) -> Tuple[int, int]:
        """Returns the row and column for a given cell (eg B1 returns (0, 0)."""
        colchar = cellCode[0].upper()
        rowchar = cellCode[1]
        if colchar in BINGO:
            col = BINGO.find(colchar)
        else:
            col = 0
        row = int(rowchar)-1
        row = max(0,min(4,row))
        return (col, row)

    def __init__(self, filename:str):
        """Initialize with an ID and filename (ie, read the file found at filename)."""
        self.filename = filename
        with open (filename) as IN:
            self.card_content = json.load(IN)
        self.validate()

    def validate(self):
        """Fixes the card content based on business logic rules."""
        if not isinstance(self.card_content, dict):
            raise RuntimeError(f"Card content is not valid dictionary for {self.filename}")
        # Add the challenges if not present
        if self.CHALLENGES not in self.card_content:
            self.card_content[self.CHALLENGES] = dict()
        if self.INSTRUCTIONS not in self.card_content:
            self.card_content[self.INSTRUCTIONS] = dict()
        # That's all for now.

    def write_to_file(self):
        """Overwrites the old file with the current content."""
        with open (self.filename, 'w') as OUT:
            OUT.write(json.dumps(self.card_content, indent=4))

    def get_title(self) -> str:
        """Returns the title string."""
        return self.card_content["title"]

    def set_title(self, title:str):
        """Replaces current title with this new one."""
        self.card_content["title"] = title
        self.write_to_file()

    def get_description(self) -> str:
        """Returns current description."""
        return self.card_content["description"]

    def set_description(self, description:str):
        """Replaces current description with this new one."""
        self.card_content["description"] = description
        self.write_to_file()

    def get_creator(self):
        """Returns the creator name."""
        return self.card_content["creator"]

    def get_status(self):
        """Returns the current publication status."""
        return self.card_content["status"]

    def publish(self):
        """Sets the current status to published."""
        if not self.get_status() == self.STATUS_DRAFT:
            raise BookBingoException(f"Can't publish when status is {self.get_status()}")
        missing = self.is_not_fully_specified()
        if missing:
            raise(f"Can't publish incomplete challenge (missing {missing}.")
        self.card_content["status"] = "published"
        self.write_to_file()

    def archive(self):
        """Sets the current status to archived."""
        if not self.get_status() == self.STATUS_PUBLISHED:
            raise BookBingoException(f"Can't archive when status is {self.get_status()}")
        self.card_content["status"] = "archived"
        self.write_to_file()

    def set_challenge(self, cell:str, challenge:str, instructions:str):
        """Sets or replaces current challenge text in given cell."""
        if not self.get_status() == self.STATUS_DRAFT:
            raise(BookBingoException("Can't modify published bingo card."))
        self.card_content["challenges"][cell] = challenge
        self.card_content["instructions"][cell] = instructions
        self.write_to_file()

    def get_challenge(self, cell:str) -> str:
        """Returns the challenge title for the given cell."""
        return self.card_content["challenges"].get(cell,"Reader's choice")

    def get_instructions(self, cell:str) -> str:
        """Returns the challenge title for the given cell."""
        return self.card_content["instructions"].get(cell,"")

    def is_not_fully_specified(self) -> bool:
        """Returns first empty cell or None for cully specified."""
        for colchar in BINGO:
            for row in range(1,5):
                cell = f"{colchar}{row}"
                if cell not in self.card_content[self.CHALLENGES]:
                    return cell
        return None

class CardIndex:

    def __new__(cls):
        """This makes it a singleton class."""
        if not hasattr(cls, 'instance'):
            cls.instance = super(CardIndex, cls).__new__(cls)
        return cls.instance

    def __init__(self):
        """Initialize the singleton instance by reading the file."""
        with open (INDEX_FILE) as IN:
            self.filename_list: List[str] = json.load(IN)
        # No fallback, so the file had better be there :)
        self.cardList:List[BookBingoCard] = list()
        self.cardTitleList:List[str] = list()
        for filename in self.filename_list:
            self.load_card(filename)


    def load_card(self, filename) -> BookBingoCard:
        """Loads a particular card and returns the BookBingoCard object."""
        result = BookBingoCard(filename)
        self.cardList.append(result)
        self.cardTitleList.append(result.get_title())
        return result

    def _load_cards(self):
        """Based on the index file, find all the cards, load and index them."""

    def write_to_file(self):
        """Serializes the list of filenames to the index file."""
        with open (INDEX_FILE, 'w') as OUT:
            OUT.write(json.dumps(self.filename_list, indent=4))

    def mint_card(self, title, creator, description) -> BookBingoCard:
        """Creates a new card and adds it to the indexes."""
        new_card_filename = BookBingoCard.mint_card(title, description, creator)
        new_card = self.load_card(new_card_filename)
        self.filename_list.append(new_card_filename)
        self.write_to_file()
        return new_card

    def get_published_cards(self) -> List[BookBingoCard]:
        result = list()
        for card in self.cardList:
            if card.get_status() == card.STATUS_PUBLISHED:
                result.append(card)
        return result

    def get_my_drafts(self, creator) -> List[BookBingoCard]:
        result = list()
        for card in self.cardList:
            if card.get_status() == card.STATUS_DRAFT and card.get_creator() == creator:
                result.append(card)
        return result

class BookBingoPlayerProgress:
    """Encapsulates a specific player's progress on a specific card."""

    def __init__(self, player: str, card:BookBingoCard):
        """Initialize with an ID and filename (ie, read the file found at filename)."""
        self.player = player
        self.card = card
        self.filename = f"{PLAYER_DIR}{player}/{card.filename}"
        if os.path.exists(self.filename):
            with open(self.filename) as IN:
                self.progress = json.load(IN)
        else:
            self.progress = {}
        self.validate()

    def validate(self):
        return True

    def write_to_file(self):
        """Serializes to local file."""
        fpath = Path(self.filename)
        pardir = fpath.parent.absolute()
        os.makedirs(pardir, exist_ok=True)
        with open(self.filename, 'w') as OUT:
            OUT.write(json.dumps(self.progress, indent=2))

    def get_cell_progress(self, cell):
        """Returns the book details of a given cell, if any."""
        return self.progress.get(cell,{})

    def get_cell_title(self, cell):
        """Returns the book title of a given cell, if any."""
        prog_struct = self.get_cell_progress(cell)
        return prog_struct.get("title","")

    def get_cell_author(self, cell):
        """Returns the book title of a given cell, if any."""
        prog_struct = self.get_cell_progress(cell)
        return prog_struct.get("author","")

    def get_cell_title_and_author(self, cell):
        """Returns {title} by {author} if populated."""
        if self.get_cell_progress(cell):
            prog_struct = self.get_cell_progress(cell)
            return prog_struct.get("title","No book") + " by " + prog_struct.get("author", "No author")
        return None

    def get_cell_image(self, cell):
        """Returns the book title of a given cell, if any."""
        prog_struct = self.get_cell_progress(cell)
        return prog_struct.get("image","")

    def get_cell_status(self, cell):
        """Returns the book title of a given cell, if any."""
        prog_struct = self.get_cell_progress(cell)
        return prog_struct.get("status",None)

    def set_cell_progress(self, cell, title, author, image, status):
        """Establishes a full book and status for a particular cell."""
        prog_struct = dict()
        prog_struct["title"] = title
        prog_struct["author"] = author
        prog_struct["image"]=  image
        prog_struct["status"] = status
        self.progress[cell] = prog_struct
        self.write_to_file()

    def set_cell_status(self, cell, status):
        if self.get_cell_status(cell):
            self.progress[cell]["status"] = status
        self.write_to_file()

    def is_win_row(self, rownum):
        """Returns True if all books in specified row are status FINISHED."""
        for colnum in range(0,5):
            cell = self.card.index_to_cell_code(colnum, rownum)
            status = self.get_cell_status(cell)
            if status != STATUS_FINISHED:
                return False
        return True

    def is_win_col(self, colnum):
        """Returns True if all books in specified column are status FINISHED."""
        for rownum in range(0,5):
            cell = self.card.index_to_cell_code(colnum, rownum)
            status = self.get_cell_status(cell)
            if status != STATUS_FINISHED:
                return False
        return True

    def is_win_diag(self, direction):
        """Returns True if all books in specified diagnoal are status FINISHED."""
        for colnum in range(0,5):
            if direction == DIRECTION_ASC:
                rownum = 5-colnum
            else:
                rownum = colnum
            cell = self.card.index_to_cell_code(colnum, rownum)
            status = self.get_cell_status(cell)
            if status != STATUS_FINISHED:
                return False
        return True

    def is_win_blackout(self):
        """Returns true if all cells are finished."""
        for colnum in range(0,5):
            for rownum in range(0,5):
                cell = self.card.index_to_cell_code(colnum, rownum)
                status = self.get_cell_status(cell)
                if status != STATUS_FINISHED:
                    return False
        return True

    def get_wins(self):
        """Checks current progress to see if any win conditions exist and returns a list."""
        wins = list()
        for colnum in range(0,5):
            if self.is_win_col(colnum):
                wins.append(f"Column {BINGO[colnum]}")
            if self.is_win_row(colnum):
                wins.append(f"Row {colnum+1}")
        if self.is_win_diag(DIRECTION_ASC):
            wins.append(f"Diagonal {DIRECTION_ASC}")
        if self.is_win_diag(DIRECTION_DESC):
            wins.append(f"Diagonal {DIRECTION_DESC}")
        if self.is_win_blackout():
            wins.append("Blackout!!!")

def authors_to_author(authors: List[str]) -> str:
    """Lists or abbreviates authors as a string."""
    if len(authors) == 0:
        return "no author"
    elif len(authors) == 1:
        return authors[0]
    elif len(authors) <= 3:
        return ", ".join(authors)
    else:
        return authors[0] + " et. al."

@streamlit.cache
def search_books_g(query_author, query_title):
    """Use the Google Books api to search for books, authors, and images by title and author prompt."""
    if query_title:
        title_query = urllib.parse.quote(str(query_title).encode('utf-8'))
    else:
        title_query = ""
    if query_author:
        author_query = urllib.parse.quote(b"inauthor:" + str(query_author).encode('utf-8'))
    else:
        author_query = ""
    query = title_query + "+" + author_query
    url = f"https://www.googleapis.com/books/v1/volumes?q={query}&key={API_KEY}"
    response = requests.get(url)
    print(response.status_code)
    print(response.text)
    responseJson = response.json()
    responseItems = responseJson["items"]
    responseItems = responseItems[0:min(10,len(responseItems))]
    result = list()
    for item in responseItems:
        vol = item["volumeInfo"]
        thisResult = dict()
        thisResult["title"] = vol["title"]
        if vol.get("subtitle",""):
            thisResult["title"] += ": " + vol["subtitle"]
        thisResult["author"] = authors_to_author(vol.get("authors",["no author"]))
        thisResult["image"] = vol.get("imageLinks", {}).get("thumbnail", BLANK_COVER)
        thisResult["url"] = vol.get('canonicalVolumeLink','')
        result.append(thisResult)
    return(result)

@streamlit.cache
def search_books_ol(query_author, query_title):
    """Use the OpenLibrary api to search for books, authors, and images by title and author prompt."""
    params = dict()
    if query_title:
        params["title"] = urllib.parse.quote(str(query_title).encode('utf-8'))
    if query_author:
        params["author"] = urllib.parse.quote(str(query_author).encode('utf-8'))
    url = f"https://openlibrary.org/search.json"
    response = requests.get(url, params=params)
    if response.status_code != 200:
        print(response.status_code)
        print(response.text)
    rjson = response.json()
    docs = rjson["docs"]
    docs = docs[0:min(10,len(docs))]
    result = list()
    for doc in docs:
        thisResult = dict()
        thisResult["title"] = doc["title"]
        thisResult["author"] = authors_to_author(doc.get("author_name", ["no author"]))
        imgNum = doc.get("cover_i","")
        thisResult["image"] = f"https://covers.openlibrary.org/b/id/{imgNum}-M.jpg"
        thisResult["url"] = "foo"
        result.append(thisResult)
    print(response.status_code)
    print(response.text)
    return(result)


