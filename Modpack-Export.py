launch_message = """
▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄▄
█                           █
█  HaXr's Modpack CLI Tool  █
█                           █
▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀▀"""

import os, sys
import os.path
import json
import subprocess
from shutil import rmtree, make_archive, move, copytree
from pathlib import Path

import toml  # pip install toml
import yaml # pip install PyYAML
from ruamel.yaml import YAML
from mdutils.mdutils import MdUtils
from mdutils import Html
import re
import requests

# GitHub Download
from GitHubDownloader import AsyncGitHubDownloader
import asyncio

############################################################
# Variables

user_path = os.path.expanduser("~")

# Get path of project dynamically.
script_path = __file__
git_path = str(os.path.dirname(os.path.dirname(script_path))).replace("/","\\") # .replace("/","\\") is to ensure that the path will be in the Windows format.

packwiz_path = git_path + "\\Packwiz\\"
serverpack_path = git_path + "\\Server Pack\\"
packwiz_exe_path = os.path.expanduser("~") + "\\go\\bin\\packwiz.exe"
packwiz_manifest = "pack.toml"
bcc_client_config_path = packwiz_path + "config\\bcc.json"
bcc_server_config_path = serverpack_path + "config\\bcc.json"
export_path = git_path + "\\Export\\"
tempfolder_path = export_path + "temp\\"
temp_mods_path = tempfolder_path + "mods\\"
settings_path = git_path + "\\settings.yml"
packwiz_mods_path = packwiz_path + "mods\\"
prev_release = git_path + "\\Modpack-CLI-Tool\\prev_release"


############################################################
# Functions

def determine_server_export():
    """This method determines whether whether the server pack should be exported or not and returns a boolean."""
    export_server_val = settings_yml['export_server']
    if export_server_val:
        if input("Want to export server pack? [N]: ") in ("y", "Y", "yes", "Yes"):
            return True
        else:
            return False
    else:
        return False

def markdown_list_maker(lines):
    """This method takes a yml object of strings, formats them and returns the result."""
    processed_lines = []
    for line in lines:
        processed_lines.append("- " + line)
    return """{}""".format("\n".join(processed_lines[0:]))

def remove_bracketed_text(input_str):
    """This method takes an input string and removes any text surrounded by parentheses (), square brackets [], and curly braces {}."""
    # Define a pattern to match text within parentheses (), square brackets [], and curly braces {}
    pattern = r'\(.*?\)|\[.*?\]|\{.*?\}'
    
    # Use re.sub() to replace the matched text with an empty string
    result = re.sub(pattern, '', input_str)
    
    # Return the cleaned string
    return result.strip()

def parse_active_projects(input_path, parse_object):
    """This method takes a path as input and parses the pw.toml files inside, returning the names of activate projects in a list."""
    active_project = []
    for mod_toml in os.listdir(input_path):
        mod_toml_path = input_path + mod_toml
        try:
            if os.path.isfile(mod_toml_path): # Checks if mod_toml_path is a file.
                with open(mod_toml_path, "r", encoding="utf8") as f:
                    mod_toml = toml.load(f)
                    side = str(mod_toml['side'])
                    if side in ("both", "client", "server"):
                        mod_name = remove_bracketed_text(mod_toml[parse_object])
                        
                        if side == "both":
                            active_project.append(mod_name)
                        else:
                            active_project.append(f"{mod_name} [{side.capitalize()}]")
        except Exception as ex:
            print(ex, mod_toml)
    return active_project

#print(markdown_list_maker(parse_active_projects(packwiz_mods_path, "name")))
# print(markdown_list_maker(parse_active_projects(packwiz_mods_path, "filename")))

def get_latest_release_version(owner, repo):
    """
    Retrieve the latest release version from a GitHub repository.

    Parameters:
    - owner (str): The owner of the GitHub repository (e.g., 'torvalds' for https://github.com/torvalds/linux).
    - repo (str): The name of the GitHub repository (e.g., 'linux' for https://github.com/torvalds/linux).

    Returns:
    - str: The tag name of the latest release version, or a message if no release found.
    """
    url = f"https://api.github.com/repos/{owner}/{repo}/releases/latest"
    headers = {"Accept": "application/vnd.github.v3+json"}

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raise an error for bad status codes

        data = response.json()

        # Return the tag name of the latest release
        return data.get("tag_name", "No releases found.")
    
    except requests.exceptions.HTTPError as http_err:
        return f"HTTP error occurred: {http_err}"
    except Exception as err:
        return f"Error occurred: {err}"



def compare_toml_files(dir1, dir2):
    # Initialize dictionaries to store TOML data
    toml_data_1 = {}
    toml_data_2 = {}
    
    # Load TOML files from the first directory
    for filename in os.listdir(dir1):
        if filename.endswith('.toml'):
            filepath = os.path.join(dir1, filename)
            toml_data_1[filename] = toml.load(filepath)

    # Load TOML files from the second directory
    for filename in os.listdir(dir2):
        if filename.endswith('.toml'):
            filepath = os.path.join(dir2, filename)
            toml_data_2[filename] = toml.load(filepath)

    # Prepare to store results
    results = {
        'added': [],
        'removed': [],
        'modified': []
    }

    # Check for added and modified files
    for filename, data in toml_data_2.items():
        if filename not in toml_data_1:
            results['added'].append(data.get('name', filename))
        else:
            # Compare "version" fields
            version1 = toml_data_1[filename].get('filename', None)
            version2 = data.get('filename', None)
            if version1 != version2:
                results['modified'].append((data.get('name', filename), version1, version2))

    # Check for removed files
    for filename in toml_data_1.keys():
        if filename not in toml_data_2:
            results['removed'].append(toml_data_1[filename].get('name', filename))

    return results



def write_differences_to_markdown(differences, input_modpack_name, version1, version2, output_file=None, ):
    markdown_lines = []
    
    # Title for the Markdown report
    markdown_lines.append(f"# {input_modpack_name} {version1} -> {version2}\n")
    
    # Added section
    if differences['added']:
        markdown_lines.append("## Added\n")
        for name in differences['added']:
            markdown_lines.append(f"- {name}")
    else:
        markdown_lines.append("## Added\n- None")
    
    # Removed section
    if differences['removed']:
        markdown_lines.append("## Removed\n")
        for name in differences['removed']:
            markdown_lines.append(f"- {name}")
    else:
        markdown_lines.append("## Removed\n- None")
    
    # Modified section
    if differences['modified']:
        markdown_lines.append("## Modified\n")
        for name, old_version, new_version in differences['modified']:
            markdown_lines.append(f"- **{name}**: Changed from `{old_version}` to `{new_version}`")
    else:
        markdown_lines.append("## Modified\n- None")
    
    # Join all lines into a single string
    markdown_output = "\n".join(markdown_lines)
    
    # Write to a file if an output path is provided
    if output_file:
        with open(output_file, 'w', encoding="utf8") as f:
            f.write(markdown_output)
    
    return markdown_output

############################################################
# Start Message

os.chdir(packwiz_path)

# Parse pack.toml for modpack version.
with open(packwiz_manifest, "r") as f:
    pack_toml = toml.load(f)
pack_version = pack_toml["version"]
modpack_name = pack_toml["name"]
minecraft_version = pack_toml["versions"]["minecraft"]

input(f"""{launch_message}
Modpack: {modpack_name}
Version: {pack_version}
Minecraft: {minecraft_version}

Press Enter to continue...""")


############################################################
# Configuration

with open(settings_path, "r") as s_file:
    settings_yml = yaml.safe_load(s_file)

# These lines contains all global configuration variables.
export_client = refresh_only = update_bcc_version = cleanup_temp = create_release_notes = print_path_debug = update_publish_workflow = download_prev_release = bool
bh_banner = repo_owner = repo_name = str
server_mods_remove_list = list

# Parse settings file and update variables.
for key, value in settings_yml.items():
    globals()[key] = value

export_server = determine_server_export()
prev_release_version = get_latest_release_version(repo_owner, repo_name)

if print_path_debug:
    print("[DEBUG] " + git_path)
    print("[DEBUG] " + packwiz_path)
    print("[DEBUG] " + packwiz_exe_path)
    print("[DEBUG] " + bcc_client_config_path)
    print("[DEBUG] " + bcc_server_config_path)


############################################################
# Class Objects

downloader = AsyncGitHubDownloader(repo_owner, repo_name, branch=prev_release_version)


############################################################
# Main Program

def main():

    if not refresh_only:

        #----------------------------------------
        # Download previous release files.
        #----------------------------------------
        if download_prev_release:
            if os.path.exists(prev_release):
                rmtree(prev_release)
                os.makedirs(prev_release)
            else:
                os.makedirs(prev_release)
                
            async def download_mod_files():
                # Download all files from a folder asynchronously
                await downloader.download_folder('Packwiz/mods', prev_release)
                return

            # Run the main function
            try:
                asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
                asyncio.run(download_mod_files())
            except Exception as ex:
                print(ex)

        #----------------------------------------
        # Compare previous release.
        #----------------------------------------

        # print(parse_active_projects(packwiz_mods_path, "filename"))
        # print(parse_active_projects(packwiz_mods_path, "filename"))
        differences = compare_toml_files(prev_release, packwiz_mods_path)
        print(write_differences_to_markdown(differences, modpack_name, prev_release_version, pack_version, git_path + f'\\Changelogs\\changelog_mods_{pack_version}.md'))


        #----------------------------------------
        # Update publish workflow values.
        #----------------------------------------
        if update_publish_workflow:
            yaml2 = YAML()

            publish_workflow_path = git_path + f"\\.github\\workflows\\publish.yml"

            with open(publish_workflow_path, "r") as pw_file:
                publish_workflow_yml = yaml2.load(pw_file)

            publish_workflow_yml['env']['MC_VERSION'] = minecraft_version

            if "beta" in pack_version:
                pw_release_type = "beta"
            elif "alpha" in pack_version:
                pw_release_type = "alpha"
            else:
                pw_release_type = "release"
            
            publish_workflow_yml['env']['RELEASE_TYPE'] = pw_release_type

            with open(publish_workflow_path, "w") as pw_file:
                yaml2.dump(publish_workflow_yml, pw_file)
        

        #----------------------------------------
        # Create release notes.
        #----------------------------------------

        # Parse the related changelog file for overview details and create release markdown files for CF and MR.
        if create_release_notes:
            os.chdir(git_path)
            changelog_path = git_path + f"\\Changelogs\\{pack_version}+{minecraft_version}.yml"
            
            md_element_full_changelog = f"#### **[[Full Changelog]](https://wiki.crismpack.net/modpacks/{modpack_name.lower()}/changelog/{minecraft_version}#v{pack_version})**"
            md_element_pre_release = '**This is a pre-release. Here be dragons!**'
            md_element_bh_banner = f"[![BisectHosting Banner]({bh_banner})](https://bisecthosting.com/CRISM)"
            md_element_crism_spacer = "![CrismPack Spacer](https://github.com/CrismPack/CDN/blob/main/desc/breakneck/79ESzz1-tiny.png?raw=true)"
            # html_element_bh_banner = "<p><a href='https://bisecthosting.com/CRISM'><img src='https://github.com/CrismPack/CDN/blob/main/desc/insomnia/bhbanner.png?raw=true' width='800' /></a></p>"

            with open(changelog_path, "r", encoding="utf8") as f:
                changelog_yml = yaml.safe_load(f)
            update_overview = changelog_yml['Update overview']
            #update_overview = update_overview.replace("-","### -")

            mdFile_CF = MdUtils(file_name='CurseForge-Release')
            
            if "beta" in pack_version or "alpha" in pack_version:
                print("pack_version = " + pack_version)
                mdFile_CF.new_paragraph(md_element_pre_release)

            mdFile_CF.new_paragraph(markdown_list_maker(update_overview))
            mdFile_CF.new_paragraph(md_element_full_changelog)
            mdFile_CF.new_paragraph("<br>")
            mdFile_CF.new_paragraph(md_element_bh_banner)
            mdFile_CF.create_md_file()


        #----------------------------------------
        # Update BCC version number.
        #----------------------------------------

        if update_bcc_version:
            os.chdir(packwiz_path)
            # Client
            with open(bcc_client_config_path, "r") as f:
                bcc_json = json.load(f)
            bcc_json["modpackVersion"] = pack_version
            with open(bcc_client_config_path, "w") as f:
                json.dump(bcc_json, f)
            # Server
            with open(bcc_server_config_path, "r") as f:
                bcc_json = json.load(f)
            bcc_json["modpackVersion"] = pack_version
            with open(bcc_server_config_path, "w") as f:
                json.dump(bcc_json, f)


        #----------------------------------------
        # Export client pack.
        #----------------------------------------
        os.chdir(packwiz_path)

        # Refresh the packwiz index
        subprocess.call(f"{packwiz_exe_path} refresh", shell=True)

        # Packwiz exporting
        file = f'{modpack_name}-{pack_version}.zip'
        if export_client:
            # Export CF modpack using Packwiz.
            subprocess.call(f"{packwiz_exe_path} cf export", shell=True)
            move(file, f"{export_path}{file}")
            print("[PackWiz] Client exported.")


        #----------------------------------------
        # Export server pack
        # ----------------------------------------
        if export_server:
            # Export CF modpack using Packwiz.
            subprocess.call(f"{packwiz_exe_path} cf export -s server", shell=True)
            file_server_name = f'{modpack_name}-Server-{pack_version}.zip'
            move(file, f"{export_path}{file_server_name}")
            print("[PackWiz] Server exported.")

            os.chdir(git_path)
            # Deletes the temp folder if it already exists.
            if os.path.isdir(tempfolder_path):
                rmtree(tempfolder_path)

            copytree("Server Pack", tempfolder_path) # Copies contents of "Server Pack" folder into the temp folder.

            # Console input.
            server_mods_path = input(f'Create a new modpack instance in the CurseForge launcher using the {file_server_name} file. Then drag the mods folder from that instance into the terminal (No spaces allowed for the source directory): ')
            
            copytree(server_mods_path, temp_mods_path, dirs_exist_ok=True)
            
            # Removes specified files from mods folder
            os.chdir(temp_mods_path)
            for file in os.listdir():
                if file in server_mods_remove_list:
                    os.remove(file)

            os.chdir(export_path)
            make_archive(f"{modpack_name}-Server-{pack_version}", 'zip', tempfolder_path)


        #----------------------------------------
        # Temp cleanup
        #----------------------------------------
        if cleanup_temp and os.path.isdir(tempfolder_path):
            rmtree(tempfolder_path)
            print("Temp folder cleanup finished.")
        
        os.chdir(packwiz_path)
        subprocess.call(f"{packwiz_exe_path} refresh", shell=True)
        
    elif refresh_only:
        subprocess.call(f"{packwiz_exe_path} refresh", shell=True)


if __name__ == "__main__":
    try:
        print("")
        main()
    except KeyboardInterrupt:
        print("Operation aborted by user.")
        exit(-1)