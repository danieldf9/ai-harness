import re
s = "<thought>User's request: 'deep research...'"
print(repr(re.sub(r'<(?:thought|think)>.*?(?:</(?:thought|think)>|$)', '', s, flags=re.DOTALL | re.IGNORECASE)))
