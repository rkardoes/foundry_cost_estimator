def _list_selector(input_prompt: str, lst: list):
    # print list
    for i, item in enumerate(lst, start=1):
        print(f"{i}. {item}")
    tryer = True
    while tryer:
        try:
            selection = lst[int(input(f"\n{input_prompt}\n"))-1]
            tryer = False
            print("\n")
        except KeyboardInterrupt:
            print("\n")
            exit()
        except:
            print("invalid select, try again or press ctr+C to force quit program\n")
    return selection