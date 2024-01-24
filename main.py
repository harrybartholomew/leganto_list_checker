import pandas
import html_writer as hw
import References as Ref

library_name = "Queens'" # ADD LIBRARY NAME
# READ CSVs
list_title = "POL4 Comparative Politics" # ADD A TITLE FOR THE READING LIST
leganto_list_data = pandas.read_csv("leganto_lists/pol4.csv") # ADD LEGANTO LIST CSV FILE NAME BEFORE ".csv"
library_holdings_data = pandas.read_csv("library_holdings.csv", encoding="utf-8") # MAKE SURE "library_holdings.csv" IS CORRECT FILENAME
library_isbns = []
for i, row in library_holdings_data.iterrows():
    if isinstance(row["ISBN"], str):
        library_isbns += row["ISBN"].split("; ")

# CREATE HTML
hw.create_new_html("results.html", list_title, dataframe=leganto_list_data)

counter = 1
sections = []
for index, row in leganto_list_data.iterrows():
    print(f"Checking item {counter} of {len(leganto_list_data.index)}")
    counter += 1
    #CREATE OBJECT
    if not isinstance(row['Item Title'], str):
        continue
    if row["Item Type"] in ["Book", "Book Chapter", "Book Extract", "E-book"]:
        reference = Ref.BookReference(index, row)
    elif row["Item Type"] == "Article":
        reference = Ref.ArticleReference(index, row)
    else:
        reference = Ref.Reference(index, row)
    print(f"TITLE: {reference.title}")
    # STRUCTURE INTO SECTIONS
    sections = reference.check_new_section(sections, reference.section)
    # CHECK FOR MATCHES
    if reference.type == "book":
        if not reference.check_attached_holdings(library_name):
            if not reference.check_isbn(library_isbns):
                if not reference.check_alternative_isbns(library_isbns):
                    reference.check_title_matches(library_holdings_data)

    # HTML FORMATTING
    with open("results.html", "a", encoding="utf-8") as file:
        file.write(reference.write_reference())

hw.write_footer("results.html")