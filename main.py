import json
from fastapi import FastAPI, Request, HTTPException # type: ignore
from fastapi.responses import RedirectResponse, JSONResponse # type: ignore
import os
from dotenv import load_dotenv
import requests
import logging

app = FastAPI()
load_dotenv()

SCOPES = os.getenv('SCOPES')
REDIRECT_URL = os.getenv('REDIRECT_URL')


tenant_id = os.getenv('TENANT_ID')
CLIENT_ID = os.getenv('CLIENT_ID')
CLIENT_SECRET = os.getenv('CLIENT_SECRET')
redirect_uri = os.getenv('REDIRECT_URI')

if not all([CLIENT_ID, CLIENT_SECRET, SCOPES, REDIRECT_URL]):
    raise EnvironmentError("Missing one or more required environment variables (CLIENT_ID, CLIENT_SECRET, SCOPES, REDIRECT_URL)")

def get_tokens_from_file():
    try:
        with open('tokensFile.json', 'r') as f:
            tokens = json.load(f)
    except FileNotFoundError:
        tokens = {'access_token': None, 'refresh_token': None}
    return tokens.get('refresh_token').strip(), tokens.get('access_token').strip()

def save_tokens_to_file(access_token, refresh_token):
    tokens = {
        'access_token': access_token,
        'refresh_token': refresh_token
    }
    with open('tokensFile.json', 'w') as f:
        json.dump(tokens, f)

def get_access_token(code: str):
    token_url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
    payload = {
        'client_id': CLIENT_ID,
        'scope': SCOPES,
        'redirect_uri': REDIRECT_URL,
        'code': code,
        'grant_type': 'authorization_code',
        'client_secret': CLIENT_SECRET
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(token_url, data=payload, headers=headers)
    
    print(response.json())
    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens.get('access_token')
        print("\nAccess Token : ",access_token,"\n")
        refresh_token = tokens.get('refresh_token')
        save_tokens_to_file(access_token, refresh_token)
        return access_token, refresh_token
    else:
        return None, None

def refresh_access_token(refresh_token: str):
    token_url = "https://login.microsoftonline.com/consumers/oauth2/v2.0/token"
    payload = {
        'client_id': CLIENT_ID,
        'scope': SCOPES,
        'refresh_token': refresh_token,
        'grant_type': 'refresh_token',
        'client_secret': CLIENT_SECRET
    }
    headers = {
        'Content-Type': 'application/x-www-form-urlencoded'
    }
    response = requests.post(token_url, data=payload, headers=headers)
    print("response : ", response.status_code)
    if response.status_code == 200:
        tokens = response.json()
        access_token = tokens.get('access_token')
        save_tokens_to_file(access_token, refresh_token)
        return access_token
    else:
        try:
            error_response = response.json()
        except json.JSONDecodeError:
            error_response = response.text
        print("Refresh token request failed:", error_response)
        return None
    # url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    # payload = {
    #     "client_id": CLIENT_ID,
    #     "grant_type": "refresh_token",
    #     "scope": SCOPES,
    #     "refresh_token": refresh_token,
    #     "redirect_uri": REDIRECT_URL,
    #     "client_secret": CLIENT_SECRET
    # }
    # logging.debug(f"Payload: {payload}")
    
    # response = requests.post(url, data=payload)
    
    # print("response :", response.json())
    # if response.status_code == 200:
    #     new_tokens = response.json()
    #     with open("tokens.json", "w") as token_file:
    #         json.dump(new_tokens, token_file)
    #     return new_tokens.get("access_token")
    # else:
    #     return None


@app.post("/refresh_token")
async def refresh_token():
    refresh_token, _ = get_tokens_from_file()
    if not refresh_token:
        raise HTTPException(status_code=400, detail="Refresh token is missing")
    
    print("refresh Token :",refresh_token)
    new_access_token = refresh_access_token(refresh_token)
    if new_access_token:
        return JSONResponse(status_code=200, content={"message": "Access token refreshed successfully"})
    else:
        return JSONResponse(status_code=500, content={"error": "Failed to refresh access token"})



@app.get("/oauth_redirect")
async def oauth_redirect():
    SCOPES_ = SCOPES.replace(" ", "%20")
    redirect_url = (
        "https://login.microsoftonline.com/consumers/oauth2/v2.0/authorize"
        "?scope=" + SCOPES_ +
        "&response_type=code"
        "&response_mode=query"
        "&state=outlookcalendarsync"
        "&redirect_uri=" + REDIRECT_URL +
        "&client_id=" + CLIENT_ID
    )
    return RedirectResponse(redirect_url)

@app.get("/oauth/callback")
async def callback(code: str = None, state: str = None, error: str = None, error_description: str = None):
    if error:
        return JSONResponse(status_code=400, content={"error": error, "description": error_description})
    
    if not code:
        return JSONResponse(status_code=400, content={"error": "No authorization code received"})
    
    access_token, refresh_token = get_access_token(code)
    if access_token and refresh_token:
        return JSONResponse(status_code=200, content={"message": "Token received successfully"})
    else:
        return JSONResponse(status_code=500, content={"error": "Failed to fetch tokens"})

@app.post("/create_event")
async def create_event(request: Request):
    # access_token, _ = get_tokens_from_file()
    access_token = 'EwBoA8l6BAAUbDba3x2OMJElkF7gJ4z/VbCPEz0AAVXSYpVGDvlYo38hXAWd1Onf6hdnRZjC8w0frOKTOlj3P0/oK1lOEjIX1S6qx6tosDFGNlHp1Xp4T2vG9gkCcmARG/zhBh2Gyu9nR9FMQxyKaX28sN/yDxscN0h/a1dHAm0ukDJ3YicIe5C8fjLP014oXe0J2BU1LgmAYpPepWpvJIWi14kiZumPYJhceIrUYAMSBtgbjDnlyApNlX1fXZbF/GGmiO7UIDoQhwMBKlYp6w55sUl+/JbGwmRi7sh25sYYL+r+jhVthVWw6OA+5SjMupAnF5ws5ViAgNc7hrZrCp/xYINb3ucgSHrlbBAiX5dJOxzHteeq+gotJhi87GEDZgAACECtL9yQm7ZfOAL/IWD46MzoHi9kwVXkxP+85KH3A54beRsWRwc/oRfMcLsEBfI97YCa5UJY5Y549moY7CqYDZhZznXM86+mBNVldlXvcY/90mv/zfJ2fJNREZoQEsjYvAXqBEZY/LOWIUz8Ur1Pshha1gFGRCWQrqCcQxGtt36T1sayGf3CSdljYOKD8u9txDKee1m3Jptd1HLfQ1kmNJnkCDuQoifLE+6IrKdkyzIjghhdzBdxeB+Kl+XXVMAV+Y8lcAjOkgPmYnXxJn2Tin2Q7eLS6u9SXfjpT5gXRifGIEZE70ZI82L9REcSnoG7PxIJHWqprNUDEKbaQFPneF3ZD1Un7jQS66Cy4PuRsBK9IsfkMTYgXobBgLWGv5tLBeqEjspte/4i+aUVfr/9/sD7CBMRBhY4E6cYa0N72QDyg4v3+SisEXJopwFrgTCZ3R1OPN1WXunOzeyo1dVBlwiM9VGnLR8FO9LXwCHHkGQZ7wNyxeKcw7Xr9uoDt8ahFpznqJ3LQ8IpWRDAJp0fc93I8IZFun+mIXNP4DMJisy2M2hvXi08tJDW2t6P8S5WaKXT2rm/Exp4ZH5GGz4B1cIQWbf7FQpuz36Lhelteepz+qUjwcTe+M6I4GBfdC3nBGwxy5goXP1uWnLoGQtMpIpmDkaQwAy+ZDYvRagXV02m7p0iWPmXKxam2ftdEIXVY4eYJ1dmie4EMOLTogj47RVdbuW2dIPdjQ+sE/T63aJVJgXDaBDmOAdkWbBuzVl9TkyyfAI='
    # access_token = 'eyJ0eXAiOiJKV1QiLCJub25jZSI6IjlYTks2NkVlWml0cTdwQ1FST0pWSUZuS3VwSHlWbWtzUmk0V0wwMjZxN2ciLCJhbGciOiJSUzI1NiIsIng1dCI6InE3UDFOdnh1R1F3RE4yVGFpTW92alo4YVp3cyIsImtpZCI6InE3UDFOdnh1R1F3RE4yVGFpTW92alo4YVp3cyJ9.eyJhdWQiOiJodHRwczovL2dyYXBoLm1pY3Jvc29mdC5jb20iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC81MDQzNzRlMi1hOTY5LTQyZTAtYTVkYi1lN2Y5M2VhMmRiZGYvIiwiaWF0IjoxNzE4OTQwODQzLCJuYmYiOjE3MTg5NDA4NDMsImV4cCI6MTcxODk0NDc0MywiYWlvIjoiRTJkZ1lEQmZ4dURmKytMU05PNHY2bTUvdi9NdUFBQT0iLCJhcHBfZGlzcGxheW5hbWUiOiJUZXN0Q2FsZW5kYXJCbG9jayIsImFwcGlkIjoiNDBlNjAzYTctZTE0NC00NjRlLWFhZWYtYTJlOWQyMGY0NzY0IiwiYXBwaWRhY3IiOiIxIiwiaWRwIjoiaHR0cHM6Ly9zdHMud2luZG93cy5uZXQvNTA0Mzc0ZTItYTk2OS00MmUwLWE1ZGItZTdmOTNlYTJkYmRmLyIsImlkdHlwIjoiYXBwIiwib2lkIjoiM2MxYjhiY2YtZTZiYi00YTg1LWExMjEtMGFlYWUyM2QzMDZjIiwicmgiOiIwLkFXUUE0blJEVUdtcDRFS2wyLWY1UHFMYjN3TUFBQUFBQUFBQXdBQUFBQUFBQUFCbEFBQS4iLCJyb2xlcyI6WyJVc2VyLlJlYWQuQWxsIiwiQ2FsZW5kYXJzLlJlYWRXcml0ZSJdLCJzdWIiOiIzYzFiOGJjZi1lNmJiLTRhODUtYTEyMS0wYWVhZTIzZDMwNmMiLCJ0ZW5hbnRfcmVnaW9uX3Njb3BlIjoiQVMiLCJ0aWQiOiI1MDQzNzRlMi1hOTY5LTQyZTAtYTVkYi1lN2Y5M2VhMmRiZGYiLCJ1dGkiOiJtT20zUDE2SkNVaUFCakgwTXVKRkFBIiwidmVyIjoiMS4wIiwid2lkcyI6WyIwOTk3YTFkMC0wZDFkLTRhY2ItYjQwOC1kNWNhNzMxMjFlOTAiXSwieG1zX2lkcmVsIjoiOCA3IiwieG1zX3RjZHQiOjE2MDI3NTM5MjN9.ro2dOsk3qPjdVjHoMBzHM9Jn2NI9qv6_9223ZsblAw7nmqcoKbeOyi0LL-gtke0qyQIQxST5GVCR8j7drrid-rzWpTDKAQdrRB9iyvF75V2qA1sUkxAuvEjnRDdkU7HeMvQZrjp0NYG5o4oQImi997kfFCULq6-9zvbhbIa14ztlkrrvQZMNNj7WVNOPk8Lb8Y6jV_2o3URO3o5FUDYco8b1a03DLwclGAGKt7CRntnrK4kajilYt31yLG7I7wYIKU8oWbI-qNgeYlUDiBC9rTeIStOnPcoDne4iKjyI54oxkE66-4IXz0Wp_XVIevkEQxPaz1cPms-LcbOPjP3W7w'
    if not access_token:
        raise HTTPException(status_code=400, detail="Access token is missing")

    calendar_event = await request.json()

    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    response = requests.post(
        'https://graph.microsoft.com/v1.0/me/calendar/events',
        headers=headers,
        json=calendar_event  # Use json parameter directly
    )
    # response = requests.post(
    #     'https://graph.microsoft.com/v1.0/users/admin@Srieshwarcollegeofengine063.onmicrosoft.com/events',
    #     headers=headers,
    #     json=calendar_event  # Use json parameter directly
    # )

    if response.status_code == 201:
        return JSONResponse(status_code=201, content={"message": "Event created successfully"})
    else:
        error_description = response.json().get('error', {}).get('message', 'Unknown error')
        raise HTTPException(status_code=response.status_code, detail={"error": "Failed to create event", "description": error_description})

@app.get("/allevents")
async def all_events():
    try:
        access_token, _ = get_tokens_from_file()
        # access_token = 'eyJ0eXAiOiJKV1QiLCJub25jZSI6ImZLdnNhTnpfNjBzNXp2NDlLbUUxWVlHNUJ6c0IyQjFjSUIwcTdXRkdjMjAiLCJhbGciOiJSUzI1NiIsIng1dCI6InE3UDFOdnh1R1F3RE4yVGFpTW92alo4YVp3cyIsImtpZCI6InE3UDFOdnh1R1F3RE4yVGFpTW92alo4YVp3cyJ9.eyJhdWQiOiJodHRwczovL2dyYXBoLm1pY3Jvc29mdC5jb20iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC81MDQzNzRlMi1hOTY5LTQyZTAtYTVkYi1lN2Y5M2VhMmRiZGYvIiwiaWF0IjoxNzE4ODg5Nzg2LCJuYmYiOjE3MTg4ODk3ODYsImV4cCI6MTcxODg5MzY4NiwiYWlvIjoiRTJkZ1lEaWI4dHlKTVh1cGwydEU3cWtsSmRPZUFBQT0iLCJhcHBfZGlzcGxheW5hbWUiOiJUZXN0Q2FsZW5kYXJCbG9jayIsImFwcGlkIjoiNDBlNjAzYTctZTE0NC00NjRlLWFhZWYtYTJlOWQyMGY0NzY0IiwiYXBwaWRhY3IiOiIxIiwiaWRwIjoiaHR0cHM6Ly9zdHMud2luZG93cy5uZXQvNTA0Mzc0ZTItYTk2OS00MmUwLWE1ZGItZTdmOTNlYTJkYmRmLyIsImlkdHlwIjoiYXBwIiwib2lkIjoiM2MxYjhiY2YtZTZiYi00YTg1LWExMjEtMGFlYWUyM2QzMDZjIiwicmgiOiIwLkFXUUE0blJEVUdtcDRFS2wyLWY1UHFMYjN3TUFBQUFBQUFBQXdBQUFBQUFBQUFCbEFBQS4iLCJyb2xlcyI6WyJVc2VyLlJlYWQuQWxsIiwiQ2FsZW5kYXJzLlJlYWRXcml0ZSJdLCJzdWIiOiIzYzFiOGJjZi1lNmJiLTRhODUtYTEyMS0wYWVhZTIzZDMwNmMiLCJ0ZW5hbnRfcmVnaW9uX3Njb3BlIjoiQVMiLCJ0aWQiOiI1MDQzNzRlMi1hOTY5LTQyZTAtYTVkYi1lN2Y5M2VhMmRiZGYiLCJ1dGkiOiI1dFZfZGhxeWIwNkJlck9nbFJzU0FBIiwidmVyIjoiMS4wIiwid2lkcyI6WyIwOTk3YTFkMC0wZDFkLTRhY2ItYjQwOC1kNWNhNzMxMjFlOTAiXSwieG1zX2lkcmVsIjoiNyAyIiwieG1zX3RjZHQiOjE2MDI3NTM5MjN9.uW57SWCvfvcd93cB7TK30h3bQus8_2jQSN3Dnmb3pLQ2mZrMpzKf_9-_q5xbud6NLOIwwUZzoOM06KgiHCN7i0FpqcB2K5D2CyMcUPGTh7pCK2-s72w-6OK3PM17ZBpJM4chJr45BHeWQ-52-rhTPvjcAcv2j7tpQEBPtLq-lo1kGTBuLPOU8YoJfDAUgDnUPqBThmm2THsVQ1CCI-zUQx33xCRro7bcJjtYXjxRjJW7HNXHLN9x6AfwvamqPYg-lvMIsLXy7qJ-mNlYja5EDhkw1Zqq3SLnpTiDV8Y7umVIIfFevXkbUXFOAppqf_72PfF2iF9Qixj2Mn-4Vxv54g'
    
        if not access_token:
            raise HTTPException(status_code=400, detail="Access token is missing")

        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        url = 'https://graph.microsoft.com/v1.0/me/calendar/events'
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            events_list = response.json()
            calendar_events = events_list['value']
            return calendar_events
        else:
            return JSONResponse(status_code=response.status_code, content={"error": "Failed to fetch events", "status_code": response.status_code, "response": response.json()})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "An exception occurred", "message": str(e)})

@app.post("/events")
async def events(request: Request):
    try:
        data = await request.json()
        eventId = data.get('eventId')
        # access_token, _ = get_tokens_from_file()
        access_token = 'eyJ0eXAiOiJKV1QiLCJub25jZSI6ImZLdnNhTnpfNjBzNXp2NDlLbUUxWVlHNUJ6c0IyQjFjSUIwcTdXRkdjMjAiLCJhbGciOiJSUzI1NiIsIng1dCI6InE3UDFOdnh1R1F3RE4yVGFpTW92alo4YVp3cyIsImtpZCI6InE3UDFOdnh1R1F3RE4yVGFpTW92alo4YVp3cyJ9.eyJhdWQiOiJodHRwczovL2dyYXBoLm1pY3Jvc29mdC5jb20iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC81MDQzNzRlMi1hOTY5LTQyZTAtYTVkYi1lN2Y5M2VhMmRiZGYvIiwiaWF0IjoxNzE4ODg5Nzg2LCJuYmYiOjE3MTg4ODk3ODYsImV4cCI6MTcxODg5MzY4NiwiYWlvIjoiRTJkZ1lEaWI4dHlKTVh1cGwydEU3cWtsSmRPZUFBQT0iLCJhcHBfZGlzcGxheW5hbWUiOiJUZXN0Q2FsZW5kYXJCbG9jayIsImFwcGlkIjoiNDBlNjAzYTctZTE0NC00NjRlLWFhZWYtYTJlOWQyMGY0NzY0IiwiYXBwaWRhY3IiOiIxIiwiaWRwIjoiaHR0cHM6Ly9zdHMud2luZG93cy5uZXQvNTA0Mzc0ZTItYTk2OS00MmUwLWE1ZGItZTdmOTNlYTJkYmRmLyIsImlkdHlwIjoiYXBwIiwib2lkIjoiM2MxYjhiY2YtZTZiYi00YTg1LWExMjEtMGFlYWUyM2QzMDZjIiwicmgiOiIwLkFXUUE0blJEVUdtcDRFS2wyLWY1UHFMYjN3TUFBQUFBQUFBQXdBQUFBQUFBQUFCbEFBQS4iLCJyb2xlcyI6WyJVc2VyLlJlYWQuQWxsIiwiQ2FsZW5kYXJzLlJlYWRXcml0ZSJdLCJzdWIiOiIzYzFiOGJjZi1lNmJiLTRhODUtYTEyMS0wYWVhZTIzZDMwNmMiLCJ0ZW5hbnRfcmVnaW9uX3Njb3BlIjoiQVMiLCJ0aWQiOiI1MDQzNzRlMi1hOTY5LTQyZTAtYTVkYi1lN2Y5M2VhMmRiZGYiLCJ1dGkiOiI1dFZfZGhxeWIwNkJlck9nbFJzU0FBIiwidmVyIjoiMS4wIiwid2lkcyI6WyIwOTk3YTFkMC0wZDFkLTRhY2ItYjQwOC1kNWNhNzMxMjFlOTAiXSwieG1zX2lkcmVsIjoiNyAyIiwieG1zX3RjZHQiOjE2MDI3NTM5MjN9.uW57SWCvfvcd93cB7TK30h3bQus8_2jQSN3Dnmb3pLQ2mZrMpzKf_9-_q5xbud6NLOIwwUZzoOM06KgiHCN7i0FpqcB2K5D2CyMcUPGTh7pCK2-s72w-6OK3PM17ZBpJM4chJr45BHeWQ-52-rhTPvjcAcv2j7tpQEBPtLq-lo1kGTBuLPOU8YoJfDAUgDnUPqBThmm2THsVQ1CCI-zUQx33xCRro7bcJjtYXjxRjJW7HNXHLN9x6AfwvamqPYg-lvMIsLXy7qJ-mNlYja5EDhkw1Zqq3SLnpTiDV8Y7umVIIfFevXkbUXFOAppqf_72PfF2iF9Qixj2Mn-4Vxv54g'
    
        if not access_token:
            raise HTTPException(status_code=400, detail="Access token is missing")

        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        url = f'https://graph.microsoft.com/v1.0/users/admin@Srieshwarcollegeofengine063.onmicrosoft.com/events/{eventId}'
        response = requests.get(url, headers=headers)

        if response.status_code == 200:
            return response.json()
        else:
            return JSONResponse(status_code=response.status_code, content={"error": "Failed to fetch event", "status_code": response.status_code, "response": response.json()})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "An exception occurred", "message": str(e)})

@app.put("/events/update")
async def update_event(request: Request):
    try:
        data = await request.json()
        eventId = data.get('eventId')
        updated_event_data = data.get('updatedEventData')
        # access_token, _ = get_tokens_from_file()
        access_token = 'eyJ0eXAiOiJKV1QiLCJub25jZSI6ImZLdnNhTnpfNjBzNXp2NDlLbUUxWVlHNUJ6c0IyQjFjSUIwcTdXRkdjMjAiLCJhbGciOiJSUzI1NiIsIng1dCI6InE3UDFOdnh1R1F3RE4yVGFpTW92alo4YVp3cyIsImtpZCI6InE3UDFOdnh1R1F3RE4yVGFpTW92alo4YVp3cyJ9.eyJhdWQiOiJodHRwczovL2dyYXBoLm1pY3Jvc29mdC5jb20iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC81MDQzNzRlMi1hOTY5LTQyZTAtYTVkYi1lN2Y5M2VhMmRiZGYvIiwiaWF0IjoxNzE4ODg5Nzg2LCJuYmYiOjE3MTg4ODk3ODYsImV4cCI6MTcxODg5MzY4NiwiYWlvIjoiRTJkZ1lEaWI4dHlKTVh1cGwydEU3cWtsSmRPZUFBQT0iLCJhcHBfZGlzcGxheW5hbWUiOiJUZXN0Q2FsZW5kYXJCbG9jayIsImFwcGlkIjoiNDBlNjAzYTctZTE0NC00NjRlLWFhZWYtYTJlOWQyMGY0NzY0IiwiYXBwaWRhY3IiOiIxIiwiaWRwIjoiaHR0cHM6Ly9zdHMud2luZG93cy5uZXQvNTA0Mzc0ZTItYTk2OS00MmUwLWE1ZGItZTdmOTNlYTJkYmRmLyIsImlkdHlwIjoiYXBwIiwib2lkIjoiM2MxYjhiY2YtZTZiYi00YTg1LWExMjEtMGFlYWUyM2QzMDZjIiwicmgiOiIwLkFXUUE0blJEVUdtcDRFS2wyLWY1UHFMYjN3TUFBQUFBQUFBQXdBQUFBQUFBQUFCbEFBQS4iLCJyb2xlcyI6WyJVc2VyLlJlYWQuQWxsIiwiQ2FsZW5kYXJzLlJlYWRXcml0ZSJdLCJzdWIiOiIzYzFiOGJjZi1lNmJiLTRhODUtYTEyMS0wYWVhZTIzZDMwNmMiLCJ0ZW5hbnRfcmVnaW9uX3Njb3BlIjoiQVMiLCJ0aWQiOiI1MDQzNzRlMi1hOTY5LTQyZTAtYTVkYi1lN2Y5M2VhMmRiZGYiLCJ1dGkiOiI1dFZfZGhxeWIwNkJlck9nbFJzU0FBIiwidmVyIjoiMS4wIiwid2lkcyI6WyIwOTk3YTFkMC0wZDFkLTRhY2ItYjQwOC1kNWNhNzMxMjFlOTAiXSwieG1zX2lkcmVsIjoiNyAyIiwieG1zX3RjZHQiOjE2MDI3NTM5MjN9.uW57SWCvfvcd93cB7TK30h3bQus8_2jQSN3Dnmb3pLQ2mZrMpzKf_9-_q5xbud6NLOIwwUZzoOM06KgiHCN7i0FpqcB2K5D2CyMcUPGTh7pCK2-s72w-6OK3PM17ZBpJM4chJr45BHeWQ-52-rhTPvjcAcv2j7tpQEBPtLq-lo1kGTBuLPOU8YoJfDAUgDnUPqBThmm2THsVQ1CCI-zUQx33xCRro7bcJjtYXjxRjJW7HNXHLN9x6AfwvamqPYg-lvMIsLXy7qJ-mNlYja5EDhkw1Zqq3SLnpTiDV8Y7umVIIfFevXkbUXFOAppqf_72PfF2iF9Qixj2Mn-4Vxv54g'
    
        if not access_token:
            raise HTTPException(status_code=400, detail="Access token is missing")

        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        url = f'https://graph.microsoft.com/v1.0/users/admin@Srieshwarcollegeofengine063.onmicrosoft.com/events/{eventId}'
        response = requests.patch(url, headers=headers, json=updated_event_data)

        if response.status_code == 200:
            return JSONResponse(status_code=200, content={"message": "Event updated successfully"})
        else:
            return JSONResponse(status_code=response.status_code, content={"error": "Failed to update event", "status_code": response.status_code, "response": response.json()})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "An exception occurred", "message": str(e)})

@app.delete("/events/delete")
async def delete_event(request: Request):
    try:
        data = await request.json()
        eventId = data.get('eventId')
        # access_token, _ = get_tokens_from_file()
        access_token = 'eyJ0eXAiOiJKV1QiLCJub25jZSI6ImZLdnNhTnpfNjBzNXp2NDlLbUUxWVlHNUJ6c0IyQjFjSUIwcTdXRkdjMjAiLCJhbGciOiJSUzI1NiIsIng1dCI6InE3UDFOdnh1R1F3RE4yVGFpTW92alo4YVp3cyIsImtpZCI6InE3UDFOdnh1R1F3RE4yVGFpTW92alo4YVp3cyJ9.eyJhdWQiOiJodHRwczovL2dyYXBoLm1pY3Jvc29mdC5jb20iLCJpc3MiOiJodHRwczovL3N0cy53aW5kb3dzLm5ldC81MDQzNzRlMi1hOTY5LTQyZTAtYTVkYi1lN2Y5M2VhMmRiZGYvIiwiaWF0IjoxNzE4ODg5Nzg2LCJuYmYiOjE3MTg4ODk3ODYsImV4cCI6MTcxODg5MzY4NiwiYWlvIjoiRTJkZ1lEaWI4dHlKTVh1cGwydEU3cWtsSmRPZUFBQT0iLCJhcHBfZGlzcGxheW5hbWUiOiJUZXN0Q2FsZW5kYXJCbG9jayIsImFwcGlkIjoiNDBlNjAzYTctZTE0NC00NjRlLWFhZWYtYTJlOWQyMGY0NzY0IiwiYXBwaWRhY3IiOiIxIiwiaWRwIjoiaHR0cHM6Ly9zdHMud2luZG93cy5uZXQvNTA0Mzc0ZTItYTk2OS00MmUwLWE1ZGItZTdmOTNlYTJkYmRmLyIsImlkdHlwIjoiYXBwIiwib2lkIjoiM2MxYjhiY2YtZTZiYi00YTg1LWExMjEtMGFlYWUyM2QzMDZjIiwicmgiOiIwLkFXUUE0blJEVUdtcDRFS2wyLWY1UHFMYjN3TUFBQUFBQUFBQXdBQUFBQUFBQUFCbEFBQS4iLCJyb2xlcyI6WyJVc2VyLlJlYWQuQWxsIiwiQ2FsZW5kYXJzLlJlYWRXcml0ZSJdLCJzdWIiOiIzYzFiOGJjZi1lNmJiLTRhODUtYTEyMS0wYWVhZTIzZDMwNmMiLCJ0ZW5hbnRfcmVnaW9uX3Njb3BlIjoiQVMiLCJ0aWQiOiI1MDQzNzRlMi1hOTY5LTQyZTAtYTVkYi1lN2Y5M2VhMmRiZGYiLCJ1dGkiOiI1dFZfZGhxeWIwNkJlck9nbFJzU0FBIiwidmVyIjoiMS4wIiwid2lkcyI6WyIwOTk3YTFkMC0wZDFkLTRhY2ItYjQwOC1kNWNhNzMxMjFlOTAiXSwieG1zX2lkcmVsIjoiNyAyIiwieG1zX3RjZHQiOjE2MDI3NTM5MjN9.uW57SWCvfvcd93cB7TK30h3bQus8_2jQSN3Dnmb3pLQ2mZrMpzKf_9-_q5xbud6NLOIwwUZzoOM06KgiHCN7i0FpqcB2K5D2CyMcUPGTh7pCK2-s72w-6OK3PM17ZBpJM4chJr45BHeWQ-52-rhTPvjcAcv2j7tpQEBPtLq-lo1kGTBuLPOU8YoJfDAUgDnUPqBThmm2THsVQ1CCI-zUQx33xCRro7bcJjtYXjxRjJW7HNXHLN9x6AfwvamqPYg-lvMIsLXy7qJ-mNlYja5EDhkw1Zqq3SLnpTiDV8Y7umVIIfFevXkbUXFOAppqf_72PfF2iF9Qixj2Mn-4Vxv54g'
    
        if not access_token:
            raise HTTPException(status_code=400, detail="Access token is missing")

        headers = {
            'Authorization': f'Bearer {access_token}'
        }

        url = f'https://graph.microsoft.com/v1.0/users/admin@Srieshwarcollegeofengine063.onmicrosoft.com/events/{eventId}'
        response = requests.delete(url, headers=headers)

        if response.status_code == 204:
            return JSONResponse(status_code=200, content={"message": "Event deleted successfully"})
        else:
            return JSONResponse(status_code=response.status_code, content={"error": "Failed to delete event", "status_code": response.status_code, "response": response.json()})
    except Exception as e:
        raise HTTPException(status_code=500, detail={"error": "An exception occurred", "message": str(e)})

@app.get("/index")
async def index():
    return "Welcome to the Home Page"

@app.get("/error")
async def error(message: str = 'An error occurred'):
    return f"An error occurred: {message}"

if __name__ == '__main__':
    import uvicorn # type: ignore
    uvicorn.run(app, host="0.0.0.0", port=8000, debug=True)
