"""
Parses required places in the cp-ansible project for all instances of tags in following format
tags: <test-tag>
tags:
    - <test-tag>

And writes the list of tags to a formatted markdown file.
Adds new entries for new tags with blank description (to be filled by the user).
For the existing entries with description, lets it stay as is.
"""

import os

# Parse all tags in cp-ansible
def get_all_tags(directory, search_text, filePattern):
    
    all_tags = set()
    for path, dirs, files in os.walk(os.path.abspath(directory)):
        for filename in files:
            if not filename.endswith(filePattern) : 
                continue
            filepath = os.path.join(path, filename)
            with open(filepath, "r") as f:
                file_content = f.read()
            if search_text not in file_content:
                continue
            list_lines = file_content.split("\n")
            i = 0
            while (i < len(list_lines)):
                line = list_lines[i]
                i = i+1
                if search_text in line:
                    tag = line.replace(search_text,'').strip()
                    if (tag == ''):
                        while(i< len(list_lines) and "-" in list_lines[i]):
                            new_tag = list_lines[i].replace("-", '').strip()
                            if (len(new_tag.split()) == 1):
                                all_tags.add(new_tag)
                            i = i+1
                    else:
                        all_tags.add(tag)
    
    return all_tags

# Create TAGS.md after parsing all tags in cp-ansible
def create_docs_tag(tags):
    tags_doc = ""
    if os.path.isfile("./TAGS.md"):
        with open("./TAGS.md") as f:
            tags_doc = f.read()

    docs_file = open("./TAGS.md", "a")

    intro_text = ("# Refer to this doc to get an overview of all tags used inside the cp-ansible project"
        "\n\nRefer https://docs.ansible.com/ansible/latest/user_guide/playbooks_tags.html to know more about ansible tags"
        "\nWhile running cp-ansible, you can use --tags or --skip-tags to run or skip any specific tag. E.g."
        "\nansible-playbook -i hosts.yml confluent.platform.all --tags 'tag-name'"
        "\nansible-playbook -i hosts.yml confluent.platform.all --skip-tags 'tag-name'")

    if len(tags_doc) == 0:
        docs_file.write(intro_text)
        docs_file.write("\n\n")
        docs_file.write("***")
    for tag in tags:
        tag_def = f'### Tag - {tag}'
        if tag_def in tags_doc:
            continue
        docs_file.write("\n\n")
        docs_file.write(f'### Tag - {tag}')
        docs_file.write("\n\n")
        docs_file.write(f"Description: ")
        docs_file.write("\n\n")
        docs_file.write("***")
    docs_file.close()

if __name__ == "__main__":
    base_dir = ["../roles", "../playbooks"]
    tags = set()
    
    for item in base_dir:
        tags_temp = get_all_tags(item, " tags:", ('.yaml', '.yml'))
        tags.update(tags_temp)

    tags = sorted(tags)
    create_docs_tag(tags)
