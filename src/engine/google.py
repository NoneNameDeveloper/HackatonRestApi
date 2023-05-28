from googleapiclient.discovery import build


api_key = 'AIzaSyDYm3RMp-tdVHB1nDolab2-QW75ZOT-sHs'

service = build("customsearch", "v1", developerKey=api_key)


def search_links(query: str) -> list[str]:
    res = service.cse().list(q=query, cx='86165028723124a88').execute()
    return [item['link'] for item in res['items']]
