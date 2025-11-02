PLATFORM_TO_REGION = {
    "euw1": "europe",
    "eune1": "europe",
    "tr1": "europe",
    "ru": "europe",
    "me1": "europe",
    "na1": "americas",
    "br1": "americas",
    "la1": "americas",
    "la2": "americas",
    "kr": "asia",
    "jp1": "asia",
    "oc1": "sea",
    "sg2": "sea",
    "tw2": "sea",
    "vn2": "sea",
}

PLATFORM_NAMES = {
    "euw1": "Europe West",
    "eune1": "Europe Nordic & East",
    "tr1": "Turkey",
    "ru": "Russia",
    "me1": "Middle East",
    "na1": "North America",
    "br1": "Brazil",
    "la1": "Latin America North",
    "la2": "Latin America South",
    "kr": "Korea",
    "jp1": "Japan",
    "oc1": "Oceania",
    "sg2": "Singapore",
    "tw2": "Taiwan",
    "vn2": "Vietnam",
}


def get_region_from_platform(platform):
    return PLATFORM_TO_REGION.get(platform.lower())


def is_valid_platform(platform):
    return platform.lower() in PLATFORM_TO_REGION


def get_all_platforms():
    return [(code, PLATFORM_NAMES[code]) for code in sorted(PLATFORM_TO_REGION.keys())]


def group_platforms_by_region():
    grouped = {}
    for platform, name in get_all_platforms():
        region = PLATFORM_TO_REGION[platform]
        if region not in grouped:
            grouped[region] = []
        grouped[region].append((platform, name))
    return grouped


def display_region_menu():
    print("\n" + "=" * 60)
    print("  SELECT YOUR REGION")
    print("=" * 60 + "\n")

    grouped = group_platforms_by_region()
    options = {}
    idx = 1

    for region in ["europe", "americas", "asia", "sea"]:
        if region in grouped:
            print(f"\n{region.upper()}:")
            for platform, name in grouped[region]:
                print(f"  {idx}. {name} ({platform})")
                options[idx] = (platform, region)
                idx += 1

    print(f"\n  0. Cancel\n")
    return options


def get_user_choice(options):
    while True:
        try:
            choice = input("Enter your choice: ").strip()
            choice_num = int(choice)

            if choice_num == 0:
                return None, None

            if choice_num in options:
                platform, region = options[choice_num]
                print(f"\nSelected: {PLATFORM_NAMES[platform]} ({platform})")
                return platform, region

            print(f"Please enter a number between 0 and {len(options)}.")
        except ValueError:
            print("Please enter a valid number.")
        except KeyboardInterrupt:
            print("\n\nCancelled.")
            return None, None


def prompt_for_region():
    options = display_region_menu()
    return get_user_choice(options)


def auto_configure_region(platform):
    platform = platform.lower()
    if is_valid_platform(platform):
        region = get_region_from_platform(platform)
        return platform, region
    return None, None


def get_region_config(platform=None):
    if platform:
        config = auto_configure_region(platform)
        if config[0]:
            return config
        print(f"Invalid platform: {platform}")

    return prompt_for_region()
