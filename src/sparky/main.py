import click

CONTEXT_SETTINGS = dict(help_option_names=["-h", "--help"])

@click.group(
    help="A tool to help find code in any ServiceNow instance.",
    context_settings=CONTEXT_SETTINGS,
)
def cli() -> None:
    from .cmd_funcs.profile import startup_profile
    startup_profile()

@cli.command("version", help="Shows the current version.")
def version_cmd() -> None:
    click.echo("{} {}\n\n{}".format(
        click.style("DetectiveSparky", fg="green"),
        click.style("v1.0.0", fg="bright_white", bold=True),
        click.style("Written by Blake Duckworth", fg="blue", dim=True)
        )
    )

### PROFILE COMMANDS

@click.group("profile", help="Contains commands for managing SNow profiles. Use the command 'sparky profile --help' for additional options.")
def profile_cmd() -> None:
    pass

@profile_cmd.command("new", help="Adds a new profile to your list of available selections. When adding a profile, please make sure that the associated account contains credentials with admin access so that script/html/xml fields can be searched against.")
def profile_add():
    from .cmd_funcs.profile import new_profile
    new_profile();

@profile_cmd.command("list", help="Displays a list of existing profiles that have been added to sparky.")
def profile_list():
    from .cmd_funcs.profile import list_profiles
    list_profiles()

@profile_cmd.command("delete", help="Removes an existing profile.")
def profile_del():
    from .cmd_funcs.profile import delete_profile
    delete_profile()

@profile_cmd.command("select", help="Selects the primary profile to be used for all future queries.")
def profile_select():
    from .cmd_funcs.profile import select_profile
    select_profile()

@profile_cmd.command("edit", help="Edits an existing profile.")
def profile_edit():
    from .cmd_funcs.profile import edit_profile
    edit_profile()

### QUERY COMMANDS

@cli.group("query", help="All commands for querying using the selected profile. Use the command 'sparky query -h' for additional options. Please note that these commands will not work if you have not both created and selected a profile.")
def query_cmd() -> None:
    pass

@query_cmd.command("script", help="Queries against script fields using the selected profile.")
@click.option(
    "--filename",
    "-f",
    help=(
        "Instead of performing the default search against all script records, specify a file by path "
        "that lists the tables and corresponding field names to perform the query against."
        "\n\nExample file format: sys_script_include,script"
    ),
    type=str,
    default=None,
    required=False,
)
def query_script(filename: str):
    from .cmd_funcs.query import run_query
    run_query("script", filename)

@query_cmd.command("html", help="Queries against HTML fields using the selected profile.")
@click.option(
    "-f",
    "--filename",
    help=(
        "Instead of performing the default search against all HTML records, specify a file by path "
        "that lists the tables and corresponding field names to perform the query against."
        "\n\nExample file format: sp_widget,template"
    ),
    type=str,
    default=None,
    required=False,
)
def query_html(filename: str):
    from .cmd_funcs.query import run_query
    run_query("html", filename)

@query_cmd.command("xml", help="Queries against XML fields using the selected profile.")
@click.option(
    "-f",
    "--filename",
    help=(
        "Instead of performing the default search against all XML records, specify a file by path "
        "that lists the tables and corresponding field names to perform the query against."
        "\n\nExample file format: sys_ui_page,html"
    ),
    type=str,
    default=None,
    required=False,
)
def query_xml(filename: str):
    from .cmd_funcs.query import run_query
    run_query("xml", filename)
    
@query_cmd.command("workflow", help="Performs queries against scripts in workflows.")
def query_wf():
    from .cmd_funcs.query import query_workflow
    query_workflow()

cli.add_command(version_cmd)
cli.add_command(profile_cmd)
cli.add_command(query_cmd)
