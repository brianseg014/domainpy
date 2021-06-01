import decimal

def serialize(obj):
    if isinstance(obj, list):
        for i in range(len(obj)):
            obj[i] = serialize(obj[i])
        return obj
    elif isinstance(obj, dict):
        for k in obj.keys():
            obj[k] = serialize(obj[k])
        return obj
    elif isinstance(obj, float):
        return decimal.Decimal(str(obj))
    else:
        return obj


def deserialize(obj):
    if isinstance(obj, list):
        for i in range(len(obj)):
            obj[i] = deserialize(obj[i])
        return obj
    elif isinstance(obj, dict):
        for k in obj.keys():
            obj[k] = deserialize(obj[k])
        return obj
    elif isinstance(obj, decimal.Decimal):
        if obj % 1 == 0:
            return int(obj)
        else:
            return float(obj)
    else:
        return obj