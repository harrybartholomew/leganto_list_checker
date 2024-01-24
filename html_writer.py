def create_new_html(file_name, list_title, dataframe):
    with open(file_name, "w", encoding="utf-8") as file:
        file.write(f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
      <meta charset="UTF-8">
      <title>{list_title}</title>
    </head>
    <body><h1>{list_title}</h1>{write_contents(dataframe)}''')


def write_contents(dataframe):
    html = "<h3 id='top'>Contents:</h3><ul>"
    sections = dataframe['Section Name'].unique()
    for i in range(len(sections)):
        html += f"<li><a href='#{i + 1}'>{sections[i]}</a></li>"
    html += "</ul>"
    return html


def write_footer(file_name):
    with open(file_name, "a", encoding="utf-8") as file:
        file.write('''
    </body>
    </html>
    ''')
