import requests
import json
import datetime
import os

class Node:
    def __init__(self, name, data=None):
        self.name = name
        self.children = {}
        self.data = data

    def add_child(self, key, obj):
        self.children[key] = obj
        return obj

client_id = 'znngmjkvikxp1yxvfb8xqkh9yki9e6' 
client_secret = 'yctyde3vftm4yec6dkiufj8mk3ers8' 

def get_access_token(client_id, client_secret):
    token_url = 'https://id.twitch.tv/oauth2/token'
    payload = {
        'client_id': client_id,
        'client_secret': client_secret,
        'grant_type': 'client_credentials'
    }
    response = requests.post(token_url, data=payload)
    if response.status_code == 200:
        access_token = response.json()['access_token']
        return access_token
    else:
        return None
    
def fetch_platform_ids(access_token, platform_names):
    url = 'https://api.igdb.com/v4/platforms'
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {access_token}'
    }
    platform_names_str = '","'.join(platform_names)
    body = f'fields name; where name = ("{platform_names_str}");'
    
    response = requests.post(url, headers=headers, data=body)
    if response.status_code == 200:
        return {platform['name']: platform['id'] for platform in response.json()}
    else:
        raise Exception(f"Failed to fetch platform IDs: {response.text}")
    

def fetch_games(access_token, platform_ids, limit=500):
    url = 'https://api.igdb.com/v4/games'
    headers = {
        'Client-ID': client_id,
        'Authorization': f'Bearer {access_token}'
    }
    platforms_filter = ','.join(str(id) for id in platform_ids)
    current_year = datetime.datetime.now().year
    five_years_ago = current_year - 5
    body = f'fields name, genres.name, platforms.name, themes.name, release_dates.y; where platforms = ({platforms_filter}) & release_dates.y > {five_years_ago}; sort popularity desc; limit {limit};'
    response = requests.post(url, headers=headers, data=body)
    if response.status_code == 200:
        return response.json()
    else:
        raise Exception(f"Failed to fetch games: {response.text}")
    

def cache_games(games):
    with open('games_cache.json', 'w') as f:
        json.dump(games, f)

def load_games_from_cache():
    with open('games_cache.json', 'r') as f:
        return json.load(f)
    
relevant_platforms = ['PC (Microsoft Windows)', 'PlayStation 4', 'Xbox One', 'Nintendo Switch'] 

def build_games_tree(games, relevant_platforms):
    root = Node("Game Recommendations")

    for game in games:
        earliest_year = min(release_date['y'] for release_date in game.get('release_dates', [{'y': float('inf')}]) if 'y' in release_date)
        if earliest_year == float('inf'):
            earliest_year = 'Unknown'

        for platform in game.get('platforms', []):
            platform_name = platform.get('name', 'Unknown')
            if platform_name in relevant_platforms:
                platform_node = root.children.get(platform_name) or root.add_child(platform_name, Node(platform_name))

                for genre in game.get('genres', [{'name': 'Unknown'}]):
                    genre_name = genre.get('name', 'Unknown')
                    genre_node = platform_node.children.get(genre_name) or platform_node.add_child(genre_name, Node(genre_name))

                    for theme in game.get('themes', [{'name': 'Unknown'}]):
                        theme_name = theme.get('name', 'Unknown')
                        theme_node = genre_node.children.get(theme_name) or genre_node.add_child(theme_name, Node(theme_name))

                        year_node = theme_node.children.get(str(earliest_year)) or theme_node.add_child(str(earliest_year), Node(str(earliest_year)))
                        if game['name'] not in year_node.children:
                            game_node = Node(game['name'], data=game)
                            year_node.add_child(game['name'], game_node)

    return root


def get_user_choice(options, prompt):
    print(prompt)
    for i, option in enumerate(options, start=1):
        print(f"{i}. {option}")
    choice = int(input("Enter your choice (number): "))
    return options[choice - 1]

def check_and_get_choice(options, level, tree, previous_choices):
    if options:
        return get_user_choice(options, f"Choose a {level}:")
    else:
        print(f"No games found matching your criteria for {' - '.join(previous_choices)}. Please try different selections.")
        exit()

def display_game_details(game_node):
    if not game_node.data:
        print("No game data available.")
        return

    game_data = game_node.data

    print(f"\nName: {game_data.get('name', 'No Title')}")

    genres = ', '.join(genre['name'] for genre in game_data.get('genres', [{'name': 'Unknown'}]))
    print(f"Genre: {genres}")

    platforms = ', '.join(platform['name'] for platform in game_data.get('platforms', [{'name': 'Unknown'}]))
    print(f"Platforms: {platforms}")

    themes = ', '.join(theme['name'] for theme in game_data.get('themes', [{'name': 'Unknown'}]))
    print(f"Themes: {themes}")

    release_year = str(game_data.get('release_dates', [{'y': 'Unknown'}])[0].get('y', 'Unknown'))
    print(f"Original Release Year: {release_year}")

def fetch_steam_game_details(game_name):
    try:
        query = '+'.join(game_name.split())
        search_url = f"https://store.steampowered.com/api/storesearch/?term={query}&cc=US&l=english"
        search_response = requests.get(search_url)
        if search_response.status_code != 200:
            print("Failed to search game on Steam.")
            return None

        search_results = search_response.json().get('items', [])
        
        steam_app_id = None
        for item in search_results:
            if game_name.lower() in item['name'].lower(): 
                steam_app_id = item['id']
                break

        if not steam_app_id:
            print("Game not found on Steam.")
            return None

        details_url = f"http://store.steampowered.com/api/appdetails?appids={steam_app_id}"
        details_response = requests.get(details_url)
        if details_response.status_code != 200:
            print("Failed to fetch game details from Steam.")
            return None

        game_details = details_response.json().get(str(steam_app_id), {}).get('data', None)
        return game_details if game_details else None
    
    except requests.exceptions.ConnectionError:
        print("Failed to connect to Steam API. Please check your connection or try again later.")
        return None
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
        return None



def display_steam_game_details(game_details):
    if game_details:
        print(f"\nSteam Game Details for {game_details.get('name', 'No Title')}:")

        price_info = game_details.get('price_overview', {})
        price = price_info.get('final_formatted', 'Price not available')
        print(f"Price: {price}")

        metacritic = game_details.get('metacritic', {}).get('score', 'Metacritic score not available')
        print(f"Metacritic Score: {metacritic}")

        header_image = game_details.get('header_image', 'Image not available')
        print(f"Header Image: {header_image}")

        required_age = game_details.get('required_age', 'Age rating not available')
        print(f"Required Age: {required_age}")

    else:
         print("Failed to fetch game details from Steam. This could be due to an API issue such as max retries exceeded. Please try again later.")

def get_user_choice(options, prompt):
    print(prompt)
    for i, option in enumerate(options, start=1):
        print(f"{i}. {option}")
    print("Type 'exit' to quit the program.")

    while True:
        user_input = input("Enter your choice (number) or 'exit': ").strip()
        if user_input.lower() == 'exit':
            print("Exiting program.")
            exit()

        try:
            choice = int(user_input)
            if 1 <= choice <= len(options):
                return options[choice - 1]
            else:
                print(f"Please enter a number between 1 and {len(options)}, or type 'exit' to quit.")
        except ValueError:
            print("Invalid input. Please enter a number or type 'exit' to quit.")

def get_numeric_input(prompt, min_val, max_val):
    while True:
        user_input = input(prompt).strip()
        if user_input.lower() == 'exit':
            print("Exiting program.")
            exit()

        if user_input.isdigit():
            user_choice = int(user_input)
            if min_val <= user_choice <= max_val:
                return user_choice
            else:
                print(f"Please enter a number between {min_val} and {max_val}, or type 'exit' to quit.")
        else:
            print("Invalid input. Please enter a number or type 'exit' to quit.")


def serialize_tree(node):
    if not node:
        return None

    serialized_node = {
        'name': node.name,
        'data': node.data,
        'children': {}
    }

    for key, child in node.children.items():
        serialized_node['children'][key] = serialize_tree(child)

    return serialized_node




def main():
    platform_names = ['PC (Microsoft Windows)', 'PlayStation 4', 'PlayStation 5', 'Xbox One', 'Nintendo Switch']
    
    cache_filename = 'games_cache.json'
    games = []

    if os.path.exists(cache_filename):
        print("Loading games from cache...")
        games = load_games_from_cache()
    else:
        try:
            access_token = get_access_token(client_id, client_secret)
            platform_ids = fetch_platform_ids(access_token, platform_names)
            games = fetch_games(access_token, list(platform_ids.values()))
            cache_games(games)
        except Exception as e:
            print(f"An error occurred: {e}")
            return 

    games_tree = build_games_tree(games, platform_names)

    # serialized_tree = serialize_tree(games_tree)
    # with open('tree_structure.json', 'w') as file:
    #     json.dump(serialized_tree, file, indent=4)

    platform_choice = check_and_get_choice(list(games_tree.children.keys()), "platform", games_tree, [])
    if platform_choice is None:
        return 
    genre_options = list(games_tree.children[platform_choice].children.keys())
    genre_choice = check_and_get_choice(genre_options, "genre", games_tree, [platform_choice])
    
    theme_options = list(games_tree.children[platform_choice].children[genre_choice].children.keys())
    theme_choice = check_and_get_choice(theme_options, "theme", games_tree, [platform_choice, genre_choice])

    current_year = datetime.datetime.now().year
    recent_years = [str(year) for year in range(current_year - 9, current_year + 1)] 
    release_year_options = sorted(
        [year for year in games_tree.children[platform_choice].children[genre_choice].children[theme_choice].children.keys() if year in recent_years],
        key=lambda x: (x.isdigit(), x),
        reverse=True
    )
    release_year_choice = check_and_get_choice(release_year_options, "original release year", games_tree, [platform_choice, genre_choice, theme_choice])

    selected_games_node = games_tree.children[platform_choice].children[genre_choice].children[theme_choice].children.get(release_year_choice)
    
    if selected_games_node and selected_games_node.children:
        print(f"\nGames list for {platform_choice} - {genre_choice} - {theme_choice} - {release_year_choice}:")
        for i, (game_name, game_node) in enumerate(selected_games_node.children.items(), start=1):
            print(f"{i}. {game_name}")
        print("Type 'exit' to quit the program.")

        while True:
            user_input = input("Enter the number of the game you want to view details for, or 'exit': ").strip()
            if user_input.lower() == 'exit':
                print("Exiting program.")
                exit()

            if user_input.isdigit():
                game_choice = int(user_input)
                if 1 <= game_choice <= len(selected_games_node.children):
                    selected_game_names = list(selected_games_node.children.keys())
                    selected_game_name = selected_game_names[game_choice - 1]
                    selected_game_node = selected_games_node.children[selected_game_name]
                    break
                else:
                    print(f"Please enter a number between 1 and {len(selected_games_node.children)}, or type 'exit' to quit.")
            else:
                print("Invalid input. Please enter a number or type 'exit' to quit.")
        
        display_game_details(selected_game_node)

        is_available_on_pc = any(platform.get('name') == 'PC (Microsoft Windows)' for platform in selected_game_node.data.get('platforms', []))

        if is_available_on_pc:
            while True:
                user_input = input("Do you want to search this game on Steam? (yes=1/no=0/exit): ").strip().lower()
                if user_input == 'exit':
                    print("Exiting program.")
                    exit()
                elif user_input in ['0', '1']:
                    search_steam = int(user_input)
                    break
                else:
                    print("Invalid input. Please enter '1' for yes, '0' for no, or 'exit' to quit.")

            if search_steam == 1:
                steam_game_details = fetch_steam_game_details(selected_game_node.data['name'])
                if steam_game_details:
                    display_steam_game_details(steam_game_details)
        else:
            print("No games found matching your criteria. Please try different selections.")



if __name__ == "__main__":
    main()