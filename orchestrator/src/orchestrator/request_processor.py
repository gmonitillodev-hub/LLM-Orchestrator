from classes import Request


def get_request():
    file_path = input("\n   File path: ")

    request = Request(
        file_path=file_path
    )

    return request


def accept_new_request():
    try:

        return get_request()

    except Exception as e:
        print("\n Wrong input data, details: ")

        if hasattr(e, "errors"):

            for error in e.errors():

                if error['loc']:
                    field_name = error['loc'][0]
                elif error['input']:
                    field_name = list(error['input'].keys())[0]
                else:
                    field_name = "Field"

                error_msg = f"{field_name} -> {error['msg']}"
                print(f"    {error_msg}")

            return accept_new_request()

        else:
            print(e)
            return accept_new_request()


def ask_new_request():
    while True:
        new_request = input("\n Do you want to send another request (y/n)? ").strip().lower()

        match new_request:
            case "y":
                return True
            case "n":
                return False
            case _:
                print(" Invalid input. Please type 'y' or 'n'.")
