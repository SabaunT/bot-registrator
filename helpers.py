def listener(messages):
    """
    When new messages arrive bot will call this function.
    """
    for m in messages:
        if m.content_type == 'text':
            # print the sent message to the console
            print(f'{m.chat.first_name} [{m.chat.id}] : {m.text}')
