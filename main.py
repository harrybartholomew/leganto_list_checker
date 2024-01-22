import pandas
import requests

library_name = "Queens'" #ADD LIBRARY NAME
# READ CSVs
list_title = "POL4 Comparative Politics" #ADD A TITLE FOR THE READING LIST
leganto_list_data = pandas.read_csv("pol4.csv") #ADD LEGANTO LIST CSV FILE NAME BEFORE ".csv"
library_holdings_data = pandas.read_csv("library_holdings.csv", encoding="utf-8") #MAKE SURE "library_holdings.csv" IS CORRECT FILENAME


# FUNCTIONS
def get_json_from_openlibrary(query):
    response = requests.get(url=f"https://openlibrary.org/{query}.json")
    if response.status_code != 200:
        return False
    json_data = response.json()
    return json_data


def use_leganto_author(row):
    if isinstance(row['Item Author'], str):
        if len(row['Item Author']) > 0:
            return [f"({row['Item Author']})"]
        else:
            return ["[no author retrieved]"]
    else:
        return ["[no author retrieved]"]


def get_author_names(json_data, row):
    if json_data:
        author_names = []
        if "authors" in json_data.keys():
            for author in json_data['authors']:
                author_json = get_json_from_openlibrary(author['key'])
                if "name" in author_json.keys():
                    author_names.append(author_json["name"])
                elif "personal_name" in author_json.keys():
                    author_names.append(author_json["personal_name"])
                else:
                    author_names.append("[no author]")
            source = "openlibrary"
            return author_names, source
        else:
            source = "leganto"
            return use_leganto_author(row), source
    else:
        source = "leganto"
        return use_leganto_author(row), source


def format_author_string(info):
    author_list, source = info
    if source == "openlibrary":
        num_authors = len(author_list)
        formatted_authors = []
        for i, author in enumerate(author_list):
            name_parts = author.split()
            if len(name_parts) == 1:
                formatted_authors.append(name_parts[0])
            else:
                last_name = name_parts[-1]
                first_name = ' '.join(name_parts[:-1])
                formatted_authors.append(f"{last_name}, {first_name}")
        if num_authors > 3:
            formatted_authors = [formatted_authors[0], 'et al.']
        elif num_authors > 1:
            formatted_authors[-1] = 'and ' + formatted_authors[-1]
        if num_authors > 2:
            formatted_authors[-2] += ','
        return ', '.join(formatted_authors)
    if source == "leganto":
        return author_list[0]


def get_publisher(json_data):
    if "publishers" in json_data.keys():
        publisher = json_data["publishers"][0]
    else:
        publisher = "[no publisher]"
    return publisher


def remove_statement_of_responsibility(title_string):
    x = title_string.find("/")
    return title_string[:x].strip()


def remove_digits(string):
    digits = "0123456789.-"
    no_digits = ""
    for char in string:
        if char not in digits:
            no_digits += char
    return no_digits


def remove_punctuation(string):
    punctuation = '''!()-[]{};:'’‘"\;,<>./?@#$%^&*_~'''
    no_punc = ""
    for char in string:
        if char not in punctuation:
            no_punc += char
    return no_punc


def check_if_statement_of_res(title_string):
    if "/" in title_string:
        return True
    else:
        return False


def format_title(string):
    title_proper = remove_statement_of_responsibility(string)
    formatted_title_proper = remove_punctuation(title_proper).lower().strip()
    split_string = formatted_title_proper.split()
    new_string = " ".join(split_string)
    return new_string


def get_notes_and_tags_html(row):
    notes_and_tags_html = ""
    if isinstance(row['Item Public note'], str):
        notes_and_tags_html += f'"{row["Item Public note"]}"<br>'
    if isinstance(row['Item Tags'], str):
        notes_and_tags_html += "<span style='color: grey'><em>"
        split_tags = row['Item Tags'].split(", ")
        for tag in split_tags:
            tag.replace(" ", "_")
            notes_and_tags_html += f"#{tag} "
        notes_and_tags_html += "</em></span><br>"
    return notes_and_tags_html


# CREATE HTML
with open("results.html", "w", encoding="utf-8") as file:
    file.write(f'''
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>{list_title}</title>
</head>
<body>''')


# CREATE TABLE OF CONTENTS
html_contents = "<h3 id='top'>Contents:</h3><ul>"
sections = leganto_list_data['Section Name'].unique()
for i in range(len(sections)):
    html_contents += f"<li><a href='#{i + 1}'>{sections[i]}</a></li>"
html_contents += "</ul>"
with open("results.html", "a", encoding="utf-8") as file:
    file.write(f"<h1>{list_title}</h1>")
    file.write(html_contents)

counter = 1
sections = []
current_section = ""
for index, row in leganto_list_data.iterrows():
    print(f"Checking item {counter} of {len(leganto_list_data.index)}")
    counter += 1
    bib_data = {}
    if not isinstance(row['Item Title'], str):
        continue
    print(f"TITLE: {row['Item Title']}")
    # STRUCTURE INTO SECTIONS
    html_section = ""
    if row["Section Name"] != current_section:
        sections.append(row["Section Name"])
        current_section = row["Section Name"]
        html_section += f"<h2 style='display: inline-block' id='{len(sections)}'>{row['Section Name']}</h2> [<a href='#top'>back to top</a>]"
        if isinstance(row["Section Description"], str):
            html_section += f"<br>&nbsp;<strong><em>{row['Section Description']}</em></strong>"
    # STEP 1: CHECK IF THIS IS A BOOK
    if row["Item Type"] in ["Book", "Book Chapter", "Book Extract", "E-book"]:
        ol_book_data = get_json_from_openlibrary("isbn/" + str(row["Item ISBN"]))
        # STEP 2: DOES LIBRARY HAVE A HOLDINGS RECORD ATTACHED?
        if library_name in str(row["Item Availability"]):
            bib_data["match"] = "Library's holdings are attached."
            bib_data["colour"] = "MediumSeaGreen"
            bib_data['match_info'] = ""
        # STEP 3: DOES THE ISBN MATCH LIBRARY ISBNs?
        if "match" not in bib_data.keys():
            leganto_ISBN = row["Item ISBN"]
            library_ISBNs = []  # used in step 4
            for i, r in library_holdings_data.iterrows():
                if isinstance(r["ISBN"], str):
                    library_ISBNs += r["ISBN"].split("; ")
                    if leganto_ISBN in r["ISBN"].split("; "):
                        bib_data["match"] = "ISBN matches library's holdings."
                        bib_data["colour"] = "MediumSeaGreen"
                        bib_data['match_info'] = ""
                        break
        # STEP 4: DO ANY OF THE OTHER OPEN LIBRARY EDITIONS MATCH LIBRARY ISBNs?
        if "match" not in bib_data.keys():
            if ol_book_data is not False:
                if "works" in ol_book_data.keys():
                    work_ID = ol_book_data["works"][0]["key"]
                    ol_work_data = get_json_from_openlibrary(work_ID + "/editions")
                    if ol_work_data['size'] > 1:
                        for edition in ol_work_data["entries"]:
                            if "isbn_13" in edition.keys():
                                for edition_ISBN in edition['isbn_13']:
                                    if int(edition_ISBN) in library_ISBNs:
                                        bib_data["match"] = "work"
                                        bib_data["colour"] = "LightGreen"
                                        bib_data[
                                            'match_info'] = f"Library has {edition['publishers'][0]}, {edition['publish_date']} edition."
                                        break
        # STEP 5: ARE THERE ANY TEXT MATCHES FOR AUTHORS/TITLES AMONG LIBRARY HOLDINGS?
        if "match" not in bib_data.keys():
            matches = []
            leganto_title = format_title(row["Item Title"])
            for i, r in library_holdings_data.iterrows():
                library_title = format_title(r["Title"])
                if leganto_title in library_title:
                    matches.append({
                        "MMSID": r["MMS Id"],
                        "location": r["Location Name"],
                        "classmark": r["Permanent Call Number"],
                        "statement of res": r["245$c"],
                        "title": r["Title"],
                        "publisher": r["Publisher"],
                        "date": r["Publication Date"]
                    })
                    bib_data["match"] = "Matches for this title are found among library holdings:"
                    bib_data["colour"] = "Orange"
                    bib_data["notes and tags"] = get_notes_and_tags_html(row)
                    if len(matches) > 7:
                        bib_data["match"] = "This title matched with too many library titles to be accurate."
                        bib_data["colour"] = "Orange"
                        bib_data["match_info"] = ""
                        break
            if 0 < len(matches) < 8:
                bib_data["match_info"] = "<ul>"
                for match in matches:
                    bib_data["match_info"] += f'''
    <li><strong>{match['location']}: {match['classmark']}</strong> {match['title']} {match['statement of res']}<br>
    —{match["publisher"]}, {match['date']} [MMSID: {match['MMSID']}]</li>
    '''
                bib_data["match_info"] += "</ul>"
        # STEP 6: REMAINING ITEMS WITH NO MATCHES
        if "match" not in bib_data.keys():
            bib_data["match"] = "No match found."
            bib_data["colour"] = "OrangeRed"
            bib_data['match_info'] = f"[<a href='https://blackwells.co.uk/bookshop/product/{row['Item ISBN']}'>Heffers</a>]"
            bib_data["notes and tags"] = get_notes_and_tags_html(row)
        # BOOK HTML FORMATTING
        html_chapter_author = ""
        if isinstance(row["Item Chapter Author"], str):
            html_chapter_author = f"{row['Item Chapter Author'].replace('author', '')}, "
        html_chapter = ""
        if row["Item Type"] == "Book Chapter":
            html_chapter = f"'{row['Item Chapter Title']}' in:<br>"
        author_string = format_author_string(get_author_names(ol_book_data, row))
        if author_string is None:
            author_string = ""
        if len(author_string) > 0:
            html_author = f"{author_string},"
        else:
            html_author = author_string
        if check_if_statement_of_res(row['Item Title']):
            html_title = remove_statement_of_responsibility(row['Item Title'])
        else:
            html_title = row['Item Title']
        html_edition = ""
        if isinstance(row["Item Edition"], str):
            html_edition += f"—{row['Item Edition']}"
        html_pub = "—"
        if isinstance(row["Item Place of publication"], str):
            html_pub += f"{row['Item Place of publication']} : "
        if isinstance(row["Item Publisher"], str):
            html_pub += row["Item Publisher"]
        if html_pub[-1] not in ["]", ".", "-"]:
            html_pub += f", {row['Item Publication Date']}."
        if "notes and tags" not in bib_data.keys():
            bib_data["notes and tags"] = ""
        with open("results.html", "a", encoding="utf-8") as file:
            file.write(f'''
            {html_section}
        <p>{html_chapter_author}{html_chapter}
        <span style="color:{bib_data['colour']}"><strong>{html_author} <em>{html_title}</em></strong>
        <br>{html_edition}{html_pub}<br>
        </span>{bib_data["notes and tags"]}⮩{bib_data["match"]}<br>{bib_data["match_info"]}
        </p>
        ''')
    elif row['Item Type'] == "Article":
        with open("results.html", "a", encoding="utf-8") as file:
            file.write(f'''
            {html_section}
        <p><strong><span style="color:DimGrey">{row['Item Author']}, 
        "{row['Item Title']}", <em>{row['Item Journal Title']}</em>
         ({row['Item Publication Date']})</span></strong> 
        </p>
        ''')
    else:  # NON-BOOK/ARTICLE ITEMS
        with open("results.html", "a", encoding="utf-8") as file:
            file.write(f'''
            {html_section}
        <p><strong>{row['Item Type']}:</strong> <span style="color:DimGrey"><em>{row['Item Title']}</em></span>
        </p>
        ''')

with open("results.html", "a", encoding="utf-8") as file:
    file.write('''
</body>
</html>
''')