import click
from ..connection import conn
import os, sys
import re

def text_search():
    click.echo("Enter the table name and sys_id of a record to search")
    table_name = input(click.style("Table name >> ", fg="bright_white", bold=True)).strip()
    sys_id = input(click.style("sys_id >> ", fg="bright_white", bold=True)).strip()
    fragment = input(click.style("Search string >> ", fg="bright_white", bold=True)).strip()

    if table_name == "" or sys_id == "":
        click.secho("You must enter both a sys_id and table name to search", fg="red")
        sys.exit(os.EX_DATAERR)

    if len(sys_id) != 32:
        click.secho("Invalid sys_id", fg="red")
        sys.exit(os.EX_DATAERR)
    
    s, url = conn.setup_connection()
    resp = s.get(url + "/api/now/table/" + table_name, params={"sysparm_query": "sys_id=" + sys_id})

    body = resp.json()
    if resp.status_code != 200:
        try:
            err = body.get('error').get('message')
            click.secho("Search failed with status " + str(resp.status_code) + ' - ' + err, fg="red")
        except:
            click.secho("Search failed with status " + str(resp.status_code), fg="red")
        finally:
            sys.exit(os.EX_DATAERR)
    
    res = body.get('result')
    if len(res) == 0:
        click.secho("No results found.", fg="bright_white", bold=True)
        sys.exit(os.EX_DATAERR)

    obj = res[0] # at this point, we have a full record in the form of a dict
    found_results = False
    for prop in obj:
        search_results = search(fragment, obj[prop])
        if len(search_results) > 0:
            click.secho("\nIn column " + click.style(prop, fg="yellow") + ":")
            print_results(search_results)
            found_results = True
    if not found_results:
        click.secho("No results found", fg="yellow")

"""Takes a string value with multiple newlines and searches it against a fragment.
Returns a list of found results with the term
"""
def search(fragment, value):
    value = str(value)
    ret = []
    lines = value.split("\r\n")
    for inx, item in enumerate(lines):
        term = re.search(fragment, item)
        if term != None:
            #Search term found, line count, full line
            ret.append((term.group(), inx + 1, item))
    return ret

"""Color prints the list of search results for each field"""
def print_results(results):
    for item in results:
        line_num = str(item[1])
        line_found = color(str(item[2]).strip(), str(item[0]), "blue")
        
        click.secho(click.style("\tLine " + line_num + ": ", fg="bright_white", bold=True) + line_found)

"""Colors input word found in given line by CLI color"""
def color(line: str, word: str, color: str):
    color_text = click.style(word, fg=color, bold=True)
    return line.replace(word, color_text)