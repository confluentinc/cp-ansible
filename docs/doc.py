"""
Reads variable files with variables documented like:
### Description
variable: default

And writes to formatted markdown file
"""


def parse_variable_file(role_name, docs_file):
    docs_file.write("# " + role_name)
    docs_file.write("\n\n")
    docs_file.write("Below are the supported variables for the role " + role_name)
    docs_file.write("\n\n")
    docs_file.write("***")
    docs_file.write("\n\n")

    variables_file = open("../roles/" + role_name + "/defaults/main.yml", "r")
    lines = variables_file.read().split('\n')
    for i in range(len(lines)):
        if lines[i].startswith("### "):
            description = lines[i][4:]
            colon_index = lines[i + 1].index(":")
            variable = lines[i + 1][:colon_index]
            default = lines[i + 1][colon_index + 1:]

            docs_file.write("### " + variable)
            docs_file.write("\n\n")
            docs_file.write(description)
            docs_file.write("\n\n")
            docs_file.write("Default: " + default)
            docs_file.write("\n\n")
            docs_file.write("***")
            docs_file.write("\n\n")

    variables_file.close()


if __name__ == "__main__":
    docs_file = open("VARIABLES.md", "w")

    for role_name in ["variables", "common", "control_center",
                      "kafka_broker", "kafka_connect", "kafka_rest",
                      "ksql", "schema_registry", "zookeeper",
                      "kafka_connect_replicator", "ssl"]:
        parse_variable_file(role_name, docs_file)

    docs_file.close()
