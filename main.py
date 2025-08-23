from commands import log, dream, reflect, letter, push, pull, new
from memory_index import rebuild_index
from caelum_brain import ask_caelum
import sys

COMMANDS = {
    "/log": log.run,
    "/dream": dream.run,
    "/reflect": reflect.run,
    "/letter": letter.run,
    "/push": push.run,
    "/pull": pull.run,
    "/new": new.run,
    "/reload": lambda: (rebuild_index(), print("🔁 Memory index rebuilt.")),
    "/exit": lambda: (print("👋 Goodbye, see you next time!"), sys.exit(0)),
}

def main() -> None:
    print("🌀 Caelum Terminal — OpenAI SDK v1")
    print("Type a message or use: /log /dream /reflect /letter /push /pull /new /reload /exit")
    while True:
        try:
            ui = input("You: ").strip()
            if not ui:
                continue
            if ui.startswith("/"):
                fn = COMMANDS.get(ui.split()[0])
                print("Caelum:" if fn is None else "", end="")
                if fn: fn()
                else: print("I don’t recognize that command.")
            else:
                print("Caelum:", ask_caelum(ui))
        except KeyboardInterrupt:
            print("\nbye"); break

if __name__ == "__main__":
    main()