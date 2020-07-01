"""
Reads variable files with variables documented like:
### Description
variable: default

And writes to formatted markdown file
"""

docs_file = open("docs.md", "w")

variables_file = open("roles/confluent.common/defaults/main.yml", "r")
lines = variables_file.read().split('\n')

for i in range(len(lines)):
    if lines[i].startswith("### "):
        description = lines[i][4:]
        colon_index = lines[i+1].index(":")
        variable = lines[i+1][:colon_index]
        default = lines[i+1][colon_index+1:]

        docs_file.write("***")
        docs_file.write("\n\n")
        docs_file.write("### " + variable)
        docs_file.write("\n\n")
        docs_file.write(description)
        docs_file.write("\n\n")
        docs_file.write("Default: " + default)
        docs_file.write("\n\n")

variables_file.close

docs_file.close
