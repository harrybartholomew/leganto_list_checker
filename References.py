import api_user as au


def remove_statement_of_responsibility(title_string):
    x = title_string.find("/")
    return title_string[:x].strip()


def normalise_title(title):
    def remove_punctuation(string):
        punctuation = '''!()-[]{};:'’‘"\;,<>./?@#$%^&*_~'''
        no_punc = ""
        for char in string:
            if char not in punctuation:
                no_punc += char
        return no_punc

    x = title.find("/")
    title[:x].strip()
    normalised_title = remove_punctuation(title).lower().strip()
    split_string = normalised_title.split()
    normalised_title = " ".join(split_string)
    return normalised_title


class Reference:
    def __init__(self, dataframe_index, dataframe_row):
        self.index = dataframe_index
        self.data = dataframe_row
        self.section = self.data["Section Name"]
        self.type = self.data['Item Type']
        self.title = self.data['Item Title']
        self.font_colour = "DimGrey"
        self.section_html = ""

    def get_author(self):
        author = self.data['Item Author'].replace("author.", "")

        def remove_digits(string):
            digits = "0123456789-"
            no_digits = ""
            for char in string:
                if char not in digits:
                    no_digits += char
            return no_digits

        if isinstance(author, str) and len(author) > 0:
            return f"({remove_digits(author)})"
        else:
            return "[no author retrieved]"

    def write_new_section(self, updated_sections):
        section_html = f'''
            <h2 style='display: inline-block' id='{len(updated_sections)}'>{self.section}</h2> 
            [<a href='#top'>back to top</a>]
            '''
        if isinstance(self.data["Section Description"], str):
            section_html += f"<br>&nbsp;<strong><em>{self.data['Section Description']}</em></strong>"
        self.section_html = section_html
        return updated_sections

    def check_new_section(self, previous_sections, current_section):
        if self.section != current_section:
            previous_sections.append(self.data["Section Name"])
            self.write_new_section(previous_sections)
        else:
            return previous_sections

    def write_reference(self):
        return f'''{self.section_html}
        <p><strong>{self.type}:</strong> <span style="color:{self.font_colour}"><em>{self.title}</em></span></p>
        '''

    def check_attached_holdings(self):
        return True


class BookReference(Reference):
    def __init__(self, dataframe_index, dataframe_row):
        Reference.__init__(self, dataframe_index, dataframe_row)
        self.author_statement = ""
        self.type = "book"
        self.library_matches = ""
        self.alternative_editions = None
        self.isbn = None
        self.open_library_json = au.get_json_from_openlibrary("isbn/" + str(self.data["Item ISBN"]))
        self.edition_html = ""
        if isinstance(self.data["Item Edition"], str):
            self.edition_html += f"—{self.data['Item Edition']}"
        self.match_status = "No match found."
        self.font_colour = "OrangeRed"

    def check_attached_holdings(self, library_name):
        if library_name in str(self.data["Item Availability"]):
            self.match_status = "Library's holdings are attached."
            self.font_colour = "MediumSeaGreen"
            return True
        else:
            return False

    def check_isbn(self, library_isbns):
        self.isbn = self.data["Item ISBN"]
        if self.isbn in library_isbns:
            self.match_status = "ISBN matches library's holdings."
            self.font_colour = "MediumSeaGreen"
            return True
        else:
            return False

    def check_alternative_isbns(self, library_isbns):
        self.alternative_editions = au.get_alternative_editions(self.data)
        for edition in self.alternative_editions:
            if edition["isbn"] in library_isbns:
                self.match_status = f"Library has {edition['publisher']}, {edition['year']} edition."
                self.font_colour = "LightGreen"
                return True
        return False

    def check_title_matches(self, library_data):
        self.library_matches = []
        normalised_reference_title = normalise_title(self.title)
        for i, library_holding in library_data.iterrows():
            normalised_library_title = normalise_title(library_holding["Title"])
            if normalised_reference_title in normalised_library_title:
                self.library_matches.append({
                    "MMSID": library_holding["MMS Id"],
                    "location": library_holding["Location Name"],
                    "classmark": library_holding["Permanent Call Number"],
                    "statement of res": library_holding["245$c"],
                    "title": library_holding["Title"],
                    "publisher": library_holding["Publisher"],
                    "date": library_holding["Publication Date"]
                })
                if len(self.library_matches) > 7:
                    self.match_status = "This title matched with too many library titles to be accurate."
                    self.font_colour = "Orange"
                    self.library_matches = []
                    return True
        if 0 < len(self.library_matches) < 8:
            self.match_status = "Matches for this title are found among library holdings:"
            self.font_colour = "Orange"
            return True
        else:
            return False

    def write_chapter_details(self):
        chapter_html = ""
        if self.data["Item Type"] == "Book Chapter":
            chapter_html += f'''
                            {self.data['Item Chapter Author'].replace(' author', '')}, 
                            {self.data['Item Chapter Title']}' in:<br>
                            '''
        return chapter_html

    def write_author_statement(self):
        author_names = au.get_author_names(self.open_library_json)
        if author_names:
            author_statement = au.format_author_list(author_names)
        else:
            editor_names = au.get_editor_names(self.open_library_json)
            if editor_names:
                author_statement = au.format_editor_list(editor_names)
            else:
                author_statement = self.get_author()
        return author_statement

    def write_pub_statement(self):
        pub_html = "—"
        if isinstance(self.data["Item Place of publication"], str):
            pub_html += f"{self.data['Item Place of publication']} : "
        if isinstance(self.data["Item Publisher"], str):
            pub_html += self.data["Item Publisher"]
        if pub_html[-1] not in ["]", ".", "-"]:
            pub_html += f", {self.data['Item Publication Date']}."
        return pub_html

    def write_notes(self):
        notes_html = ""
        if isinstance(self.data['Item Public note'], str):
            notes_html += f'"{self.data["Item Public note"]}"<br>'
        return notes_html

    def write_tags(self):
        tags_html = ""
        if isinstance(self.data['Item Tags'], str):
            tags_html += "<span style='color: grey'><em>"
            split_tags = self.data['Item Tags'].split(", ")
            for tag in split_tags:
                tag.replace(" ", "_")
                tags_html += f"#{tag} "
            tags_html += "</em></span><br>"
        return tags_html

    def write_title_matches(self):
        title_match_html = ""
        for match in self.library_matches:
            title_match_html += f'''
                <li><strong>{match['location']}: {match['classmark']}</strong> {match['title']} {match[
                'statement of res']}<br>
                —{match["publisher"]}, {match['date']} [MMSID: {match['MMSID']}]</li>
                '''
        return title_match_html

    def write_reference(self):
        return f'''{self.section_html}
                <p>{self.write_chapter_details()}<span style="color:{self.font_colour}">
                <strong>{self.write_author_statement()}, <em>{remove_statement_of_responsibility(self.title)}</em></strong>
                <br>{self.edition_html}{self.write_pub_statement()}<br>
                </span>{self.write_notes()}{self.write_tags()}⮩{self.match_status}<br>{self.write_title_matches()}
                </p>
                '''


class ArticleReference(Reference):
    def __init__(self, dataframe_index, dataframe_row):
        Reference.__init__(self, dataframe_index, dataframe_row)
        self.author = self.get_author(self)
        self.journal_title = self.data['Item Journal Title']
        self.publication_date = self.data['Item Publication Date']

    def write_reference(self):
        return f'''{self.section_html}
                <p><strong><span style="{self.font_colour}">{self.author}, 
                "{self.title}", <em>{self.journal_title}</em>
                 ({self.publication_date})</span></strong> 
                </p>
                '''
