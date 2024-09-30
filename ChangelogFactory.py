import os
import yaml
from mdutils.mdutils import MdUtils

class ChangelogFactory:
    def __init__(self, changelog_dir, modpack_name):
        self.changelog_dir = changelog_dir
        self.modpack_name = modpack_name

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

    def markdown_list_maker(self, lines):
        """This method takes a yml object of strings, formats them and returns the result."""
        processed_lines = []
        for line in lines:
            processed_lines.append("- " + line)
        return """{}""".format("\n".join(processed_lines[0:]))

    def build_markdown_changelog(self, repo_owner, repo_name, output_file=None):
        mdFile = MdUtils(file_name='CHANGELOG-test')
        for changelog in reversed(os.listdir(self.changelog_dir)):
            if changelog.endswith(('.yml', '.yaml')):  # Filter only YAML files
                version = self.get_changelog_value(changelog, "version")
                fabric_loader = self.get_changelog_value(changelog, "Fabric version")
                improvements = self.get_changelog_value(changelog, "Changes/Improvements")
                overview_legacy = self.get_changelog_value(changelog, "Update overview")
                bug_fixes = self.get_changelog_value(changelog, "Bug Fixes")
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
                mdFile.new_paragraph("---")
        mdFile.create_md_file()



# Set the changelog directory
changelog_dir = r"D:\GitHub Projects\Insomnia-Hardcore\Changelogs"


repo_owner = "CrismPack"
repo_name = "Insomnia-Hardcore"

# Create an instance of ChangelogFactory and print the changelog names
changelog = ChangelogFactory(changelog_dir, "Insomnia: Hardcore")
#print(changelog.get_changelog_value("name"))

#print(changelog.markdown_list_maker(changelog.get_changelog_value()))

changelog.build_markdown_changelog(repo_owner, repo_name)