def hello(event, context):
    return {
        "Message": f"Hello {event['name']}"
    }

def goodbye(event, context):
    return {
        "Message": f"Goodbye {event['name']}"
    }
