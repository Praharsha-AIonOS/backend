def get_voice(gender: str) -> str:
    gender = gender.lower()
    if gender == "male":
        return "hitesh"
    elif gender == "female":
        return "manisha"
    else:
        raise ValueError("Unsupported gender")
