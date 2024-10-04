import os
import yaml
from mdutils.mdutils import MdUtils
import re
import toml
import itertools
import MarkdownHelper as markdown

class ChangelogFactory:
    def __init__(self, changelog_dir, modpack_name, modpack_version):
        self.changelog_dir = changelog_dir
        self.modpack_name = modpack_name
        self.modpack_version = modpack_version
    
    def get_changelog_value(self, changelog_yml, key):
        if changelog_yml.endswith(('.yml', '.yaml')) and changelog_yml:  # Filter only YAML files
            file_path = os.path.join(self.changelog_dir, changelog_yml)
            try:
                with open(file_path, "r", encoding="utf8") as f: # Open the YAML file and load its contents
                    changelog_data = yaml.safe_load(f)
                    return changelog_data[key] # Returns value of key
            except yaml.YAMLError as e:
                print(f"Error parsing {file_path}: {e}") # Handle YAML errors gracefully
            except KeyError:
                print(f"Key '{key}' not found in {file_path}") # Handle missing key
            finally:
                f.close()

    def compare_toml_files(self, dir1, dir2):
        # Initialize dictionaries to store TOML data
        toml_data_1 = {}
        toml_data_2 = {}
        

        def local_load_toml_files_from_dir(dir, dict):
            try:
                for filename in os.listdir(dir):
                    if filename.endswith('.toml'):
                        filepath = os.path.join(dir, filename)
                        with open(filepath, "r", encoding="utf8") as f:
                            mod_toml = toml.load(f)
                            side = str(mod_toml['side'])
                            if side in ("both", "client", "server"):
                                dict[filename] = toml.load(filepath)
            except Exception as ex:
                print(ex)

        local_load_toml_files_from_dir(dir1, toml_data_1)
        local_load_toml_files_from_dir(dir2, toml_data_2)


        # Prepare to store results
        results = {
            'added': [],
            'removed': [],
            'modified': []
        }

        # Check for added and modified files
        for filename, data in toml_data_2.items():
            if filename not in toml_data_1:
                name_data = data.get('name', filename)
                side_data = data.get('side', filename)
                if side_data != "both":
                    side_str = f" [{str(side_data).capitalize()}]"
                else:
                    side_str = ""
                results['added'].append(markdown.remove_bracketed_text(name_data) + side_str) # + str(data.get('side', filename)).capitalize()
            else:
                # Compare "version" fields
                version1 = toml_data_1[filename].get('filename', None)
                version2 = data.get('filename', None)
                if version1 != version2:
                    results['modified'].append((data.get('name', filename), version1, version2))

        # Check for removed files
        for filename in toml_data_1.keys():
            if filename not in toml_data_2:
                results['removed'].append(markdown.remove_bracketed_text(toml_data_1[filename].get('name', filename)))

        return results


    def Reverse(self, lst):
        new_lst = lst[::-1]
        return new_lst


    def build_markdown_changelog(self, repo_owner, repo_name, tempgit_path, packwiz_mods_path, file_name="CHANGELOG", repo_branch = "main", mc_version=None):
        mdFile = MdUtils(file_name)

        changelog_list = self.Reverse(os.listdir(self.changelog_dir))
        #changelog_list_reversed = self.Reverse(changelog_list)
        #changelog_iter1, changelog_iter2 = itertools.tee(changelog_list)

        # Iterate over the list with an index using enumerate
        mdFile.new_paragraph(f"##### {self.modpack_name}")

        if mc_version:
            mdFile.new_paragraph(f"# Changelog - {mc_version}")
        else:
            mdFile.new_paragraph(f"# Changelog")

        for i, changelog in enumerate(changelog_list):
            # Check if there's a "next" item
            if i + 1 < len(changelog_list):
                next_changelog = changelog_list[i + 1]
            else:
                next_changelog = None  # No next item if we're at the last one


            added_mods = None
            removed_mods = None

            if changelog.endswith(('.yml', '.yaml')):  # Filter only YAML files
                version = self.get_changelog_value(changelog, "version")
                if next_changelog:
                    next_version = self.get_changelog_value(next_changelog , "version")

                fabric_loader = self.get_changelog_value(changelog, "Fabric version")
                improvements = self.get_changelog_value(changelog, "Changes/Improvements")
                overview_legacy = self.get_changelog_value(changelog, "Update overview")
                bug_fixes = self.get_changelog_value(changelog, "Bug Fixes")
                config_changes = self.get_changelog_value(changelog, "Config Changes")

                next_version_path = os.path.join(tempgit_path, str(next_version))
                version_path = os.path.join(tempgit_path, str(version))

                print(f"[DEBUG] {next_version_path} + {version_path}")

                if str(version) != str(self.modpack_version) and next_version:
                    differences = self.compare_toml_files(next_version_path, version_path)
                elif str(version) == str(self.modpack_version) and next_version:
                    differences = self.compare_toml_files(next_version_path, packwiz_mods_path)
                else:
                    differences = None

                if differences:
                    added_mods = differences['added']
                    removed_mods = differences['removed']
                
                # if not "v" in version:
                #     mdFile.new_paragraph(f"## {self.modpack_name} | v{version}")
                # else:
                #     mdFile.new_paragraph(f"## {self.modpack_name} | {version}")

                if not "v" in version:
                    mdFile.new_paragraph(f"## v{version}")
                else:
                    mdFile.new_paragraph(f"## {version}")

                mdFile.new_paragraph(f"*Fabric Loader {fabric_loader}* | *[Mod Updates](https://github.com/{repo_owner}/{repo_name}/blob/{repo_branch}/Changelogs/changelog_mods_{version}.md)*")
                if improvements:
                    mdFile.new_paragraph("### Changes/Improvements ⭐")
                    mdFile.new_paragraph(markdown.markdown_list_maker(improvements))
                if overview_legacy:
                    mdFile.new_paragraph("### Update overview")
                    mdFile.new_paragraph(markdown.markdown_list_maker(overview_legacy))
                if bug_fixes:
                    mdFile.new_paragraph("### Bug Fixes 🪲")
                    mdFile.new_paragraph(markdown.markdown_list_maker(bug_fixes))
                if added_mods:
                    mdFile.new_paragraph("### Added Mods ✅")
                    mdFile.new_paragraph(markdown.codify_bracketed_text(markdown.markdown_list_maker(added_mods)))
                if removed_mods:
                    mdFile.new_paragraph("### Removed Mods ❌")
                    mdFile.new_paragraph(markdown.codify_bracketed_text(markdown.markdown_list_maker(removed_mods)))
                if config_changes:
                    mdFile.new_paragraph("### Config Changes 📝")
                    mdFile.new_paragraph(markdown.codify_bracketed_text(config_changes))
                #mdFile.new_paragraph("---")
        mdFile.create_md_file()


# # Set the changelog directory
# changelog_dir = r"D:\GitHub Projects\Insomnia-Hardcore\Changelogs"


# repo_owner = "CrismPack"
# repo_name = "Insomnia-Hardcore"
# modpack_version_ = "2.2.0"

# # Create an instance of ChangelogFactory and print the changelog names
# changelogfactory = ChangelogFactory(changelog_dir, "Insomnia: Hardcore", modpack_version_)
# #print(changelog.get_changelog_value("name"))

# #print(changelog.markdown_list_maker(changelog.get_changelog_value()))

# tempgit_path = r"D:\GitHub Projects\Insomnia-Hardcore\Modpack-CLI-Tool\tempgit"
# packwiz_mods = r"D:\GitHub Projects\Insomnia-Hardcore\Packwiz\mods"
# changelogfactory.build_markdown_changelog(repo_owner, repo_name, tempgit_path, packwiz_mods)