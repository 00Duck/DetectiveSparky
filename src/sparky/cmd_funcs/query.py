import json
from typing import List, Tuple
import keyring
import sqlite3
import click
from pathlib import Path
import os, sys
import requests
from urllib.parse import quote

def setup_connection() -> Tuple[requests.Session, str]:
    """Constructs the session using our profile and performs checks to ensure querying will go smoothly."""
    try:
        wd = Path(__file__).parent.parent.resolve()
        conn = sqlite3.connect(os.path.join(wd, 'sparky.db'))
        cur = conn.cursor()
        # Make sure we have a profile
        sel_resp = cur.execute("""SELECT rowid, profile_name, user, url FROM profile WHERE selected = 1;""").fetchone()
        if sel_resp == None:
            click.secho("No profile currently selected. Please use 'sparky profile select' to select a profile before querying.", fg="red")
            sys.exit(os.EX_DATAERR)
    except Exception as e:
        click.secho("Error selecting profile during connection setup. Aborting with error: " + str(e), fg="red")
        sys.exit(os.EX_DATAERR)
    finally:
        conn.close()
    # Make sure we can get the password
    pw = keyring.get_password("sparky - " + str(sel_resp[0]) + " - " + sel_resp[1], sel_resp[2])
    if pw == None:
        click.secho("Could not find a password for the selected profile. Please try removing and adding the selected profile again.", fg="red")
        sys.exit(os.EX_DATAERR)
    
    # clean up URL
    url = str(sel_resp[3]).strip().replace("http://", "https://")
    if url.find("https://") == -1:
        url = "https://" + url
    if not url.endswith("service-now.com"):
        url += ".service-now.com"

    click.echo("Profile " + click.style(sel_resp[1], fg="green") + " is selected. (" + url + ")")
    
    # Do pre-flight check for access to instance and ability to query admin tables
    s = requests.Session()
    s.auth = (str(sel_resp[2]), pw)
    resp = s.get(url + '/api/now/table/sys_dictionary', params = {'sysparm_fields': 'sys_id', 'sysparm_limit': '1'}, headers={'Content-Type': 'application/json'})
    if resp.status_code == 401:
        click.secho("User credentials for the selected profile failed to authentcate.", fg="red")
        sys.exit(os.EX_DATAERR)
    elif resp.status_code == 403:
        click.secho("The profile selected is not authorized to query admin tables. Please ensure your ServiceNow user has admin access.", fg="red")
        sys.exit(os.EX_DATAERR)
    elif resp.status_code >= 200 and resp.status_code <= 299:
        return s, url
    else:
        click.secho("Abnormal status code for instance (" + str(resp.status_code) + "), aborting.", fg="red")
        sys.exit(os.EX_DATAERR)

def get_full_query_list(s: requests.Session, url: str, query_type: str) -> List[Tuple[str, str]]:
    """Queries for the entire list of tables with the corresponding """
    sd_query = "internal_type=script_plain^ORinternal_type=script_server^ORinternal_type=script^active=true"
    if query_type == "xml":
        sd_query = "internal_type=xml^active=true"
    elif query_type == "html":
        sd_query = "internal_type=html^ORinternal_type=html_script^ORinternal_type=html_template^active=true"

    # on sys_dictionary, name is the table name and element is the field name
    resp = s.get(url + "/api/now/table/sys_dictionary", params={"sysparm_fields": "name,element", "sysparm_query": sd_query})
    if resp.status_code != 200:
        click.secho("Received status code " + str(resp.status_code) + " while retrieving list of " + query_type + " tables to query. Aborting.", fg="red")
        sys.exit(os.EX_DATAERR)
    resp_json = resp.json()
    ret = []
    if resp_json['result'] != None:
        for i in resp_json['result']:
            ret.append((i['name'], i['element']))
    return ret

def get_list_from_file(filename: str) -> List[Tuple[str, str]]:
    ret = []
    try:
        with open(filename, 'r') as file:
            for line in file.readlines():
                line_arr = line.split(',')
                if len(line_arr) != 2:
                    click.secho("File " + filename + " is not formatted correctly. Aborting query.", fg="red")
                    sys.exit(os.EX_DATAERR)
                table = str(line_arr[0]).strip()
                field = str(line_arr[1]).strip()
                if table == "" or field == "":
                    click.secho("File " + filename + " is not formatted correctly. Aborting query.", fg="red")
                    sys.exit(os.EX_DATAERR)
                ret.append( (str(line_arr[0]), str(line_arr[1])) )
    except Exception as e:
        click.secho("Could not open " + filename + ": " + str(e), fg="red")
        sys.exit(os.EX_DATAERR)
    return ret

def generic_lookup(s: requests.Session, url: str, query_list: List[Tuple[str, str]], query_string: str):
    click.echo("[ Found " + click.style(str(len(query_list)), fg="blue") + " entries to scan ]")
    click.echo(click.style("{:<35} {:<25} {:<25} {:<50}".format('Sys ID', 'Table', 'Field', 'Name'), fg="bright_white", bold=True) )
    for item in query_list:
        table = str(item[0]).strip()
        field = str(item[1]).strip()
        resp = s.get(url + "/api/now/table/" + table, params={"sysparm_fields":"sys_id,name,u_name,sys_name", "sysparm_query": field + "LIKE" + quote(query_string)})
        if resp.status_code == 401 or resp.status_code == 500 or resp.status_code == 429:
            click.secho("Received status code " + str(resp.status_code) + " while retrieving data for table: " + table + ", field: " + field + ". Aborting.", fg="red")
            sys.exit(os.EX_DATAERR)
        elif resp.status_code == 403: # sometimes we don't have access to query a table. Let's just skip these.
            continue
        try:
            resp_json = resp.json()
            if resp_json.get('result') != None:
                for i in resp_json['result']:
                    click.echo("{:<35} {:<25} {:<25} {:<50}".format(i.get('sys_id'), table, field, str(i.get('name') or i.get('sys_name') or i.get('u_name')).strip() ))
            elif resp.json.get('error') != None:
                click.secho("Error while querying: " + str(resp_json['error']), fg="yellow")
        except: # This could hit if the user fat-fingered a custom query list.
            if resp_json.get('error') != None:
                click.secho("Error while querying: " + str(resp_json['error']), fg="yellow")
    click.secho("Finished.", fg="bright_white", bold=True)

def run_query(query_type: str, filename: str):
    click.echo("Input query string for lookup")
    query_string = input(click.style(">> ", fg="bright_white", bold=True))
    s, url = setup_connection()
    if filename == None:
        query_list = get_full_query_list(s, url, query_type)
    else:
        query_list = get_list_from_file(filename)
    generic_lookup(s, url, query_list, query_string)

def wf_script_lookup(s: requests.Session, url: str, query_list: List[Tuple[str, str, str]], query_string: str):
    click.echo("[ Found " + click.style(str(len(query_list)), fg="blue") + " entries to scan ]")
    click.echo(click.style("{:<35} {:<35} {:<35} {:<50}".format('WF Activity Sys ID', 'WF Version Sys ID', 'Sys Variable Value Sys ID', 'WF Activity Name'), fg="bright_white", bold=True) )
    for item in query_list:
        wf_act_sys_id = str(item[0]).strip()
        wf_activity_name = str(item[1]).strip()
        wf_version_sys_id = str(item[2]).strip()
        query = "document=wf_activity^document_key={}^variable.internal_type=script^ORvariable.internal_type=script_plain^valueLIKE{}".format(
            wf_act_sys_id,
            query_string.strip()
        )
        resp = s.get(url + "/api/now/table/sys_variable_value", params={"sysparm_fields":"sys_id", "sysparm_query": query})
        if resp.status_code == 401 or resp.status_code == 500 or resp.status_code == 429:
            click.secho("Received status code " + str(resp.status_code) + " while retrieving data for wf_activity: " + wf_act_sys_id + ", name: " + wf_activity_name + ". Aborting.", fg="red")
            sys.exit(os.EX_DATAERR)
        elif resp.status_code == 403: # This should never happen...
            click.secho("403 while querying sys_variable_value", fg="yellow")
            continue
        try:
            resp_json = resp.json()
            if resp_json.get('result') != None:
                for i in resp_json['result']:
                    click.echo("{:<35} {:<35} {:<35} {:<50}".format( wf_act_sys_id, wf_version_sys_id, i.get('sys_id'), wf_activity_name ))
            elif resp.json.get('error') != None:
                click.secho("Error while querying: " + str(resp_json['error']), fg="yellow")
        except: # This should also never happen, but just in case!
            if resp_json.get('error') != None:
                click.secho("Error while querying: " + str(resp_json['error']), fg="yellow")
    click.secho("Finished.", fg="bright_white", bold=True)

def wf_activity_lookup(s: requests.Session, url: str, wf_name: str) -> List[Tuple[str, str, str]]:
    """Grabs a list of all published wf_activity records that match the given workflow. This will build our initial list of activities to
    query against, to be limited again by sys_variable_value's that reference a script variable."""
    query = "workflow_version.published=true^workflow_version.name=" + wf_name

    resp = s.get(url + "/api/now/table/wf_activity", params={"sysparm_fields": "sys_id,name,workflow_version", "sysparm_query": query})
    if resp.status_code != 200:
        click.secho("Received status code " + str(resp.status_code) + " while retrieving list of wf_activity records to query. Aborting.", fg="red")
        sys.exit(os.EX_DATAERR)
    resp_json = resp.json()
    ret = []
    if resp_json.get('result') != None:
        for i in resp_json['result']:
            ret.append( (i.get('sys_id'), i.get('name'), i.get('workflow_version').get('value')) )
    elif resp.json.get('error') != None:
            click.secho("Error while querying: " + str(resp_json['error']), fg="yellow")
    return ret

def query_workflow():
    click.echo("Enter name of workflow to search")
    wf_name = input(click.style(">> ", fg="bright_white", bold=True)).strip()
    click.echo("Enter script fragment to search")
    query_string = input(click.style(">> ", fg="bright_white", bold=True)).strip()
    s, url = setup_connection()
    query_list = wf_activity_lookup(s, url, wf_name)
    wf_script_lookup(s, url, query_list, query_string)
