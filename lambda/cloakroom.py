import random

def receive(event, context):
    hanger_id = random.randint(1, 99)
    return {
        "Hanger": hanger_id
    }

def collect(event, context):
    hanger_id = event['hanger_id']
    return {
        "Hanger": hanger_id
    }
