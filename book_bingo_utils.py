"""Model classes for book bingo."""

import json
from hashlib import blake2b
from typing import Any, Dict, Tuple, List

CARD_DIR = "cards/"
INDEX_FILE = f"{CARD_DIR}index.json"
BINGO = "BINGO"

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
