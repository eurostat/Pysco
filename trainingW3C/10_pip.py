
# https://pypi.org/
# pip3 install camelcase
# pip3 uninstall camelcase
# pip3 list

import camelcase

c = camelcase.CamelCase()
txt = "hello world"
print(c.hump(txt))

