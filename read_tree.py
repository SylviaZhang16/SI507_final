import json

def load_tree_from_json(filename):
    with open(filename, 'r') as file:
        data = json.load(file)
    return data

def display_tree(node, level=0):
    indent = "  " * level
    print(f"{indent}{node['name']}")
    for child in node['children'].values():
        display_tree(child, level + 1)

if __name__ == "__main__":
    tree_file = 'tree_structure.json'
    tree_data = load_tree_from_json(tree_file)
    print("Tree Structure:")
    display_tree(tree_data)