import getpass
import click
import sqlite3
import keyring
from pathlib import Path
import os

def startup_profile():
    import sys
    try:
        # parent.parent is only needed here since this file is in cmd_funcs
        wd = Path(__file__).parent.parent.resolve()
        conn = sqlite3.connect(os.path.join(wd, 'sparky.db'))
    except:
        try:
            wd = Path(__file__).parent.parent.resolve()
            os.system("sqlite3 " + os.path.join(wd, 'sparky.db'))
            conn = sqlite3.connect(os.path.join(wd, 'sparky.db'))
        except:
            click.secho("Failed to load sparky database.", fg="red")
            sys.exit(os.EX_DATAERR)
    try:
        cur = conn.cursor()
        cur.execute('''CREATE TABLE IF NOT EXISTS profile (
            profile_name text,
            url text,
            user text,
            selected int
        );''')
        conn.commit()
    except:
        click.secho("Error connecting to profile. Please check the sparky database or recreate if you are having issues.", fg="red")
        sys.exit(os.EX_DATAERR)
    finally:
        conn.close()

def new_profile():
    click.echo("\nEnter a profile name")
    pn = input(click.style(">> ", fg="bright_white", bold=True))
    click.echo("Enter a URL")
    url = input(click.style(">> ", fg="bright_white", bold=True))
    click.echo("Enter an admin user name")
    user = input(click.style(">> ", fg="bright_white", bold=True))
    click.echo("Enter the user's password")
    pw = getpass.getpass(prompt=click.style(">> ", fg="bright_white", bold=True), stream=None) 
    if pn == "" or url == "" or user == "" or pw == "":
        click.echo("Missing input - profile not created.")
        return
    try:
        wd = Path(__file__).parent.parent.resolve()
        conn = sqlite3.connect(os.path.join(wd, 'sparky.db'))
        cur = conn.cursor()
        cur.execute('''insert into profile values (?, ?, ?, ?)''', (pn, url, user, 0))
        conn.commit()
        if cur.lastrowid != 0:
            click.echo("Profile " + pn + " created.")
            keyring.set_password("sparky - " + str(cur.lastrowid) + " - " + pn, user, pw)
            
    except Exception as e:
        click.secho("Error creating profile " + pn + ": " + str(e), fg="red")
    finally:
        conn.close()

def list_profiles():
    try:
        click.echo()
        wd = Path(__file__).parent.parent.resolve()
        conn = sqlite3.connect(os.path.join(wd, 'sparky.db'))
        cur = conn.cursor()
        profs = cur.execute('''SELECT rowid, profile_name, user, selected, url FROM profile''').fetchall()
        if profs == []:
            click.echo("You have no profiles. Type 'sparky profile new' to create a new one.\n")
        else:
            click.secho("{:<15} {:<20} {:<30} {:<10} {:<30}".format('Row ID', 'Profile Name', 'User', 'Selected', 'URL'), fg="bright_white", bold=True)
        for i in profs:
            click.echo("{:<15} {:<20} {:<30} {:<10} {:<30}".format(i[0], i[1], i[2], '' if i[3] == 0 else 'True', i[4]))
    except Exception as e:
        click.secho("Error listing profiles: " + str(e), fg="red")
    finally:
        conn.close()
    return profs

def delete_profile():
    profiles = list_profiles()
    if len(profiles) > 0:
        click.echo("\nEnter the Row ID to delete")
        rowid = input(click.style(">> ", fg="bright_white", bold=True))
    else:
        return

    try:
        int(rowid) # throw ValueError if we didn't get an integer
    except ValueError:
        click.secho("Invalid input.", fg="red")
        return

    try:
        wd = Path(__file__).parent.parent.resolve()
        conn = sqlite3.connect(os.path.join(wd, 'sparky.db'))
        cur = conn.cursor()
        sel_resp = cur.execute("""SELECT profile_name, user FROM profile WHERE rowid = ?;""", (rowid,)).fetchone()
        if sel_resp != None:
            try:
                keyring.delete_password("sparky - " + rowid + " - " + sel_resp[0], sel_resp[1])
            except Exception as e:
                click.secho("Could not delete password in keychain: " + str(e), fg="red")
        del_resp = cur.execute("""DELETE FROM profile WHERE rowid = ?;""", (rowid,))
        conn.commit()
        if del_resp.rowcount == 0:
            click.echo("Could not find row " + str(rowid) + " to delete")
        else:
            click.echo("Profile deleted.")
    except Exception as e:
        click.secho("Error deleting profile with rowid " + rowid + ": " + str(e), fg="red")
    finally:
        conn.close()

def edit_profile():
    profiles = list_profiles()
    if len(profiles) > 0:
        click.echo("\nEnter the Row ID to edit")
        rowid = input(click.style(">> ", fg="bright_white", bold=True))
    else:
        return

    try:
        int(rowid) # throw ValueError if we didn't get an integer
    except ValueError:
        click.secho("Invalid input.", fg="red")
        return

    try:
        wd = Path(__file__).parent.parent.resolve()
        conn = sqlite3.connect(os.path.join(wd, 'sparky.db'))
        cur = conn.cursor()
        sel_resp = cur.execute("""SELECT profile_name, url, user, selected FROM profile WHERE rowid = ?;""", (rowid,)).fetchone()
        if sel_resp == None:
            click.secho("No profile found with Row ID " + rowid, fg="red")
            return
        
        profile_name = sel_resp[0]
        url = sel_resp[1]
        user = sel_resp[2]
        selected = sel_resp[3]
        try:
            pw = keyring.get_password("sparky - " + rowid + " - " + profile_name, user)
        except:
            pw = ""

        click.echo("Input new Profile Name (or press ENTER to skip)")
        edit_profile_name = input(click.style("(" + profile_name + ") >> ", fg="bright_white", bold=True)) or profile_name
        click.echo("Input new URL (or press ENTER to skip)")
        edit_url = input(click.style("(" + url + ") >> ", fg="bright_white", bold=True)) or url
        click.echo("Input new User (or press ENTER to skip)")
        edit_user = input(click.style("(" + user + ") >> ", fg="bright_white", bold=True)) or user
        click.echo("Input new Password (or press ENTER to skip)")
        edit_password = getpass.getpass(prompt=click.style(">> ", fg="bright_white", bold=True), stream=None) or pw

        try:
            keyring.delete_password("sparky - " + rowid + " - " + profile_name, user)
        except:
            pass
        
        try:
            keyring.set_password("sparky - " + rowid + " - " + edit_profile_name, edit_user, edit_password)
        except:
            pass
        cur.execute("""UPDATE profile SET profile_name = ?, url = ?, user = ?, selected = ? WHERE rowid = ?;""", (edit_profile_name, edit_url, edit_user, selected, rowid) )
        conn.commit()

    except Exception as e:
        click.secho("Error editing profile with rowid " + rowid + ": " + str(e), fg="red")
    finally:
        conn.close()

def select_profile():
    profiles = list_profiles()
    if len(profiles) > 0:
        click.echo("\nEnter the Row ID to select")
        rowid = input(click.style(">> ", fg="bright_white", bold=True))
    else:
        return

    try:
        int(rowid) # throw ValueError if we didn't get an integer
    except ValueError:
        click.secho("Invalid input.", fg="red")
        return

    try:
        wd = Path(__file__).parent.parent.resolve()
        conn = sqlite3.connect(os.path.join(wd, 'sparky.db'))
        cur = conn.cursor()
        sel_resp = cur.execute("""UPDATE profile SET selected = 1 WHERE rowid = ?;""", (rowid,))
        if sel_resp.rowcount == 0:
            click.echo("Could not find row " + str(rowid) + " to select")
        else:
            cur.execute("""UPDATE profile SET selected = 0 WHERE rowid != ?;""", (rowid,))
            conn.commit()
            click.echo("Profile selected.")
    except Exception as e:
        click.secho("Error selecting profile with rowid " + str(rowid) + ": " + str(e), fg="red")
    finally:
        conn.close()