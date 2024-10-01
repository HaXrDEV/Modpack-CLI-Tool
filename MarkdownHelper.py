import re

def remove_bracketed_text(input_str):
        """This method takes an input string and removes any text surrounded by parentheses (), square brackets [], and curly braces {}."""
        # Define a pattern to match text within parentheses (), square brackets [], and curly braces {}
        pattern = r'\(.*?\)|\[.*?\]|\{.*?\}'

        # Use re.sub() to replace the matched text with an empty string
        result = re.sub(pattern, '', input_str)

        # Return the cleaned string
        return result.strip()



def markdown_list_maker(lines):
        """This method takes a yml object of strings, formats them and returns the result."""
        processed_lines = []
        for line in lines:
                processed_lines.append("- " + line)
        return """{}""".format("\n".join(processed_lines[0:]))