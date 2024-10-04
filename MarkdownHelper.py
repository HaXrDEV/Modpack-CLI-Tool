import re

def remove_bracketed_text(input_str):
        """This method takes an input string and removes any text surrounded by parentheses (), square brackets [], and curly braces {}."""
        # Define a pattern to match text within parentheses (), square brackets [], and curly braces {}
        pattern = r'\(.*?\)|\[.*?\]|\{.*?\}'

        # Use re.sub() to replace the matched text with an empty string
        result = re.sub(pattern, '', input_str)

        # Return the cleaned string
        return result.strip()

def codify_bracketed_text(input_str, keep_brackets=False):
        """This method takes an input string and formats any text surrounded by square brackets [] to code."""
        
        if keep_brackets:
            # This regex finds text inside brackets without removing them
            return re.sub(r'(\[)([^\]]+)(\])', r'`\1\2\3`', input_str)
        else:
            # This regex finds text inside brackets
            #return re.sub(r'\[([^\]]+)\]', r'`\1`', input_str)
            return re.sub(r'(?<!\\)\[([^\]]+)\]', r'`\1`', input_str)
            

def markdown_list_maker(lines):
        """This method takes a yml object of strings, formats them and returns the result."""
        processed_lines = []
        for line in lines:
                processed_lines.append("- " + line)
        return """{}""".format("\n".join(processed_lines[0:]))


def write_differences_to_markdown(differences, input_modpack_name, version1, version2, output_file=None, ):
    markdown_lines = []
    
    # Title for the Markdown report
    markdown_lines.append(f"# {input_modpack_name} {version1} -> {version2}\n")
    
    # Added section
    if differences['added']:
        markdown_lines.append("## Added\n")
        for name in differences['added']:
            markdown_lines.append(f"- {remove_bracketed_text(name)}")
    else:
        markdown_lines.append("## Added\n- None")
    
    # Removed section
    if differences['removed']:
        markdown_lines.append("## Removed\n")
        for name in differences['removed']:
            markdown_lines.append(f"- {remove_bracketed_text(name)}")
    else:
        markdown_lines.append("## Removed\n- None")
    
    # Modified section
    if differences['modified']:
        markdown_lines.append("## Modified\n")
        for name, old_version, new_version in differences['modified']:
            markdown_lines.append(f"- **{remove_bracketed_text(name)}**: Changed from `{old_version}` to `{new_version}`")
    else:
        markdown_lines.append("## Modified\n- None")
    
    # Join all lines into a single string
    markdown_output = "\n".join(markdown_lines)
    
    # Write to a file if an output path is provided
    if output_file:
        with open(output_file, 'w', encoding="utf8") as f:
            f.write(markdown_output)
    
    return markdown_output