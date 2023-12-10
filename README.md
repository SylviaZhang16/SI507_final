# SI 507 Final Project - Game Explorer

run the program: python3 game-explorer
Required Python package: import requests, json, datetime, os

## Interaction

Users can select games based on platforms, genres, themes, and release years. For selected games, detailed information is displayed. if it’s available on PC, users can further choose to whether search the game information on Steam by Steam API.

## API keys

IGDB: client_id, client_secret, included in py file
Steam storefront API: no authentication

## Data structure

- The data is organized into a tree structure. The root node represents the initial query for game recommendations. Subsequent levels represent platforms, genres, themes, and release years.The tree is dynamically generated based on user selections at each step, using the data fetched from the IGDB API and Steam API.
- Parent and Children Node: Each parent node in this tree represents a category or a group of games. For example, a parent node might represent a specific gaming platform like "PlayStation 4" or a game genre like "Action." Under each parent node, there are children nodes, representing subcategories or specific elements within the parent category. For instance, under a parent node of "PlayStation 4," the children nodes might be different genres available on that platform, like "Adventure," "Racing," etc. Further, under a genre node like "Adventure," there might be nodes for different themes or release years.
- Data: Each node can hold data. In the case of game nodes, this data could include the game's name, its genre, the platforms it's available on, and other relevant information.
- Hierarchy:
  1. gaming platforms (PlayStation, Xbox, PC, etc.).
  2. genres (Action, Puzzle, Shooter, etc.).
  3. themes (Sci-fi, Fantasy, Horror, etc.).
  4. releasng years(available within recent 10 years)
  5. Finally, each game is represented as a node containing its details.
- files:
  - game_explorer.py: the project py file that constructs your graphs or trees from the stored data using Node class
  - tree_structure.json: the tree (If you want to regenerate it, you can uncommet the several lines in main of the project py file to export serialized_tree.
  - read_tree.py: a stand alone python file that reads the json of your graphs or trees.
