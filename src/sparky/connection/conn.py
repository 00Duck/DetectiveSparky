import keyring
import sqlite3
import click
from pathlib import Path
from typing import Tuple
import requests
import os, sys

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
            sys.exit()
    except Exception as e:
        click.secho("Error selecting profile during connection setup. Aborting with error: " + str(e), fg="red")
        sys.exit()
    finally:
        conn.close()
    # Make sure we can get the password
    pw = keyring.get_password("sparky - " + str(sel_resp[0]) + " - " + sel_resp[1], sel_resp[2])
    if pw == None:
        click.secho("Could not find a password for the selected profile. Please try removing and adding the selected profile again.", fg="red")
        sys.exit()
    
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
        sys.exit()
    elif resp.status_code == 403:
        click.secho("The profile selected is not authorized to query admin tables. Please ensure your ServiceNow user has admin access.", fg="red")
        sys.exit()
    elif resp.status_code >= 200 and resp.status_code <= 299:
        return s, url
    else:
        click.secho("Abnormal status code for instance (" + str(resp.status_code) + "), aborting.", fg="red")
        sys.exit()


if __name__ == '__main__':
    url = str('https://brinkscustomerdev.service-now.com/').strip().replace("http://", "https://")
    if url.find("https://") == -1:
        url = "https://" + url
    # Remove trailing slashes before appending the rest of the URL (common if copied from a browser)
    if url[-1] == '/':
        url = url[:-1]
    if not url.endswith("service-now.com"):
        url += ".service-now.com"
 

    print(url)