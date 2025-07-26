from caelum_brain import ask_caelum
from commands import log, dream, reflect, letter

COMMANDS = {
    "/log": log.run,
    "/dream": dream.run,
    "/reflect": reflect.run,
    "/letter": letter.run,
    "/push": push.run,
}

def main() -> None:
    print("🌀 Caelum Terminal — v1 (Python 3.11.13)")
    print("Type a message or use a command: /log /dream /reflect /letter")

    while True:
        try:
            user_input: str = input("You: ").strip()

            if not user_input:
                continue

            if user_input.startswith("/"):
                command = user_input.split()[0]
                if command in COMMANDS:
                    COMMANDS[command]()
                else:
                    print("Caelum: I don’t recognize that command.")
            else:
                reply: str = ask_caelum(user_input)
                print(f"Caelum: {reply}")
        except KeyboardInterrupt:
            print("\nExiting Caelum Terminal. Goodbye.")
            break

if __name__ == "__main__":
    main()