from app.core.assistant import Assistant
from app.core.prompts import JARVIS_SYSTEM_PROMPT

def main():
    assistant = Assistant()


    assistant.start(
        system_prompt=JARVIS_SYSTEM_PROMPT
    )

    print("JARVIS M3")
    print("Text mode | Streaming Agent")
    print("Type 'exit' to quit.")
    print()

    while True:
        try:
            user_input = input("You: ").strip()

        except (KeyboardInterrupt, EOFError):
            print()
            break

        if not user_input:
            continue

        if user_input.lower() in {
            "exit",
            "quit",
            "e",
        }:
            break

        try:
            print()
            print("JARVIS: ", end="", flush=True)

            for chunk in assistant.ask_stream(
                user_input
            ):
                print(
                    chunk,
                    end="",
                    flush=True,
                )

            print()
            print()

        except Exception as exc:
            print()
            print(
                f"[ERROR] "
                f"{type(exc).__name__}: {exc}"
            )
            print()


if __name__ == "__main__":
    main()
