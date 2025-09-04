# client.py: A simple asynchronous TCP client for interacting with the T.H.E.A. core.
# It uses `aioconsole` for non-blocking user input and `colorama` for styled output.
# The client handles a custom message protocol with a unique delimiter to ensure
# complete messages are processed correctly.

import asyncio
import aioconsole
from colorama import init, Fore, Style

init(autoreset=True)

# --- Connection Settings ---
HOST = "127.0.0.1"
PORT = 8888

END_OF_MESSAGE = "\n\n__END_OF_MESSAGE__\n\n"


async def display_from_server(reader):
    """Asynchronously listens for delimited messages from the server and displays them."""
    buffer = ""
    while True:
        try:
            chunk = await reader.read(1024)
            if not chunk:
                print(f"{Fore.RED}\n[CLIENT: Connection to the core was lost...]")
                break

            buffer += chunk.decode("utf-8", errors="ignore")

            while END_OF_MESSAGE in buffer:

                message, buffer = buffer.split(END_OF_MESSAGE, 1)

                if ":::" in message:
                    msg_type, content = message.split(":::", 1)
                else:
                    msg_type = "SYSTEM"
                    content = "[Message from core without header]:\n" + message

                if msg_type == "RESPONSE":
                    print(
                        f"\n{Fore.YELLOW}<< Entity:{Style.RESET_ALL}\n{Fore.CYAN}{content}"
                    )
                elif msg_type == "SYSTEM":
                    print(
                        f"\n{Fore.YELLOW}<< SYSTEM:{Style.RESET_ALL}\n{Fore.WHITE}{content}"
                    )

                print(
                    f"{Fore.GREEN}>> Your input: {Style.RESET_ALL}", end="", flush=True
                )

        except (asyncio.IncompleteReadError, ConnectionResetError):
            print(f"{Fore.RED}\n[CLIENT: The connection to the core was terminated.]")
            break
        except Exception as e:
            print(f"{Fore.RED}\n[CLIENT: An error occurred: {e}]")
            break


async def send_to_server(writer):
    """Waits for user input and sends it to the server."""
    while True:
        user_input = await aioconsole.ainput()
        if user_input:
            clear_line = "\r\033[K"
            print(f"{clear_line}{Fore.GREEN}>> {user_input}{Style.RESET_ALL}")
            writer.write(user_input.encode("utf-8"))
            await writer.drain()


async def main():
    print(f"{Fore.CYAN}[CLIENT: Attempting to connect to the core at {HOST}:{PORT}...]")
    try:
        reader, writer = await asyncio.open_connection(HOST, PORT)
        print(
            f"{Fore.GREEN}[CLIENT: Connection established. You can now start the conversation.]"
        )
        print(f"{Fore.GREEN}>> Your input: {Style.RESET_ALL}", end="", flush=True)

        await asyncio.gather(display_from_server(reader), send_to_server(writer))
    except ConnectionRefusedError:
        print(f"{Fore.RED}[CLIENT: Connection failed. Is the core (main.py) running?]")
    finally:
        print(f"{Fore.RED}[CLIENT: Session terminated.]")


if __name__ == "__main__":
    try:
        import aioconsole
    except ImportError:
        import subprocess, sys

        print("Installing 'aioconsole' for asynchronous input...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "aioconsole"])

    try:
        import sentence_transformers
    except ImportError:
        import subprocess, sys

        print("Installing 'sentence-transformers' for the reranker...")
        subprocess.check_call(
            [sys.executable, "-m", "pip", "install", "-U", "sentence-transformers"]
        )

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        pass
