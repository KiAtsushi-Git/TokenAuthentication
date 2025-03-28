import asyncio
import aiohttp


async def send_token_request(token):
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"http://127.0.0.1:1830/Tlogin", params={"token": token}
        ) as response:
            if response.status == 200:
                """Тут вы можете выполнить функцию сохранения токена"""
                return await response.json()
            else:
                return None


if __name__ == "__main__":
    token = "токен"
    if token:
        check = asyncio.run(send_token_request(token))
        if check:
            print("Login")
        else:
            print("No-No-No")
    else:
        print("Invalid token")
        exit()
