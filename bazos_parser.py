import requests
from bs4 import BeautifulSoup
import json
import re
import pandas as pd
import argparse

def get_ad_links(url):
    print(url)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    links = []

    nadpises = soup.find_all('h2', class_='nadpis')
    for nadpis in nadpises:
        links.append('https://auto.bazos.cz' + nadpis.find('a')['href'])
    return links


def find_part(parts: list, pattern: str):
    return [x for x in parts if pattern in x][0].replace(pattern, '')


def get_phone_id(soup):
    # id of phone:
    span = soup.find('span', class_='teldetail')
    # Extract the value of the onclick attribute from the span
    onclick = span['onclick']
    # Use regular expression to match `idphone=3093275`
    match = re.search('idphone=(\d+)', onclick)
    if match:
        phone_id = match.group(1)
    return phone_id


def get_description_parts(soup):
    meta_tag = soup.find('meta', attrs={'name': 'description'})
    content = meta_tag['content']
    parts = content.split(", ")
    return parts


def get_mileage(soup):
    popis = soup.find('div', class_='popis').text
    pattern = r'\d+(?: \d+)*(?: tis)? km'
    match = re.search(pattern, popis)

    if match:
        return match.group()
    else:
        return ''


def parse_json_from_html(url):
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')

    # From description
    description_parts = get_description_parts(soup)
    make_and_model = description_parts[0][description_parts[0].find(':') + 2:].split(' ')
    price = find_part(description_parts, 'Cena: ')
    branch_location = find_part(description_parts, 'Lokalita: ')

    mileage = get_mileage(soup)

    phone_id = get_phone_id(soup)

    # Constructing JSON
    result_json = {
        "phone_number": "",
        "gpt_make_fon": make_and_model[0],
        "gpt_model_fon": make_and_model[1],
        "customer_name": '',
        "customer_surname": '',
        "user_salutation": "",
        "gender": "",
        "car_mileage_range": "",
        "car_fuel": "diesel",
        "initial_message_outbound": "string",
        "initial_message_nr_inbound": "string",
        "car_manufacture_year": None,
        "users_car_price": price,
        "prerecord": True,
        "from_phone": "420910920502",
        "id": phone_id,
        "prompt_template_filename": "outbound_ticking_single_prompt.json",
        "branch_location": branch_location,
        "url": url
    }

    return result_json


def parse_json(base_url, n, count):
    json_list = []
    for i in range(count):
        url = base_url + str(n + i * 20) + '/'
        ad_links = get_ad_links(url)
        for link in ad_links:
            result_json = parse_json_from_html(link)
            # print(result_json)
            json_list.append(result_json)
    return json_list


def main():
    parser = argparse.ArgumentParser(__doc__)
    parser.add_argument("--base_url", type=str, default='https://auto.bazos.cz/')
    parser.add_argument("-c", "--count", type=str, default=3)
    args = parser.parse_args()
    n = 100
    count = args.n
    json_list = parse_json(args.base_url, n, count)
    df = pd.DataFrame(json_list)
    vc = df['id'].value_counts()
    vc_unique = vc[vc.values == 1]
    df = df[df['id'].isin(vc_unique.index)]
    print(df)
    for i, line in df.iterrows():
        print(line.to_dict())


if __name__ == '__main__':
    main()
