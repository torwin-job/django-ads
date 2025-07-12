import requests
from rich.console import Console
from rich.table import Table
from rich.theme import Theme
import json

BASE_URL = "http://127.0.0.1:8000/api"
console = Console(theme=Theme({"success": "green", "error": "bold red", "info": "cyan"}), width=120, style="dim")

def smart_shorten_response(resp):
    try:
        data = resp.json()
    except Exception:
        return str(resp.text)[:60]
    # Если список
    if isinstance(data, list):
        if len(data) == 0:
            return "[]"
        if isinstance(data[0], dict) and "id" in data[0]:
            ids = [str(x.get("id")) for x in data[:2]]
            return f"list[{len(data)}] id: {', '.join(ids)}"
        return f"list[{len(data)}]"
    # Если словарь с results (пагинация)
    if isinstance(data, dict) and "results" in data:
        results = data["results"]
        if isinstance(results, list) and results and isinstance(results[0], dict) and "id" in results[0]:
            ids = [str(x.get("id")) for x in results[:2]]
            return f"results[{len(results)}] id: {', '.join(ids)} count: {data.get('count')}"
        return f"results[{len(results)}] count: {data.get('count')}"
    # Если обычный объект
    keys_priority = ["id", "username", "status", "detail", "count", "message"]
    short = []
    for k in keys_priority:
        if k in data:
            short.append(f"{k}: {data[k]}")
    if short:
        return ", ".join(short)
    # Если ничего не подошло, просто первые 60 символов
    return json.dumps(data, ensure_ascii=False)[:60]

def print_request_result(name, method, url, params=None, data=None, headers=None, resp=None):
    table = Table(show_header=True, header_style="bold magenta", box=None, show_lines=False, pad_edge=False)
    table.add_column("Step", style="dim", width=14, no_wrap=True)
    table.add_column("Meth", style="cyan", width=4, no_wrap=True)
    table.add_column("URL", style="yellow", width=48, no_wrap=True)
    table.add_column("St", style="bold", width=3, no_wrap=True)
    table.add_column("Result", style="white", width=60, no_wrap=True)
    status_color = "success" if resp is not None and resp.status_code in (200, 201, 205) else "error"
    result = smart_shorten_response(resp) if resp is not None else ""
    table.add_row(
        name,
        method,
        url,
        f"[{status_color}]{resp.status_code if resp else ''}[/{status_color}]",
        result
    )
    console.print(table)
    # Вывод полного результата (только 1-2 значения, остальные скрыты)
    if resp is not None:
        try:
            data = resp.json()
            # Если список
            if isinstance(data, list):
                show = data[:2]
                console.print("[info]Первые элементы:[/info]")
                for item in show:
                    console.print_json(json.dumps(item, ensure_ascii=False), highlight=True)
                if len(data) > 2:
                    console.print(f"[dim]... и ещё {len(data)-2}[/dim]")
            # Если results
            elif isinstance(data, dict) and "results" in data and isinstance(data["results"], list):
                show = data["results"][:2]
                console.print("[info]Первые элементы results:[/info]")
                for item in show:
                    console.print_json(json.dumps(item, ensure_ascii=False), highlight=True)
                if len(data["results"]) > 2:
                    console.print(f"[dim]... и ещё {len(data['results'])-2}[/dim]")
                # Показываем count, если есть
                if "count" in data:
                    console.print(f"[info]count: {data['count']}[/info]")
            # Если обычный объект
            else:
                console.print_json(json.dumps(data, ensure_ascii=False), highlight=True)
        except Exception:
            console.print(resp.text, style="error")

def api_request(name, method, url, params=None, data=None, headers=None):
    full_url = BASE_URL + url
    resp = requests.request(method, full_url, params=params, json=data, headers=headers)
    print_request_result(name, method, full_url, params, data, headers, resp)
    return resp

def main():
    reg_data = {"username": "apitestuser", "password": "apitestpass"}
    api_request("Register", "POST", "/register/", data=reg_data)
    login_data = {"username": "apitestuser", "password": "apitestpass"}
    r = api_request("Login", "POST", "/token/", data=login_data)
    tokens = r.json()
    access = tokens.get("access")
    refresh = tokens.get("refresh")
    headers = {"Authorization": f"Bearer {access}"}

    ad_data = {"title": "API Test Ad", "description": "Test", "category": "Test", "condition": "new"}
    r = api_request("Create Ad", "POST", "/ads/", data=ad_data, headers=headers)
    if r.status_code != 201: return
    ad_id = r.json().get("id")

    api_request("List Ads", "GET", "/ads/", headers=headers)
    api_request("Indicators", "POST", "/ads/exchange_indicators/", data={"ad_ids": [ad_id]}, headers=headers)

    reg_data2 = {"username": "apitestuser2", "password": "apitestpass2"}
    api_request("Register2", "POST", "/register/", data=reg_data2)
    r2 = api_request("Login2", "POST", "/token/", data=reg_data2)
    tokens2 = r2.json()
    access2 = tokens2.get("access")
    headers2 = {"Authorization": f"Bearer {access2}"}
    ad_data2 = {"title": "API Test Ad 2", "description": "Test2", "category": "Test", "condition": "used"}
    r = api_request("Create Ad2", "POST", "/ads/", data=ad_data2, headers=headers2)
    if r.status_code != 201: return
    ad_id2 = r.json().get("id")

    proposal_data = {"ad_sender": ad_id2, "ad_receiver": ad_id, "status": "pending", "comment": "Тест"}
    r = api_request("Create Proposal", "POST", "/proposals/", data=proposal_data, headers=headers2)
    if r.status_code != 201: return
    proposal_id = r.json().get("id")

    api_request("List Proposals", "GET", "/proposals/", headers=headers)
    for status_value in ["accepted", "rejected", "pending"]:
        api_request(f"Set Status:{status_value}", "POST", f"/proposals/{proposal_id}/set_status/", data={"status": status_value}, headers=headers)
    api_request("Logout", "POST", "/logout/", data={"refresh": refresh}, headers=headers)

    # Пагинация
    for i in range(5):
        ad_data_pag = {"title": f"PagAd{i}", "description": "desc", "category": "cat", "condition": "new"}
        requests.post(f"{BASE_URL}/ads/", json=ad_data_pag, headers=headers)
    api_request("Ads Page 1", "GET", "/ads/", headers=headers)
    api_request("Ads Page 2", "GET", "/ads/", params={"page": 2}, headers=headers)

    # Поиск
    api_request("Search Ads q=PagAd1", "GET", "/ads/", params={"q": "PagAd1"}, headers=headers)
    api_request("Search Ads category=cat", "GET", "/ads/", params={"category": "cat"}, headers=headers)
    api_request("Search Ads q=API Test Ad", "GET", "/ads/", params={"q": "API Test Ad"}, headers=headers)
    api_request("Search Ads q=Test&category=cat", "GET", "/ads/", params={"q": "Test", "category": "cat"}, headers=headers)
    api_request("Search Proposals status=pending", "GET", "/proposals/", params={"status": "pending"}, headers=headers)
    api_request("Search Proposals q=Тестовый", "GET", "/proposals/", params={"q": "Тестовый"}, headers=headers)
    api_request("Search Proposals status=accepted", "GET", "/proposals/", params={"status": "accepted"}, headers=headers)
    api_request("Search Proposals q=PagAd", "GET", "/proposals/", params={"q": "PagAd"}, headers=headers)

if __name__ == "__main__":
    main()
