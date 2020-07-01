"""
Reads variable files with variables documented like:
### Description
variable: default

And writes to formatted markdown file
"""

def parse_variable_file(filepath, docs_file):
    variables_file = open(filepath, "r")
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


docs_file = open("docs.md", "w")

for role_name in ["common", "control_center", "kafka_broker", "kafka_connect", "kafka_rest", "ksql", "schema_registry", "zookeeper"]:
    parse_variable_file("roles/confluent." + role_name + "/defaults/main.yml", docs_file)

docs_file.close
