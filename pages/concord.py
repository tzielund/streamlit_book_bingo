import streamlit
import csv
import json
import pandas

from book_bingo_utils import search_books_ol, search_books_g

streamlit.header("Goodread export matcher")

with open ("goodreads_library_export.csv") as IN:
    df = pandas.read_csv(IN)
    # df

select_options = list()
for rownum, row in df.iterrows():
    title = row[1]
    author = row[2]
    select_options.append(f'{title} by {author}')
r = streamlit.sidebar.radio("Pick one", options=range(0,len(select_options)),
                            format_func=lambda x:select_options[x])

regular_old_dict = dict()
for columnName in df.columns:
    column = df[columnName]
    rowColVal = column[r]
    # label,value = streamlit.columns(2)
    # label.write(columnName)
    # value.write(rowColVal)
    regular_old_dict[columnName] = rowColVal

search_type = streamlit.selectbox("Choose search service",["OpenLibrary","Google"])

title = regular_old_dict["Title"]
author = regular_old_dict["Author"]

streamlit.write(f"Searching for {title} by {author}")
if search_type=="OpenLibrary":
    items = search_books_ol(author, title)
else:
    items = search_books_g(author, title)
if len(items) == 0:
    streamlit.write("No volumes found")
else:
    useItButtons = dict()
    useItData = dict()
    itemnum = 0
    for item in items:
        img,md = streamlit.columns([1,5])
        img.image(item["image"])
        md.markdown(f"[{item['title']}]({item['url']})")
        md.text(item['author'])
        useItButtons[itemnum] = md.button("Use this one", key=f"useItButton{itemnum}")
        useItData[itemnum] = item
        itemnum += 1

streamlit.header("Modified search")
typedTitle = streamlit.text_input("title", value=title)
typedAuthor = streamlit.text_input("author", value=author)
if search_type=="OpenLibrary":
    items2 = search_books_ol(author, title)
else:
    items2 = search_books_g(author, title)
# items2
if len(items2) == 0:
    streamlit.write("No volumes found")
else:
    useItButtons = dict()
    useItData = dict()
    itemnum = 0
    for item in items2:
        img,md = streamlit.columns([1,5])
        img.image(item["image"])
        md.markdown(f"[{item['title']}]({item['url']})")
        md.text(item['author'])
        useItButtons[itemnum] = md.button("Use this one", key=f"useItButton{itemnum}")
        useItData[itemnum] = item
        itemnum += 1

