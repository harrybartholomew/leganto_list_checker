import requests


def get_json_from_openlibrary(query):
    response = requests.get(url=f"https://openlibrary.org/{query}.json")
    if response.status_code != 200:
        return False
    else:
        return response.json()


def get_author_names(edition_json):
    if not edition_json:
        return False
    author_names = []
    if "authors" in edition_json.keys():
        for author in edition_json['authors']:
            author_json = get_json_from_openlibrary(author['key'])
            if "name" in author_json.keys():
                author_names.append(author_json["name"])
            elif "personal_name" in author_json.keys():
                author_names.append(author_json["personal_name"])
            else:
                author_names.append("[no author]")
            return author_names
        else:
            return False


def get_editor_names(edition_json):
    if not edition_json:
        return False
    editor_names = []
    if "contributions" in edition_json.keys():
        for contributor in edition_json['contributions']:
            if "(Editor)" in contributor.lower():
                editor_names.append(contributor.replace("(Editor)", ""))
        if len(editor_names) == 0:
            for contributor in edition_json['contributions']:
                editor_names.append(contributor)
        return editor_names
    else:
        return False


def get_alternative_editions(edition_json):
    alternative_editions = []
    if "works" in edition_json.keys():
        work_id = edition_json["works"][0]["key"]
        editions_json = get_json_from_openlibrary(work_id + "/editions")
        if editions_json['size'] > 1:
            for edition in editions_json["entries"]:
                if "isbn_13" in edition.keys():
                    for isbn in edition['isbn_13']:
                        alternative_editions.append({"isbn": isbn,
                                                     "publisher": edition['publishers'][0],
                                                     "year": edition['publish_date']})
    return alternative_editions


def format_author_list(author_list):
    formatted_authors = []

    def reverse_names(name):
        name_words = name.split()
        if len(name_words) == 1:
            return name_words
        else:
            last_name = name_words[-1]
            first_names = ' '.join(name_words[:-1])
            return f"{last_name}, {first_names}"

    for i, author in enumerate(author_list):
        if i == 0:
            formatted_authors.append(reverse_names(author))
        else:
            formatted_authors.append(author)

    author_string = formatted_authors[0]
    if len(formatted_authors) > 3:
        author_string += " et al."
    elif len(formatted_authors) == 3:
        author_string += f", {formatted_authors[1]} and + {formatted_authors[2]}"
    elif len(formatted_authors) == 2:
        author_string += f"and {formatted_authors[1]}"
    return author_string


def format_editor_list(editor_list):
    if len(editor_list) == 1:
        return f"{format_author_list(editor_list)} (ed.)"
    else:
        return f"{format_author_list(editor_list)} (eds.)"


def get_publisher(edition_json):
    if "publishers" in edition_json.keys():
        publisher = edition_json["publishers"][0]
    else:
        publisher = "[no publisher]"
    return publisher
