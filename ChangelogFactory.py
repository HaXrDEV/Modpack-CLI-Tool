import os
import yaml
from mdutils.mdutils import MdUtils
import re
import toml

class ChangelogFactory:
    def __init__(self, changelog_dir, modpack_name, modpack_version):
        self.changelog_dir = changelog_dir
        self.modpack_name = modpack_name
        self.modpack_version = modpack_version

    def get_changelog_value(self, changelog_yml, key):
        if changelog_yml.endswith(('.yml', '.yaml')):  # Filter only YAML files
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

    def markdown_list_maker(self, lines):
        """This method takes a yml object of strings, formats them and returns the result."""
        processed_lines = []
        for line in lines:
            processed_lines.append("- " + line)
        return """{}""".format("\n".join(processed_lines[0:]))

    def compare_toml_files(self, dir1, dir2):
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


    def build_markdown_changelog(self, repo_owner, repo_name, tempgit_path, packwiz_mods_path):
        mdFile = MdUtils(file_name='CHANGELOG-test')

        changelog_list = iter(reversed(os.listdir(self.changelog_dir)))

        for changelog in changelog_list:
            if changelog.endswith(('.yml', '.yaml')):  # Filter only YAML files
                version = self.get_changelog_value(changelog, "version")
                next_changelog = next(changelog_list)
                prev_release = self.get_changelog_value(next_changelog, "version")

                try:
                    fabric_loader = self.get_changelog_value(changelog, "Fabric version")
                    improvements = self.get_changelog_value(changelog, "Changes/Improvements")
                    overview_legacy = self.get_changelog_value(changelog, "Update overview")
                    bug_fixes = self.get_changelog_value(changelog, "Bug Fixes")
                except:
                    continue
                
                #tempgit_path = r"D:\GitHub Projects\Insomnia-Hardcore\Modpack-CLI-Tool\tempgit"
                prev_release_path = os.path.join(tempgit_path, str(prev_release))
                version_path = os.path.join(tempgit_path, str(version))

                #differences = self.compare_toml_files(prev_release_path, version_path)
                if str(version) != str(modpack_version):
                    differences = self.compare_toml_files(prev_release_path, version_path)
                else:
                    differences = self.compare_toml_files(prev_release_path, packwiz_mods_path)
                
                added_mods = differences['added']
                removed_mods = differences['removed']

                mdFile.new_paragraph(f"## {self.modpack_name} | v{version}")
                mdFile.new_paragraph(f"*Fabric Loader {fabric_loader}* | *[Mod Updates](https://github.com/{repo_owner}/{repo_name}/blob/main/changelogs/changelog_mods_{version}.md)*")
                if improvements:
                    mdFile.new_paragraph("### Changes/Improvements ⭐")
                    mdFile.new_paragraph(self.markdown_list_maker(improvements))
                if overview_legacy:
                    mdFile.new_paragraph("### Update overview")
                    mdFile.new_paragraph(self.markdown_list_maker(overview_legacy))
                if bug_fixes:
                    mdFile.new_paragraph("### Bug Fixes 🪲")
                    mdFile.new_paragraph(self.markdown_list_maker(bug_fixes))
                if added_mods:
                    mdFile.new_paragraph("### Added Mods ✅")
                    mdFile.new_paragraph(self.markdown_list_maker(added_mods))
                if removed_mods:
                    mdFile.new_paragraph("### Removed Mods ❌")
                    mdFile.new_paragraph(self.markdown_list_maker(removed_mods))
                mdFile.new_paragraph("---")
        mdFile.create_md_file()


# Set the changelog directory
changelog_dir = r"D:\GitHub Projects\Insomnia-Hardcore\Changelogs"


repo_owner = "CrismPack"
repo_name = "Insomnia-Hardcore"
modpack_version = "2.2.0"

# Create an instance of ChangelogFactory and print the changelog names
changelog = ChangelogFactory(changelog_dir, "Insomnia: Hardcore", modpack_version)
#print(changelog.get_changelog_value("name"))

#print(changelog.markdown_list_maker(changelog.get_changelog_value()))

tempgit_path = r"D:\GitHub Projects\Insomnia-Hardcore\Modpack-CLI-Tool\tempgit"
packwiz_mods = r"D:\GitHub Projects\Insomnia-Hardcore\Packwiz\mods"
changelog.build_markdown_changelog(repo_owner, repo_name, tempgit_path, packwiz_mods)