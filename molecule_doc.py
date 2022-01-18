"""
Reads molecule inventory files with the following structure:
### Tested Functionality 1
### Test Functionality 2
### etc...

And writes to formatted markdown file.
"""

import os

# Set path to molecule scenarios
path = 'molecule/'

# Define a list to contain tags to search against
tags = ["###","####"]

# Define a list to hold scenario names
scenario_name = []

# Define a list to hold directory contents
directory_contents = []

def parse_molecule_scenario(scenario_name, docs_file):
      length = len(scenario_name)
      for l in range(length):
        sn = scenario_name[l]
        docs_file.write("### confluent.test/molecule/" + str(sn))
        docs_file.write("\n\n")
        docs_file.write("#### Scenario " + str(sn) + " test's the following:")
        docs_file.write("\n\n")

        # Read Inventory file and check for tags and write them
        inventory_file = open("molecule/" + str(sn) + "/molecule.yml", "r")
        lines = inventory_file.read().split('\n')

        for i in range(len(lines)):
            if lines[i].startswith(tuple(tags)):
                description = lines[i][4:]
                docs_file.write(description)
                docs_file.write("\n\n")   
        
        docs_file.write("#### Scenario " + str(sn) + " verify test's the following:")
        docs_file.write("\n\n")

        # Read Verify file and check for tags and write them
        verify_file = open("molecule/" + str(sn) + "/verify.yml", "r")
        verify_lines = verify_file.read().split('\n')

        for i in range(len(verify_lines)):
            if verify_lines[i].startswith(tuple(tags)):
                verify_description = verify_lines[i][4:]
                docs_file.write(verify_description)
                docs_file.write("\n\n")

        docs_file.write("***")
        docs_file.write("\n\n")

        inventory_file.close
        verify_file.close

# Open the file to write to.
docs_file = open("MOLECULE_SCENARIOS.md", "w")

# Get directory listing in molecule directory.
directory_contents = os.listdir(path)

# Parse out the subdirectories for each unique scenario.
for item in directory_contents:
    full_path = os.path.join(path, item)
    if os.path.isdir(full_path):
            scenario_name.append(item)

# Call function to write content to docs file
parse_molecule_scenario(scenario_name, docs_file)  

# Close docs file once writing is complete.
docs_file.close
