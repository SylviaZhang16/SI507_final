import requests
import json
import datetime

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
    tree = {}
    for game in games:
        for platform in game.get('platforms', []):
            platform_name = platform.get('name', 'Unknown')
            if platform_name in relevant_platforms:
                for genre in game.get('genres', [{'name': 'Unknown'}]):
                    genre_name = genre.get('name', 'Unknown')
                    for theme in game.get('themes', [{'name': 'Unknown'}]):
                        theme_name = theme.get('name', 'Unknown')
                        for release_date in game.get('release_dates', [{'y': 'Unknown'}]):
                            release_year = str(release_date.get('y', 'Unknown'))
                            if platform_name not in tree:
                                tree[platform_name] = {}
                            if genre_name not in tree[platform_name]:
                                tree[platform_name][genre_name] = {}
                            if theme_name not in tree[platform_name][genre_name]:
                                tree[platform_name][genre_name][theme_name] = {}
                            if release_year not in tree[platform_name][genre_name][theme_name]:
                                tree[platform_name][genre_name][theme_name][release_year] = []
                            if game not in tree[platform_name][genre_name][theme_name][release_year]:
                                tree[platform_name][genre_name][theme_name][release_year].append(game)
    return tree

# def build_tree_recursive(node, categories, game):
#     if not categories:
#         return

#     category, *remaining_categories = categories

#     for item in game.get(category, [{'name': 'Unknown'}]):
#         item_name = item.get('name', 'Unknown')
#         if item_name not in node:
#             node[item_name] = {}

#         if not remaining_categories:
#             node[item_name].setdefault('games', []).append(game)
#         else:
#             build_tree_recursive(node[item_name], remaining_categories, game)

# def build_games_tree(games, relevant_platforms):
#     tree = {}
#     categories = ['platforms', 'genres', 'themes', 'release_dates']

#     for game in games:
#         if 'platforms' in game and any(platform.get('name') in relevant_platforms for platform in game['platforms']):
#             build_tree_recursive(tree, categories, game)

#     return tree

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

def display_game_details(game):
    print(f"\nName: {game.get('name', 'No Title')}:")

    genres = [genre['name'] for genre in game.get('genres', [{'name': 'Unknown'}])]
    print(f"Genre: {', '.join(genres)}")

    platforms = [platform['name'] for platform in game.get('platforms', [{'name': 'Unknown'}])]
    print(f"Platforms: {', '.join(platforms)}")

    themes = [theme['name'] for theme in game.get('themes', [{'name': 'Unknown'}])]
    print(f"Themes: {', '.join(themes)}")

    release_year = game.get('release_dates', [{'y': 'Unknown'}])[0].get('y', 'Unknown')
    print(f"Original Release Year: {release_year}")


def fetch_steam_game_details(game_name):
    query = '+'.join(game_name.split())
    search_url = f"https://store.steampowered.com/api/storesearch/?term={query}&cc=US&l=english"
    search_response = requests.get(search_url)
    if search_response.status_code != 200:
        print("Failed to search game on Steam.")
        return None

    search_results = search_response.json().get('items', [])
    
    # Find the best match for the game
    steam_app_id = None
    for item in search_results:
        if game_name.lower() in item['name'].lower():  # Check for partial match
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
    return game_details


def display_steam_game_details(game_details):
    if game_details:
        print(f"\nSteam Game Details for {game_details.get('name')}:")
        print(f"Price: {game_details.get('price_overview', {}).get('final_formatted', 'Free or Unknown')}")
        print(f"Metacritic Score: {game_details.get('metacritic', {}).get('score', 'N/A')}")
        print(f"Header Image: {game_details.get('header_image', 'N/A')}")
        required_age = game_details.get('required_age', 'Not specified')
        print(f"Required Age: {required_age}")

        # detailed_description = game_details.get('detailed_description', 'Description not available.')
        # print(f"Detailed Description: {detailed_description}")
    else:
        print("No additional details available from Steam.")

def main():
    platform_names = ['PC (Microsoft Windows)', 'PlayStation 4', 'PlayStation 5', 'Xbox One', 'Nintendo Switch']
    try:
        access_token = get_access_token(client_id, client_secret)
        
        platform_ids = fetch_platform_ids(access_token, platform_names)
        games = fetch_games(access_token, list(platform_ids.values()))
        cache_games(games)
    except Exception as e:
        print(f"An error occurred: {e}")
        games = load_games_from_cache()  # Load from cache if fetching fails

    games_tree = build_games_tree(games, platform_names)

    platform_choice = check_and_get_choice(list(games_tree.keys()), "platform", games_tree, [])
    genre_options = list(games_tree[platform_choice].keys())
    genre_choice = check_and_get_choice(genre_options, "genre", games_tree, [platform_choice])
    
    theme_options = list(games_tree[platform_choice][genre_choice].keys())
    theme_choice = check_and_get_choice(theme_options, "theme", games_tree, [platform_choice, genre_choice])

    current_year = datetime.datetime.now().year
    release_years = [str(year) for year in range(current_year - 5, current_year + 1)]
    release_year_choice = check_and_get_choice(release_years, "release year on this platform", games_tree, [platform_choice, genre_choice, theme_choice])

    selected_games = games_tree[platform_choice][genre_choice][theme_choice].get(release_year_choice, [])
    if selected_games:
        print(f"\nGames list for {platform_choice} - {genre_choice} - {theme_choice} - {release_year_choice}:")
        for i, game in enumerate(selected_games, start=1):
            print(f"{i}. {game['name']}")

        try:
            game_choice = int(input("Enter the number of the game you want to view details for: "))
            if 1 <= game_choice <= len(selected_games):
                selected_game = selected_games[game_choice - 1]
                display_game_details(selected_game)

                # Fetch and display Steam details if the game is on PC
                if 'PC (Microsoft Windows)' in [platform['name'] for platform in selected_game.get('platforms', [])]:
                    steam_game_details = fetch_steam_game_details(selected_game['name'])
                    display_steam_game_details(steam_game_details)
            else:
                print("Invalid selection. Please choose a valid game number.")
        except ValueError:
            print("Invalid input. Please enter a number.")
    else:
        print("No games found matching your criteria. Please try different selections.")


if __name__ == "__main__":
    main()