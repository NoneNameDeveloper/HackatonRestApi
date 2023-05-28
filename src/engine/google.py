from googleapiclient.discovery import build


api_key = 'AIzaSyCtGE_QI_PU09bF7uAxKb4UgPfaVW_DmD8'

service = build("customsearch", "v1", developerKey=api_key)

def search_links(query: str) -> list[str]:
    res = service.cse().list(q=query, cx='86165028723124a88').execute()
    return [item['link'] for item in res['items']]
